import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencies import (
    CurrentPrincipal,
    PaginationDep,
    get_action_service,
    get_current_principal,
)
from app.api.schemas import ApiResponse, ErrorResponse
from app.domains.actions.schemas import (
    ActionExecuteRequest,
    ActionExecuteResponse,
    FormSubmissionRead,
)
from app.domains.actions.service import ActionService

router = APIRouter(
    prefix="/actions", tags=["Actions"], dependencies=[Depends(get_current_principal)]
)


@router.post(
    "/execute",
    summary="Execute an action",
    description=(
        "Runs one allowlisted action (filter, sort, refresh, navigate, submit, search, "
        "generate, export, record_create, record_update, record_delete) for a workspace. "
        "Any other action type is rejected."
    ),
    responses={
        status.HTTP_403_FORBIDDEN: {"model": ErrorResponse, "description": "Action not allowed."},
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse, "description": "Unknown workspace."},
    },
)
async def execute_action(
    payload: ActionExecuteRequest,
    service: Annotated[ActionService, Depends(get_action_service)],
    principal: CurrentPrincipal,
) -> ApiResponse[ActionExecuteResponse]:
    return ApiResponse(data=await service.execute(principal, payload))


submissions_router = APIRouter(
    prefix="/workspaces/{workspace_id}",
    tags=["Actions"],
    dependencies=[Depends(get_current_principal)],
)


@submissions_router.delete(
    "/records",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Reset application data",
    description=(
        "Forgets every change made to the application's data while using it; the sample "
        "records of the current version are shown again. Versions are not affected."
    ),
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse, "description": "Unknown workspace."}
    },
)
async def reset_records(
    workspace_id: uuid.UUID,
    service: Annotated[ActionService, Depends(get_action_service)],
    principal: CurrentPrincipal,
) -> None:
    await service.reset_data(principal, workspace_id)


@submissions_router.get(
    "/submissions",
    summary="List form submissions",
    description="Values submitted through forms in this workspace's UI, newest first.",
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse, "description": "Unknown workspace."}
    },
)
async def list_submissions(
    workspace_id: uuid.UUID,
    service: Annotated[ActionService, Depends(get_action_service)],
    principal: CurrentPrincipal,
    pagination: PaginationDep,
) -> ApiResponse[list[FormSubmissionRead]]:
    submissions = await service.list_submissions(
        principal, workspace_id, limit=pagination.limit, offset=pagination.offset
    )
    return ApiResponse(data=submissions)
