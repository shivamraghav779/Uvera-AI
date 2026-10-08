"""The application generation pipeline.

    idea
      -> understand           ApplicationPlanner      blueprint
      -> design               DesignDirector          theme, style, imagery
      -> plan data            DataPlanner             entities with records
      -> plan screens         ScreenPlanner           composition per screen
      -> plan interactions    InteractionPlanner      what people can do
      -> plan + fetch assets  AssetPlanner, engine    stored images
      -> generate screens     ScreenGenerator         validated component trees
      -> assemble
      -> evaluate / refine    DesignQualityEvaluator  bounded passes
      -> validate             UISchemaValidator       the whole document
      -> a complete application document

The pipeline sequences stages and passes typed results between them. It holds
no prompts and no validation rules. Failures are contained where the product
allows it: a missing image becomes an internal placeholder, a screen that cannot
be generated becomes a clearly marked stand-in that can be retried, and only a
failure of the application as a whole fails the run.
"""

import asyncio
import re
import uuid
from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from app.ai.orchestration.application.stages import (
    ApplicationPlanner,
    AssetPlanner,
    DataPlanner,
    DesignDirector,
    GeneratedScreen,
    InteractionPlanner,
    ScreenGenerator,
    ScreenPlanner,
    ScreenTask,
)
from app.ai.prompts.application import SCREEN_GENERATOR_PROMPT, render_direction
from app.core.exceptions import (
    AppException,
    LLMException,
    LLMProvidersExhaustedException,
    UIGenerationException,
)
from app.core.logging import get_logger
from app.domains.assets.service import AssetEngine
from app.domains.data_sources.schemas import DatasetDescriptor
from app.domains.generation.assembly import (
    ResolvedDesign,
    ScreenContext,
    attach_record_images,
    build_application,
    build_interactions,
    build_navigation,
    ensure_unique_ids,
    palette_of,
    placeholder_screen,
    plan_assets,
    resolve_design,
    stub_screen,
)
from app.domains.generation.blueprint import (
    ApplicationBlueprint,
    GenerationScope,
    InteractionBrief,
    ScreenBrief,
    ScreenPlan,
)
from app.domains.generation.quality import (
    DesignQualityEvaluator,
    QualityReport,
    refinement_briefs,
)
from app.domains.generation.schemas import JobStage
from app.domains.generative_ui.contracts import (
    ApplicationBuildInput,
    ApplicationBuildOutput,
    QualityFinding,
)
from app.domains.generative_ui.design_registry import DesignRegistry
from app.domains.generative_ui.document import (
    ApplicationSpec,
    Asset,
    DesignConfig,
    Entity,
    Navigation,
    Theme,
    UIDocument,
)
from app.domains.generative_ui.planner import ConversationTurn
from app.domains.generative_ui.schemas import ScreenType
from app.domains.generative_ui.validator import (
    UISchemaValidator,
    ValidationContext,
    ValidationIssue,
)

logger = get_logger(__name__)

_MARKETING = frozenset({ScreenType.LANDING, ScreenType.CONTENT, ScreenType.PRICING})
_LLM_FAILURES = (LLMException, LLMProvidersExhaustedException)
_PAGE_SCREENS = "page.components."

# stage, percent complete, what is happening
ProgressCallback = Callable[[JobStage, int, str | None], Awaitable[None]]


async def _silent(_stage: JobStage, _percent: int, _detail: str | None) -> None:
    return None


@dataclass(frozen=True, slots=True)
class PipelineSettings:
    max_assets: int = 10
    screen_concurrency: int = 2
    refinement_passes: int = 1
    max_refined_screens: int = 3
    # Below this score a refinement pass is worth its cost.
    refinement_threshold: int = 85


_PRODUCT_IDEA = re.compile(
    r"\b(app|apps|application|platform|saas|website|site|web ?shop|marketplace|portal|crm|"
    r"startup|landing page)\b",
    re.IGNORECASE,
)
_OWN_DATA = re.compile(
    r"\b(my|our|existing|uploaded|available|this|the)\s+(data|dataset|datasets|csv|records)\b",
    re.IGNORECASE,
)


