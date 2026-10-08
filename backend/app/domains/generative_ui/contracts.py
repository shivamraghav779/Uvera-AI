"""Contracts of the Generative UI use cases: ports to the AI layer and HTTP DTOs."""

import uuid
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any, Protocol, Self

from pydantic import BaseModel, Field, JsonValue, model_validator

from app.domains.common import DataRow
from app.domains.conversation.schemas import MAX_MESSAGE_LENGTH
from app.domains.data_sources.schemas import DatasetDescriptor
from app.domains.generative_ui.design_registry import FrameworkStatus
from app.domains.generative_ui.diff import ChangeKind
from app.domains.generative_ui.document import DesignConfig, Theme, ThemePatch, UIDocument
from app.domains.generative_ui.intent import UIIntent
from app.domains.generative_ui.mutator import MutationOutcome
from app.domains.generative_ui.operations import MAX_OPERATIONS, DocumentOperation
from app.domains.generative_ui.planner import ConversationTurn
from app.domains.generative_ui.registry import ComponentCategory
from app.domains.generative_ui.schemas import ComponentId, ComponentType
from app.domains.generative_ui.validator import ValidationContext, ValidationStage

# --- Progress reporting ----------------------------------------------------------


class ProgressStage(StrEnum):
    UNDERSTANDING = "understanding"
    PLANNING = "planning"
    GENERATING = "generating"
    VALIDATING = "validating"
    REPAIRING = "repairing"
    FINISHING = "finishing"


@dataclass(frozen=True, slots=True)
class ProgressEvent:
    stage: ProgressStage
    # Characters of model output received so far (while generating).
    characters: int | None = None


# Called as work advances, so a client can be told what is happening. Optional everywhere.
ProgressReporter = Callable[[ProgressEvent], Awaitable[None]]


async def report(progress: "ProgressReporter | None", stage: ProgressStage) -> None:
    if progress is not None:
        await progress(ProgressEvent(stage))


# --- Ports implemented by the AI orchestration layer ---------------------------


@dataclass(frozen=True, slots=True)
class UIGenerationInput:
    user_request: str
    history: Sequence[ConversationTurn]
    # Theme and design the generated page is combined with (the workspace's current
    # ones, or the defaults for a new workspace).
    base_theme: Theme
    design: DesignConfig
    progress: ProgressReporter | None = None


@dataclass(frozen=True, slots=True)
class UIGenerationOutput:
    document: UIDocument
    intent: UIIntent
    provider: str
    model: str
    prompt_version: str
    repair_attempts: int


class UIGenerator(Protocol):
    """Produces a complete, validated UI document for a request."""

    async def generate(self, request: UIGenerationInput) -> UIGenerationOutput: ...


@dataclass(frozen=True, slots=True)
class VersionInfo:
    """What the model may know about a stored version."""

    version_number: int
    description: str
    source: str
    created_at: datetime
    is_current: bool


@dataclass(frozen=True, slots=True)
class UIMutationInput:
    instruction: str
    document: UIDocument
    selected_component_id: str | None

    versions: Sequence[VersionInfo]
    history: Sequence[ConversationTurn]
    datasets: Sequence[DatasetDescriptor]
    validation_context: ValidationContext
    progress: ProgressReporter | None = None
    # For an application: the screen the user is looking at, and the workspace
    # new images would belong to.
    active_screen_id: str | None = None
    workspace_id: uuid.UUID | None = None


class MutationPlanKind(StrEnum):
    OPERATIONS = "operations"
    RESTORE = "restore"
    COMPARE = "compare"
    MESSAGE = "message"


@dataclass(frozen=True, slots=True)
class UIMutationOutput:
    kind: MutationPlanKind
    message: str
    # Set for OPERATIONS: the normalised steps and the validated resulting document.
    outcome: MutationOutcome | None
    # Set for RESTORE / COMPARE.
    version_number: int | None
    provider: str
    model: str
    prompt_version: str
    repair_attempts: int


