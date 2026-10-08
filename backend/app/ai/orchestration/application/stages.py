"""The specialised stages of application generation.

Each class does one job and returns a typed plan:

    ApplicationPlanner   idea            -> blueprint (screens, entities, shell)
    DesignDirector       blueprint       -> design plan (style, palette, imagery)
    DataPlanner          entities        -> realistic sample records
    PatternPlanner       screens         -> relevant part of the pattern catalogue
    ScreenPlanner        screens         -> composition of each screen
    AssetPlanner         sections        -> image briefs and how to obtain each
    InteractionPlanner   screens         -> what people can do and where
    ScreenGenerator      one screen plan -> a validated component tree

Stages hold no prompt text (see ``app.ai.prompts.application``) and no knowledge
of each other; the pipeline sequences them.
"""

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from app.ai.llm.base import GenerationOptions
from app.ai.orchestration.application.runner import StageRejectedError, StageRunner, reject
from app.ai.prompts.actions import ActionGuideEntry
from app.ai.prompts.application import (
    APPLICATION_PLANNER_PROMPT,
    ASSET_PLANNER_PROMPT,
    DATA_PLANNER_PROMPT,
    DESIGN_DIRECTOR_PROMPT,
    INTERACTION_PLANNER_PROMPT,
    SCREEN_ADDITION_PROMPT,
    SCREEN_GENERATOR_PROMPT,
    SCREEN_PLANNER_PROMPT,
    build_asset_messages,
    build_data_messages,
    build_design_messages,
    build_interaction_messages,
    build_planner_messages,
    build_screen_addition_messages,
    build_screen_messages,
    build_screen_plan_messages,
)
from app.core.exceptions import UIGenerationException
from app.core.logging import get_logger
from app.domains.data_sources.schemas import DatasetDescriptor
from app.domains.generation.assembly import (
    ScreenContext,
    build_entities,
    build_screen,
    normalise_screen_plans,
)
from app.domains.generation.blueprint import (
    ApplicationBlueprint,
    AssetBrief,
    AssetPlan,
    DataPlan,
    DesignPlan,
    EntityBrief,
    GenerationScope,
    InteractionBrief,
    InteractionPlan,
    ScreenBrief,
    ScreenPlan,
    ScreenPlans,
    normalise_blueprint,
)
from app.domains.generative_ui.design_registry import DesignRegistry
from app.domains.generative_ui.document import (
    PRIMARY_KEY,
    Asset,
    DesignDirection,
    Entity,
    EntityFieldType,
    ImageryKind,
)
from app.domains.generative_ui.pattern_registry import (
    Composition,
    PatternDescriptor,
    PatternRegistry,
)
from app.domains.generative_ui.planner import ConversationTurn
from app.domains.generative_ui.registry import ComponentDefinition, ComponentRegistry
from app.domains.generative_ui.schemas import ComponentType, ScreenType
from app.domains.generative_ui.validator import ValidationIssue

logger = get_logger(__name__)

_FIELD_TYPES = tuple(field_type.value for field_type in EntityFieldType)
_MARKETING = frozenset({ScreenType.LANDING, ScreenType.CONTENT, ScreenType.PRICING})
_T = ComponentType
# Primitives every screen may use, and those that only application screens need.
_BASE_COMPONENTS = (_T.SECTION, _T.CARD, _T.TEXT, _T.BUTTON, _T.BADGE, _T.DIVIDER, _T.ALERT)
_APP_COMPONENTS = (
    _T.METRIC, _T.TABLE, _T.CHART, _T.SELECT, _T.INPUT, _T.TABS, _T.LIST, _T.PROGRESS,
    _T.TIMELINE,
)  # fmt: skip
_FORM_COMPONENTS = (_T.FORM, _T.INPUT, _T.SELECT, _T.CHECKBOX)
MAX_ENTITIES_PER_DATA_CALL = 3
SUMMARY_ROWS = 20


