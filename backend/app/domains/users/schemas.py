import uuid
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128


def _normalise_email(value: object) -> object:
    return value.strip().lower() if isinstance(value, str) else value


Email = Annotated[
    str,
    # Normalised first, so "  Ana@Example.com " and "ana@example.com" are one account.
    BeforeValidator(_normalise_email),
    Field(max_length=320, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", examples=["ana@example.com"]),
]
Password = Annotated[str, Field(min_length=MIN_PASSWORD_LENGTH, max_length=MAX_PASSWORD_LENGTH)]


class UserRegister(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: Email
    password: Password


class UserLogin(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: Email
    # Not length-checked on login: a wrong password is "invalid credentials", not a 422.
    password: str = Field(min_length=1, max_length=MAX_PASSWORD_LENGTH)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int = Field(description="Lifetime of the token in seconds.")
    user: UserRead


class AuthConfig(BaseModel):
    """Tells a client whether it has to sign in."""

    auth_required: bool
    min_password_length: int = MIN_PASSWORD_LENGTH
