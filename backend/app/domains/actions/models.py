import uuid
from typing import Any

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, CreatedAtMixin, JSONDocument, UUIDPrimaryKeyMixin
from app.domains.workspaces.models import Workspace


class UIAction(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """Audit record of an allowlisted action executed for a workspace."""

    __tablename__ = "ui_actions"
    __table_args__ = (Index("ix_ui_actions_workspace_id_created_at", "workspace_id", "created_at"),)

    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey(Workspace.id, ondelete="CASCADE"))
    action_type: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONDocument, default=dict)
