"""Contracts of generation jobs."""

import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from app.domains.conversation.schemas import MAX_MESSAGE_LENGTH
from app.domains.generative_ui.schemas import ComponentId


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    READY = "ready"
    FAILED = "failed"
    CANCELLED = "cancelled"


ACTIVE_STATUSES = frozenset({JobStatus.QUEUED, JobStatus.RUNNING})


class JobStage(StrEnum):
    """Where a run is. Reported from the pipeline itself, never from a timer."""

    QUEUED = "queued"
    UNDERSTANDING = "understanding"
    PLANNING = "planning"
    DESIGNING = "designing"
    GENERATING_ASSETS = "generating_assets"
    GENERATING_SCREENS = "generating_screens"
    ASSEMBLING = "assembling"
    VALIDATING = "validating"
    READY = "ready"
    FAILED = "failed"


class JobKind(StrEnum):
    # Build what the instruction describes: a whole application, or a single view.
    BUILD = "build"
    # Generate one screen of the current application again.
    SCREEN = "screen"


class GenerationJobCreate(BaseModel):
    workspace_id: uuid.UUID
    instruction: str = Field(
        min_length=1,
        max_length=MAX_MESSAGE_LENGTH,
        examples=["Build me a modern SaaS platform for AI-powered recruitment."],
    )
    kind: JobKind = JobKind.BUILD
    screen_id: ComponentId | None = Field(
        default=None, description="For kind 'screen': the screen to generate again."
    )
    theme_preset: str | None = Field(default=None, description="Preferred palette.")
    design_system: str | None = Field(default=None, description="Preferred visual style.")
    framework: str | None = None


class GenerationJobRead(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    kind: JobKind
    instruction: str
    status: JobStatus
    stage: JobStage
    progress: int = Field(ge=0, le=100, description="Percent complete, from the pipeline.")
    detail: str | None = Field(description="What is happening right now, in words.")
    base_version_id: uuid.UUID | None
    proposal: dict[str, Any] | None = Field(
        description="The proposal (see ProposalRead) once the job is ready. Nothing is saved."
    )
    error: dict[str, Any] | None = Field(description="The standard error body if it failed.")
    created_at: datetime
    updated_at: datetime
    finished_at: datetime | None
