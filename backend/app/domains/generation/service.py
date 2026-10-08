"""Generation jobs: start one, follow it, cancel it.

Building a whole application takes many model calls, so it does not run inside
the request that asks for it. The request stores a job and hands it to a
``JobRunner``; clients poll the job. The runner is an interface: the in-process
implementation runs jobs as asyncio tasks of this server, and a queue-backed
one could replace it without touching anything here.
"""

import asyncio
import uuid
from collections.abc import Callable, Coroutine
from typing import Any, Protocol

from app.core.exceptions import ConflictException, ResourceNotFoundException, ValidationException
from app.core.logging import get_logger
from app.core.security import Principal
from app.database.unit_of_work import UnitOfWork
from app.domains.generation.models import GenerationJob
from app.domains.generation.repository import GenerationJobRepository
from app.domains.generation.schemas import (
    ACTIVE_STATUSES,
    GenerationJobCreate,
    GenerationJobRead,
    JobKind,
    JobStage,
    JobStatus,
)
from app.domains.workspaces.service import WorkspaceService
from app.utils.datetime import utc_now

logger = get_logger(__name__)

JobWork = Callable[[uuid.UUID, Principal], Coroutine[Any, Any, None]]


class JobRunner(Protocol):
    """Runs submitted jobs outside the request that created them."""

    def submit(self, job_id: uuid.UUID, principal: Principal) -> None: ...

    def cancel(self, job_id: uuid.UUID) -> bool: ...


class InProcessJobRunner:
    """Runs jobs as asyncio tasks of this process.

    Enough for a single server. Jobs do not survive a restart: on startup the
    application marks any job left running as failed, so a client never waits
    for work that is no longer being done.
    """

    def __init__(self, work: JobWork) -> None:
        self._work = work
        self._tasks: dict[uuid.UUID, asyncio.Task[None]] = {}

    def submit(self, job_id: uuid.UUID, principal: Principal) -> None:
        task = asyncio.create_task(self._work(job_id, principal), name=f"generation-{job_id}")
        self._tasks[job_id] = task
        task.add_done_callback(lambda _finished: self._tasks.pop(job_id, None))

    def cancel(self, job_id: uuid.UUID) -> bool:
        task = self._tasks.get(job_id)
        if task is None or task.done():
            return False
        task.cancel()
        return True

    async def shutdown(self) -> None:
        tasks = list(self._tasks.values())
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)


def to_read(job: GenerationJob) -> GenerationJobRead:
    return GenerationJobRead(
        id=job.id,
        workspace_id=job.workspace_id,
        kind=JobKind(job.kind),
        instruction=job.instruction,
        status=JobStatus(job.status),
        stage=JobStage(job.stage),
        progress=job.progress,
        detail=job.detail,
        base_version_id=job.base_version_id,
        proposal=job.result,
        error=job.error,
        created_at=job.created_at,
        updated_at=job.updated_at,
        finished_at=job.finished_at,
    )


class GenerationJobService:
    def __init__(
        self,
        *,
        repository: GenerationJobRepository,
        workspaces: WorkspaceService,
        runner: JobRunner,
        uow: UnitOfWork,
    ) -> None:
        self._repository = repository
        self._workspaces = workspaces
        self._runner = runner
        self._uow = uow

    async def start(self, principal: Principal, payload: GenerationJobCreate) -> GenerationJobRead:
        workspace = await self._workspaces.get(principal, payload.workspace_id, for_update=True)
        if await self._repository.active_for_workspace(workspace.id):
            raise ConflictException("A generation is already running for this workspace.")
        if payload.kind is JobKind.SCREEN:
            if payload.screen_id is None:
                raise ValidationException("A screen job needs 'screen_id'.")
            if workspace.current_version_id is None:
                raise ValidationException("This workspace has no application yet.")
        job = await self._repository.add(
            GenerationJob(
                workspace_id=workspace.id,
                created_by=principal.user_id,
                kind=payload.kind.value,
                instruction=payload.instruction,
                options={
                    "screen_id": payload.screen_id,
                    "theme_preset": payload.theme_preset,
                    "design_system": payload.design_system,
                    "framework": payload.framework,
                },
                base_version_id=workspace.current_version_id,
                status=JobStatus.QUEUED.value,
                stage=JobStage.QUEUED.value,
                progress=0,
                detail="Waiting to start",
            )
        )
        await self._uow.commit()
        self._runner.submit(job.id, principal)
        logger.info("generation_job_started", extra={"kind": job.kind})
        return to_read(job)

    async def get(self, principal: Principal, job_id: uuid.UUID) -> GenerationJobRead:
        return to_read(await self._require(principal, job_id))

    async def latest(
        self, principal: Principal, workspace_id: uuid.UUID
    ) -> GenerationJobRead | None:
        """The workspace's most recent job, so a client can pick up after a reload."""
        workspace = await self._workspaces.get(principal, workspace_id)
        job = await self._repository.latest_for_workspace(workspace.id)
        return to_read(job) if job else None

    async def cancel(self, principal: Principal, job_id: uuid.UUID) -> GenerationJobRead:
        job = await self._require(principal, job_id)
        if JobStatus(job.status) in ACTIVE_STATUSES:
            self._runner.cancel(job.id)
            job.status = JobStatus.CANCELLED.value
            job.detail = "Cancelled"
            job.finished_at = utc_now()
            await self._uow.commit()
        return to_read(job)

    async def _require(self, principal: Principal, job_id: uuid.UUID) -> GenerationJob:
        job = await self._repository.get(job_id)
        if job is None:
            raise ResourceNotFoundException.for_resource("Generation job", job_id)
        # Ownership is the workspace's: someone else's job is indistinguishable from none.
        try:
            await self._workspaces.get(principal, job.workspace_id)
        except ResourceNotFoundException:
            raise ResourceNotFoundException.for_resource("Generation job", job_id) from None
        return job
