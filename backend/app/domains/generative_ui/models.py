import uuid
from typing import Any

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, CreatedAtMixin, JSONDocument, UUIDPrimaryKeyMixin
from app.domains.users.models import User
from app.domains.workspaces.models import Workspace


class UIVersion(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """One immutable, approved state of a workspace's UI.

    Rows are only ever inserted. Restoring an old version inserts a copy as the
    newest version. A database trigger (see migration 0002) rejects updates to
    the content columns, so history cannot be rewritten even by mistake.
    """

    __tablename__ = "ui_versions"
    __table_args__ = (
        UniqueConstraint(
            "workspace_id", "version_number", name="uq_ui_versions_workspace_id_version_number"
        ),
    )

    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey(Workspace.id, ondelete="CASCADE"))
    version_number: Mapped[int] = mapped_column(Integer)
    parent_version_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("ui_versions.id", ondelete="SET NULL")
    )
    # The component tree, including its data bindings and actions.
    ui_schema: Mapped[dict[str, Any]] = mapped_column(JSONDocument)
    theme: Mapped[dict[str, Any]] = mapped_column(JSONDocument)
    # Framework and design-system selection.
    design: Mapped[dict[str, Any]] = mapped_column(JSONDocument)
    # The product around the screens (navigation, entities, assets, design direction).
    # NULL for a single stand-alone view.
    application: Mapped[dict[str, Any] | None] = mapped_column(JSONDocument)
    description: Mapped[str] = mapped_column(String(300))
    source: Mapped[str] = mapped_column(String(32))
    # How the version came to be: proposal id, instruction, operations, restored-from.
    source_metadata: Mapped[dict[str, Any]] = mapped_column(JSONDocument, default=dict)
    created_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey(User.id, ondelete="SET NULL"))
