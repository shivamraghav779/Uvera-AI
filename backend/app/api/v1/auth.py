from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencies import (
    CurrentPrincipal,
    SettingsDep,
    enforce_auth_rate_limit,
    get_auth_service,
)
from app.api.schemas import ApiResponse, ErrorResponse
from app.domains.users.schemas import AuthConfig, TokenResponse, UserLogin, UserRead, UserRegister
from app.domains.users.service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])

AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
# Credential endpoints get their own, stricter budget to slow down guessing.
THROTTLED = [Depends(enforce_auth_rate_limit)]


@router.get(
    "/config",
    summary="Authentication requirements",
    description="Whether clients must sign in. Public.",
)
async def auth_config(settings: SettingsDep) -> ApiResponse[AuthConfig]:
    return ApiResponse(data=AuthConfig(auth_required=settings.auth_required))


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    summary="Create an account",
    description="Registers an email and password and returns an access token.",
    dependencies=THROTTLED,
    responses={
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": "Email already registered.",
        }
    },
)
async def register(payload: UserRegister, service: AuthServiceDep) -> ApiResponse[TokenResponse]:
    return ApiResponse(data=await service.register(payload))


@router.post(
    "/login",
    summary="Sign in",
    description="Exchanges an email and password for an access token (`Authorization: Bearer`).",
    dependencies=THROTTLED,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse, "description": "Wrong credentials."}
    },
)
async def login(payload: UserLogin, service: AuthServiceDep) -> ApiResponse[TokenResponse]:
    return ApiResponse(data=await service.login(payload))


@router.get(
    "/me",
    summary="Current user",
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse, "description": "Not signed in."}
    },
)
async def me(service: AuthServiceDep, principal: CurrentPrincipal) -> ApiResponse[UserRead]:
    return ApiResponse(data=UserRead.model_validate(await service.current_user(principal)))
