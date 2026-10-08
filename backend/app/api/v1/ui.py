from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import StreamingResponse

from app.api.dependencies import (
    CurrentPrincipal,
    enforce_ai_rate_limit,
    get_current_principal,
    get_generative_ui_service,
    get_ui_catalogue_service,
    get_ui_inspection_service,
)
from app.api.schemas import ApiResponse, ErrorResponse
from app.api.streaming import proposal_stream
from app.domains.generative_ui.contracts import (
    CapabilitiesResponse,
    ComponentCatalogResponse,
    FrameworkCatalogResponse,
    GenerateUIRequest,
    MutateUIRequest,
    PatternCatalogResponse,
    ProposalRead,
    ThemeCatalogResponse,
    ValidateUIRequest,
    ValidateUIResponse,
)
from app.domains.generative_ui.service import GenerativeUIService, UISchemaInspectionService

router = APIRouter(prefix="/ui", tags=["Generative UI"])

GenerativeUIServiceDep = Annotated[GenerativeUIService, Depends(get_generative_ui_service)]
InspectionServiceDep = Annotated[UISchemaInspectionService, Depends(get_ui_inspection_service)]
CatalogueServiceDep = Annotated[UISchemaInspectionService, Depends(get_ui_catalogue_service)]
# Order matters: who you are is established before any budget or provider is touched.
PROTECTED = [Depends(get_current_principal)]
AI_BUDGET = [*PROTECTED, Depends(enforce_ai_rate_limit)]
STREAM_RESPONSE: dict[int | str, dict[str, Any]] = {
    status.HTTP_200_OK: {
        "description": (
            "Server-sent events: `progress` ({stage, characters}) while the model works, then "
            "one `proposal` (the envelope of the non-streaming endpoint) or `error` (the "
            "standard error envelope)."
        ),
        "content": {"text/event-stream": {}},
    }
}

AI_ERRORS: dict[int | str, dict[str, Any]] = {
    status.HTTP_404_NOT_FOUND: {"model": ErrorResponse, "description": "Unknown workspace."},
    status.HTTP_502_BAD_GATEWAY: {
        "model": ErrorResponse,
        "description": "The model failed or could not produce valid output.",
    },
    status.HTTP_503_SERVICE_UNAVAILABLE: {
        "model": ErrorResponse,
        "description": "No language model provider is configured.",
    },
}


@router.post(
    "/generate",
    summary="Propose a new UI",
    description=(
        "Interprets the instruction, plans an interface, asks the language model for a UI "
        "schema and validates it. Returns a **proposal**: nothing is saved until it is "
        "approved through `POST /workspaces/{id}/versions`."
    ),
    response_model_exclude_none=True,
    responses=AI_ERRORS,
    dependencies=AI_BUDGET,
)
async def generate_ui(
    payload: GenerateUIRequest, service: GenerativeUIServiceDep, principal: CurrentPrincipal
) -> ApiResponse[ProposalRead]:
    return ApiResponse(data=await service.generate(principal, payload))


@router.post(
    "/generate/stream",
    summary="Propose a new UI, with live progress",
    description="Same as `POST /ui/generate`, reporting progress as server-sent events.",
    response_class=StreamingResponse,
    responses=STREAM_RESPONSE,
    dependencies=AI_BUDGET,
)
async def generate_ui_stream(
    payload: GenerateUIRequest, request: Request, principal: CurrentPrincipal
) -> StreamingResponse:
    return proposal_stream(
        request.app,
        principal,
        lambda service, progress: service.generate(principal, payload, progress),
    )


@router.post(
    "/mutate",
    summary="Propose changes to the current UI",
    description=(
        "With `instruction`: asks the model for operations (or a version restore/compare) "
        "against the current version and returns the validated result as a proposal. "
        "With `operations`: validates client-made operations and returns the resulting "
        "state without calling a model. Nothing is saved either way."
    ),
    response_model_exclude_none=True,
    responses={
        **AI_ERRORS,
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": "`base_version_id` is no longer the workspace's current version.",
        },
    },
    dependencies=AI_BUDGET,
)
async def mutate_ui(
    payload: MutateUIRequest, service: GenerativeUIServiceDep, principal: CurrentPrincipal
) -> ApiResponse[ProposalRead]:
    return ApiResponse(data=await service.mutate(principal, payload))


@router.post(
    "/mutate/stream",
    summary="Propose changes to the current UI, with live progress",
    description="Same as `POST /ui/mutate`, reporting progress as server-sent events.",
    response_class=StreamingResponse,
    responses=STREAM_RESPONSE,
    dependencies=AI_BUDGET,
)
async def mutate_ui_stream(
    payload: MutateUIRequest, request: Request, principal: CurrentPrincipal
) -> StreamingResponse:
    return proposal_stream(
        request.app,
        principal,
        lambda service, progress: service.mutate(principal, payload, progress),
    )


@router.post(
    "/validate",
    summary="Validate a UI document",
    description=(
        "Runs a document through the same pipeline as generated output: schema, component "
        "and action registries, semantic rules, theme and design rules. Always returns 200; "
        "see `valid`."
    ),
    response_model_exclude_none=True,
    dependencies=PROTECTED,
)
async def validate_ui(
    payload: ValidateUIRequest, service: InspectionServiceDep
) -> ApiResponse[ValidateUIResponse]:
    return ApiResponse(data=await service.validate(payload.document))


@router.get(
    "/components",
    summary="List registered components",
    description="The component catalogue the frontend must be able to render, with JSON Schema.",
)
async def list_components(service: CatalogueServiceDep) -> ApiResponse[ComponentCatalogResponse]:
    return ApiResponse(data=service.catalog())


@router.get(
    "/frameworks",
    summary="List frameworks and design systems",
    description="Ids a document's `design` may reference. The frontend maps ids to adapters.",
    response_model_exclude_none=True,
)
async def list_frameworks(service: CatalogueServiceDep) -> ApiResponse[FrameworkCatalogResponse]:
    return ApiResponse(data=service.frameworks())


@router.get(
    "/patterns",
    summary="List design patterns",
    description=(
        "The design knowledge library: patterns with what each is for and where it fits, "
        "example compositions per kind of screen, effects and icon names."
    ),
)
async def list_patterns(service: CatalogueServiceDep) -> ApiResponse[PatternCatalogResponse]:
    return ApiResponse(data=service.patterns())


@router.get(
    "/themes",
    summary="List theme presets",
    description="Named sets of colour tokens, and the default theme of a new workspace.",
    response_model_exclude_none=True,
)
async def list_themes(service: CatalogueServiceDep) -> ApiResponse[ThemeCatalogResponse]:
    return ApiResponse(data=service.themes())


@router.get(
    "/capabilities",
    summary="Describe what a UI can contain",
    description="Components, chart types, layout model, actions, operations and theme tokens.",
)
async def get_capabilities(service: CatalogueServiceDep) -> ApiResponse[CapabilitiesResponse]:
    return ApiResponse(data=service.capabilities())
