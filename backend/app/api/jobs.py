"""Runs generation jobs outside the request that created them.

``execute_generation_job`` is the work an ``InProcessJobRunner`` schedules. It
builds its own services (a job outlives its request's dependencies), reports
progress to the job row as the pipeline advances, and ends by storing either
the proposal or the error. Whatever happens, the job reaches a final status.
"""

import asyncio
import uuid
from typing import Any

from fastapi import FastAPI
from sqlalchemy.exc import SQLAlchemyError

from app.api.dependencies import generative_ui_service_scope
from app.core.exceptions import AppException, ErrorCode
from app.core.logging import get_logger
from app.core.security import Principal
from app.database.connection import Database
from app.domains.generation.models import GenerationJob
from app.domains.generation.repository import GenerationJobRepository
from app.domains.generation.schemas import JobKind, JobStage, JobStatus
from app.domains.generative_ui.contracts import GenerateUIRequest, ProposalRead
from app.middleware.error_handler import translate_database_error
from app.utils.datetime import utc_now

logger = get_logger(__name__)

MAX_DETAIL_LENGTH = 300
INTERRUPTED_MESSAGE = "The server restarted while this was being generated. Please try again."


class JobProgressWriter:
    """Writes a job's progress and outcome, each in its own short transaction.

    The pipeline reports from concurrent tasks; a lock keeps the writes in order
    and off the session the pipeline itself is using.
    """

    def __init__(self, database: Database, job_id: uuid.UUID) -> None:
        self._database = database
        self._job_id = job_id
        self._lock = asyncio.Lock()
        self._percent = 0

    async def _update(self, **values: Any) -> GenerationJob | None:
        async with self._lock, self._database.session() as session:
            job = await session.get(GenerationJob, self._job_id)
            # A cancelled job stays cancelled even if the work reports once more.
            if job is None or job.status == JobStatus.CANCELLED.value:
                return job
            for key, value in values.items():
                setattr(job, key, value)
            await session.commit()
            return job

    async def load(self) -> GenerationJob | None:
        async with self._database.session() as session:
            return await session.get(GenerationJob, self._job_id)

    async def started(self) -> None:
        await self._update(
            status=JobStatus.RUNNING.value, stage=JobStage.UNDERSTANDING.value, detail="Starting"
        )

    async def report(self, stage: str, percent: int, detail: str | None) -> None:
        # Screens finish out of order; the bar never moves backwards.
        self._percent = max(self._percent, min(percent, 99))
        await self._update(
            stage=stage,
            progress=self._percent,
            detail=detail[:MAX_DETAIL_LENGTH] if detail else None,
        )

    async def ready(self, proposal: ProposalRead) -> None:
        await self._update(
            status=JobStatus.READY.value,
            stage=JobStage.READY.value,
            progress=100,
            detail="Ready for review",
            result=proposal.model_dump(mode="json", exclude_none=True),
            finished_at=utc_now(),
        )

    async def failed(self, error: AppException) -> None:
        await self._update(
            status=JobStatus.FAILED.value,
            stage=JobStage.FAILED.value,
            detail=error.message[:MAX_DETAIL_LENGTH],
            error={
                "code": error.code.value,
                "message": error.message,
                "details": [dict(detail) for detail in error.details] or None,
            },
            finished_at=utc_now(),
        )


def _to_app_exception(error: Exception) -> AppException:
    if isinstance(error, AppException):
        return error
    if isinstance(error, SQLAlchemyError):
        return translate_database_error(error)
    logger.exception("generation_job_crashed", extra={"error_type": type(error).__name__})
    failure = AppException("The generation failed unexpectedly. Please try again.")
    assert failure.code is ErrorCode.INTERNAL_ERROR
    return failure


async def execute_generation_job(app: FastAPI, job_id: uuid.UUID, principal: Principal) -> None:
    writer = JobProgressWriter(app.state.database, job_id)
    try:
        job = await writer.load()
        if job is None or job.status != JobStatus.QUEUED.value:
            return
        await writer.started()
        options = job.options or {}
        async with generative_ui_service_scope(app, principal) as service:
            if job.kind == JobKind.SCREEN.value:
                proposal = await service.regenerate_screen(
                    principal, job.workspace_id, str(options.get("screen_id")), job.instruction
                )
            else:
                proposal = await service.build(
                    principal,
                    GenerateUIRequest(
                        workspace_id=job.workspace_id,
                        instruction=job.instruction,
                        theme_preset=options.get("theme_preset"),
                        design_system=options.get("design_system"),
                        framework=options.get("framework"),
                    ),
                    writer.report,
                )
        await writer.ready(proposal)
        logger.info("generation_job_ready", extra={"kind": job.kind})
    except asyncio.CancelledError:
        logger.info("generation_job_cancelled")
        raise
    except Exception as exc:
        error = _to_app_exception(exc)
        logger.warning("generation_job_failed", extra={"code": error.code.value})
        await writer.failed(error)


async def fail_interrupted_jobs(database: Database) -> None:
    """On startup: no job can still be running, because the process that ran it is gone."""
    try:
        async with database.session() as session:
            closed = await GenerationJobRepository(session).fail_interrupted(INTERRUPTED_MESSAGE)
            await session.commit()
    except (SQLAlchemyError, OSError) as exc:
        # The database may be down or not migrated yet; the health endpoint reports that.
        logger.warning("interrupted_jobs_not_closed", extra={"error_type": type(exc).__name__})
        return
    if closed:
        logger.info("interrupted_jobs_closed", extra={"count": closed})
