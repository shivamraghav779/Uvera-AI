"""What each planning stage of application generation produces.

Every stage of the pipeline returns one of these models. They are parsed
leniently (unknown keys ignored, sensible defaults) because they are plans for
later stages, not the final document; ``normalise_*`` then makes each plan
internally consistent so later stages can rely on it. The final document is
validated strictly by the UI validator like any other.
"""

import re
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domains.actions.schemas import ActionType
from app.domains.assets.schemas import AssetDecision
from app.domains.common import DataRow
from app.domains.generative_ui.application import route_params
from app.domains.generative_ui.document import (
    PRIMARY_KEY,
    AssetKind,
    EntityField,
    EntityFieldType,
    GradientLevel,
    ImageryKind,
    MotionLevel,
    NavigationStyle,
    SurfaceStyle,
    ThemeColorsPatch,
    ThemeMode,
    TypographyPatch,
)
from app.domains.generative_ui.schemas import (
    Effect,
    ScreenType,
    ScreenWidth,
    VisualPriority,
)

MAX_BLUEPRINT_SCREENS = 20
_SLUG = re.compile(r"[^a-z0-9]+")
_ROUTE_SEGMENT = re.compile(r"^(?::[A-Za-z][A-Za-z0-9_]*|[A-Za-z0-9_-]+)$")


class _Plan(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)


def slug(text: str, fallback: str = "item") -> str:
    """A lower-case identifier made from ``text`` (letters, digits, underscores)."""
    cleaned = _SLUG.sub("_", text.lower()).strip("_")
    if not cleaned:
        return fallback
    return cleaned if cleaned[0].isalpha() else f"{fallback}_{cleaned}"


def _clip(text: str | None, limit: int = 200) -> str | None:
    return text[:limit] if text else None


# --- Stage 1: the application blueprint ----------------------------------------------


class GenerationScope(StrEnum):
    APPLICATION = "application"
    SINGLE_VIEW = "single_view"


class ScreenBrief(_Plan):
    id: str
    name: str
    route: str
    type: ScreenType = ScreenType.CUSTOM
    purpose: str = ""
    user_goal: str | None = None
    in_navigation: bool = True
    icon: str | None = None
    group: str | None = None
    entity: str | None = Field(default=None, description="Main entity the screen is about.")


class EntityBrief(_Plan):
    name: str
    label: str
    description: str | None = None
    title_field: str = ""
    fields: list[EntityField] = Field(default_factory=list)


class Workflow(_Plan):
    name: str
    steps: list[str] = Field(default_factory=list)


class ApplicationBlueprint(_Plan):
    """The product as understood from the user's idea: screens, data and shell."""

    scope: GenerationScope = GenerationScope.APPLICATION
    name: str
    category: str = "Application"
    description: str = ""
    target_users: list[str] = Field(default_factory=list)
    goals: list[str] = Field(default_factory=list)
    features: list[str] = Field(default_factory=list)
    navigation_style: NavigationStyle = NavigationStyle.SIDEBAR
    home: str = ""
    screens: list[ScreenBrief] = Field(default_factory=list)
    entities: list[EntityBrief] = Field(default_factory=list)
    workflows: list[Workflow] = Field(default_factory=list)

    @property
    def brief(self) -> str:
        """One line of text for keyword retrieval over the design catalogue."""
        return " ".join([self.name, self.category, self.description, *self.features]).lower()

    def screen(self, screen_id: str) -> ScreenBrief | None:
        return next((screen for screen in self.screens if screen.id == screen_id), None)


def _normalise_route(route: str, screen_id: str) -> str:
    segments = [s for s in route.strip().split("?")[0].split("/") if s]
    kept = [s for s in segments if _ROUTE_SEGMENT.match(s)]
    return "/" + "/".join(kept) if kept or not segments else f"/{screen_id.replace('_', '-')}"


def _unique(candidate: str, taken: set[str]) -> str:
    name, counter = candidate, 2
    while name in taken:
        name, counter = f"{candidate}_{counter}", counter + 1
    taken.add(name)
    return name


def _normalise_entity(entity: EntityBrief, taken: set[str]) -> EntityBrief | None:
    seen: set[str] = set()
    fields: list[EntityField] = []
    for field in entity.fields:
        key = slug(field.key, "field")
        if key == PRIMARY_KEY or key in seen:
            continue
        seen.add(key)
        fields.append(field.model_copy(update={"key": key}))
    if not fields:
        return None
    title = slug(entity.title_field, "field") if entity.title_field else ""
    return entity.model_copy(
        update={
            "name": _unique(slug(entity.name, "entity")[:60], taken),
            "label": entity.label[:200] or entity.name,
            "description": _clip(entity.description),
            "fields": fields[:24],
            "title_field": title if title in seen else fields[0].key,
        }
    )