def datasets_for(
    user_request: str, datasets: Sequence[DatasetDescriptor]
) -> Sequence[DatasetDescriptor]:
    """The existing datasets an idea is about.

    A request for one view ("a sales dashboard") is about the data that is
    there, so it sees all of it. A product idea ("a recruitment SaaS", "an
    architecture studio website") gets its own data model; data that merely
    happens to exist in the account must not shape it. It sees a dataset only
    when the idea names that data's subject, or says to use the user's data.
    """
    if not _PRODUCT_IDEA.search(user_request) or _OWN_DATA.search(user_request):
        return datasets

    def named(dataset: DatasetDescriptor) -> bool:
        subject = re.escape(dataset.name.split("_")[0])
        return re.search(rf"\b{subject}(s|es)?\b", user_request, re.IGNORECASE) is not None

    return [dataset for dataset in datasets if named(dataset)]


@dataclass(frozen=True, slots=True)
class ApplicationRequest:
    user_request: str
    workspace_id: uuid.UUID
    history: Sequence[ConversationTurn] = ()
    datasets: Sequence[DatasetDescriptor] = ()
    framework: str = "shadcn"
    # Look preferences set by the user outside the request text; they win over the director.
    style: str | None = None
    palette: str | None = None
    progress: ProgressCallback = _silent


@dataclass(frozen=True, slots=True)
class ApplicationResult:
    document: UIDocument
    blueprint: ApplicationBlueprint
    quality: QualityReport
    failed_screens: tuple[str, ...]
    provider: str | None
    model: str | None
    repair_attempts: int
    refinement_passes: int


@dataclass(slots=True)
class ApplicationContext:
    """The parts of an application that screens are generated against.

    Built once during generation, or rebuilt from a stored document when an
    edit needs to generate a screen for an existing application.
    """

    blueprint: ApplicationBlueprint
    theme: Theme
    design: DesignConfig
    navigation: Navigation
    entities: list[Entity]
    assets: list[Asset]
    interactions: list[InteractionBrief]
    direction_text: str
    effects: tuple[str, ...]
    datasets: Mapping[str, DatasetDescriptor] = field(default_factory=dict)

    def screen_context(self) -> ScreenContext:
        routes = {screen.id: screen.route for screen in self.blueprint.screens}
        return ScreenContext(
            routes=routes,
            home_route=routes.get(self.blueprint.home, "/"),
            asset_ids=frozenset(asset.id for asset in self.assets),
            entity_names=frozenset(entity.name for entity in self.entities),
        )

    def application(self, resolved: ResolvedDesign | None = None) -> dict[str, Any]:
        """The application section as JSON (interactions are added at assembly)."""
        payload: dict[str, Any] = {
            "name": self.blueprint.name,
            "category": self.blueprint.category,
            "description": self.blueprint.description,
            "navigation": self.navigation.model_dump(mode="json", exclude_none=True),
            "entities": [e.model_dump(mode="json", exclude_none=True) for e in self.entities],
            "assets": [a.model_dump(mode="json", exclude_none=True) for a in self.assets],
        }
        if resolved is not None:
            payload["design_direction"] = resolved.direction.model_dump(
                mode="json", exclude_none=True
            )
        return payload


class ScreenWorkbench:
    """Generates single screens against an ``ApplicationContext``.

    Used for every screen of a new application and, later, for redesigning or
    adding one screen of an existing application.
    """

    def __init__(self, generator: ScreenGenerator, validator: UISchemaValidator) -> None:
        self._generator = generator
        self._validator = validator

    async def generate(
        self,
        context: ApplicationContext,
        brief: ScreenBrief,
        plan: ScreenPlan,
        *,
        current_screen: Mapping[str, Any] | None = None,
        instruction: str | None = None,
        review: str | None = None,
        reserved_ids: frozenset[str] = frozenset(),
    ) -> GeneratedScreen:
        marketing = brief.type in _MARKETING
        referenced = {s.entity for s in plan.sections if s.entity} | (
            {brief.entity} if brief.entity else set()
        )
        entities = [
            entity
            for entity in context.entities
            if entity.name in referenced or (not marketing and len(context.entities) <= 6)
        ]
        task = ScreenTask(
            blueprint=context.blueprint,
            brief=brief,
            plan=plan,
            direction_text=context.direction_text,
            effects=context.effects if marketing else (),
            entities=entities,
            assets=[a for a in context.assets if a.screen_id in (brief.id, None)],
            interactions=[i for i in context.interactions if i.screen_id == brief.id],
            context=context.screen_context(),
            validate=lambda screen: self.screen_issues(context, brief, screen),
            current_screen=current_screen,
            instruction=instruction,
            review=review,
            reserved_ids=reserved_ids,
        )
        return await self._generator.generate(task)

    def screen_issues(
        self, context: ApplicationContext, brief: ScreenBrief, screen: Mapping[str, Any]
    ) -> list[ValidationIssue]:
        """Validate one screen inside the application, the others standing in as stubs."""
        screens = [
            dict(screen) if other.id == brief.id else stub_screen(other)
            for other in context.blueprint.screens
        ]
        index = next(i for i, other in enumerate(context.blueprint.screens) if other.id == brief.id)
        document = {
            "page": {"type": "page", "title": context.blueprint.name, "components": screens},
            "theme": context.theme.model_dump(mode="json", exclude_none=True),
            "design": context.design.model_dump(mode="json"),
            "application": context.application(),
        }
        report = self._validator.inspect_document(
            document, ValidationContext(datasets=context.datasets)
        )
        prefix = f"{_PAGE_SCREENS}{index}"
        return [
            ValidationIssue(issue.stage, issue.path[len(prefix) :].lstrip("."), issue.message)
            for issue in report.issues
            if issue.path.startswith(prefix)
        ]


