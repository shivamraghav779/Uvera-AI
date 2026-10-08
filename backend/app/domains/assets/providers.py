"""Sources of images, behind one contract.

    generate   make a new image from a prompt        (Pollinations)
    search     find an existing, licensed photograph (Unsplash, Openverse)
    internal   draw one here, from the theme colours (always available)

The asset engine picks a provider per asset and falls back to the internal one
when a remote provider fails, so a missing image never fails a generation.
Remote providers only ever receive the prompt or query text.
"""

import asyncio
import hashlib
import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from urllib.parse import quote, urlsplit

import httpx
from pydantic import SecretStr

from app.core.exceptions import AssetException, DataSourceException
from app.core.logging import get_logger
from app.domains.data_sources.providers.rest import HostCheck, reject_private_hosts
from app.domains.generative_ui.document import AssetSource

logger = get_logger(__name__)

MAX_IMAGE_BYTES = 6_000_000
_MAGIC: tuple[tuple[bytes, str], ...] = (
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"RIFF", "image/webp"),
)


@dataclass(frozen=True, slots=True)
class ImageRequest:
    """What an image should show. ``prompt`` drives generation, ``query`` drives search."""

    prompt: str
    query: str
    width: int
    height: int
    # Theme colours, used by the internal provider so placeholders match the design.
    palette: tuple[str, ...] = ()
    seed: int = 0


@dataclass(frozen=True, slots=True)
class ImageResult:
    content: bytes
    content_type: str
    width: int
    height: int
    attribution: str | None = None


def sniff_image_type(content: bytes) -> str | None:
    """The image type the bytes really are, whatever a server claimed."""
    for magic, content_type in _MAGIC:
        if content.startswith(magic):
            if content_type == "image/webp" and content[8:12] != b"WEBP":
                continue
            return content_type
    return None


class ImageProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Stable identifier, e.g. ``"pollinations"``."""

    @property
    @abstractmethod
    def source(self) -> AssetSource: ...

    @abstractmethod
    async def fetch(self, request: ImageRequest) -> ImageResult:
        """Return an image for the request; raise ``AssetException`` when it cannot."""


class _RemoteImageProvider(ImageProvider):
    def __init__(
        self,
        client: httpx.AsyncClient,
        *,
        timeout_seconds: float,
        check_host: HostCheck = reject_private_hosts,
    ) -> None:
        self._client = client
        self._timeout = timeout_seconds
        self._check_host = check_host

    def _failure(self, reason: str) -> AssetException:
        logger.warning("image_provider_failed", extra={"provider": self.name, "reason": reason})
        error = AssetException(f"The image provider '{self.name}' could not supply an image.")
        # Kept for callers that treat "slow down" differently from "cannot".
        error.reason = reason  # type: ignore[attr-defined]
        return error

    async def _get(self, url: str, **kwargs: object) -> httpx.Response:
        try:
            response = await self._client.get(url, timeout=self._timeout, **kwargs)  # type: ignore[arg-type]
        except httpx.TimeoutException:
            raise self._failure("timeout") from None
        except httpx.HTTPError as exc:
            raise self._failure(type(exc).__name__) from None
        if response.is_error:
            raise self._failure(f"HTTP {response.status_code}")
        return response

    async def _download(self, url: str) -> tuple[bytes, str]:
        """Image bytes from a public https URL, verified to be an image we serve."""
        parts = urlsplit(url)
        if parts.scheme != "https" or not parts.hostname:
            raise self._failure("non-https image url")
        try:
            await self._check_host(parts.hostname)
        except DataSourceException:
            raise self._failure("image host not allowed") from None
        response = await self._get(url, follow_redirects=True)
        content = response.content
        if len(content) > MAX_IMAGE_BYTES:
            raise self._failure("image too large")
        content_type = sniff_image_type(content)
        if content_type is None:
            raise self._failure("not a supported image")
        return content, content_type


class PollinationsImageProvider(_RemoteImageProvider):
    """Text-to-image through the public Pollinations endpoint (no API key)."""

    BASE_URL = "https://image.pollinations.ai/prompt"

    @property
    def name(self) -> str:
        return "pollinations"

    @property
    def source(self) -> AssetSource:
        return AssetSource.GENERATED

    # The keyless tier serves one request at a time and answers 402/429 to a second one.
    # All requests of this process therefore queue here, and a refusal is waited out.
    _queue = asyncio.Lock()
    THROTTLED = frozenset({"HTTP 402", "HTTP 429"})
    ATTEMPTS = 3
    COOL_OFF_SECONDS = 300.0
    retry_pause_seconds: float = 6.0
    _refused_until: float = 0.0

    async def fetch(self, request: ImageRequest) -> ImageResult:
        url = (
            f"{self.BASE_URL}/{quote(request.prompt[:900], safe='')}"
            f"?width={request.width}&height={request.height}&seed={request.seed}&nologo=true"
        )
        async with self._queue:
            if time.monotonic() < type(self)._refused_until:
                # It kept refusing a moment ago; asking again now only delays the build.
                raise self._failure("cooling off after refusals")
            for attempt in range(1, self.ATTEMPTS + 1):
                try:
                    content, content_type = await self._download(url)
                except AssetException as exc:
                    throttled = getattr(exc, "reason", None) in self.THROTTLED
                    if throttled and attempt == self.ATTEMPTS:
                        type(self)._refused_until = time.monotonic() + self.COOL_OFF_SECONDS
                    if not throttled or attempt == self.ATTEMPTS:
                        raise
                    await asyncio.sleep(self.retry_pause_seconds * attempt)
                else:
                    return ImageResult(content, content_type, request.width, request.height)
        raise self._failure("no attempt made")  # unreachable; keeps the return type total


def _orientation(request: ImageRequest) -> str:
    ratio = request.width / request.height
    if ratio > 1.2:
        return "landscape"
    return "portrait" if ratio < 0.85 else "squarish"


class UnsplashImageProvider(_RemoteImageProvider):
    """Photograph search on Unsplash. Needs an access key."""

    SEARCH_URL = "https://api.unsplash.com/search/photos"

    def __init__(
        self,
        client: httpx.AsyncClient,
        access_key: SecretStr,
        *,
        timeout_seconds: float,
        check_host: HostCheck = reject_private_hosts,
    ) -> None:
        super().__init__(client, timeout_seconds=timeout_seconds, check_host=check_host)
        self._access_key = access_key

    @property
    def name(self) -> str:
        return "unsplash"

    @property
    def source(self) -> AssetSource:
        return AssetSource.SEARCH

    async def fetch(self, request: ImageRequest) -> ImageResult:
        response = await self._get(
            self.SEARCH_URL,
            params={
                "query": request.query[:200],
                "per_page": 6,
                "orientation": _orientation(request),
                "content_filter": "high",
            },
            headers={"Authorization": f"Client-ID {self._access_key.get_secret_value()}"},
        )
        try:
            results = response.json()["results"]
            photo = results[request.seed % len(results)]
            raw_url, author = photo["urls"]["raw"], photo["user"]["name"]
            width, height = int(photo["width"]), int(photo["height"])
        except (ValueError, KeyError, IndexError, TypeError, ZeroDivisionError):
            raise self._failure("no usable result") from None
        sized = f"{raw_url}&w={request.width}&h={request.height}&fit=crop&q=80&fm=jpg"
        content, content_type = await self._download(sized)
        del width, height  # the crop is exactly the requested size
        return ImageResult(
            content, content_type, request.width, request.height, f"Photo by {author} on Unsplash"
        )


class OpenverseImageProvider(_RemoteImageProvider):
    """Search of openly licensed images through Openverse (no API key)."""

    SEARCH_URL = "https://api.openverse.org/v1/images/"

    @property
    def name(self) -> str:
        return "openverse"

    @property
    def source(self) -> AssetSource:
        return AssetSource.SEARCH

    async def fetch(self, request: ImageRequest) -> ImageResult:
        wide = request.width >= request.height
        response = await self._get(
            self.SEARCH_URL,
            params={
                "q": request.query[:200],
                "page_size": 8,
                # Licences that allow commercial use and modification (cropping).
                "license_type": "commercial,modification",
                "aspect_ratio": "wide" if wide else "tall",
                "size": "large,medium",
                "mature": "false",
            },
            headers={"User-Agent": "generative-ui-platform/1.0"},
        )
        try:
            results = response.json()["results"]
        except (ValueError, KeyError, TypeError):
            raise self._failure("unreadable search response") from None
        if not results:
            raise self._failure("no results")
        # Start at a seed-dependent result; move on if one cannot be downloaded.
        start = request.seed % len(results)
        for item in results[start:] + results[:start]:
            try:
                content, content_type = await self._download(str(item["url"]))
            except (AssetException, KeyError):
                continue
            creator = item.get("creator") or "unknown author"
            licence = str(item.get("license", "")).upper()
            return ImageResult(
                content,
                content_type,
                int(item.get("width") or request.width),
                int(item.get("height") or request.height),
                f"{creator} (CC {licence}) via Openverse"[:200],
            )
        raise self._failure("no downloadable result")


class InternalImageProvider(ImageProvider):
    """Abstract artwork drawn from the theme's colours. Needs nothing and never fails.

    Used when an asset is meant to be internal, when no remote provider is
    configured, and as the fallback when one fails.
    """

    _FALLBACK_PALETTE = ("#4F46E5", "#0EA5E9", "#F5F3EF", "#18181B")

    @property
    def name(self) -> str:
        return "internal"

    @property
    def source(self) -> AssetSource:
        return AssetSource.INTERNAL

    async def fetch(self, request: ImageRequest) -> ImageResult:
        svg = self.render(request)
        return ImageResult(svg.encode(), "image/svg+xml", request.width, request.height)

    def render(self, request: ImageRequest) -> str:
        """A soft colour field: blurred blobs of the palette over its background."""
        palette = request.palette or self._FALLBACK_PALETTE
        digest = hashlib.sha256(f"{request.prompt}|{request.seed}".encode()).digest()
        rng = random.Random(digest)
        width, height = request.width, request.height
        background, accents = palette[-2] if len(palette) > 2 else "#F5F5F4", palette[:3]
        blobs = []
        for index in range(5):
            colour = accents[index % len(accents)]
            cx, cy = rng.randint(0, width), rng.randint(0, height)
            radius = rng.randint(min(width, height) // 3, max(width, height) // 2)
            opacity = rng.choice((0.35, 0.45, 0.55))
            blobs.append(
                f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="{colour}" opacity="{opacity}"/>'
            )
        blur = max(width, height) // 9
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
            f'width="{width}" height="{height}" preserveAspectRatio="xMidYMid slice">'
            f'<defs><filter id="b" x="-50%" y="-50%" width="200%" height="200%">'
            f'<feGaussianBlur stdDeviation="{blur}"/></filter></defs>'
            f'<rect width="{width}" height="{height}" fill="{background}"/>'
            f'<g filter="url(#b)">{"".join(blobs)}</g></svg>'
        )