class ApplicationPlanner:
    """Understands the product and lays out its screens, entities and shell."""

    def __init__(self, runner: StageRunner, design: DesignRegistry, *, max_screens: int) -> None:
        self._runner = runner
        self._design = design
        self._max_screens = max_screens

    async def plan(
        self,
        user_request: str,
        history: Sequence[ConversationTurn],
        datasets: Sequence[DatasetDescriptor],
    ) -> ApplicationBlueprint:
        messages = build_planner_messages(
            user_request=user_request,
            history=history,
            datasets=datasets,
            max_screens=self._max_screens,
            field_types=_FIELD_TYPES,
            icons=self._design.icons(),
        )
        result = await self._runner.run(APPLICATION_PLANNER_PROMPT, messages, self._parse)
        return result.value

    def _parse(self, payload: object) -> ApplicationBlueprint:
        blueprint = normalise_blueprint(
            ApplicationBlueprint.model_validate(payload), self._max_screens
        )
        if blueprint.scope is GenerationScope.APPLICATION and not blueprint.screens:
            raise reject("screens", "An application needs at least one screen.")
        if blueprint.scope is GenerationScope.APPLICATION and not blueprint.home:
            raise reject("home", "At least one screen needs a route without parameters.")
        return blueprint

    async def extend(
        self, instruction: str, blueprint: ApplicationBlueprint
    ) -> tuple[list[ScreenBrief], list[EntityBrief]]:
        """New screens (and entities they need) for an existing application."""
        messages = build_screen_addition_messages(
            instruction=instruction,
            blueprint=blueprint,
            field_types=_FIELD_TYPES,
            icons=self._design.icons(),
        )

        def parse(payload: object) -> tuple[list[ScreenBrief], list[EntityBrief]]:
            if not isinstance(payload, dict):
                raise reject("", "Output must be an object.")
            addition = normalise_blueprint(
                ApplicationBlueprint.model_validate(
                    {
                        "name": blueprint.name,
                        "screens": [
                            *(s.model_dump() for s in blueprint.screens),
                            *(payload.get("screens") or []),
                        ],
                        "entities": [
                            *(e.model_dump() for e in blueprint.entities),
                            *(payload.get("entities") or []),
                        ],
                        "home": blueprint.home,
                    }
                ),
                len(blueprint.screens) + 4,
            )
            screens = addition.screens[len(blueprint.screens) :]
            if not screens:
                raise reject("screens", "Add at least one new screen.")
            return screens, addition.entities[len(blueprint.entities) :]

        return (await self._runner.run(SCREEN_ADDITION_PROMPT, messages, parse)).value


class DesignDirector:
    """Sets the visual language of the whole product before any screen exists."""

    def __init__(self, runner: StageRunner, design: DesignRegistry) -> None:
        self._runner = runner
        self._design = design

    async def direct(
        self,
        user_request: str,
        blueprint: ApplicationBlueprint,
        *,
        current: DesignDirection | None = None,
        instruction: str | None = None,
    ) -> DesignPlan:
        messages = build_design_messages(
            user_request=user_request,
            blueprint=blueprint,
            design=self._design,
            current=current,
            instruction=instruction,
        )
        return (await self._runner.run(DESIGN_DIRECTOR_PROMPT, messages, self._parse)).value

    def _parse(self, payload: object) -> DesignPlan:
        plan = DesignPlan.model_validate(payload)
        if self._design.design_system(plan.style) is None:
            known = ", ".join(system.id for system in self._design.design_systems())
            raise reject("style", f"Unknown style '{plan.style}'. Use one of: {known}.")
        return plan


class DataPlanner:
    """Writes realistic, mutually consistent sample records for the entities."""

    def __init__(self, runner: StageRunner, *, records_per_entity: int) -> None:
        self._runner = runner
        self._records = records_per_entity

    async def plan(
        self,
        blueprint: ApplicationBlueprint,
        entities: Sequence[EntityBrief] | None = None,
        existing: Sequence[Entity] = (),
    ) -> list[Entity]:
        """Entities with records. Large models are filled a few entities at a time,
        each call seeing the ids already created so references stay consistent."""
        briefs = list(entities if entities is not None else blueprint.entities)
        built: list[Entity] = list(existing)
        fresh: list[Entity] = []
        for start in range(0, len(briefs), MAX_ENTITIES_PER_DATA_CALL):
            chunk = briefs[start : start + MAX_ENTITIES_PER_DATA_CALL]
            fresh += await self._fill(blueprint, chunk, [*built, *fresh])
        return fresh

    async def _fill(
        self, blueprint: ApplicationBlueprint, chunk: Sequence[EntityBrief], known: Sequence[Entity]
    ) -> list[Entity]:
        existing = {
            entity.name: [
                {PRIMARY_KEY: r[PRIMARY_KEY], entity.title_field: r.get(entity.title_field)}
                for r in entity.records[:SUMMARY_ROWS]
            ]
            for entity in known
        }
        messages = build_data_messages(
            blueprint=blueprint,
            entities=chunk,
            existing=existing,
            records=self._records,
            today=date.today().isoformat(),
        )

        def parse(payload: object) -> list[Entity]:
            entities = build_entities(chunk, DataPlan.model_validate(payload))
            empty = [entity.name for entity in entities if not entity.records]
            if empty:
                raise reject("entities", f"No records were written for: {', '.join(empty)}.")
            return entities

        return (await self._runner.run(DATA_PLANNER_PROMPT, messages, parse)).value


