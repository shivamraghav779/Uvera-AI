import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies import PaginationDep, get_current_principal, get_reference_library
from app.api.schemas import ApiResponse, ErrorResponse
from app.domains.references.schemas import (
    ReferenceCatalog,
    ReferenceDetail,
    ReferenceFacet,
    ReferenceKind,
    ReferenceSource,
)
from app.domains.references.service import ReferenceLibrary

router = APIRouter(
    prefix="/references",
    tags=["Reference components"],
    dependencies=[Depends(get_current_principal)],
)

LibraryDep = Annotated[ReferenceLibrary, Depends(get_reference_library)]
NOT_FOUND: dict[int | str, dict[str, Any]] = {
    status.HTTP_404_NOT_FOUND: {"model": ErrorResponse, "description": "Unknown component."}
}


@router.get(
    "",
    summary="Browse reference components",
    description=(
        "Source code of UI components published elsewhere, stored locally as design "
        "reference (filled by `python -m scripts.import_references`). It is reading "
        "material for building this platform's own patterns: generated UIs cannot use it, "
        "and the model never sees it. Each entry names its author, licence and origin."
    ),
)
async def list_references(
    library: LibraryDep,
    pagination: PaginationDep,
    source: Annotated[ReferenceSource | None, Query()] = None,
    kind: Annotated[ReferenceKind | None, Query()] = None,
    category: Annotated[str | None, Query(max_length=64)] = None,
    q: Annotated[
        str | None, Query(max_length=100, description="Text in the name, category or description.")
    ] = None,
    with_code: Annotated[
        bool | None, Query(description="Only entries with (true) or without (false) source code.")
    ] = None,
) -> ApiResponse[ReferenceCatalog]:
    catalog = await library.search(
        source=source,
        kind=kind,
        category=category,
        query=q,
        with_code=with_code,
        limit=pagination.limit,
        offset=pagination.offset,
    )
    return ApiResponse(data=catalog)


@router.get(
    "/facets",
    summary="Sources and categories",
    description="How many components each source holds per category, and how many have code.",
)
async def reference_facets(library: LibraryDep) -> ApiResponse[list[ReferenceFacet]]:
    return ApiResponse(data=await library.facets())


@router.get(
    "/{reference_id}",
    summary="Get a reference component with its source code",
    responses=NOT_FOUND,
)
async def get_reference(
    reference_id: uuid.UUID, library: LibraryDep
) -> ApiResponse[ReferenceDetail]:
    return ApiResponse(data=await library.get(reference_id))
