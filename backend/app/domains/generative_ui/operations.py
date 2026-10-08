"""The mutation language: every way a UI document can change.

The model (and the editor) express changes as these operations. They are data:
the mutation engine interprets them, and the result is validated like any other
document. The same contract is implemented by the frontend engine.
"""

from enum import StrEnum
from typing import Annotated, Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator

from app.domains.common import StrictModel
from app.domains.generative_ui.document import (
    Asset,
    Entity,
    NavigationItem,
    NavigationStyle,
    ThemePatch,
)
from app.domains.generative_ui.schemas import (
    GRID_COLUMNS,
    Alignment,
    ColorRole,
    Component,
    ComponentDensity,
    ComponentId,
    Effect,
    Emphasis,
    FieldKey,
    HeightPreset,
    ShortText,
    SurfaceVariant,
    VisualPriority,
)

MAX_OPERATIONS = 50


class OperationType(StrEnum):
    CREATE = "CREATE"
    DELETE = "DELETE"
    MOVE = "MOVE"
    RESIZE = "RESIZE"
    STYLE = "STYLE"
    UPDATE = "UPDATE"
    REORDER = "REORDER"
    GROUP = "GROUP"
    UNGROUP = "UNGROUP"
    REPLACE = "REPLACE"
    SET_THEME = "SET_THEME"
    SET_FRAMEWORK = "SET_FRAMEWORK"
    SET_DESIGN_SYSTEM = "SET_DESIGN_SYSTEM"
    # Application-level: change the product around the screens.
    SET_NAVIGATION = "SET_NAVIGATION"
    UPDATE_APPLICATION = "UPDATE_APPLICATION"
    ADD_ASSETS = "ADD_ASSETS"
    UPSERT_ENTITIES = "UPSERT_ENTITIES"


class VersionOperationType(StrEnum):
    RESTORE_VERSION = "RESTORE_VERSION"
    COMPARE_VERSIONS = "COMPARE_VERSIONS"


class GroupContainerType(StrEnum):
    SECTION = "section"
    CARD = "card"


class _Placement(StrictModel):
    """Where to put a component: inside ``parent_id``, at one optional anchor."""

    parent_id: ComponentId | None = Field(
        default=None, description="Container (or tab) id. Defaults to the current parent / page."
    )
    before: ComponentId | None = None
    after: ComponentId | None = None
    index: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def _single_anchor(self) -> Self:
        anchors = [self.before, self.after, self.index]
        if sum(anchor is not None for anchor in anchors) > 1:
            raise ValueError("Use at most one of 'before', 'after' and 'index'.")
        return self


class CreateOperation(_Placement):
    type: Literal[OperationType.CREATE]
    component: Component


class DeleteOperation(StrictModel):
    type: Literal[OperationType.DELETE]
    target: ComponentId


class MoveOperation(_Placement):
    type: Literal[OperationType.MOVE]
    target: ComponentId


class ResizeOperation(StrictModel):
    type: Literal[OperationType.RESIZE]
    target: ComponentId
    span: int | None = Field(default=None, ge=1, le=GRID_COLUMNS)
    height: HeightPreset | None = None

    @model_validator(mode="after")
    def _changes_something(self) -> Self:
        if self.span is None and self.height is None:
            raise ValueError("RESIZE needs 'span' and/or 'height'.")
        return self


class StylePatch(StrictModel):
    """``null`` clears a style token."""

    tone: ColorRole | None = None
    emphasis: Emphasis | None = None
    surface: SurfaceVariant | None = None
    priority: VisualPriority | None = None
    density: ComponentDensity | None = None
    align: Alignment | None = None
    effects: list[Effect] | None = Field(default=None, max_length=3)


class StyleOperation(StrictModel):
    type: Literal[OperationType.STYLE]
    target: ComponentId
    style: StylePatch


class UpdateOperation(StrictModel):
    """Shallow-merge ``props`` into a component; ``null`` removes an optional prop."""

    type: Literal[OperationType.UPDATE]
    target: ComponentId
    props: dict[str, JsonValue] = Field(min_length=1)


class ReorderOperation(StrictModel):
    type: Literal[OperationType.REORDER]
    parent_id: ComponentId
    order: list[ComponentId] = Field(min_length=1)


class GroupSpec(StrictModel):
    id: ComponentId
    type: GroupContainerType = GroupContainerType.SECTION
    title: ShortText | None = None


