import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencies import CurrentPrincipal, get_current_principal, get_data_source_service
from app.api.schemas import ApiResponse, ErrorResponse
from app.domains.data_sources.schemas import DatasetDescriptor, DataSourceCreate, DataSourceRead
from app.domains.data_sources.service import DataSourceService

router = APIRouter(
    prefix="/data-sources", tags=["Data Sources"], dependencies=[Depends(get_current_principal)]
)

DataSourceServiceDep = Annotated[DataSourceService, Depends(get_data_source_service)]


@router.get("", summary="List data sources", description="Data sources registered by the caller.")
async def list_data_sources(
    service: DataSourceServiceDep, principal: CurrentPrincipal
) -> ApiResponse[list[DataSourceRead]]:
    return ApiResponse(data=await service.list_data_sources(principal))


@router.get(
    "/datasets",
    summary="List available datasets",
    description="Every dataset generated UIs can bind to: the caller's sources plus demo data.",
)
async def list_datasets(service: DataSourceServiceDep) -> ApiResponse[list[DatasetDescriptor]]:
    return ApiResponse(data=await service.list_datasets())


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Register a data source",
    description=(
        "Connects uploaded CSV/JSON (`file_upload`), an HTTPS JSON API (`rest_api`) or read-only "
        "SQL queries (`postgresql`). The source is read once before it is saved, so a source "
        "that cannot be reached is rejected. Credentials are never accepted in the request: "
        "use `credentials_ref` to name a secret the server holds."
    ),
    responses={
        status.HTTP_409_CONFLICT: {"model": ErrorResponse, "description": "Dataset name in use."},
        status.HTTP_502_BAD_GATEWAY: {
            "model": ErrorResponse,
            "description": "The source could not be read.",
        },
    },
)
async def create_data_source(
    payload: DataSourceCreate, service: DataSourceServiceDep, principal: CurrentPrincipal
) -> ApiResponse[DataSourceRead]:
    return ApiResponse(data=await service.create(principal, payload))


@router.delete(
    "/{data_source_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a data source",
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse, "description": "Unknown source."}
    },
)
async def delete_data_source(
    data_source_id: uuid.UUID, service: DataSourceServiceDep, principal: CurrentPrincipal
) -> None:
    await service.delete(principal, data_source_id)