class UIMutationPlanner(Protocol):
    """Turns an edit instruction into validated operations or a version request."""

    async def plan(self, request: UIMutationInput) -> UIMutationOutput: ...


# What an application build reports while it runs: stage name, percent, detail.
BuildProgress = Callable[[str, int, str | None], Awaitable[None]]


@dataclass(frozen=True, slots=True)
class ApplicationBuildInput:
    user_request: str
    workspace_id: uuid.UUID
    history: Sequence[ConversationTurn]
    datasets: Sequence[DatasetDescriptor]
    framework: str
    design_system: str | None
    theme_preset: str | None
    progress: BuildProgress | None = None


@dataclass(frozen=True, slots=True)
class QualityFinding:
    category: str
    severity: str
    message: str
    recommendation: str
    screen_id: str | None


@dataclass(frozen=True, slots=True)
class ApplicationBuildOutput:
    """``document`` is ``None`` when the request turned out to be for a single view,
    which the caller then generates through ``UIGenerator``."""

    document: UIDocument | None
    quality_score: int | None
    findings: Sequence[QualityFinding]
    failed_screen_ids: Sequence[str]
    provider: str | None
    model: str | None
    prompt_version: str
    repair_attempts: int


class ApplicationBuilder(Protocol):
    """Designs and builds a complete application from an idea."""

    async def build(self, request: ApplicationBuildInput) -> ApplicationBuildOutput: ...


# --- Versions -----------------------------------------------------------------


class VersionSource(StrEnum):
    AI_GENERATION = "ai_generation"
    AI_MUTATION = "ai_mutation"
    MANUAL_EDIT = "manual_edit"
    RESTORE = "restore"


