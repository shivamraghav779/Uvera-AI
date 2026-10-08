import uuid
from collections.abc import Mapping, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.generative_ui.models import UIVersion


class UIVersionRepository:
    """Append-only access to UI versions. There is deliberately no update or delete."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def add(
        self,
        *,
        workspace_id: uuid.UUID,
        version_number: int,
        parent_version_id: uuid.UUID | None,
        ui_schema: Mapping[str, object],
        theme: Mapping[str, object],
        design: Mapping[str, object],
        application: Mapping[str, object] | None = None,
        description: str,
        source: str,
        source_metadata: Mapping[str, object],
        created_by: uuid.UUID | None,
    ) -> UIVersion:
        version = UIVersion(
            workspace_id=workspace_id,
            version_number=version_number,
            parent_version_id=parent_version_id,
            ui_schema=dict(ui_schema),
            theme=dict(theme),
            design=dict(design),
            application=dict(application) if application is not None else None,
            description=description,
            source=source,
            source_metadata=dict(source_metadata),
            created_by=created_by,
        )
        self._db.add(version)
        await self._db.flush()
        return version

    async def get(self, workspace_id: uuid.UUID, version_id: uuid.UUID) -> UIVersion | None:
        statement = select(UIVersion).where(
            UIVersion.id == version_id, UIVersion.workspace_id == workspace_id
        )
        return (await self._db.scalars(statement)).first()

    async def get_by_number(self, workspace_id: uuid.UUID, version_number: int) -> UIVersion | None:
        statement = select(UIVersion).where(
            UIVersion.workspace_id == workspace_id, UIVersion.version_number == version_number
        )
        return (await self._db.scalars(statement)).first()

    async def list_for_workspace(
        self, workspace_id: uuid.UUID, *, limit: int, offset: int = 0
    ) -> Sequence[UIVersion]:
        """Versions of a workspace, newest first."""
        statement = (
            select(UIVersion)
            .where(UIVersion.workspace_id == workspace_id)
            .order_by(UIVersion.version_number.desc())
            .limit(limit)
            .offset(offset)
        )
        return (await self._db.scalars(statement)).all()

    async def numbers_for(self, version_ids: Sequence[uuid.UUID]) -> dict[uuid.UUID, int]:
        if not version_ids:
            return {}
        statement = select(UIVersion.id, UIVersion.version_number).where(
            UIVersion.id.in_(version_ids)
        )
        return {row.id: row.version_number for row in await self._db.execute(statement)}
