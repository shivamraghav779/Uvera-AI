import uuid
from collections.abc import Mapping, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.conversation.models import ConversationMessage
from app.domains.conversation.schemas import MessageRole


class ConversationRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def add(
        self,
        *,
        workspace_id: uuid.UUID,
        role: MessageRole,
        content: str,
        details: Mapping[str, object] | None = None,
    ) -> ConversationMessage:
        message = ConversationMessage(
            workspace_id=workspace_id,
            role=role,
            content=content,
            details=dict(details) if details is not None else None,
        )
        self._db.add(message)
        await self._db.flush()
        return message

    async def list_for_workspace(
        self, workspace_id: uuid.UUID, *, limit: int, offset: int
    ) -> Sequence[ConversationMessage]:
        statement = (
            select(ConversationMessage)
            .where(ConversationMessage.workspace_id == workspace_id)
            .order_by(ConversationMessage.created_at, ConversationMessage.id)
            .limit(limit)
            .offset(offset)
        )
        return (await self._db.scalars(statement)).all()

    async def recent(self, workspace_id: uuid.UUID, *, limit: int) -> list[ConversationMessage]:
        """The latest ``limit`` messages, oldest first."""
        statement = (
            select(ConversationMessage)
            .where(ConversationMessage.workspace_id == workspace_id)
            .order_by(ConversationMessage.created_at.desc(), ConversationMessage.id.desc())
            .limit(limit)
        )
        return list(reversed((await self._db.scalars(statement)).all()))
