"""Shared plumbing for providers reached over an HTTP chat-completion API."""

import asyncio
import json
import time
from abc import abstractmethod
from collections.abc import AsyncIterator, Sequence
from typing import Any

import httpx
from pydantic import SecretStr

from app.ai.llm.base import (
    GenerationOptions,
    LLMChunk,
    LLMMessage,
    LLMProvider,
    LLMResponse,
    TokenUsage,
)
from app.core.exceptions import LLMException, LLMFailureKind
from app.core.logging import get_logger

logger = get_logger(__name__)

JSON_OBJECT_RESPONSE_FORMAT = {"type": "json_object"}
SSE_DATA_PREFIX = "data:"
SSE_DONE = "[DONE]"

_REQUEST_TIMEOUT_STATUS = 408
_RATE_LIMITED_STATUS = 429
_AUTH_STATUSES = frozenset({401, 403})
_SERVER_ERROR = 500


MAX_RETRY_AFTER_SECONDS = 120.0


def _retry_after(response: httpx.Response) -> float | None:
    """Seconds the provider asked us to wait, from a numeric ``Retry-After`` header."""
    try:
        seconds = float(response.headers.get("retry-after", ""))
    except ValueError:
        return None
    return min(seconds, MAX_RETRY_AFTER_SECONDS) if seconds > 0 else None


def serialize_messages(messages: Sequence[LLMMessage]) -> list[dict[str, str]]:
    return [{"role": message.role.value, "content": message.content} for message in messages]


def failure_kind_for_status(status: int) -> LLMFailureKind:
    """Classify an upstream HTTP error status."""
    if status == _RATE_LIMITED_STATUS:
        return LLMFailureKind.RATE_LIMITED
    if status == _REQUEST_TIMEOUT_STATUS:
        return LLMFailureKind.TIMEOUT
    if status in _AUTH_STATUSES:
        return LLMFailureKind.AUTHENTICATION
    if status >= _SERVER_ERROR:
        return LLMFailureKind.UNAVAILABLE
    return LLMFailureKind.BAD_REQUEST


