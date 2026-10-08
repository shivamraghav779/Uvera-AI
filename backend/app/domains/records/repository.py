import uuid
from collections.abc import Mapping, Sequence

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.records.models import WorkspaceRecord


class WorkspaceRecordRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_for_workspace(self, workspace_id: uuid.UUID) -> Sequence[WorkspaceRecord]:
        """Every stored change of a workspace, oldest first (creation order of new records)."""
        statement = (
            select(WorkspaceRecord)
            .where(WorkspaceRecord.workspace_id == workspace_id)
            .order_by(WorkspaceRecord.created_at, WorkspaceRecord.id)
        )
        return (await self._db.scalars(statement)).all()

    async def get(
        self, workspace_id: uuid.UUID, entity: str, record_key: str
    ) -> WorkspaceRecord | None:
        statement = select(WorkspaceRecord).where(
            WorkspaceRecord.workspace_id == workspace_id,
            WorkspaceRecord.entity == entity,
            WorkspaceRecord.record_key == record_key,
        )
        return (await self._db.scalars(statement)).first()

    async def upsert(
        self,
        *,
        workspace_id: uuid.UUID,
        entity: str,
        record_key: str,
        values: Mapping[str, object],
        deleted: bool = False,
    ) -> WorkspaceRecord:
        """Merge ``values`` into the stored change for a record, creating it if needed."""
        record = await self.get(workspace_id, entity, record_key)
        if record is None:
            record = WorkspaceRecord(
                workspace_id=workspace_id,
                entity=entity,
                record_key=record_key,
                data=dict(values),
                deleted=deleted,
            )
            self._db.add(record)
        else:
            record.data = {**record.data, **values}
            record.deleted = deleted
        await self._db.flush()
        return record

    async def clear(self, workspace_id: uuid.UUID) -> int:
        """Forget every change: the application shows its sample records again."""
        result = await self._db.execute(
            delete(WorkspaceRecord).where(WorkspaceRecord.workspace_id == workspace_id)
        )
        return int(result.rowcount or 0)  # type: ignore[attr-defined]
