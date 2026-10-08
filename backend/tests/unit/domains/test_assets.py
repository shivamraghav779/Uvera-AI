"""Image providers and the asset engine: what is fetched, verified, stored and referenced."""

import asyncio
import uuid
from typing import Any

import httpx
import pytest
from pydantic import SecretStr

from app.core.exceptions import AssetException
from app.domains.assets.providers import (
    ImageProvider,
    ImageRequest,
    ImageResult,
    InternalImageProvider,
    OpenverseImageProvider,
    PollinationsImageProvider,
    UnsplashImageProvider,
    sniff_image_type,
)
from app.domains.assets.schemas import AssetDecision, PlannedAsset
from app.domains.assets.service import AssetEngine
from app.domains.data_sources.providers.rest import allow_any_host, reject_private_hosts
from app.domains.generative_ui.document import AssetSource
from scripts.sample_build import MemoryAssetRepository

JPEG = b"\xff\xd8\xff\xe0" + b"0" * 64
PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 64
REQUEST = ImageRequest(
    prompt="A quiet harbour at dawn", query="harbour dawn", width=1200, height=800
)
WORKSPACE = uuid.uuid4()


def _client(handler: Any) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


def test_image_types_are_recognised_from_bytes_not_claims() -> None:
    assert sniff_image_type(JPEG) == "image/jpeg"
    assert sniff_image_type(PNG) == "image/png"
    assert sniff_image_type(b"RIFF\x00\x00\x00\x00WEBPVP8 ") == "image/webp"
    assert sniff_image_type(b"RIFF\x00\x00\x00\x00WAVEfmt ") is None
    assert sniff_image_type(b"<html><script>alert(1)</script></html>") is None


async def test_internal_provider_draws_from_the_palette_and_is_deterministic() -> None:
    provider = InternalImageProvider()
    request = ImageRequest(
        prompt="hero", query="", width=640, height=360, palette=("#112233", "#445566", "#778899")
    )

    first, second = await provider.fetch(request), await provider.fetch(request)

    svg = first.content.decode()
    assert first.content == second.content, "the same request gives the same picture"
    assert first.content_type == "image/svg+xml" and (first.width, first.height) == (640, 360)
    assert 'viewBox="0 0 640 360"' in svg and "#112233" in svg
    assert "<script" not in svg and "href" not in svg, "nothing in it can load or run anything"
    other = await provider.fetch(ImageRequest(prompt="other", query="", width=640, height=360))
    assert other.content != first.content


async def test_pollinations_sends_only_the_prompt_and_returns_the_image() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, content=JPEG, headers={"content-type": "text/plain"})

    provider = PollinationsImageProvider(
        _client(handler), timeout_seconds=5, check_host=allow_any_host
    )

    image = await provider.fetch(REQUEST)

    [request] = seen
    assert request.url.host == "image.pollinations.ai"
    assert "A%20quiet%20harbour%20at%20dawn" in str(request.url)
    assert dict(request.url.params) == {
        "width": "1200",
        "height": "800",
        "seed": "0",
        "nologo": "true",
    }
    assert "authorization" not in request.headers
    assert (image.content_type, image.width, provider.source) == (
        "image/jpeg",
        1200,
        AssetSource.GENERATED,
    )


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(500),
        httpx.Response(200, content=b"<html>not an image</html>"),
        httpx.Response(200, content=JPEG + b"0" * 6_000_001),
    ],
    ids=["server error", "not an image", "too large"],
)
async def test_unusable_downloads_are_refused(response: httpx.Response) -> None:
    provider = PollinationsImageProvider(
        _client(lambda _request: response), timeout_seconds=5, check_host=allow_any_host
    )

    with pytest.raises(AssetException):
        await provider.fetch(REQUEST)