class ApplicationGenerator:
    def __init__(
        self,
        *,
        planner: ApplicationPlanner,
        director: DesignDirector,
        data_planner: DataPlanner,
        screen_planner: ScreenPlanner,
        asset_planner: AssetPlanner,
        interaction_planner: InteractionPlanner,
        workbench: ScreenWorkbench,
        assets: AssetEngine,
        evaluator: DesignQualityEvaluator,
        validator: UISchemaValidator,
        design: DesignRegistry,
        settings: PipelineSettings,
    ) -> None:
        self._planner = planner
        self._director = director
        self._data_planner = data_planner
        self._screen_planner = screen_planner
        self._asset_planner = asset_planner
        self._interaction_planner = interaction_planner
        self._workbench = workbench
        self._assets = assets
        self._evaluator = evaluator
        self._validator = validator
        self._design = design
        self._settings = settings

    async def understand(self, request: ApplicationRequest) -> ApplicationBlueprint:
        """Stage 1 on its own: callers use the scope to choose the path to take."""
        await request.progress(JobStage.UNDERSTANDING, 3, "Understanding the product")
        return await self._planner.plan(request.user_request, request.history, request.datasets)

    async def generate(
        self, request: ApplicationRequest, blueprint: ApplicationBlueprint
    ) -> ApplicationResult:
        if blueprint.scope is not GenerationScope.APPLICATION:
            raise ValueError("generate() needs an application blueprint.")
        progress = request.progress
        count = len(blueprint.screens)
        await progress(
            JobStage.PLANNING,
            10,
            f"Planning {count} screen{'' if count == 1 else 's'} and the data",
        )
        # Sample data does not depend on the design, so it is written alongside it.
        data_task = asyncio.create_task(self._data_planner.plan(blueprint))
        try:
            await progress(JobStage.DESIGNING, 16, "Setting the design direction")
            plan = await self._director.direct(request.user_request, blueprint)
            resolved = resolve_design(
                plan,
                self._design,
                framework=request.framework,
                forced_style=request.style,
                forced_palette=request.palette,
            )
            style = self._design.design_system(resolved.design.design_system)
            direction_text = render_direction(resolved.direction, resolved.theme, style)
            navigation_style = plan.navigation_style.value if plan.navigation_style else None
            await progress(
                JobStage.DESIGNING, 24, f"Composing screens in {resolved.direction.summary}"
            )
            plans = await self._screen_planner.plan(blueprint, direction_text)
            interactions = await self._interaction_planner.plan(blueprint, plans)
            entities = await data_task
        except BaseException:
            data_task.cancel()
            raise

        await progress(JobStage.GENERATING_ASSETS, 36, "Preparing images")
        assets = await self._prepare_assets(request, blueprint, resolved, plans, entities)

        context = ApplicationContext(
            blueprint=blueprint,
            theme=resolved.theme,
            design=resolved.design,
            navigation=build_navigation(blueprint, navigation_style),
            entities=entities,
            assets=assets,
            interactions=interactions,
            direction_text=direction_text,
            effects=tuple(effect.value for effect in resolved.direction.effects),
            datasets={dataset.name: dataset for dataset in request.datasets},
        )
        screens, failed, meta = await self._generate_screens(context, plans, progress)

        await progress(JobStage.ASSEMBLING, 86, "Assembling the application")
        document = self._validated(context, resolved, screens, failed)
        quality = self._evaluator.evaluate(document)
        passes = 0
        while (
            passes < self._settings.refinement_passes
            and quality.score < self._settings.refinement_threshold
            and quality.screens_to_refine
        ):
            passes += 1
            await progress(JobStage.ASSEMBLING, 90, "Reviewing the design and refining screens")
            refined = await self._refine(context, plans, screens, quality, failed)
            if not refined:
                break
            document = self._validated(context, resolved, screens, failed)
            quality = self._evaluator.evaluate(document)

        await progress(JobStage.VALIDATING, 96, "Checking the application")
        logger.info(
            "application_generated",
            extra={
                "screens": len(screens),
                "failed_screens": len(failed),
                "assets": len(assets),
                "entities": len(entities),
                "quality_score": quality.score,
                "refinement_passes": passes,
            },
        )
        return ApplicationResult(
            document=document,
            blueprint=blueprint,
            quality=quality,
            failed_screens=tuple(failed),
            provider=meta.provider,
            model=meta.model,
            repair_attempts=meta.repair_attempts,
            refinement_passes=passes,
        )

    # --- Assets ---------------------------------------------------------------------

    async def _prepare_assets(
        self,
        request: ApplicationRequest,
        blueprint: ApplicationBlueprint,
        resolved: ResolvedDesign,
        plans: Mapping[str, ScreenPlan],
        entities: Sequence[Entity],
    ) -> list[Asset]:
        """Plan and fetch images. Images are optional: any failure yields fewer, not none."""
        try:
            briefs = await self._asset_planner.plan(
                blueprint, resolved.direction, plans, entities, limit=self._settings.max_assets
            )
            planned, by_id = plan_assets(briefs, blueprint, self._settings.max_assets)
            if not planned:
                return []
            assets = await self._assets.create_many(
                request.workspace_id, planned, palette_of(resolved.theme)
            )
        except (AppException, *_LLM_FAILURES) as error:
            logger.warning("asset_stage_skipped", extra={"error_type": type(error).__name__})
            return []
        attach_record_images(entities, assets, by_id)
        return assets

    # --- Screens --------------------------------------------------------------------

    async def _generate_screens(
        self,
        context: ApplicationContext,
        plans: Mapping[str, ScreenPlan],
        progress: ProgressCallback,
    ) -> tuple[dict[str, dict[str, Any]], list[str], "_Meta"]:
        briefs = context.blueprint.screens
        limit = asyncio.Semaphore(self._settings.screen_concurrency)
        screens: dict[str, dict[str, Any]] = {}
        failed: list[str] = []
        meta = _Meta()
        done = 0

        async def one(brief: ScreenBrief) -> None:
            nonlocal done
            async with limit:
                try:
                    generated = await self._workbench.generate(context, brief, plans[brief.id])
                except (UIGenerationException, *_LLM_FAILURES) as error:
                    logger.warning(
                        "screen_failed",
                        extra={"screen": brief.id, "error_type": type(error).__name__},
                    )
                    failed.append(brief.id)
                    screens[brief.id] = placeholder_screen(
                        brief, "It could not be generated this time."
                    )
                else:
                    screens[brief.id] = generated.screen
                    meta.record(generated)
            done += 1
            percent = 40 + round(44 * done / len(briefs))
            await progress(
                JobStage.GENERATING_SCREENS,
                percent,
                f"Designed {done} of {len(briefs)} screens (latest: {brief.name})",
            )

        await progress(JobStage.GENERATING_SCREENS, 40, f"Designing {len(briefs)} screens")
        await asyncio.gather(*(one(brief) for brief in briefs))
        if len(failed) == len(briefs):
            raise UIGenerationException("None of the application's screens could be generated.")
        ordered = {brief.id: screens[brief.id] for brief in briefs}
        return ordered, failed, meta

    async def _refine(
        self,
        context: ApplicationContext,
        plans: Mapping[str, ScreenPlan],
        screens: dict[str, dict[str, Any]],
        quality: QualityReport,
        failed: Sequence[str],
    ) -> bool:
        """Regenerate the worst-reviewed screens with the review as their brief."""
        briefs = [
            brief
            for brief in refinement_briefs(quality, self._settings.max_refined_screens)
            if brief.screen_id not in failed
        ]
        changed = False
        for refinement in briefs:
            screen_brief = context.blueprint.screen(refinement.screen_id)
            if screen_brief is None:
                continue
            try:
                generated = await self._workbench.generate(
                    context,
                    screen_brief,
                    plans[refinement.screen_id],
                    current_screen=screens[refinement.screen_id],
                    review=refinement.as_text(),
                )
            except (UIGenerationException, *_LLM_FAILURES):
                continue  # the first draft of this screen stands
            screens[refinement.screen_id] = generated.screen
            changed = True
        return changed

    # --- Assembly and validation ------------------------------------------------------

    def _document(
        self,
        context: ApplicationContext,
        resolved: ResolvedDesign,
        screens: Mapping[str, dict[str, Any]],
    ) -> dict[str, Any]:
        ordered = [screens[brief.id] for brief in context.blueprint.screens]
        ensure_unique_ids(ordered)
        application: ApplicationSpec = build_application(
            context.blueprint,
            navigation=context.navigation,
            entities=context.entities,
            interactions=build_interactions(context.interactions, context.blueprint),
            assets=context.assets,
            direction=resolved.direction,
        )
        return {
            "page": {"type": "page", "title": context.blueprint.name, "components": ordered},
            "theme": resolved.theme.model_dump(mode="json", exclude_none=True),
            "design": resolved.design.model_dump(mode="json"),
            "application": application.model_dump(mode="json", exclude_none=True),
        }

    def _validated(
        self,
        context: ApplicationContext,
        resolved: ResolvedDesign,
        screens: dict[str, dict[str, Any]],
        failed: list[str],
    ) -> UIDocument:
        """The final document. A screen that breaks it is replaced by its stand-in once."""
        validation = ValidationContext(datasets=context.datasets)
        report = self._validator.inspect_document(
            self._document(context, resolved, screens), validation
        )
        if report.document is not None and report.is_valid:
            return report.document
        briefs = context.blueprint.screens
        broken = {
            briefs[int(issue.path[len(_PAGE_SCREENS) :].split(".")[0])].id
            for issue in report.issues
            if issue.path.startswith(_PAGE_SCREENS)
        }
        if not broken or len(broken) == len(briefs):
            raise UIGenerationException(details=[issue.to_detail() for issue in report.issues])
        for screen_id in broken:
            brief = context.blueprint.screen(screen_id)
            assert brief is not None
            screens[screen_id] = placeholder_screen(brief, "It did not pass the final check.")
            if screen_id not in failed:
                failed.append(screen_id)
        return self._validator.validate_document(
            self._document(context, resolved, screens), validation
        )