class GroupOperation(StrictModel):
    type: Literal[OperationType.GROUP]
    targets: list[ComponentId] = Field(min_length=1)
    group: GroupSpec


class UngroupOperation(StrictModel):
    type: Literal[OperationType.UNGROUP]
    target: ComponentId


class ReplaceOperation(StrictModel):
    type: Literal[OperationType.REPLACE]
    target: ComponentId
    component: Component


class SetThemeOperation(StrictModel):
    type: Literal[OperationType.SET_THEME]
    preset: FieldKey | None = None
    tokens: ThemePatch | None = None

    @model_validator(mode="after")
    def _changes_something(self) -> Self:
        if self.preset is None and self.tokens is None:
            raise ValueError("SET_THEME needs 'preset' and/or 'tokens'.")
        return self


class SetFrameworkOperation(StrictModel):
    type: Literal[OperationType.SET_FRAMEWORK]
    framework: FieldKey


class SetDesignSystemOperation(StrictModel):
    type: Literal[OperationType.SET_DESIGN_SYSTEM]
    design_system: FieldKey
    tokens: ThemePatch | None = Field(
        default=None, description="Filled in by the backend from the design system."
    )


class SetNavigationOperation(StrictModel):
    """Change the application shell. Omitted fields keep their value."""

    type: Literal[OperationType.SET_NAVIGATION]
    style: NavigationStyle | None = None
    brand: ShortText | None = None
    tagline: ShortText | None = None
    home: ComponentId | None = None
    items: list[NavigationItem] | None = Field(default=None, max_length=20)
    action: NavigationItem | None = None

    @model_validator(mode="after")
    def _changes_something(self) -> Self:
        if not self.model_fields_set - {"type"}:
            raise ValueError("SET_NAVIGATION needs at least one field to change.")
        return self


class UpdateApplicationOperation(StrictModel):
    """Shallow-merge descriptive fields of the application; ``null`` removes an optional one."""

    type: Literal[OperationType.UPDATE_APPLICATION]
    props: dict[str, JsonValue] = Field(min_length=1)


class AddAssetsOperation(StrictModel):
    """Register stored images so components can reference them. Same id replaces."""

    type: Literal[OperationType.ADD_ASSETS]
    assets: list[Asset] = Field(min_length=1, max_length=20)


class UpsertEntitiesOperation(StrictModel):
    """Add data entities, or replace ones with the same name (fields and sample records)."""

    type: Literal[OperationType.UPSERT_ENTITIES]
    entities: list[Entity] = Field(min_length=1, max_length=10)


DocumentOperation = Annotated[
    CreateOperation
    | DeleteOperation
    | MoveOperation
    | ResizeOperation
    | StyleOperation
    | UpdateOperation
    | ReorderOperation
    | GroupOperation
    | UngroupOperation
    | ReplaceOperation
    | SetThemeOperation
    | SetFrameworkOperation
    | SetDesignSystemOperation
    | SetNavigationOperation
    | UpdateApplicationOperation
    | AddAssetsOperation
    | UpsertEntitiesOperation,
    Field(discriminator="type"),
]


class RestoreVersionOperation(StrictModel):
    type: Literal[VersionOperationType.RESTORE_VERSION]
    version_number: int = Field(ge=1)


class CompareVersionsOperation(StrictModel):
    type: Literal[VersionOperationType.COMPARE_VERSIONS]
    version_number: int = Field(ge=1)


VersionOperation = RestoreVersionOperation | CompareVersionsOperation

AssistantOperation = Annotated[
    CreateOperation
    | DeleteOperation
    | MoveOperation
    | ResizeOperation
    | StyleOperation
    | UpdateOperation
    | ReorderOperation
    | GroupOperation
    | UngroupOperation
    | ReplaceOperation
    | SetThemeOperation
    | SetFrameworkOperation
    | SetDesignSystemOperation
    | SetNavigationOperation
    | UpdateApplicationOperation
    | AddAssetsOperation
    | UpsertEntitiesOperation
    | RestoreVersionOperation
    | CompareVersionsOperation,
    Field(discriminator="type"),
]