async def test_timeouts_and_private_hosts_are_failures_not_crashes() -> None:
    def timeout(_request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("slow")

    slow = PollinationsImageProvider(_client(timeout), timeout_seconds=1, check_host=allow_any_host)
    with pytest.raises(AssetException):
        await slow.fetch(REQUEST)

    results = {
        "results": [{"url": "https://127.0.0.1/secret.png", "creator": "x", "license": "by"}]
    }
    internal = OpenverseImageProvider(
        _client(lambda _request: httpx.Response(200, json=results)),
        timeout_seconds=1,
        check_host=reject_private_hosts,
    )
    with pytest.raises(AssetException):
        await internal.fetch(REQUEST)


async def test_openverse_searches_licensed_images_and_keeps_the_attribution() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "api.openverse.org":
            assert request.url.params["q"] == "harbour dawn"
            assert request.url.params["license_type"] == "commercial,modification"
            return httpx.Response(200, json={"results": [
                {"url": "https://images.example.org/broken.jpg", "creator": "A", "license": "by"},
                {"url": "https://images.example.org/good.jpg", "creator": "Mika Ito",
                 "license": "by-sa", "width": 2000, "height": 1300},
            ]})  # fmt: skip
        if request.url.path == "/broken.jpg":
            return httpx.Response(404)
        return httpx.Response(200, content=JPEG)

    provider = OpenverseImageProvider(
        _client(handler), timeout_seconds=5, check_host=allow_any_host
    )

    image = await provider.fetch(REQUEST)

    assert image.attribution == "Mika Ito (CC BY-SA) via Openverse"
    assert (image.width, image.height, provider.source) == (2000, 1300, AssetSource.SEARCH)


async def test_openverse_without_results_is_a_failure() -> None:
    provider = OpenverseImageProvider(
        _client(lambda _request: httpx.Response(200, json={"results": []})),
        timeout_seconds=5,
        check_host=allow_any_host,
    )

    with pytest.raises(AssetException):
        await provider.fetch(REQUEST)


async def test_unsplash_authenticates_with_its_key_and_crops_to_size() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if request.url.host == "api.unsplash.com":
            return httpx.Response(200, json={"results": [
                {"urls": {"raw": "https://images.unsplash.com/photo-1?ixid=1"},
                 "user": {"name": "Lena Brandt"}, "width": 4000, "height": 3000},
            ]})  # fmt: skip
        return httpx.Response(200, content=PNG)

    provider = UnsplashImageProvider(
        _client(handler), SecretStr("unsplash-key"), timeout_seconds=5, check_host=allow_any_host
    )

    image = await provider.fetch(REQUEST)

    search, download = seen
    assert search.headers["authorization"] == "Client-ID unsplash-key"
    assert search.url.params["orientation"] == "landscape"
    assert "authorization" not in download.headers, "the key is not sent to the image host"
    assert "w=1200" in str(download.url) and "h=800" in str(download.url)
    assert image.attribution == "Photo by Lena Brandt on Unsplash"
    assert "unsplash-key" not in repr(provider.__dict__)


# --- The engine --------------------------------------------------------------------------


class _Provider(ImageProvider):
    def __init__(self, name: str, source: AssetSource, *, fail: bool = False) -> None:
        self._name, self._source, self._fail = name, source, fail
        self.requests: list[ImageRequest] = []

    @property
    def name(self) -> str:
        return self._name

    @property
    def source(self) -> AssetSource:
        return self._source

    async def fetch(self, request: ImageRequest) -> ImageResult:
        self.requests.append(request)
        if self._fail:
            raise AssetException("down")
        return ImageResult(JPEG, "image/jpeg", request.width, request.height, f"by {self._name}")


class _Commits:
    count = 0

    async def commit(self) -> None:
        self.count += 1

    async def rollback(self) -> None:
        return None


def _plan(asset_id: str, decision: AssetDecision) -> PlannedAsset:
    return PlannedAsset(
        id=asset_id, decision=decision, prompt=f"{asset_id} prompt", query=f"{asset_id} query",
        alt=f"{asset_id} alt", width=800, height=600, screen_id="home",
    )  # fmt: skip


def _engine(
    generator: ImageProvider | None, searcher: ImageProvider | None
) -> tuple[AssetEngine, MemoryAssetRepository, _Commits]:
    repository, commits = MemoryAssetRepository(), _Commits()
    engine = AssetEngine(
        repository=repository,  # type: ignore[arg-type]
        internal=InternalImageProvider(),
        generator=generator,
        searcher=searcher,
        uow=commits,
    )
    return engine, repository, commits


async def test_each_decision_goes_to_its_provider_and_non_images_store_nothing() -> None:
    generator = _Provider("gen", AssetSource.GENERATED)
    searcher = _Provider("find", AssetSource.SEARCH)
    engine, repository, commits = _engine(generator, searcher)

    assets = await engine.create_many(
        WORKSPACE,
        [
            _plan("made", AssetDecision.GENERATE),
            _plan("found", AssetDecision.SEARCH),
            _plan("drawn", AssetDecision.INTERNAL),
            _plan("symbol", AssetDecision.ICON),
            _plan("figure", AssetDecision.DATA_VISUALIZATION),
        ],
        palette=("#111111", "#222222"),
    )

    assert [(a.id, a.provider, a.source.value) for a in assets] == [
        ("made", "gen", "generated"),
        ("found", "find", "search"),
        ("drawn", "internal", "internal"),
    ]  # fmt: skip
    assert len(repository.assets) == 3 and commits.count == 1
    assert assets[0].prompt == "made prompt" and assets[1].prompt == "found query"
    assert assets[1].attribution == "by find" and assets[0].screen_id == "home"
    assert all(
        a.url == f"/api/v1/assets/{s.id}/content"
        for a, s in zip(assets, repository.assets, strict=True)
    )
    assert {s.workspace_id for s in repository.assets} == {WORKSPACE}
    assert generator.requests[0].palette == ("#111111", "#222222")


async def test_a_failing_provider_falls_back_to_an_internal_image() -> None:
    engine, repository, _ = _engine(_Provider("gen", AssetSource.GENERATED, fail=True), None)

    [asset] = await engine.create_many(WORKSPACE, [_plan("hero", AssetDecision.GENERATE)], ())

    assert (asset.provider, asset.source) == ("internal", AssetSource.INTERNAL)
    assert repository.assets[0].content_type == "image/svg+xml"


async def test_a_missing_provider_is_substituted_by_the_other_kind() -> None:
    generator = _Provider("gen", AssetSource.GENERATED)
    only_generator, _, _ = _engine(generator, None)
    neither, _, _ = _engine(None, None)

    assert only_generator.provider_for(AssetDecision.SEARCH) is generator
    assert neither.provider_for(AssetDecision.GENERATE).name == "internal"
    assert neither.provider_for(AssetDecision.SEARCH).name == "internal"


async def test_a_photograph_that_cannot_be_found_is_generated_before_giving_up() -> None:
    generator = _Provider("gen", AssetSource.GENERATED)
    engine, _, _ = _engine(generator, _Provider("find", AssetSource.SEARCH, fail=True))

    [asset] = await engine.create_many(WORKSPACE, [_plan("hero", AssetDecision.SEARCH)], ())

    assert (asset.provider, asset.source) == ("gen", AssetSource.GENERATED)
    assert [p.name for p in engine.providers_for(AssetDecision.GENERATE)] == [
        "gen",
        "find",
        "internal",
    ]


async def test_built_in_artwork_is_used_only_when_every_provider_fails() -> None:
    engine, _, _ = _engine(
        _Provider("gen", AssetSource.GENERATED, fail=True),
        _Provider("find", AssetSource.SEARCH, fail=True),
    )

    [asset] = await engine.create_many(WORKSPACE, [_plan("hero", AssetDecision.SEARCH)], ())

    assert (asset.provider, asset.source) == ("internal", AssetSource.INTERNAL)


async def test_pollinations_waits_out_a_refusal_and_takes_one_request_at_a_time() -> None:
    answers = [httpx.Response(402), httpx.Response(429), httpx.Response(200, content=JPEG)]
    active = peak = 0

    async def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal active, peak
        active += 1
        peak = max(peak, active)
        await asyncio.sleep(0)
        active -= 1
        return answers.pop(0) if answers else httpx.Response(200, content=JPEG)

    provider = PollinationsImageProvider(
        _client(handler), timeout_seconds=5, check_host=allow_any_host
    )
    provider.retry_pause_seconds = 0

    images = await asyncio.gather(*(provider.fetch(REQUEST) for _ in range(3)))

    assert [image.content_type for image in images] == ["image/jpeg"] * 3
    assert peak == 1, "the keyless tier refuses concurrent requests"


async def test_pollinations_gives_up_on_a_lasting_refusal_and_cools_off() -> None:
    calls = 0

    def refuse(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(402)

    provider = PollinationsImageProvider(
        _client(refuse), timeout_seconds=5, check_host=allow_any_host
    )
    provider.retry_pause_seconds = 0
    try:
        with pytest.raises(AssetException):
            await provider.fetch(REQUEST)
        assert calls == PollinationsImageProvider.ATTEMPTS
        # Having been refused repeatedly, it stops asking for a while instead of delaying builds.
        with pytest.raises(AssetException):
            await provider.fetch(REQUEST)
        assert calls == PollinationsImageProvider.ATTEMPTS
    finally:
        PollinationsImageProvider._refused_until = 0.0


def test_a_documents_image_size_keeps_the_shape_within_bounds() -> None:
    from app.domains.assets.service import document_size

    assert document_size(1200, 800) == (1200, 800)
    assert document_size(7087, 5102) == (4096, 2949)
    assert document_size(0, 0) == (16, 16)
    assert document_size(9000, 4) == (4096, 16)
