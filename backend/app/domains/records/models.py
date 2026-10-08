import uuid
from typing import Any

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, JSONDocument, TimestampMixin, UUIDPrimaryKeyMixin
from app.domains.workspaces.models import Workspace


class WorkspaceRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A change someone made to an application's data while using it.

    Versions hold the application's design and its sample records and never
    change. What users do in the running application (create a job, shortlist a
    candidate) is kept here instead, one row per touched record, and laid over
    the sample records whenever the data is read.
    """

    __tablename__ = "workspace_records"
    __table_args__ = (
        UniqueConstraint(
            "workspace_id", "entity", "record_key", name="uq_workspace_records_workspace_id_entity"
        ),
    )

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(Workspace.id, ondelete="CASCADE"), index=True
    )
    entity: Mapped[str] = mapped_column(String(64))
    record_key: Mapped[str] = mapped_column(String(128))
    # Field values to lay over the sample record (all of them for a created record).
    data: Mapped[dict[str, Any]] = mapped_column(JSONDocument, default=dict)
    deleted: Mapped[bool] = mapped_column(Boolean, default=False)
