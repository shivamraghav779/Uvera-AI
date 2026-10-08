"""The asset engine: turns planned images into stored assets and serves them.

For each planned image it picks the provider its decision calls for, falls back
to the internal provider when that one is missing or fails, stores the bytes and
returns the reference a UI document carries. An image is optional by design: no
failure here may fail the generation that asked for it.
"""

import asyncio
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from itertools import pairwise

from app.core.exceptions import AssetException, ResourceNotFoundException
from app.core.logging import get_logger
from app.core.security import Principal
from app.database.unit_of_work import UnitOfWork
from app.domains.assets.models import StoredAsset
from app.domains.assets.providers import ImageProvider, ImageRequest, ImageResult
from app.domains.assets.repository import AssetRepository
from app.domains.assets.schemas import (
    IMAGE_DECISIONS,
    AssetCreate,
    AssetDecision,
    AssetRead,
    PlannedAsset,
)
from app.domains.generative_ui.document import Asset, AssetKind, AssetSource
from app.domains.workspaces.service import WorkspaceService

logger = get_logger(__name__)

MAX_CONCURRENT_FETCHES = 3
# The size written into a document says how an image is proportioned, within these bounds.
MIN_DOCUMENT_SIDE, MAX_DOCUMENT_SIDE = 16, 4096


def document_size(width: int, height: int) -> tuple[int, int]:
    """An image's proportions as a size a document accepts.

    A found photograph can be far larger than anything a document may claim
    (or report no size at all); the shape is kept and the numbers are scaled.
    """
    width, height = max(width, 1), max(height, 1)
    scale = min(1.0, MAX_DOCUMENT_SIDE / max(width, height))

    def side(value: int) -> int:
        return min(max(round(value * scale), MIN_DOCUMENT_SIDE), MAX_DOCUMENT_SIDE)

    return side(width), side(height)


MAX_ASSETS_LISTED = 200
CACHE_SECONDS = 31_536_000  # assets never change once stored


def asset_url(asset_id: uuid.UUID) -> str:
    return f"/api/v1/assets/{asset_id}/content"


@dataclass(frozen=True, slots=True)
class AssetContent:
    content: bytes
    content_type: str


class AssetEngine:
    def __init__(
        self,
        *,
        repository: AssetRepository,
        internal: ImageProvider,
        generator: ImageProvider | None,
        searcher: ImageProvider | None,
        uow: UnitOfWork,
    ) -> None:
        self._repository = repository
        self._internal = internal
        self._generator = generator
        self._searcher = searcher
        self._uow = uow

    def providers_for(self, decision: AssetDecision) -> list[ImageProvider]:
        """Providers to try for a decision, in order; built-in artwork is always last.

        A photograph that cannot be found is generated instead, and the other
        way round, before giving up on a real image.
        """
        if decision is AssetDecision.SEARCH:
            remote = [self._searcher, self._generator]
        elif decision is AssetDecision.GENERATE:
            remote = [self._generator, self._searcher]
        else:
            remote = []
        return [provider for provider in remote if provider is not None] + [self._internal]

    def provider_for(self, decision: AssetDecision) -> ImageProvider:
        """The first provider that would be tried for a decision."""
        return self.providers_for(decision)[0]

    async def create_many(
        self, workspace_id: uuid.UUID, planned: Sequence[PlannedAsset], palette: Sequence[str]
    ) -> list[Asset]:
        """Fetch the planned images concurrently, then store them. Order is kept."""
        wanted = [plan for plan in planned if plan.decision in IMAGE_DECISIONS]
        limit = asyncio.Semaphore(MAX_CONCURRENT_FETCHES)

        async def fetch(index: int, plan: PlannedAsset) -> tuple[ImageProvider, ImageResult]:
            async with limit:
                return await self._fetch(plan, tuple(palette), seed=index)

        fetched = await asyncio.gather(*(fetch(i, plan) for i, plan in enumerate(wanted)))
        assets = [
            await self._store(workspace_id, plan, provider, image)
            for plan, (provider, image) in zip(wanted, fetched, strict=True)
        ]
        await self._uow.commit()
        logger.info(
            "assets_created",
            extra={
                "count": len(assets),
                "internal": sum(asset.source is AssetSource.INTERNAL for asset in assets),
            },
        )
        return assets

    async def _fetch(
        self, plan: PlannedAsset, palette: tuple[str, ...], seed: int
    ) -> tuple[ImageProvider, ImageResult]:
        request = ImageRequest(
            prompt=plan.prompt,
            query=plan.query,
            width=plan.width,
            height=plan.height,
            palette=palette,
            seed=seed,
        )
        providers = self.providers_for(plan.decision)
        for provider, fallback in pairwise(providers):
            try:
                return provider, await provider.fetch(request)
            except AssetException:
                logger.warning(
                    "asset_fallback", extra={"provider": provider.name, "fallback": fallback.name}
                )
        # Built-in artwork needs no network; if even that fails the error is real.
        return self._internal, await self._internal.fetch(request)

    async def _store(
        self,
        workspace_id: uuid.UUID,
        plan: PlannedAsset,
        provider: ImageProvider,
        image: ImageResult,
    ) -> Asset:
        stored = await self._repository.add(
            StoredAsset(
                workspace_id=workspace_id,
                kind=plan.kind.value,
                source=provider.source.value,
                provider=provider.name,
                prompt=plan.prompt if provider.source is not AssetSource.SEARCH else plan.query,
                alt=plan.alt,
                attribution=image.attribution,
                content_type=image.content_type,
                width=image.width,
                height=image.height,
                byte_size=len(image.content),
                content=image.content,
            )
        )
        width, height = document_size(image.width, image.height)
        return Asset(
            id=plan.id,
            kind=plan.kind,
            source=provider.source,
            provider=provider.name,
            url=asset_url(stored.id),
            alt=plan.alt,
            prompt=stored.prompt,
            width=width,
            height=height,
            usage=plan.usage,
            screen_id=plan.screen_id,
            attribution=image.attribution,
            created_at=stored.created_at.isoformat(timespec="seconds"),
        )


