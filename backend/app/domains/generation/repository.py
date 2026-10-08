import uuid
from collections.abc import Sequence

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.generation.models import GenerationJob
from app.domains.generation.schemas import ACTIVE_STATUSES, JobStage, JobStatus
from app.utils.datetime import utc_now

_ACTIVE = [status.value for status in ACTIVE_STATUSES]


class GenerationJobRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def add(self, job: GenerationJob) -> GenerationJob:
        self._db.add(job)
        await self._db.flush()
        return job

    async def get(self, job_id: uuid.UUID) -> GenerationJob | None:
        return await self._db.get(GenerationJob, job_id)

    async def latest_for_workspace(self, workspace_id: uuid.UUID) -> GenerationJob | None:
        statement = (
            select(GenerationJob)
            .where(GenerationJob.workspace_id == workspace_id)
            .order_by(GenerationJob.created_at.desc(), GenerationJob.id)
            .limit(1)
        )
        return (await self._db.scalars(statement)).first()

    async def active_for_workspace(self, workspace_id: uuid.UUID) -> Sequence[GenerationJob]:
        statement = select(GenerationJob).where(
            GenerationJob.workspace_id == workspace_id, GenerationJob.status.in_(_ACTIVE)
        )
        return (await self._db.scalars(statement)).all()

    async def fail_interrupted(self, message: str) -> int:
        """Close jobs left running by a process that is gone. Returns how many."""
        result = await self._db.execute(
            update(GenerationJob)
            .where(GenerationJob.status.in_(_ACTIVE))
            .values(
                status=JobStatus.FAILED.value,
                stage=JobStage.FAILED.value,
                detail=message,
                error={"code": "GENERATION_JOB_FAILED", "message": message},
                finished_at=utc_now(),
            )
        )
        return int(result.rowcount or 0)  # type: ignore[attr-defined]
