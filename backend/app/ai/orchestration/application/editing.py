"""Editing an existing application at the level the request addresses.

    application level   "make the whole app more premium", "add an analytics section"
    screen level        "redesign the dashboard"
    component level     "move this chart", "make all tables compact", "go back to version 2"

A small routing call decides the level. Whatever the level, the result is the
same thing: validated operations on the current document. A restyle becomes
theme and style operations and touches no screen; a redesign replaces exactly
one screen; adding a screen creates it and extends the navigation. Nothing is
regenerated that the request did not ask for.
"""

from collections.abc import Sequence
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.ai.orchestration.application.pipeline import ApplicationContext, ScreenWorkbench
from app.ai.orchestration.application.runner import StageRunner
from app.ai.orchestration.application.stages import (
    ApplicationPlanner,
    DataPlanner,
    DesignDirector,
    ScreenPlanner,
)
from app.ai.orchestration.mutation import UIMutationExecutor
from app.ai.prompts.application import (
    EDIT_ROUTER_PROMPT,
    SCREEN_GENERATOR_PROMPT,
    build_router_messages,
    render_direction,
)
from app.core.exceptions import UIGenerationException
from app.core.logging import get_logger
from app.domains.generation.assembly import (
    blueprint_from_document,
    build_navigation,
    resolve_design,
)
from app.domains.generation.blueprint import InteractionBrief, ScreenBrief
from app.domains.generative_ui.contracts import (
    MutationPlanKind,
    ProgressStage,
    UIMutationInput,
    UIMutationOutput,
    report,
)
from app.domains.generative_ui.design_registry import DesignRegistry
from app.domains.generative_ui.document import (
    DesignDirection,
    ImageryKind,
    UIDocument,
    dump_document,
)
from app.domains.generative_ui.mutator import DocumentMutator
from app.domains.generative_ui.operations import (
    CreateOperation,
    ReplaceOperation,
    SetDesignSystemOperation,
    SetNavigationOperation,
    SetThemeOperation,
    UpdateApplicationOperation,
    UpsertEntitiesOperation,
)
from app.domains.generative_ui.tree import screens, walk

logger = get_logger(__name__)


class EditIntent(StrEnum):
    EDIT = "edit"
    RESTYLE = "restyle"
    REDESIGN_SCREEN = "redesign_screen"
    ADD_SCREEN = "add_screen"


