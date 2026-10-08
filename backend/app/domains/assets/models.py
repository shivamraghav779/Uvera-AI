import uuid

from sqlalchemy import ForeignKey, Integer, LargeBinary, String, Text
from sqlalchemy.orm import Mapped, deferred, mapped_column

from app.database.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin
from app.domains.workspaces.models import Workspace


class StoredAsset(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """An image belonging to a workspace: its bytes and where they came from.

    Documents refer to an asset by the URL that serves this row; the bytes are
    never embedded in a UI document. ``content`` is loaded only when served.
    """

    __tablename__ = "assets"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(Workspace.id, ondelete="CASCADE"), index=True
    )
    kind: Mapped[str] = mapped_column(String(32))
    source: Mapped[str] = mapped_column(String(32))
    provider: Mapped[str] = mapped_column(String(64))
    prompt: Mapped[str | None] = mapped_column(Text)
    alt: Mapped[str] = mapped_column(String(200))
    attribution: Mapped[str | None] = mapped_column(String(200))
    content_type: Mapped[str] = mapped_column(String(64))
    width: Mapped[int] = mapped_column(Integer)
    height: Mapped[int] = mapped_column(Integer)
    byte_size: Mapped[int] = mapped_column(Integer)
    content: Mapped[bytes] = deferred(mapped_column(LargeBinary, nullable=False))
