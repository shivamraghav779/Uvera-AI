import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from app.domains.common import StrictModel
from app.domains.generative_ui.document import AssetKind, AssetSource
from app.domains.generative_ui.schemas import AssetId, ComponentId, LongText, ShortText


class AssetDecision(StrEnum):
    """How a visual need is met. Only the first three produce a stored image."""

    GENERATE = "generate"
    SEARCH = "search"
    INTERNAL = "internal"
    ICON = "icon"
    DATA_VISUALIZATION = "data_visualization"


IMAGE_DECISIONS = frozenset({AssetDecision.GENERATE, AssetDecision.SEARCH, AssetDecision.INTERNAL})


class PlannedAsset(StrictModel):
    """One image the application needs, as decided by the asset planner."""

    id: AssetId
    decision: AssetDecision
    kind: AssetKind = AssetKind.PHOTO
    prompt: LongText = Field(description="Full description of the image, for generation.")
    query: ShortText = Field(description="A few plain words to search for the image.")
    alt: ShortText
    width: int = Field(default=1280, ge=256, le=1920)
    height: int = Field(default=800, ge=256, le=1920)
    usage: ShortText | None = None
    screen_id: ComponentId | None = None


class AssetCreate(StrictModel):
    """Ask for one more image for a workspace."""

    id: AssetId
    decision: AssetDecision = AssetDecision.GENERATE
    kind: AssetKind = AssetKind.PHOTO
    prompt: LongText
    query: ShortText | None = None
    alt: ShortText
    width: int = Field(default=1280, ge=256, le=1920)
    height: int = Field(default=800, ge=256, le=1920)


class AssetRead(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    kind: AssetKind
    source: AssetSource
    provider: str
    prompt: str | None
    alt: str
    attribution: str | None
    content_type: str
    width: int
    height: int
    byte_size: int
    url: str
    created_at: datetime