class EditRoute(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    intent: EditIntent = EditIntent.EDIT
    level: str = "component"
    screen_id: str | None = None


def application_outline(document: UIDocument) -> str:
    """Every screen with the ids and types of its components, a few words each."""
    application = document.application
    assert application is not None
    lines = [
        f"Application: {application.name} ({application.category})",
        f"Navigation: {application.navigation.style.value}; home {application.navigation.home}",
        f"Style: {document.design.design_system}; {document.theme.mode.value} mode",
    ]
    for screen in screens(document.page):
        parts = [
            f"{node.component.id} ({node.component.type.value})"
            for node in walk(screen)
            if node.depth == 2
        ]
        lines.append(
            f"- screen {screen.id} “{screen.title}” ({screen.screen_type.value}, "
            f"route {screen.route}): {', '.join(parts)}"
        )
    return "\n".join(lines)


def screen_of(document: UIDocument, component_id: str | None) -> str | None:
    """Id of the screen containing ``component_id`` (or being it)."""
    if component_id is None:
        return None
    for screen in screens(document.page):
        if any(node.component.id == component_id for node in walk(screen)):
            return screen.id
    return None


class ApplicationEditor:
    """Implements the domain's ``UIMutationPlanner`` port for applications and single views."""

    def __init__(
        self,
        *,
        direct: UIMutationExecutor,
        router: StageRunner,
        planner: ApplicationPlanner,
        director: DesignDirector,
        data_planner: DataPlanner,
        screen_planner: ScreenPlanner,
        workbench: ScreenWorkbench,
        mutator: DocumentMutator,
        design: DesignRegistry,
    ) -> None:
        self._direct = direct
        self._router = router
        self._planner = planner
        self._director = director
        self._data_planner = data_planner
        self._screen_planner = screen_planner
        self._workbench = workbench
        self._mutator = mutator
        self._design = design

    async def plan(self, request: UIMutationInput) -> UIMutationOutput:
        if request.document.application is None or request.selected_component_id is not None:
            # A single view, or a request about one selected component: operations directly.
            return await self._direct.plan(request)
        await report(request.progress, ProgressStage.UNDERSTANDING)
        route = await self._route(request)
        logger.info(
            "edit_routed",
            extra={"intent": route.intent.value, "level": route.level, "screen": route.screen_id},
        )
        if route.intent is EditIntent.RESTYLE:
            return await self._restyle(request)
        if route.intent is EditIntent.REDESIGN_SCREEN:
            screen_id = route.screen_id or request.active_screen_id
            if screen_id in {screen.id for screen in screens(request.document.page)}:
                return await self.redesign_screen(request, str(screen_id), request.instruction)
        if route.intent is EditIntent.ADD_SCREEN:
            return await self._add_screens(request)
        return await self._direct.plan(request)

    async def _route(self, request: UIMutationInput) -> EditRoute:
        messages = build_router_messages(
            instruction=request.instruction,
            outline=application_outline(request.document),
            active_screen_id=request.active_screen_id,
            selected_component_id=request.selected_component_id,
            history=request.history,
        )
        try:
            result = await self._router.run(EDIT_ROUTER_PROMPT, messages, EditRoute.model_validate)
        except UIGenerationException:
            # An unreadable routing answer must not block the edit: take the general path.
            return EditRoute()
        return result.value

    # --- Application level: restyle ---------------------------------------------------

    async def _restyle(self, request: UIMutationInput) -> UIMutationOutput:
        document = request.document
        application = document.application
        assert application is not None
        await report(request.progress, ProgressStage.PLANNING)
        blueprint = blueprint_from_document(document)
        plan = await self._director.direct(
            application.description,
            blueprint,
            current=application.design_direction,
            instruction=request.instruction,
        )
        resolved = resolve_design(plan, self._design, framework=document.design.framework)
        theme = resolved.theme.model_dump(mode="json", exclude_none=True)
        preset = theme.pop("preset", None)
        operations: list[BaseModel] = [
            SetDesignSystemOperation.model_validate(
                {"type": "SET_DESIGN_SYSTEM", "design_system": resolved.design.design_system}
            ),
            SetThemeOperation.model_validate(
                {"type": "SET_THEME", **({"preset": preset} if preset else {}), "tokens": theme}
            ),
            UpdateApplicationOperation.model_validate(
                {
                    "type": "UPDATE_APPLICATION",
                    "props": {
                        "design_direction": resolved.direction.model_dump(
                            mode="json", exclude_none=True
                        )
                    },
                }
            ),
        ]
        wanted = plan.navigation_style
        if wanted is not None and wanted is not application.navigation.style:
            operations.append(
                SetNavigationOperation.model_validate(
                    {"type": "SET_NAVIGATION", "style": wanted.value}
                )
            )
        style = self._design.design_system(resolved.design.design_system)
        message = (
            f"I'll restyle the whole application as {style.name if style else 'requested'}: "
            f"{resolved.direction.summary} Screens and content stay as they are."
        )
        return self._operations(request, operations, message)

    # --- Screen level: redesign ---------------------------------------------------------

    async def redesign_screen(
        self, request: UIMutationInput, screen_id: str, instruction: str | None
    ) -> UIMutationOutput:
        """Generate one screen again and replace it in place. Nothing else changes."""
        document = request.document
        context = self.context_for(document, request)
        brief = context.blueprint.screen(screen_id)
        if brief is None:
            raise UIGenerationException(f"Screen '{screen_id}' does not exist.")
        current = next(s for s in screens(document.page) if s.id == screen_id)
        await report(request.progress, ProgressStage.PLANNING)
        plans = await self._screen_planner.plan(
            context.blueprint, context.direction_text, screens=[brief], instruction=instruction
        )
        await report(request.progress, ProgressStage.GENERATING)
        generated = await self._workbench.generate(
            context,
            brief,
            plans[screen_id],
            current_screen=current.model_dump(mode="json", exclude_none=True),
            instruction=instruction,
            reserved_ids=self._other_ids(document, screen_id),
        )
        operation = ReplaceOperation.model_validate(
            {"type": "REPLACE", "target": screen_id, "component": generated.screen}
        )
        message = f"I redesigned “{brief.name}”. The other screens are untouched."
        return self._operations(request, [operation], message, generated.provider, generated.model)

    # --- Application level: add screens -------------------------------------------------

    async def _add_screens(self, request: UIMutationInput) -> UIMutationOutput:
        document = request.document
        application = document.application
        assert application is not None
        await report(request.progress, ProgressStage.PLANNING)
        base = blueprint_from_document(document)
        new_screens, new_entities = await self._planner.extend(request.instruction, base)
        blueprint = base.model_copy(
            update={
                "screens": [*base.screens, *new_screens],
                "entities": [*base.entities, *new_entities],
            }
        )
        entities = list(application.entities)
        if new_entities:
            entities += await self._data_planner.plan(blueprint, new_entities, entities)
        context = self.context_for(document, request)
        context.blueprint = blueprint
        context.entities = entities
        plans = await self._screen_planner.plan(
            blueprint, context.direction_text, screens=new_screens, instruction=request.instruction
        )
        await report(request.progress, ProgressStage.GENERATING)
        operations: list[BaseModel] = []
        if new_entities:
            added = entities[len(application.entities) :]
            operations.append(
                UpsertEntitiesOperation.model_validate(
                    {
                        "type": "UPSERT_ENTITIES",
                        "entities": [e.model_dump(mode="json", exclude_none=True) for e in added],
                    }
                )
            )
        reserved = self._other_ids(document, None)
        provider = model = None
        for brief in new_screens:
            generated = await self._workbench.generate(
                context,
                brief,
                plans[brief.id],
                instruction=request.instruction,
                reserved_ids=reserved,
            )
            provider, model = generated.provider, generated.model
            operations.append(
                CreateOperation.model_validate(
                    {"type": "CREATE", "parent_id": document.page.id, "component": generated.screen}
                )
            )
        navigation = build_navigation(blueprint, application.navigation.style.value)
        existing = application.navigation.items
        added_items = [
            item
            for item in navigation.items
            if item.screen_id in {brief.id for brief in new_screens}
        ]
        if added_items:
            operations.append(
                SetNavigationOperation.model_validate(
                    {
                        "type": "SET_NAVIGATION",
                        "items": [
                            item.model_dump(mode="json", exclude_none=True)
                            for item in [*existing, *added_items]
                        ],
                    }
                )
            )
        names = ", ".join(f"“{brief.name}”" for brief in new_screens)
        noun = "screen" if len(new_screens) == 1 else "screens"
        pronoun = "it" if len(new_screens) == 1 else "them"
        message = f"I added the {noun} {names} and linked {pronoun} in the navigation."
        return self._operations(request, operations, message, provider, model)

    # --- Shared -------------------------------------------------------------------------

    def context_for(self, document: UIDocument, request: UIMutationInput) -> ApplicationContext:
        """The generation context an existing application document implies."""
        application = document.application
        assert application is not None
        direction = application.design_direction or DesignDirection(
            style=document.design.design_system, summary="", imagery=ImageryKind.NONE
        )
        style = self._design.design_system(document.design.design_system)
        blueprint = blueprint_from_document(document)
        return ApplicationContext(
            blueprint=blueprint,
            theme=document.theme,
            design=document.design,
            navigation=application.navigation,
            entities=list(application.entities),
            assets=list(application.assets),
            interactions=[
                InteractionBrief(
                    id=i.id,
                    label=i.label,
                    type=i.type,
                    screen_id=i.screen_id,
                    entity=i.entity,
                    trigger=i.description,
                    result=i.result,
                )
                for i in application.interactions
            ],
            direction_text=render_direction(direction, document.theme, style),
            effects=tuple(effect.value for effect in direction.effects),
            datasets=dict(request.validation_context.datasets),
        )

    @staticmethod
    def _other_ids(document: UIDocument, screen_id: str | None) -> frozenset[str]:
        """Ids used outside ``screen_id``, which a regenerated screen must not reuse."""
        ids: set[str] = set()
        for screen in screens(document.page):
            if screen.id != screen_id:
                ids.update(node.component.id for node in walk(screen))
        return frozenset(ids)

    def _operations(
        self,
        request: UIMutationInput,
        operations: Sequence[BaseModel],
        message: str,
        provider: str | None = None,
        model: str | None = None,
    ) -> UIMutationOutput:
        outcome = self._mutator.inspect(request.document, operations, request.validation_context)
        if not outcome.is_valid:
            raise UIGenerationException(
                "The change does not produce a valid application.",
                details=[issue.to_detail() for issue in outcome.issues],
            )
        return UIMutationOutput(
            kind=MutationPlanKind.OPERATIONS,
            message=message,
            outcome=outcome,
            version_number=None,
            provider=provider or "",
            model=model or "",
            prompt_version=SCREEN_GENERATOR_PROMPT.version,
            repair_attempts=0,
        )


def screen_brief_for(document: UIDocument, screen_id: str) -> ScreenBrief | None:
    return blueprint_from_document(document).screen(screen_id)


def current_screen_json(document: UIDocument, screen_id: str) -> dict[str, Any] | None:
    page = dump_document(document)["page"]
    return next((s for s in page["components"] if s.get("id") == screen_id), None)
