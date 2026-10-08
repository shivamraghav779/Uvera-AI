import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class WorkspaceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str | None = Field(
        default=None, min_length=1, max_length=200, examples=["Q3 sales dashboard"]
    )


class WorkspaceUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=200)


class WorkspaceRead(BaseModel):
    id: uuid.UUID
    title: str | None
    current_version_id: uuid.UUID | None
    current_version_number: int | None = Field(
        description="Number of the current version; null until a UI has been approved."
    )
    created_at: datetime
    updated_at: datetime
