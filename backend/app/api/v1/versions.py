import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies import (
    CurrentPrincipal,
    get_application_query_service,
    get_current_principal,
    get_version_service,
)
from app.api.schemas import ApiResponse, ErrorResponse
from app.domains.generative_ui.contracts import (
    ApplicationRead,
    VersionComparison,
    VersionCreate,
    VersionDetail,
    VersionRestore,
    VersionSummary,
)
from app.domains.generative_ui.service import ApplicationQueryService
from app.domains.generative_ui.versioning import VersionService

CONFLICT: dict[int | str, dict[str, Any]] = {
    status.HTTP_409_CONFLICT: {
        "model": ErrorResponse,
        "description": "`base_version_id` is no longer the workspace's current version.",
    }
}

router = APIRouter(
    prefix="/workspaces/{workspace_id}/versions",
    tags=["Versions"],
    dependencies=[Depends(get_current_principal)],
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Unknown workspace or version.",
        }
    },
)

VersionServiceDep = Annotated[VersionService, Depends(get_version_service)]


@router.get(
    "",
    summary="List versions",
    description="Version history of a workspace, newest first. Versions are immutable.",
)
async def list_versions(
    workspace_id: uuid.UUID, service: VersionServiceDep, principal: CurrentPrincipal
) -> ApiResponse[list[VersionSummary]]:
    return ApiResponse(data=await service.list_versions(principal, workspace_id))


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Save an approved change as a new version",
    description=(
        "Persists an approved proposal or manual edit. Send the complete `document` or the "
        "`operations` to apply to the base version; either is fully re-validated. The new "
        "version becomes current. Rejected with 409 when `base_version_id` is stale."
    ),
    response_model_exclude_none=True,
    responses=CONFLICT,
)
async def create_version(
    workspace_id: uuid.UUID,
    payload: VersionCreate,
    service: VersionServiceDep,
    principal: CurrentPrincipal,
) -> ApiResponse[VersionDetail]:
    return ApiResponse(data=await service.create(principal, workspace_id, payload))


@router.get(
    "/{version_id}",
    summary="Get a version",
    description="The stored UI document plus current rows for the datasets it binds.",
    response_model_exclude_none=True,
)
async def get_version(
    workspace_id: uuid.UUID,
    version_id: uuid.UUID,
    service: VersionServiceDep,
    principal: CurrentPrincipal,
) -> ApiResponse[VersionDetail]:
    return ApiResponse(data=await service.get_version(principal, workspace_id, version_id))


@router.post(
    "/{version_id}/restore",
    status_code=status.HTTP_201_CREATED,
    summary="Restore a version",
    description=(
        "Makes an earlier version current by appending a copy of it as the newest version. "
        "No existing version is changed or removed."
    ),
    response_model_exclude_none=True,
    responses=CONFLICT,
)
async def restore_version(
    workspace_id: uuid.UUID,
    version_id: uuid.UUID,
    payload: VersionRestore,
    service: VersionServiceDep,
    principal: CurrentPrincipal,
) -> ApiResponse[VersionDetail]:
    return ApiResponse(data=await service.restore(principal, workspace_id, version_id, payload))


@router.get(
    "/{version_id}/compare",
    summary="Compare two versions",
    description=(
        "Schema-based list of changes that turn this version into `with` "
        "(default: the current version)."
    ),
)
async def compare_versions(
    workspace_id: uuid.UUID,
    version_id: uuid.UUID,
    service: VersionServiceDep,
    principal: CurrentPrincipal,
    other: Annotated[
        uuid.UUID | None, Query(alias="with", description="Version to compare against.")
    ] = None,
) -> ApiResponse[VersionComparison]:
    return ApiResponse(data=await service.compare(principal, workspace_id, version_id, other))


application_router = APIRouter(
    prefix="/workspaces/{workspace_id}",
    tags=["Workspaces"],
    dependencies=[Depends(get_current_principal)],
)


@application_router.get(
    "/application",
    summary="Describe the workspace's application",
    description=(
        "Summary of the current application (screens, entities, design, counts) and its "
        "graph: which screens the navigation reaches, which actions lead from one screen to "
        "another, and which screens share data. 404 when the workspace holds a single view."
    ),
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Unknown workspace, or it holds no application.",
        }
    },
)
async def get_application(
    workspace_id: uuid.UUID,
    service: Annotated[ApplicationQueryService, Depends(get_application_query_service)],
    principal: CurrentPrincipal,
) -> ApiResponse[ApplicationRead]:
    return ApiResponse(data=await service.read(principal, workspace_id))
