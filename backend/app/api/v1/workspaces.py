import uuid
from typing import Any

from fastapi import APIRouter, Depends, status

from app.api.dependencies import (
    CurrentPrincipal,
    PaginationDep,
    WorkspaceServiceDep,
    get_current_principal,
)
from app.api.schemas import ApiResponse, ErrorResponse
from app.domains.workspaces.schemas import WorkspaceCreate, WorkspaceRead, WorkspaceUpdate

router = APIRouter(
    prefix="/workspaces", tags=["Workspaces"], dependencies=[Depends(get_current_principal)]
)

NOT_FOUND: dict[int | str, dict[str, Any]] = {
    status.HTTP_404_NOT_FOUND: {"model": ErrorResponse, "description": "Unknown workspace."}
}


@router.get(
    "", summary="List workspaces", description="Workspaces of the caller, most recent first."
)
async def list_workspaces(
    service: WorkspaceServiceDep, principal: CurrentPrincipal, pagination: PaginationDep
) -> ApiResponse[list[WorkspaceRead]]:
    workspaces = await service.list_workspaces(
        principal, limit=pagination.limit, offset=pagination.offset
    )
    return ApiResponse(data=workspaces)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Create a workspace",
    description="A workspace holds one evolving UI, its version history and its conversation.",
)
async def create_workspace(
    payload: WorkspaceCreate, service: WorkspaceServiceDep, principal: CurrentPrincipal
) -> ApiResponse[WorkspaceRead]:
    return ApiResponse(data=await service.create(principal, payload))


@router.get("/{workspace_id}", summary="Get a workspace", responses=NOT_FOUND)
async def get_workspace(
    workspace_id: uuid.UUID, service: WorkspaceServiceDep, principal: CurrentPrincipal
) -> ApiResponse[WorkspaceRead]:
    return ApiResponse(data=await service.read(principal, workspace_id))


@router.patch("/{workspace_id}", summary="Rename a workspace", responses=NOT_FOUND)
async def rename_workspace(
    workspace_id: uuid.UUID,
    payload: WorkspaceUpdate,
    service: WorkspaceServiceDep,
    principal: CurrentPrincipal,
) -> ApiResponse[WorkspaceRead]:
    return ApiResponse(data=await service.rename(principal, workspace_id, payload))


@router.delete(
    "/{workspace_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a workspace",
    description="Also deletes the workspace's versions, messages and action history.",
    responses=NOT_FOUND,
)
async def delete_workspace(
    workspace_id: uuid.UUID, service: WorkspaceServiceDep, principal: CurrentPrincipal
) -> None:
    await service.delete(principal, workspace_id)
