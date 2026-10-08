import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies import (
    CurrentPrincipal,
    enforce_ai_rate_limit,
    get_current_principal,
    get_generation_job_service,
)
from app.api.schemas import ApiResponse, ErrorResponse
from app.domains.generation.schemas import GenerationJobCreate, GenerationJobRead
from app.domains.generation.service import GenerationJobService

router = APIRouter(
    prefix="/generation/jobs",
    tags=["Generation"],
    dependencies=[Depends(get_current_principal)],
)

JobServiceDep = Annotated[GenerationJobService, Depends(get_generation_job_service)]
NOT_FOUND: dict[int | str, dict[str, Any]] = {
    status.HTTP_404_NOT_FOUND: {"model": ErrorResponse, "description": "Unknown job."}
}


@router.post(
    "",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start generating",
    description=(
        "Starts building what the instruction describes: a complete application (product "
        "understanding, design direction, data, screens, images) or, when the instruction asks "
        "for one view of existing data, a single view. Kind `screen` generates one screen of "
        "the current application again. The work runs in the background; poll the job. Its "
        "result is a **proposal**: nothing is saved until it is approved through "
        "`POST /workspaces/{id}/versions`."
    ),
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse, "description": "Unknown workspace."},
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": "A generation is already running for this workspace.",
        },
    },
    dependencies=[Depends(enforce_ai_rate_limit)],
)
async def start_generation(
    payload: GenerationJobCreate, service: JobServiceDep, principal: CurrentPrincipal
) -> ApiResponse[GenerationJobRead]:
    return ApiResponse(data=await service.start(principal, payload))


@router.get(
    "",
    summary="Latest job of a workspace",
    description="The most recent job, or null. Lets a client resume after a reload.",
)
async def latest_generation(
    workspace_id: Annotated[uuid.UUID, Query()],
    service: JobServiceDep,
    principal: CurrentPrincipal,
) -> ApiResponse[GenerationJobRead | None]:
    return ApiResponse(data=await service.latest(principal, workspace_id))


@router.get(
    "/{job_id}",
    summary="Get a job",
    description=(
        "Status, stage (understanding, planning, designing, generating_assets, "
        "generating_screens, assembling, validating, ready, failed), percent complete and, "
        "once ready, the proposal."
    ),
    responses=NOT_FOUND,
)
async def get_generation(
    job_id: uuid.UUID, service: JobServiceDep, principal: CurrentPrincipal
) -> ApiResponse[GenerationJobRead]:
    return ApiResponse(data=await service.get(principal, job_id))


@router.post(
    "/{job_id}/cancel",
    summary="Cancel a job",
    description="Stops a queued or running job. A finished job is returned unchanged.",
    responses=NOT_FOUND,
)
async def cancel_generation(
    job_id: uuid.UUID, service: JobServiceDep, principal: CurrentPrincipal
) -> ApiResponse[GenerationJobRead]:
    return ApiResponse(data=await service.cancel(principal, job_id))
