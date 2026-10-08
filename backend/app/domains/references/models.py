from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, deferred, mapped_column

from app.database.base import Base, JSONDocument, TimestampMixin, UUIDPrimaryKeyMixin


class ReferenceComponent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Source code of a UI component published elsewhere, kept as design reference.

    This is reading material for the people who build the platform's own
    patterns. It is never rendered, never executed and never shown to the
    model: generated UIs can only use components of the component registry.
    Every row records where it came from and under which licence.
    """

    __tablename__ = "reference_components"
    __table_args__ = (UniqueConstraint("source", "slug"),)

    source: Mapped[str] = mapped_column(String(32), index=True)
    slug: Mapped[str] = mapped_column(String(200))
    name: Mapped[str] = mapped_column(String(200))
    kind: Mapped[str] = mapped_column(String(16))
    category: Mapped[str] = mapped_column(String(64), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    tags: Mapped[list[str]] = mapped_column(JSONDocument, default=list)
    author: Mapped[str | None] = mapped_column(String(200))
    license: Mapped[str | None] = mapped_column(String(64))
    source_url: Mapped[str] = mapped_column(String(500))
    preview_url: Mapped[str | None] = mapped_column(String(500))
    dependencies: Mapped[list[str]] = mapped_column(JSONDocument, default=list)
    registry_dependencies: Mapped[list[str]] = mapped_column(JSONDocument, default=list)
    # [{"path": ..., "content": ...}]; loaded only when one component is opened.
    files: Mapped[list[dict[str, str]]] = deferred(
        mapped_column(JSONDocument, default=list, nullable=False)
    )
    file_count: Mapped[int] = mapped_column(Integer, default=0)
    code_size: Mapped[int] = mapped_column(Integer, default=0)
    content_hash: Mapped[str] = mapped_column(String(64))
    source_revision: Mapped[str | None] = mapped_column(String(64))
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
