import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, JsonValue

MAX_MESSAGE_LENGTH = 8000


class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    role: MessageRole = MessageRole.USER
    content: str = Field(
        min_length=1, max_length=MAX_MESSAGE_LENGTH, examples=["Show me sales by region"]
    )


class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    role: MessageRole
    content: str
    details: dict[str, JsonValue] | None = None
    created_at: datetime
