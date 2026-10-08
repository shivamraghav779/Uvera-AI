import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.workspaces.models import Workspace


class WorkspaceRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, *, user_id: uuid.UUID | None, title: str | None) -> Workspace:
        workspace = Workspace(user_id=user_id, title=title)
        self._db.add(workspace)
        await self._db.flush()
        return workspace

    async def get(self, workspace_id: uuid.UUID, *, for_update: bool = False) -> Workspace | None:
        """Fetch a workspace; ``for_update`` locks its row until the transaction ends."""
        statement = select(Workspace).where(Workspace.id == workspace_id)
        if for_update:
            statement = statement.with_for_update().execution_options(populate_existing=True)
        return (await self._db.scalars(statement)).first()

    async def list_for_user(
        self, user_id: uuid.UUID | None, *, limit: int, offset: int
    ) -> Sequence[Workspace]:
        owner = Workspace.user_id.is_(None) if user_id is None else Workspace.user_id == user_id
        statement = (
            select(Workspace)
            .where(owner)
            .order_by(Workspace.updated_at.desc(), Workspace.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return (await self._db.scalars(statement)).all()

    async def delete(self, workspace: Workspace) -> None:
        await self._db.delete(workspace)
        await self._db.flush()
