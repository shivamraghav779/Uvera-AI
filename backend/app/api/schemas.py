"""Response envelopes shared by every endpoint."""

from typing import Literal

from pydantic import BaseModel, Field, JsonValue


class ApiResponse[T](BaseModel):
    """Envelope for every successful response."""

    success: Literal[True] = True
    data: T


class ErrorBody(BaseModel):
    code: str = Field(examples=["UI_SCHEMA_INVALID"])
    message: str = Field(examples=["Generated UI schema is invalid."])
    request_id: str | None = Field(default=None, examples=["3f2b6c0e9d1a4b7c8e5f0a1b2c3d4e5f"])
    details: list[dict[str, JsonValue]] | None = None


class ErrorResponse(BaseModel):
    """Envelope for every failed response."""

    success: Literal[False] = False
    error: ErrorBody