class HttpChatProvider(LLMProvider):
    """Template for vendors exposing a JSON chat endpoint with bearer auth.

    Subclasses describe the request body and how to read the response. The
    shared ``httpx.AsyncClient`` is injected and safe for concurrent requests;
    instances hold no per-request state.

    Every way a call can fail is turned into an ``LLMException`` with a
    ``LLMFailureKind``. Transient kinds (timeout, transport, 429, 5xx) are
    retried up to ``max_retries`` times with exponential backoff before the
    failure is reported to the caller (usually the fallback chain).
    """

    def __init__(
        self,
        *,
        api_key: SecretStr,
        model: str,
        base_url: str,
        client: httpx.AsyncClient,
        timeout_seconds: float,
        max_retries: int = 0,
        retry_backoff_seconds: float = 0.5,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._client = client
        self._timeout = timeout_seconds
        self._max_retries = max_retries
        self._retry_backoff = retry_backoff_seconds

    @property
    def model(self) -> str:
        return self._model

    @property
    @abstractmethod
    def _chat_path(self) -> str:
        """Path of the chat endpoint relative to the base URL."""

    @abstractmethod
    def _build_payload(
        self, messages: Sequence[LLMMessage], options: GenerationOptions, *, json_mode: bool
    ) -> dict[str, Any]: ...

    @abstractmethod
    def _parse_response(self, body: Any) -> tuple[str, TokenUsage]:
        """Extract text and usage; may raise KeyError/IndexError/TypeError on odd shapes."""

    @abstractmethod
    def _parse_stream_event(self, event: Any) -> str | None:
        """Text carried by one decoded stream event, or ``None`` for other event types."""

    async def generate_text(
        self, messages: Sequence[LLMMessage], options: GenerationOptions | None = None
    ) -> LLMResponse:
        return await self._complete(messages, options, json_mode=False)

    async def generate_structured(
        self, messages: Sequence[LLMMessage], options: GenerationOptions | None = None
    ) -> LLMResponse:
        return await self._complete(messages, options, json_mode=True)

    async def stream_text(
        self,
        messages: Sequence[LLMMessage],
        options: GenerationOptions | None = None,
        *,
        json_mode: bool = False,
    ) -> AsyncIterator[LLMChunk]:
        options = options or GenerationOptions()
        payload = self._build_payload(messages, options, json_mode=json_mode)
        payload["stream"] = True
        started = time.perf_counter()
        characters = 0
        try:
            async with self._client.stream(
                "POST",
                self._url,
                json=payload,
                headers=self._headers,
                timeout=options.timeout_seconds or self._timeout,
            ) as response:
                if response.is_error:
                    raise self._status_failure(response)
                async for line in response.aiter_lines():
                    chunk = self._decode_stream_line(line)
                    if chunk:
                        characters += len(chunk)
                        yield LLMChunk(chunk, self.name, self.model)
        except httpx.HTTPError as exc:
            raise self._transport_failure(exc) from None
        if characters == 0:
            raise self._failure(LLMFailureKind.BAD_RESPONSE, "empty stream")
        logger.info(
            "llm_stream_completed",
            extra={
                "provider": self.name,
                "model": self.model,
                "duration_ms": round((time.perf_counter() - started) * 1000, 1),
                "characters": characters,
                "json_mode": json_mode,
            },
        )

    def _decode_stream_line(self, line: str) -> str | None:
        """One server-sent-events line -> text, ignoring comments, event names and keep-alives."""
        if not line.startswith(SSE_DATA_PREFIX):
            return None
        data = line[len(SSE_DATA_PREFIX) :].strip()
        if not data or data == SSE_DONE:
            return None
        try:
            return self._parse_stream_event(json.loads(data))
        except (ValueError, KeyError, IndexError, TypeError, AttributeError):
            raise self._failure(LLMFailureKind.BAD_RESPONSE, "unreadable stream event") from None

    async def _complete(
        self, messages: Sequence[LLMMessage], options: GenerationOptions | None, *, json_mode: bool
    ) -> LLMResponse:
        options = options or GenerationOptions()
        payload = self._build_payload(messages, options, json_mode=json_mode)
        started = time.perf_counter()
        body = await self._post_with_retries(payload, options.timeout_seconds or self._timeout)
        try:
            content, usage = self._parse_response(body)
        except (KeyError, IndexError, TypeError, AttributeError):
            raise self._failure(LLMFailureKind.BAD_RESPONSE, "unexpected response shape") from None
        if not content.strip():
            raise self._failure(LLMFailureKind.BAD_RESPONSE, "empty completion")
        logger.info(
            "llm_call_completed",
            extra={
                "provider": self.name,
                "model": self.model,
                "duration_ms": round((time.perf_counter() - started) * 1000, 1),
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens,
                "json_mode": json_mode,
            },
        )
        return LLMResponse(content=content, provider=self.name, model=self.model, usage=usage)

    async def _post_with_retries(self, payload: dict[str, Any], limit_seconds: float) -> Any:
        for attempt in range(self._max_retries + 1):
            try:
                return await self._post(payload, limit_seconds)
            except LLMException as exc:
                if not exc.retryable or attempt == self._max_retries:
                    raise
                delay = self._retry_backoff * (2**attempt)
                logger.warning(
                    "llm_call_retried",
                    extra={
                        "provider": self.name,
                        "model": self.model,
                        "failure_kind": exc.kind.value,
                        "attempt": attempt + 1,
                        "retry_in_seconds": delay,
                    },
                )
                await asyncio.sleep(delay)
        raise AssertionError("unreachable")  # pragma: no cover

    async def _post(self, payload: dict[str, Any], limit_seconds: float) -> Any:
        try:
            response = await self._client.post(
                self._url, json=payload, headers=self._headers, timeout=limit_seconds
            )
        except httpx.HTTPError as exc:
            raise self._transport_failure(exc) from None
        if response.is_error:
            raise self._status_failure(response)
        try:
            return response.json()
        except ValueError:
            raise self._failure(LLMFailureKind.BAD_RESPONSE, "response is not JSON") from None

    @property
    def _url(self) -> str:
        return f"{self._base_url}{self._chat_path}"

    @property
    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._api_key.get_secret_value()}"}

    def _transport_failure(self, error: httpx.HTTPError) -> LLMException:
        if isinstance(error, httpx.TimeoutException):
            return self._failure(LLMFailureKind.TIMEOUT, "timeout")
        # Only the error class is recorded: messages can embed request details.
        return self._failure(LLMFailureKind.TRANSPORT, f"transport error ({type(error).__name__})")

    def _status_failure(self, response: httpx.Response) -> LLMException:
        status = response.status_code
        return self._failure(
            failure_kind_for_status(status),
            f"HTTP {status}",
            upstream_status=status,
            retry_after_seconds=_retry_after(response),
        )

    def _failure(
        self,
        kind: LLMFailureKind,
        reason: str,
        *,
        upstream_status: int | None = None,
        retry_after_seconds: float | None = None,
    ) -> LLMException:
        return LLMException(
            provider=self.name,
            model=self.model,
            kind=kind,
            reason=reason,
            upstream_status=upstream_status,
            retry_after_seconds=retry_after_seconds,
        )
