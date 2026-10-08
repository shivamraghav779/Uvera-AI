import uuid
from typing import Any

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, JSONDocument, TimestampMixin, UUIDPrimaryKeyMixin
from app.domains.users.models import User


class DataSource(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A registered place data can be read from.

    ``configuration`` holds non-secret settings only; credentials are referenced,
    never stored (enforced by ``DataSourceCreate``).
    """

    __tablename__ = "data_sources"

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey(User.id, ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(120))
    type: Mapped[str] = mapped_column(String(32))
    configuration: Mapped[dict[str, Any]] = mapped_column(JSONDocument, default=dict)
