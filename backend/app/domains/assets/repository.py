import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import undefer

from app.domains.assets.models import StoredAsset


class AssetRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def add(self, asset: StoredAsset) -> StoredAsset:
        self._db.add(asset)
        await self._db.flush()
        return asset

    async def get_with_content(self, asset_id: uuid.UUID) -> StoredAsset | None:
        statement = (
            select(StoredAsset)
            .where(StoredAsset.id == asset_id)
            .options(undefer(StoredAsset.content))
        )
        return (await self._db.scalars(statement)).first()

    async def list_for_workspace(
        self, workspace_id: uuid.UUID, *, limit: int, offset: int = 0
    ) -> Sequence[StoredAsset]:
        """Assets of a workspace without their bytes, newest first."""
        statement = (
            select(StoredAsset)
            .where(StoredAsset.workspace_id == workspace_id)
            .order_by(StoredAsset.created_at.desc(), StoredAsset.id)
            .limit(limit)
            .offset(offset)
        )
        return (await self._db.scalars(statement)).all()
