"""In-process rate limiting.

A sliding window per key (user id or client address). State lives in the
process, so limits are per application instance: with several instances behind
a load balancer the effective limit is multiplied. ``RateLimiter`` is the seam
for a shared store when that matters.
"""

import math
import time
from collections import deque
from collections.abc import Callable
from typing import Protocol

from app.core.exceptions import RateLimitExceededException

_PRUNE_THRESHOLD = 10_000


class RateLimiter(Protocol):
    async def check(self, key: str) -> None:
        """Record a request for ``key``; raise ``RateLimitExceededException`` if over budget."""
        ...


class SlidingWindowRateLimiter:
    """Allows at most ``limit`` requests per ``window_seconds`` for each key.

    Safe for concurrent requests on one event loop: ``check`` never awaits, so
    it cannot be interleaved.
    """

    def __init__(
        self,
        limit: int,
        window_seconds: float = 60.0,
        *,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._limit = limit
        self._window = window_seconds
        self._clock = clock
        self._hits: dict[str, deque[float]] = {}

    @property
    def enabled(self) -> bool:
        return self._limit > 0

    async def check(self, key: str) -> None:
        if not self.enabled:
            return
        now = self._clock()
        hits = self._hits.setdefault(key, deque())
        while hits and now - hits[0] >= self._window:
            hits.popleft()
        if len(hits) >= self._limit:
            raise RateLimitExceededException(math.ceil(self._window - (now - hits[0])))
        hits.append(now)
        if len(self._hits) > _PRUNE_THRESHOLD:
            self._prune(now)

    def _prune(self, now: float) -> None:
        """Forget keys with no recent requests so the table cannot grow without bound."""
        stale = [
            key for key, hits in self._hits.items() if not hits or now - hits[-1] >= self._window
        ]
        for key in stale:
            del self._hits[key]
