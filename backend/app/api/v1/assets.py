import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.api.dependencies import (
    CurrentPrincipal,
    PaginationDep,
    enforce_ai_rate_limit,
    get_asset_service,
    get_current_principal,
    get_public_asset_service,
)
from app.api.schemas import ApiResponse, ErrorResponse
from app.domains.assets.schemas import AssetCreate, AssetRead
from app.domains.assets.service import CACHE_SECONDS, AssetService
from app.domains.generative_ui.document import Asset

workspace_router = APIRouter(
    prefix="/workspaces/{workspace_id}/assets",
    tags=["Assets"],
    dependencies=[Depends(get_current_principal)],
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse, "description": "Unknown workspace."}
    },
)
router = APIRouter(prefix="/assets", tags=["Assets"])

AssetServiceDep = Annotated[AssetService, Depends(get_asset_service)]


@workspace_router.get(
    "",
    summary="List a workspace's images",
    description="Every image prepared for the workspace, newest first, with its provenance.",
)
async def list_assets(
    workspace_id: uuid.UUID,
    service: AssetServiceDep,
    principal: CurrentPrincipal,
    pagination: PaginationDep,
) -> ApiResponse[list[AssetRead]]:
    assets = await service.list_assets(
        principal, workspace_id, limit=pagination.limit, offset=pagination.offset
    )
    return ApiResponse(data=assets)


@workspace_router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Prepare an image",
    description=(
        "Generates or finds one image and stores it. Returns the asset reference to add to "
        "the UI with an `ADD_ASSETS` operation; the workspace's UI is not changed here."
    ),
    response_model_exclude_none=True,
    dependencies=[Depends(enforce_ai_rate_limit)],
)
async def create_asset(
    workspace_id: uuid.UUID,
    payload: AssetCreate,
    service: AssetServiceDep,
    principal: CurrentPrincipal,
) -> ApiResponse[Asset]:
    return ApiResponse(data=await service.create(principal, workspace_id, payload))


@router.get(
    "/{asset_id}/content",
    summary="Image bytes",
    description=(
        "The stored image. Needs no token, like any image URL: asset ids are random and "
        "are only known to those who can see a UI that uses the image."
    ),
    response_class=Response,
    responses={
        status.HTTP_200_OK: {"content": {"image/*": {}}, "description": "The image."},
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse, "description": "Unknown asset."},
    },
)
async def asset_content(
    asset_id: uuid.UUID,
    service: Annotated[AssetService, Depends(get_public_asset_service)],
) -> Response:
    asset = await service.content(asset_id)
    return Response(
        content=asset.content,
        media_type=asset.content_type,
        headers={
            "Cache-Control": f"public, max-age={CACHE_SECONDS}, immutable",
            "X-Content-Type-Options": "nosniff",
            # An SVG opened on its own must not be able to run script or load anything.
            "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'",
            "Cross-Origin-Resource-Policy": "cross-origin",
        },
    )
