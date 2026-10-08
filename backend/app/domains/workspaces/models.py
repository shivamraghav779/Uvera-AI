import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.domains.users.models import User


class Workspace(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A persistent UI the user builds through conversation and direct editing.

    The UI itself lives in immutable ``UIVersion`` rows; the workspace only
    points at the current one.
    """

    __tablename__ = "workspaces"

    # NULL while requests are anonymous (no authentication yet).
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey(User.id, ondelete="CASCADE"), index=True
    )
    title: Mapped[str | None] = mapped_column(String(200))
    # Referenced by table name: workspaces and ui_versions point at each other, so
    # this side cannot import the UIVersion class.
    current_version_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("ui_versions.id", ondelete="SET NULL", use_alter=True)
    )