class AssistantPlan(BaseModel):
    """What the model returns for an edit request."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    message: str = Field(min_length=1, max_length=1000)
    operations: list[AssistantOperation] = Field(default_factory=list, max_length=MAX_OPERATIONS)


def dump_operation(operation: BaseModel) -> dict[str, Any]:
    """JSON form of an operation. Explicit ``null``s are kept: they mean "remove"."""
    return operation.model_dump(mode="json", exclude_unset=True)


# One example per operation. Shown to the model, exported to the frontend's
# contract tests, and validated by the backend's own tests.
OPERATION_EXAMPLES: tuple[tuple[str, dict[str, Any]], ...] = (
    (
        "Add a component. Place it with parent_id plus at most one of before / after / index.",
        {
            "type": "CREATE",
            "parent_id": "page",
            "after": "revenue_metric",
            "component": {
                "type": "metric",
                "id": "orders_metric",
                "title": "Orders",
                "data_source": {"dataset": "sales_summary", "field": "total_orders"},
                "layout": {"span": 3},
            },
        },
    ),
    ("Remove a component and everything inside it.", {"type": "DELETE", "target": "old_table"}),
    (
        "Move a component among its siblings or into another container (or tab).",
        {"type": "MOVE", "target": "revenue_metric", "after": "orders_metric"},
    ),
    (
        "Change width (span, 1-12 columns) and/or height (auto, sm, md, lg, xl).",
        {"type": "RESIZE", "target": "sales_chart", "span": 8, "height": "lg"},
    ),
    (
        "Set style tokens. tone: primary, secondary, success, warning, destructive, neutral. "
        "emphasis: subtle, default, strong. null clears a token.",
        {"type": "STYLE", "target": "revenue_metric", "style": {"tone": "success"}},
    ),
    (
        "Change a component's own fields (not id, type, layout, style or children). "
        "null removes an optional field.",
        {"type": "UPDATE", "target": "sales_chart", "props": {"chart_type": "line"}},
    ),
    (
        "Set the complete order of a container's children.",
        {"type": "REORDER", "parent_id": "page", "order": ["sales_chart", "regional_table"]},
    ),
    (
        "Wrap sibling components in a new section or card.",
        {
            "type": "GROUP",
            "targets": ["revenue_metric", "orders_metric"],
            "group": {"id": "kpi_section", "type": "section", "title": "Key metrics"},
        },
    ),
    ("Dissolve a section or card, keeping its children.", {"type": "UNGROUP", "target": "kpis"}),
    (
        "Swap a component for a different one in the same place. Keep data_source when the "
        "new component shows the same data.",
        {
            "type": "REPLACE",
            "target": "regional_table",
            "component": {
                "type": "chart",
                "id": "regional_table",
                "title": "Sales by region",
                "chart_type": "bar",
                "x_key": "region",
                "y_keys": ["revenue"],
                "data_source": {"dataset": "sales_by_region"},
            },
        },
    ),
    (
        "Change the theme: a preset, individual tokens, or both (tokens override the preset).",
        {"type": "SET_THEME", "preset": "slate_dark", "tokens": {"colors": {"primary": "#38BDF8"}}},
    ),
    (
        "Render the same UI with a different component framework.",
        {"type": "SET_FRAMEWORK", "framework": "material"},
    ),
    (
        "Change shape, density and typography without changing colours or content.",
        {"type": "SET_DESIGN_SYSTEM", "design_system": "compact_pro"},
    ),
)

# Operations that only make sense for an application (a document with screens).
APPLICATION_OPERATION_EXAMPLES: tuple[tuple[str, dict[str, Any]], ...] = (
    (
        "Change the application shell: style (sidebar, topbar, bottom, minimal, none), brand, "
        "home screen, or the complete list of navigation items.",
        {"type": "SET_NAVIGATION", "style": "topbar"},
    ),
    (
        "Change descriptive fields of the application (name, category, description, "
        "target_users, goals, features, interactions, design_direction).",
        {"type": "UPDATE_APPLICATION", "props": {"name": "Hirewell"}},
    ),
)

VERSION_OPERATION_EXAMPLES: tuple[tuple[str, dict[str, Any]], ...] = (
    (
        "Go back to an earlier version (creates a new version; history is kept).",
        {"type": "RESTORE_VERSION", "version_number": 3},
    ),
    (
        "Show what differs between the current UI and an earlier version.",
        {"type": "COMPARE_VERSIONS", "version_number": 2},
    ),
)
