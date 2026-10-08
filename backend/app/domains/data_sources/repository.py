import uuid
from collections.abc import Mapping, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.data_sources.models import DataSource


class DataSourceRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(
        self,
        *,
        user_id: uuid.UUID | None,
        name: str,
        type: str,
        configuration: Mapping[str, object],
    ) -> DataSource:
        data_source = DataSource(
            user_id=user_id, name=name, type=type, configuration=dict(configuration)
        )
        self._db.add(data_source)
        await self._db.flush()
        return data_source

    async def get(self, data_source_id: uuid.UUID) -> DataSource | None:
        return await self._db.get(DataSource, data_source_id)

    async def list_for_user(
        self, user_id: uuid.UUID | None, *, limit: int, offset: int = 0
    ) -> Sequence[DataSource]:
        owner = DataSource.user_id.is_(None) if user_id is None else DataSource.user_id == user_id
        statement = (
            select(DataSource)
            .where(owner)
            .order_by(DataSource.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return (await self._db.scalars(statement)).all()

    async def delete(self, data_source: DataSource) -> None:
        await self._db.delete(data_source)
        await self._db.flush()