class PatternPlanner:
    """Retrieves the part of the design catalogue relevant to a set of screens."""

    def __init__(self, patterns: PatternRegistry) -> None:
        self._patterns = patterns

    def candidates(
        self, blueprint: ApplicationBlueprint, screens: Sequence[ScreenBrief]
    ) -> tuple[list[PatternDescriptor], list[Composition]]:
        patterns: dict[str, PatternDescriptor] = {}
        compositions: dict[str, Composition] = {}
        for screen_type in dict.fromkeys(screen.type for screen in screens):
            for pattern in self._patterns.select(screen_type, blueprint.brief):
                patterns.setdefault(pattern.id, pattern)
            for composition in self._patterns.compositions_for(screen_type, blueprint.brief):
                compositions.setdefault(composition.id, composition)
        return list(patterns.values()), list(compositions.values())


class ScreenPlanner:
    """Decides each screen's composition: which patterns, in what order, for what."""

    def __init__(self, runner: StageRunner, patterns: PatternRegistry) -> None:
        self._runner = runner
        self._patterns = patterns
        self._pattern_planner = PatternPlanner(patterns)

    async def plan(
        self,
        blueprint: ApplicationBlueprint,
        direction_text: str,
        *,
        screens: Sequence[ScreenBrief] | None = None,
        instruction: str | None = None,
    ) -> dict[str, ScreenPlan]:
        targets = list(screens if screens is not None else blueprint.screens)
        patterns, compositions = self._pattern_planner.candidates(blueprint, targets)
        messages = build_screen_plan_messages(
            blueprint=blueprint,
            direction_text=direction_text,
            patterns=patterns,
            compositions=compositions,
            screens=targets,
            instruction=instruction,
        )

        def parse(payload: object) -> dict[str, ScreenPlan]:
            plans = ScreenPlans.model_validate(payload).screens
            return normalise_screen_plans(plans, blueprint, self._patterns)

        plans = (await self._runner.run(SCREEN_PLANNER_PROMPT, messages, parse)).value
        return {screen.id: plans[screen.id] for screen in targets}


class AssetPlanner:
    """Decides which images are needed and writes the brief for each."""

    def __init__(self, runner: StageRunner) -> None:
        self._runner = runner

    async def plan(
        self,
        blueprint: ApplicationBlueprint,
        direction: DesignDirection,
        plans: Mapping[str, ScreenPlan],
        entities: Sequence[Entity],
        *,
        limit: int,
    ) -> list[AssetBrief]:
        needs = [
            f"- screen {screen_id} ({blueprint.screen(screen_id).name}), "  # type: ignore[union-attr]
            f"section {section.pattern}: {section.image_brief or section.purpose}"
            for screen_id, plan in plans.items()
            for section in plan.sections
            if section.image
        ]
        record_needs = []
        if direction.imagery is not ImageryKind.NONE:
            for entity in entities:
                image_fields = [f.key for f in entity.fields if f.type is EntityFieldType.IMAGE]
                for image_field in image_fields:
                    titles = ", ".join(
                        f"{r[PRIMARY_KEY]} ({r.get(entity.title_field)})"
                        for r in entity.records[:8]
                    )
                    record_needs.append(f"- entity {entity.name}, field {image_field}: {titles}")
        if limit <= 0 or not (needs or record_needs):
            return []
        messages = build_asset_messages(
            blueprint=blueprint,
            direction=direction,
            needs=needs,
            record_needs=record_needs,
            limit=limit,
        )
        result = await self._runner.run(
            ASSET_PLANNER_PROMPT, messages, lambda payload: AssetPlan.model_validate(payload).assets
        )
        return result.value


