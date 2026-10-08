from enum import StrEnum
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.dependencies import SettingsDep, get_database
from app.api.schemas import ApiResponse
from app.database.connection import Database

router = APIRouter(tags=["Health"])


class HealthStatus(StrEnum):
    OK = "ok"
    DEGRADED = "degraded"


class DependencyStatus(StrEnum):
    UP = "up"
    DOWN = "down"


class HealthRead(BaseModel):
    status: HealthStatus
    version: str
    environment: str
    database: DependencyStatus


@router.get(
    "/health",
    summary="Service health",
    description="Reports whether the API is running and can reach its database.",
)
async def health(
    settings: SettingsDep, database: Annotated[Database, Depends(get_database)]
) -> ApiResponse[HealthRead]:
    database_up = await database.ping()
    return ApiResponse(
        data=HealthRead(
            status=HealthStatus.OK if database_up else HealthStatus.DEGRADED,
            version=settings.app_version,
            environment=settings.app_env.value,
            database=DependencyStatus.UP if database_up else DependencyStatus.DOWN,
        )
    )
