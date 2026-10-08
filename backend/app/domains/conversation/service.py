import uuid
from collections.abc import Sequence

from app.core.security import Principal
from app.database.unit_of_work import UnitOfWork
from app.domains.conversation.models import ConversationMessage
from app.domains.conversation.repository import ConversationRepository
from app.domains.conversation.schemas import MessageCreate
from app.domains.workspaces.service import WorkspaceService


class ConversationService:
    def __init__(
        self,
        repository: ConversationRepository,
        workspaces: WorkspaceService,
        uow: UnitOfWork,
    ) -> None:
        self._repository = repository
        self._workspaces = workspaces
        self._uow = uow

    async def add_message(
        self, principal: Principal, workspace_id: uuid.UUID, payload: MessageCreate
    ) -> ConversationMessage:
        workspace = await self._workspaces.get(principal, workspace_id)
        message = await self._repository.add(
            workspace_id=workspace.id, role=payload.role, content=payload.content
        )
        await self._uow.commit()
        return message

    async def list_messages(
        self, principal: Principal, workspace_id: uuid.UUID, *, limit: int, offset: int
    ) -> Sequence[ConversationMessage]:
        workspace = await self._workspaces.get(principal, workspace_id)
        return await self._repository.list_for_workspace(workspace.id, limit=limit, offset=offset)