class InteractionPlanner:
    """Plans what people can do in the application, and where."""

    def __init__(self, runner: StageRunner) -> None:
        self._runner = runner

    async def plan(
        self, blueprint: ApplicationBlueprint, plans: Mapping[str, ScreenPlan]
    ) -> list[InteractionBrief]:
        messages = build_interaction_messages(blueprint=blueprint, plans=plans)
        result = await self._runner.run(
            INTERACTION_PLANNER_PROMPT,
            messages,
            lambda payload: InteractionPlan.model_validate(payload).interactions,
        )
        return result.value


# --- Screen generation ---------------------------------------------------------------------

ScreenValidator = Callable[[dict[str, Any]], Sequence[ValidationIssue]]


@dataclass(frozen=True, slots=True)
class ScreenTask:
    """Everything needed to design one screen."""

    blueprint: ApplicationBlueprint
    brief: ScreenBrief
    plan: ScreenPlan
    direction_text: str
    effects: Sequence[str]
    entities: Sequence[Entity]
    assets: Sequence[Asset]
    interactions: Sequence[InteractionBrief]
    context: ScreenContext
    # Checks the built screen in the context of the whole application.
    validate: ScreenValidator
    current_screen: Mapping[str, Any] | None = None
    instruction: str | None = None
    review: str | None = None
    reserved_ids: frozenset[str] = field(default_factory=frozenset)


@dataclass(frozen=True, slots=True)
class GeneratedScreen:
    screen: dict[str, Any]
    provider: str
    model: str
    repair_attempts: int


class ScreenGenerator:
    """Designs one screen as a component tree and returns it only once it validates."""

    def __init__(
        self,
        runner: StageRunner,
        *,
        registry: ComponentRegistry,
        patterns: PatternRegistry,
        design: DesignRegistry,
        actions: Sequence[ActionGuideEntry],
        options: GenerationOptions,
        sample_rows: int = 3,
    ) -> None:
        self._runner = runner
        self._registry = registry
        self._patterns = patterns
        self._design = design
        self._actions = actions
        self._options = options
        self._sample_rows = sample_rows

    def components_for(self, brief: ScreenBrief, plan: ScreenPlan) -> list[ComponentDefinition]:
        """The slice of the component catalogue this screen can need."""
        wanted: list[ComponentType] = list(_BASE_COMPONENTS)
        planned = self._patterns.components([section.pattern for section in plan.sections])
        wanted += planned
        if brief.type not in _MARKETING:
            wanted += _APP_COMPONENTS
        if _T.FORM in planned or brief.type in (ScreenType.FORM, ScreenType.SETTINGS):
            wanted += _FORM_COMPONENTS
        return [self._registry.get(t.value) for t in dict.fromkeys(wanted)]

    async def generate(self, task: ScreenTask) -> GeneratedScreen:
        messages = build_screen_messages(
            blueprint=task.blueprint,
            brief=task.brief,
            plan=task.plan,
            direction_text=task.direction_text,
            effects=task.effects,
            entities=task.entities,
            assets=task.assets,
            interactions=task.interactions,
            components=self.components_for(task.brief, task.plan),
            actions=self._actions,
            icons=self._design.icons(),
            sample_rows=self._sample_rows,
            current_screen=task.current_screen,
            instruction=task.instruction,
            review=task.review,
        )

        def parse(payload: object) -> dict[str, Any]:
            children = payload.get("children") if isinstance(payload, dict) else None
            if not isinstance(children, list) or not children:
                raise reject("children", 'Output must be {"children": [...]} with components.')
            taken = {"page", *task.context.routes, *task.reserved_ids}
            screen = build_screen(task.brief, task.plan, children, task.context, taken)
            if not screen["children"]:
                raise reject("children", "No usable component was produced.")
            issues = task.validate(screen)
            if issues:
                raise StageRejectedError(issues)
            return screen

        try:
            result = await self._runner.run(
                SCREEN_GENERATOR_PROMPT, messages, parse, options=self._options
            )
        except UIGenerationException:
            logger.warning("screen_generation_failed", extra={"screen": task.brief.id})
            raise
        return GeneratedScreen(result.value, result.provider, result.model, result.repair_attempts)
