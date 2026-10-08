import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, JSONDocument, TimestampMixin, UUIDPrimaryKeyMixin
from app.domains.users.models import User
from app.domains.workspaces.models import Workspace


class GenerationJob(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One run of the application generation pipeline.

    Generating a whole application takes longer than a request should stay
    open, so the work runs in the background and reports here. The result is a
    proposal: finishing a job saves no version.
    """

    __tablename__ = "generation_jobs"
    __table_args__ = (
        Index("ix_generation_jobs_workspace_id_created_at", "workspace_id", "created_at"),
    )

    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey(Workspace.id, ondelete="CASCADE"))
    created_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey(User.id, ondelete="SET NULL"))
    kind: Mapped[str] = mapped_column(String(32))
    instruction: Mapped[str] = mapped_column(Text)
    # Request options (look preferences, target screen) needed to run or re-run the job.
    options: Mapped[dict[str, Any]] = mapped_column(JSONDocument, default=dict)
    # The workspace version the job was started against; a proposal for another base is stale.
    base_version_id: Mapped[uuid.UUID | None] = mapped_column()
    status: Mapped[str] = mapped_column(String(16))
    stage: Mapped[str] = mapped_column(String(32))
    progress: Mapped[int] = mapped_column(Integer, default=0)
    detail: Mapped[str | None] = mapped_column(String(300))
    # The proposal, once ready.
    result: Mapped[dict[str, Any] | None] = mapped_column(JSONDocument)
    # The standard error body, if the job failed.
    error: Mapped[dict[str, Any] | None] = mapped_column(JSONDocument)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
