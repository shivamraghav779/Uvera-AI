import uuid
from typing import Any

from sqlalchemy import Enum, ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, CreatedAtMixin, JSONDocument, UUIDPrimaryKeyMixin
from app.domains.conversation.schemas import MessageRole
from app.domains.workspaces.models import Workspace


class ConversationMessage(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """One turn of a workspace's conversation."""

    __tablename__ = "conversations"
    __table_args__ = (
        Index("ix_conversations_workspace_id_created_at", "workspace_id", "created_at"),
    )

    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey(Workspace.id, ondelete="CASCADE"))
    role: Mapped[MessageRole] = mapped_column(
        Enum(
            MessageRole,
            name="message_role",
            native_enum=False,
            create_constraint=True,
            length=16,
            values_callable=lambda roles: [role.value for role in roles],
        )
    )
    content: Mapped[str] = mapped_column(Text)
    # Structured context for assistant turns (e.g. the proposal a reply described).
    details: Mapped[dict[str, Any] | None] = mapped_column(JSONDocument)