class AssetService:
    """HTTP-facing use cases: list a workspace's assets, add one, serve the bytes."""

    def __init__(
        self,
        *,
        engine: AssetEngine,
        repository: AssetRepository,
        workspaces: WorkspaceService,
        palette: Sequence[str] = (),
    ) -> None:
        self._engine = engine
        self._repository = repository
        self._workspaces = workspaces
        self._palette = palette

    async def list_assets(
        self, principal: Principal, workspace_id: uuid.UUID, *, limit: int, offset: int
    ) -> list[AssetRead]:
        workspace = await self._workspaces.get(principal, workspace_id)
        stored = await self._repository.list_for_workspace(
            workspace.id, limit=min(limit, MAX_ASSETS_LISTED), offset=offset
        )
        return [
            AssetRead(
                id=asset.id,
                workspace_id=asset.workspace_id,
                kind=AssetKind(asset.kind),
                source=AssetSource(asset.source),
                provider=asset.provider,
                prompt=asset.prompt,
                alt=asset.alt,
                attribution=asset.attribution,
                content_type=asset.content_type,
                width=asset.width,
                height=asset.height,
                byte_size=asset.byte_size,
                url=asset_url(asset.id),
                created_at=asset.created_at,
            )
            for asset in stored
        ]

    async def create(
        self, principal: Principal, workspace_id: uuid.UUID, payload: AssetCreate
    ) -> Asset:
        """Prepare one image. The result is the reference to add to the document
        with an ADD_ASSETS operation; nothing in the workspace's UI changes here."""
        workspace = await self._workspaces.get(principal, workspace_id)
        plan = PlannedAsset(
            id=payload.id,
            decision=payload.decision,
            kind=payload.kind,
            prompt=payload.prompt,
            query=payload.query or payload.alt,
            alt=payload.alt,
            width=payload.width,
            height=payload.height,
        )
        created = await self._engine.create_many(workspace.id, [plan], self._palette)
        if not created:
            raise AssetException("That kind of visual is not an image and cannot be stored.")
        return created[0]

    async def content(self, asset_id: uuid.UUID) -> AssetContent:
        """Bytes of an asset. Assets are addressed by unguessable id, like any image URL."""
        stored = await self._repository.get_with_content(asset_id)
        if stored is None:
            raise ResourceNotFoundException.for_resource("Asset", asset_id)
        return AssetContent(content=stored.content, content_type=stored.content_type)
