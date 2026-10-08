import uuid
from collections.abc import Sequence
from typing import Protocol

from app.core.exceptions import ResourceNotFoundException
from app.core.security import Principal
from app.database.unit_of_work import UnitOfWork
from app.domains.workspaces.models import Workspace
from app.domains.workspaces.repository import WorkspaceRepository
from app.domains.workspaces.schemas import WorkspaceCreate, WorkspaceRead, WorkspaceUpdate


class VersionNumberLookup(Protocol):
    """Resolves version ids to their numbers (implemented by the version repository)."""

    async def numbers_for(self, version_ids: Sequence[uuid.UUID]) -> dict[uuid.UUID, int]: ...


class WorkspaceService:
    def __init__(
        self, repository: WorkspaceRepository, versions: VersionNumberLookup, uow: UnitOfWork
    ) -> None:
        self._repository = repository
        self._versions = versions
        self._uow = uow

    async def create(self, principal: Principal, payload: WorkspaceCreate) -> WorkspaceRead:
        workspace = await self._repository.create(user_id=principal.user_id, title=payload.title)
        await self._uow.commit()
        return (await self._to_read([workspace]))[0]

    async def list_workspaces(
        self, principal: Principal, *, limit: int, offset: int
    ) -> list[WorkspaceRead]:
        workspaces = await self._repository.list_for_user(
            principal.user_id, limit=limit, offset=offset
        )
        return await self._to_read(workspaces)

    async def get(
        self, principal: Principal, workspace_id: uuid.UUID, *, for_update: bool = False
    ) -> Workspace:
        """Return the workspace if it exists and belongs to ``principal``."""
        workspace = await self._repository.get(workspace_id, for_update=for_update)
        if workspace is None or workspace.user_id != principal.user_id:
            raise ResourceNotFoundException.for_resource("Workspace", workspace_id)
        return workspace

    async def read(self, principal: Principal, workspace_id: uuid.UUID) -> WorkspaceRead:
        return (await self._to_read([await self.get(principal, workspace_id)]))[0]

    async def rename(
        self, principal: Principal, workspace_id: uuid.UUID, payload: WorkspaceUpdate
    ) -> WorkspaceRead:
        workspace = await self.get(principal, workspace_id)
        workspace.title = payload.title
        await self._uow.commit()
        return (await self._to_read([workspace]))[0]

    async def delete(self, principal: Principal, workspace_id: uuid.UUID) -> None:
        workspace = await self.get(principal, workspace_id)
        await self._repository.delete(workspace)
        await self._uow.commit()

    async def _to_read(self, workspaces: Sequence[Workspace]) -> list[WorkspaceRead]:
        current_ids = [w.current_version_id for w in workspaces if w.current_version_id]
        numbers = await self._versions.numbers_for(current_ids)
        return [
            WorkspaceRead(
                id=workspace.id,
                title=workspace.title,
                current_version_id=workspace.current_version_id,
                current_version_number=numbers.get(workspace.current_version_id)
                if workspace.current_version_id
                else None,
                created_at=workspace.created_at,
                updated_at=workspace.updated_at,
            )
            for workspace in workspaces
        ]