def normalise_blueprint(blueprint: ApplicationBlueprint, max_screens: int) -> ApplicationBlueprint:
    """Make ids, routes and references consistent; cap the number of screens."""
    entity_names: set[str] = set()
    entities = [e for e in (_normalise_entity(e, entity_names) for e in blueprint.entities) if e]
    for entity in entities:
        for field in entity.fields:
            if field.references is not None and field.references not in entity_names:
                field.references = None
            if field.type is EntityFieldType.REFERENCE and field.references is None:
                field.type = EntityFieldType.TEXT

    ids: set[str] = {"page"}
    route_shapes: set[str] = set()
    screens: list[ScreenBrief] = []
    for screen in blueprint.screens[: min(max_screens, MAX_BLUEPRINT_SCREENS)]:
        screen_id = _unique(slug(screen.id or screen.name, "screen")[:48], ids)
        route = _normalise_route(screen.route or f"/{screen_id}", screen_id)
        shape = "/".join(":" if part.startswith(":") else part for part in route.split("/"))
        if shape in route_shapes:
            route = f"/{screen_id.replace('_', '-')}"
            shape = route
        route_shapes.add(shape)
        has_params = bool(route_params(route))
        screens.append(
            screen.model_copy(
                update={
                    "id": screen_id,
                    "name": screen.name[:200] or screen_id,
                    "route": route,
                    "purpose": screen.purpose[:200],
                    "user_goal": _clip(screen.user_goal),
                    "group": _clip(screen.group, 60),
                    # A route with parameters needs a record to open; it cannot be a menu item.
                    "in_navigation": screen.in_navigation and not has_params,
                    "entity": screen.entity if screen.entity in entity_names else None,
                    "icon": slug(screen.icon, "icon").replace("_", "-")[:40]
                    if screen.icon
                    else None,
                }
            )
        )
    static = [screen.id for screen in screens if not route_params(screen.route)]
    home = slug(blueprint.home, "") if blueprint.home else ""
    if home not in static and static:
        home = static[0]
    known = {screen.id for screen in screens}
    workflows = [
        Workflow(name=w.name[:200], steps=[s for s in w.steps if s in known])
        for w in blueprint.workflows[:8]
    ]
    return blueprint.model_copy(
        update={
            "name": blueprint.name[:200],
            "category": blueprint.category[:200] or "Application",
            "description": blueprint.description[:600] or blueprint.name,
            "target_users": [t[:200] for t in blueprint.target_users[:8] if t],
            "goals": [g[:200] for g in blueprint.goals[:8] if g],
            "features": [f[:200] for f in blueprint.features[:16] if f],
            "screens": screens,
            "entities": entities[:20],
            "home": home,
            "workflows": [w for w in workflows if w.steps],
        }
    )


# --- Stage 2: design direction ---------------------------------------------------------


class DesignTokens(_Plan):
    """Overrides of the chosen style's tokens. Anything invalid is ignored."""

    radius: str | None = None
    density: str | None = None
    spacing: str | None = None
    shadows: str | None = None
    surface: SurfaceStyle | None = None
    motion: MotionLevel | None = None
    gradient: GradientLevel | None = None
    typography: TypographyPatch | None = None


class DesignPlan(_Plan):
    """The visual language for the whole product, decided before any screen."""

    style: str
    summary: str = ""
    mood: list[str] = Field(default_factory=list)
    rationale: str | None = None
    mode: ThemeMode | None = None
    palette: str | None = Field(default=None, description="Id of a theme preset.")
    colors: ThemeColorsPatch | None = Field(
        default=None, description="Individual colours to change on the preset."
    )
    tokens: DesignTokens | None = None
    imagery: ImageryKind = ImageryKind.NONE
    visual_language: str | None = None
    layout: str | None = None
    effects: list[Effect] = Field(default_factory=list)
    navigation_style: NavigationStyle | None = None


# --- Stage 3: sample data ----------------------------------------------------------------


def _flat(value: object) -> object:
    """A cell is one value. A model sometimes writes a list (tags) or an object (an address)."""
    if isinstance(value, list):
        return ", ".join(str(_flat(item)) for item in value if item is not None)
    if isinstance(value, dict):
        return ", ".join(str(_flat(item)) for item in value.values() if item is not None)
    return value


class EntityRecords(_Plan):
    name: str
    records: list[DataRow] = Field(default_factory=list)

    @field_validator("records", mode="before")
    @classmethod
    def _flatten_cells(cls, records: object) -> object:
        if not isinstance(records, list):
            return records
        return [
            {key: _flat(value) for key, value in record.items()}
            if isinstance(record, dict)
            else record
            for record in records
        ]


class DataPlan(_Plan):
    entities: list[EntityRecords] = Field(default_factory=list)


# --- Stage 4: screen plan (patterns and composition) -----------------------------------


class SectionPlan(_Plan):
    pattern: str
    purpose: str = ""
    priority: VisualPriority = VisualPriority.SECONDARY
    span: int | None = Field(default=None, ge=1, le=12)
    entity: str | None = None
    image: bool = False
    image_brief: str | None = None


class ScreenPlan(_Plan):
    screen_id: str
    width: ScreenWidth = ScreenWidth.CONTAINED
    composition: str = Field(default="", description="The layout idea in one sentence.")
    sections: list[SectionPlan] = Field(default_factory=list)
    responsive: str | None = None


class ScreenPlans(_Plan):
    screens: list[ScreenPlan] = Field(default_factory=list)


# --- Stage 5: assets -----------------------------------------------------------------------


class AssetBrief(_Plan):
    id: str
    decision: AssetDecision = AssetDecision.GENERATE
    kind: AssetKind = AssetKind.PHOTO
    prompt: str = ""
    query: str = ""
    alt: str = ""
    width: int = 1280
    height: int = 800
    usage: str | None = None
    screen_id: str | None = None
    # When the image belongs to a record: which field of which record it fills.
    entity: str | None = None
    record_id: str | None = None
    field: str | None = None


class AssetPlan(_Plan):
    assets: list[AssetBrief] = Field(default_factory=list)


# --- Stage 6: interactions ---------------------------------------------------------------


class InteractionBrief(_Plan):
    id: str
    label: str
    type: ActionType
    screen_id: str | None = None
    trigger: str | None = None
    entity: str | None = None
    target_route: str | None = None
    set_field: str | None = None
    set_value: str | None = None
    result: str | None = None


class InteractionPlan(_Plan):
    interactions: list[InteractionBrief] = Field(default_factory=list)