class VersionSummary(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    version_number: int
    parent_version_id: uuid.UUID | None
    description: str
    source: VersionSource
    metadata: dict[str, JsonValue] = Field(description="Provenance: proposal, instruction, ...")
    created_at: datetime
    created_by: uuid.UUID | None
    is_current: bool


class VersionDetail(VersionSummary):
    document: UIDocument
    data: dict[str, list[DataRow]] = Field(description="Rows for every dataset the document binds.")


class VersionCreate(BaseModel):
    """Persist an approved change as the next version.

    Send either the complete ``document`` (an approved generation) or the
    ``operations`` to apply to the base version (an approved edit).
    """

    base_version_id: uuid.UUID | None = Field(
        description="The version the change was prepared against; null only for the first version."
    )
    source: VersionSource = VersionSource.MANUAL_EDIT
    description: str | None = Field(default=None, min_length=1, max_length=300)
    proposal_id: uuid.UUID | None = None
    instruction: str | None = Field(default=None, max_length=MAX_MESSAGE_LENGTH)
    document: dict[str, JsonValue] | None = None
    operations: list[DocumentOperation] | None = Field(
        default=None, min_length=1, max_length=MAX_OPERATIONS
    )

    @model_validator(mode="after")
    def _check_payload(self) -> Self:
        if (self.document is None) == (self.operations is None):
            raise ValueError("Send exactly one of 'document' and 'operations'.")
        if self.source is VersionSource.RESTORE:
            raise ValueError("Use the restore endpoint to restore a version.")
        return self


class VersionRestore(BaseModel):
    base_version_id: uuid.UUID = Field(
        description="The workspace's current version as seen by the client."
    )
    proposal_id: uuid.UUID | None = None


class ChangeRead(BaseModel):
    kind: ChangeKind
    summary: str
    component_id: str | None = None


class VersionComparison(BaseModel):
    from_version: VersionSummary
    to_version: VersionSummary
    changes: list[ChangeRead]


# --- Proposals ----------------------------------------------------------------


class ProposalKind(StrEnum):
    GENERATE = "generate"
    MUTATE = "mutate"
    RESTORE = "restore"
    COMPARE = "compare"
    MESSAGE = "message"


class GenerateUIRequest(BaseModel):
    workspace_id: uuid.UUID
    instruction: str = Field(
        min_length=1,
        max_length=MAX_MESSAGE_LENGTH,
        examples=["Create a sales dashboard with revenue, orders and monthly sales."],
    )
    theme_preset: str | None = Field(default=None, description="Preferred theme for a new UI.")
    design_system: str | None = None
    framework: str | None = None


class MutateUIRequest(BaseModel):
    """Ask for a change (``instruction``) or check client-made ``operations``."""

    workspace_id: uuid.UUID
    base_version_id: uuid.UUID
    instruction: str | None = Field(
        default=None,
        min_length=1,
        max_length=MAX_MESSAGE_LENGTH,
        examples=["Move the revenue card to the top right."],
    )
    selected_component_id: ComponentId | None = Field(
        default=None, description="The component the user has selected; resolves 'this'."
    )
    active_screen_id: ComponentId | None = Field(
        default=None,
        description="In an application: the screen on display; resolves 'this screen'.",
    )
    operations: list[DocumentOperation] | None = Field(
        default=None, min_length=1, max_length=MAX_OPERATIONS
    )

    @model_validator(mode="after")
    def _check_payload(self) -> Self:
        if (self.instruction is None) == (self.operations is None):
            raise ValueError("Send exactly one of 'instruction' and 'operations'.")
        return self


class ProposalStep(BaseModel):
    operation: dict[str, Any] = Field(description="A normalised operation, ready to apply.")
    summary: str
    affected_component_ids: list[str]


class ValidationIssueRead(BaseModel):
    stage: ValidationStage
    path: str
    message: str


class ValidationResult(BaseModel):
    valid: bool
    issues: list[ValidationIssueRead]


class ProposalMetadata(BaseModel):
    provider: str | None = Field(default=None, examples=["groq"])
    model: str | None = None
    prompt_version: str | None = None
    repair_attempts: int = 0
    intent: UIIntent | None = None
    schema_version: str


class ScreenSummary(BaseModel):
    id: str
    title: str
    route: str
    screen_type: str
    in_navigation: bool
    failed: bool = Field(description="True when the screen could not be generated.")


class EntitySummary(BaseModel):
    name: str
    label: str
    record_count: int


class DesignSummary(BaseModel):
    style: str
    style_name: str
    summary: str | None
    mode: str
    palette: str | None
    mood: list[str]


class ApplicationSummary(BaseModel):
    """What a proposed application consists of, for approval at application level."""

    name: str
    category: str
    description: str
    navigation_style: str
    design: DesignSummary
    screens: list[ScreenSummary]
    entities: list[EntitySummary]
    interactions: list[str]
    component_count: int
    pattern_count: int = Field(description="Distinct kinds of component used.")
    asset_count: int


class GraphEdgeRead(BaseModel):
    source: str
    target: str
    kind: str = Field(description="navigation, action (a transition) or data (a shared entity).")
    label: str | None = None


class ApplicationRead(BaseModel):
    """The current application of a workspace: what it is and how its screens relate."""

    version_id: uuid.UUID
    version_number: int
    summary: ApplicationSummary
    edges: list[GraphEdgeRead]
    unreachable_screen_ids: list[str]


class QualityIssueRead(BaseModel):
    category: str
    severity: str
    message: str
    recommendation: str
    screen_id: str | None = None


class QualityRead(BaseModel):
    score: int = Field(ge=0, le=100)
    issues: list[QualityIssueRead]


class ProposalRead(BaseModel):
    """A change that has NOT been saved. Persist it through the versions API once approved."""

    proposal_id: uuid.UUID
    kind: ProposalKind
    workspace_id: uuid.UUID
    base_version_id: uuid.UUID | None
    message: str
    steps: list[ProposalStep] = Field(description="Operations of a 'mutate' proposal.")
    document: UIDocument | None = Field(description="The UI as it would be after approval.")
    data: dict[str, list[DataRow]]
    changes: list[ChangeRead] = Field(description="Differences from the current version.")
    affected_component_ids: list[str]
    target_version: VersionSummary | None = Field(description="For 'restore' and 'compare'.")
    validation: ValidationResult
    metadata: ProposalMetadata
    application: ApplicationSummary | None = Field(
        default=None, description="Set when the proposed UI is an application."
    )
    quality: QualityRead | None = Field(
        default=None, description="Design review of a generated application."
    )


class ValidateUIRequest(BaseModel):
    document: dict[str, JsonValue] = Field(description="A UI document to validate.")


class ValidateUIResponse(BaseModel):
    valid: bool
    issues: list[ValidationIssueRead]
    document: UIDocument | None = Field(default=None, description="Normalised document when valid.")


# --- Registries ---------------------------------------------------------------


class ComponentRead(BaseModel):
    type: ComponentType
    category: ComponentCategory
    description: str
    accepts_children: bool
    variants: list[str] = Field(description="Values of the component's `variant`, if any.")
    example: dict[str, JsonValue]


class ComponentCatalogResponse(BaseModel):
    schema_version: str
    components: list[ComponentRead]
    allowed_actions: list[str]
    json_schema: dict[str, JsonValue] = Field(description="JSON Schema of a complete UI document.")


class FrameworkRead(BaseModel):
    id: str
    name: str
    status: FrameworkStatus
    description: str


class DesignSystemRead(BaseModel):
    """A visual style: tokens plus what the design catalogue knows about it."""

    id: str
    name: str
    description: str
    tokens: ThemePatch
    mood: list[str] = Field(default_factory=list)
    suited_for: list[str] = Field(default_factory=list)
    imagery: str = "none"
    effects: list[str] = Field(default_factory=list)
    palettes: list[str] = Field(default_factory=list)
    navigation: list[str] = Field(default_factory=list)


class FrameworkCatalogResponse(BaseModel):
    default_framework: str
    default_design_system: str
    frameworks: list[FrameworkRead]
    design_systems: list[DesignSystemRead]


class ThemePresetRead(BaseModel):
    id: str
    name: str
    description: str
    theme: Theme


class ThemeCatalogResponse(BaseModel):
    default_theme: Theme
    presets: list[ThemePresetRead]


class PatternRead(BaseModel):
    id: str
    component: ComponentType
    variant: str | None
    category: str
    purpose: str
    screen_types: list[str]
    suited_for: list[str]
    density: str
    characteristics: list[str]
    needs_data: bool
    image: str
    effects: list[str]
    responsive: str
    frameworks: list[str]


class CompositionRead(BaseModel):
    id: str
    name: str
    screen_type: str
    suited_for: list[str]
    patterns: list[str]
    note: str


class EffectRead(BaseModel):
    id: str
    name: str
    description: str
    use_for: str


class PatternCatalogResponse(BaseModel):
    """The design knowledge library: patterns, example compositions and effects."""

    patterns: list[PatternRead]
    compositions: list[CompositionRead]
    effects: list[EffectRead]
    icons: list[str]


class LayoutCapabilities(BaseModel):
    model: str = Field(examples=["flow-grid"])
    columns: int
    heights: list[str]
    containers: list[ComponentType]


class CapabilitiesResponse(BaseModel):
    schema_version: str
    components: list[ComponentType]
    chart_types: list[str]
    layout: LayoutCapabilities
    interactions: list[ComponentType]
    actions: list[str]
    operations: list[str]
    version_operations: list[str]
    style_tones: list[str]
    theme_tokens: list[str]
    component_variants: dict[str, list[str]] = Field(
        description="Variants each component supports, keyed by component type."
    )
    surface_variants: list[str]
    button_variants: list[str]
    effects: list[str]
    screen_types: list[str]
    navigation_styles: list[str]
    fonts: list[str]
