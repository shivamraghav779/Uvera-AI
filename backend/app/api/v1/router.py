from fastapi import APIRouter, Depends

from app.api.dependencies import enforce_rate_limit
from app.api.schemas import ErrorResponse
from app.api.v1 import (
    actions,
    assets,
    auth,
    conversations,
    data,
    generation,
    health,
    references,
    ui,
    versions,
    workspaces,
)

VALIDATION_ERROR_STATUS = 422

router = APIRouter(
    dependencies=[Depends(enforce_rate_limit)],
    responses={
        VALIDATION_ERROR_STATUS: {
            "model": ErrorResponse,
            "description": "The request is invalid.",
        }
    },
)

for module in (
    health, auth, workspaces, versions, conversations, ui, generation, data, actions, assets,
    references,
):  # fmt: skip
    router.include_router(module.router)
router.include_router(actions.submissions_router)
router.include_router(assets.workspace_router)
router.include_router(versions.application_router)