@dataclass(slots=True)
class _Meta:
    """Which model answered, and how much repairing the screens needed."""

    provider: str | None = None
    model: str | None = None
    repair_attempts: int = 0

    def record(self, generated: GeneratedScreen) -> None:
        self.provider, self.model = generated.provider, generated.model
        self.repair_attempts += generated.repair_attempts


class ApplicationBuildAgent:
    """Implements the domain's ``ApplicationBuilder`` port with the pipeline."""

    def __init__(self, generator: ApplicationGenerator) -> None:
        self._generator = generator

    async def build(self, request: ApplicationBuildInput) -> ApplicationBuildOutput:
        report = request.progress

        async def progress(stage: JobStage, percent: int, detail: str | None) -> None:
            if report is not None:
                await report(stage.value, percent, detail)

        pipeline_request = ApplicationRequest(
            user_request=request.user_request,
            workspace_id=request.workspace_id,
            history=request.history,
            datasets=datasets_for(request.user_request, request.datasets),
            framework=request.framework,
            style=request.design_system,
            palette=request.theme_preset,
            progress=progress,
        )
        blueprint = await self._generator.understand(pipeline_request)
        if blueprint.scope is not GenerationScope.APPLICATION:
            return ApplicationBuildOutput(
                document=None,
                quality_score=None,
                findings=(),
                failed_screen_ids=(),
                provider=None,
                model=None,
                prompt_version=SCREEN_GENERATOR_PROMPT.version,
                repair_attempts=0,
            )
        result = await self._generator.generate(pipeline_request, blueprint)
        return ApplicationBuildOutput(
            document=result.document,
            quality_score=result.quality.score,
            findings=[
                QualityFinding(
                    category=issue.category.value,
                    severity=issue.severity.value,
                    message=issue.message,
                    recommendation=issue.recommendation,
                    screen_id=issue.screen_id,
                )
                for issue in result.quality.issues
            ],
            failed_screen_ids=result.failed_screens,
            provider=result.provider,
            model=result.model,
            prompt_version=SCREEN_GENERATOR_PROMPT.version,
            repair_attempts=result.repair_attempts,
        )
