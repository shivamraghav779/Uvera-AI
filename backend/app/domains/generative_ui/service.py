"""Application services for proposing UI changes and describing the UI vocabulary.

Nothing in this module persists a UI. Proposals are returned to the client;
approved ones come back through ``VersionService``.
"""

import random
import uuid
from collections.abc import Collection

from app.core.exceptions import ResourceNotFoundException, ValidationException
from app.core.logging import get_logger
from app.core.security import Principal
from app.database.unit_of_work import UnitOfWork
from app.domains.actions.schemas import ActionType
from app.domains.conversation.repository import ConversationRepository
from app.domains.conversation.schemas import MessageRole
from app.domains.data_sources.providers.base import DataProvider
from app.domains.generative_ui.application import build_graph, unreachable_screens
from app.domains.generative_ui.contracts import (
    ApplicationBuilder,
    ApplicationBuildInput,
    ApplicationBuildOutput,
    ApplicationRead,
    ApplicationSummary,
    BuildProgress,
    CapabilitiesResponse,
    ChangeRead,
    ComponentCatalogResponse,
    ComponentRead,
    CompositionRead,
    DesignSummary,
    DesignSystemRead,
    EffectRead,
    EntitySummary,
    FrameworkCatalogResponse,
    FrameworkRead,
    GenerateUIRequest,
    GraphEdgeRead,
    LayoutCapabilities,
    MutateUIRequest,
    MutationPlanKind,
    PatternCatalogResponse,
    PatternRead,
    ProgressReporter,
    ProgressStage,
    ProposalKind,
    ProposalMetadata,
    ProposalRead,
    ProposalStep,
    QualityIssueRead,
    QualityRead,
    ScreenSummary,
    ThemeCatalogResponse,
    ThemePresetRead,
    UIGenerationInput,
    UIGenerator,
    UIMutationInput,
    UIMutationOutput,
    UIMutationPlanner,
    ValidateUIResponse,
    ValidationIssueRead,
    ValidationResult,
    VersionInfo,
    report,
)
from app.domains.generative_ui.design_registry import (
    DEFAULT_DESIGN_SYSTEM,
    DEFAULT_FRAMEWORK,
    DesignRegistry,
)
from app.domains.generative_ui.diff import diff_documents
from app.domains.generative_ui.document import (
    DesignConfig,
    FontFamily,
    NavigationStyle,
    Theme,
    ThemeColors,
    UIDocument,
    dump_document,
)
from app.domains.generative_ui.models import UIVersion
from app.domains.generative_ui.mutation_engine import find_node
from app.domains.generative_ui.mutator import DocumentMutator, MutationOutcome
from app.domains.generative_ui.operations import OperationType, VersionOperationType
from app.domains.generative_ui.pattern_registry import PatternRegistry
from app.domains.generative_ui.planner import ConversationTurn
from app.domains.generative_ui.registry import ComponentRegistry
from app.domains.generative_ui.renderer import RecordChangeSource, UIDataResolver
from app.domains.generative_ui.repository import UIVersionRepository
from app.domains.generative_ui.schemas import (
    GRID_COLUMNS,
    UI_SCHEMA_VERSION,
    ButtonVariant,
    ChartType,
    ColorRole,
    ComponentType,
    Effect,
    HeightPreset,
    ScreenType,
    SurfaceVariant,
)
from app.domains.generative_ui.tree import screens, walk
from app.domains.generative_ui.validator import UISchemaValidator, ValidationIssue
from app.domains.generative_ui.versioning import (
    ensure_current,
    to_change_reads,
    to_document,
    to_summary,
    validation_context,
)
from app.domains.workspaces.models import Workspace
from app.domains.workspaces.service import WorkspaceService

logger = get_logger(__name__)

HISTORY_TURNS = 10
VERSIONS_SHOWN_TO_MODEL = 40
_HISTORY_ROLES = frozenset({MessageRole.USER, MessageRole.ASSISTANT})
_VALID = ValidationResult(valid=True, issues=[])


def _issue_reads(issues: Collection[ValidationIssue]) -> list[ValidationIssueRead]:
    return [
        ValidationIssueRead(stage=issue.stage, path=issue.path, message=issue.message)
        for issue in issues
    ]


def summarise_application(
    document: UIDocument, design: DesignRegistry, failed_screen_ids: Collection[str] = ()
) -> ApplicationSummary | None:
    """What an application document consists of, in numbers and names."""
    application = document.application
    if application is None:
        return None
    graph = build_graph(document)
    style = design.design_system(document.design.design_system)
    direction = application.design_direction
    nodes = [node.component for screen in screens(document.page) for node in walk(screen)]
    return ApplicationSummary(
        name=application.name,
        category=application.category,
        description=application.description,
        navigation_style=application.navigation.style.value,
        design=DesignSummary(
            style=document.design.design_system,
            style_name=style.name if style else document.design.design_system,
            summary=direction.summary if direction else None,
            mode=document.theme.mode.value,
            palette=document.theme.preset,
            mood=list(direction.mood) if direction else [],
        ),
        screens=[
            ScreenSummary(
                id=node.id,
                title=node.title,
                route=node.route,
                screen_type=node.screen_type,
                in_navigation=node.in_navigation,
                failed=node.id in failed_screen_ids,
            )
            for node in graph.nodes
        ],
        entities=[
            EntitySummary(name=e.name, label=e.label, record_count=len(e.records))
            for e in application.entities
        ],
        interactions=[interaction.label for interaction in application.interactions],
        component_count=len(nodes) - len(graph.nodes),
        pattern_count=len({component.type for component in nodes}) - 1,
        asset_count=len(application.assets),
    )


class ApplicationQueryService:
    """Read-only view of a workspace's current application: summary and screen graph."""

    def __init__(
        self, *, workspaces: WorkspaceService, versions: UIVersionRepository, design: DesignRegistry
    ) -> None:
        self._workspaces = workspaces
        self._versions = versions
        self._design = design

    async def read(self, principal: Principal, workspace_id: uuid.UUID) -> ApplicationRead:
        workspace = await self._workspaces.get(principal, workspace_id)
        version = (
            await self._versions.get(workspace.id, workspace.current_version_id)
            if workspace.current_version_id
            else None
        )
        document = to_document(version) if version else None
        summary = summarise_application(document, self._design) if document else None
        if document is None or summary is None:
            raise ResourceNotFoundException("This workspace does not hold an application.")
        graph = build_graph(document)
        return ApplicationRead(
            version_id=version.id,  # type: ignore[union-attr]
            version_number=version.version_number,  # type: ignore[union-attr]
            summary=summary,
            edges=[
                GraphEdgeRead(source=e.source, target=e.target, kind=e.kind.value, label=e.label)
                for e in graph.edges
            ],
            unreachable_screen_ids=unreachable_screens(document),
        )


class GenerativeUIService:
    """Turns instructions into proposals: a new UI, a set of operations, or a version request."""

    def __init__(
        self,
        *,
        generator: UIGenerator,
        mutation_planner: UIMutationPlanner,
        workspaces: WorkspaceService,
        conversations: ConversationRepository,
        versions: UIVersionRepository,
        mutator: DocumentMutator,
        data_provider: DataProvider,
        design: DesignRegistry,
        uow: UnitOfWork,
        rng: random.Random | None = None,
        builder: ApplicationBuilder | None = None,
        records: RecordChangeSource | None = None,
    ) -> None:
        self._rng = rng
        self._builder = builder
        self._generator = generator
        self._mutation_planner = mutation_planner
        self._workspaces = workspaces
        self._conversations = conversations
        self._versions = versions
        self._mutator = mutator
        self._data_provider = data_provider
        self._data = UIDataResolver(data_provider, records)
        self._design = design
        self._uow = uow

    # --- Build (application or single view) -----------------------------------------

    async def build(
        self,
        principal: Principal,
        request: GenerateUIRequest,
        progress: BuildProgress | None = None,
    ) -> ProposalRead:
        """Turn an idea into a proposal: a complete application, or a single view when
        that is what was asked for. Nothing is saved."""
        if self._builder is None:
            return await self.generate(principal, request)
        workspace = await self._workspaces.get(principal, request.workspace_id)
        current = await self._current(workspace)
        current_document = to_document(current) if current else None
        self._check_look(request)
        history = await self._load_history(workspace.id)
        await self._record(workspace.id, MessageRole.USER, request.instruction)
        output = await self._builder.build(
            ApplicationBuildInput(
                user_request=request.instruction,
                workspace_id=workspace.id,
                history=history,
                datasets=await self._data_provider.list_datasets(),
                framework=request.framework or DEFAULT_FRAMEWORK,
                design_system=request.design_system,
                theme_preset=request.theme_preset,
                progress=progress,
            )
        )
        if output.document is None:
            # The request is for one view of existing data: the single-view pipeline.
            if progress is not None:
                await progress("generating_screens", 40, "Designing the view")
            return await self.generate(principal, request, record_request=False)

        document = output.document
        proposal = ProposalRead(
            proposal_id=uuid.uuid4(),
            kind=ProposalKind.GENERATE,
            workspace_id=workspace.id,
            base_version_id=workspace.current_version_id,
            message=self._application_message(document, output),
            steps=[],
            document=document,
            data=await self._data.resolve(document, workspace.id),
            changes=self._changes(current_document, document),
            affected_component_ids=[],
            target_version=None,
            validation=_VALID,
            metadata=ProposalMetadata(
                provider=output.provider,
                model=output.model,
                prompt_version=output.prompt_version,
                repair_attempts=output.repair_attempts,
                schema_version=UI_SCHEMA_VERSION,
            ),
            application=self.summarise(document, output.failed_screen_ids),
            quality=QualityRead(
                score=output.quality_score or 0,
                issues=[
                    QualityIssueRead(
                        category=f.category,
                        severity=f.severity,
                        message=f.message,
                        recommendation=f.recommendation,
                        screen_id=f.screen_id,
                    )
                    for f in output.findings
                ],
            ),
        )
        await self._record_proposal(proposal)
        return proposal

    @staticmethod
    def _application_message(document: UIDocument, output: ApplicationBuildOutput) -> str:
        application = document.application
        assert application is not None
        count = len(document.page.components)
        message = (
            f"I've designed {application.name}: a {count}-screen "
            f"{application.category.lower()} application."
        )
        if output.failed_screen_ids:
            failed = len(output.failed_screen_ids)
            message += (
                f" {failed} screen{'' if failed == 1 else 's'} could not be generated and "
                "can be regenerated after you apply it."
            )
        return message

    def summarise(
        self, document: UIDocument, failed_screen_ids: Collection[str] = ()
    ) -> ApplicationSummary | None:
        return summarise_application(document, self._design, failed_screen_ids)

    def _check_look(self, request: GenerateUIRequest) -> None:
        if request.framework and not self._design.is_framework_available(request.framework):
            raise ValidationException(f"Framework '{request.framework}' is not available.")
        if request.design_system and self._design.design_system(request.design_system) is None:
            raise ValidationException(f"Design system '{request.design_system}' is not registered.")
        if request.theme_preset and self._design.theme(request.theme_preset) is None:
            raise ValidationException(f"Theme preset '{request.theme_preset}' is not registered.")

    # --- Generate ---------------------------------------------------------------

    async def generate(
        self,
        principal: Principal,
        request: GenerateUIRequest,
        progress: ProgressReporter | None = None,
        *,
        record_request: bool = True,
    ) -> ProposalRead:
        workspace = await self._workspaces.get(principal, request.workspace_id)
        current = await self._current(workspace)
        current_document = to_document(current) if current else None
        theme, design = self._starting_look(request, current_document)

        history = await self._load_history(workspace.id)
        if record_request:
            await self._record(workspace.id, MessageRole.USER, request.instruction)
        output = await self._generator.generate(
            UIGenerationInput(
                user_request=request.instruction,
                history=history,
                base_theme=theme,
                design=design,
                progress=progress,
            )
        )
        await report(progress, ProgressStage.FINISHING)

        document = output.document
        component_count = sum(1 for _ in walk(document.page)) - 1
        proposal = ProposalRead(
            proposal_id=uuid.uuid4(),
            kind=ProposalKind.GENERATE,
            workspace_id=workspace.id,
            base_version_id=workspace.current_version_id,
            message=self._draft_message(document, current_document, component_count),
            steps=[],
            document=document,
            data=await self._data.resolve(document, workspace.id),
            changes=self._changes(current_document, document),
            affected_component_ids=[],
            target_version=None,
            validation=_VALID,
            metadata=ProposalMetadata(
                provider=output.provider,
                model=output.model,
                prompt_version=output.prompt_version,
                repair_attempts=output.repair_attempts,
                intent=output.intent,
                schema_version=UI_SCHEMA_VERSION,
            ),
        )
        await self._record_proposal(proposal)
        return proposal

    def _draft_message(
        self, document: UIDocument, current: UIDocument | None, component_count: int
    ) -> str:
        noun = "component" if component_count == 1 else "components"
        message = f"I drafted “{document.page.title}” with {component_count} {noun}"
        preset = self._design.theme(document.theme.preset) if document.theme.preset else None
        if current is None and preset is not None:
            # Says which palette a first draft got, since it may have been picked for the user.
            return f"{message} in the {preset.name} palette. Ask for another look any time."
        return f"{message}."

    def _starting_look(
        self, request: GenerateUIRequest, current: UIDocument | None
    ) -> tuple[Theme, DesignConfig]:
        """Theme and design a generated page starts from: preferences, else what exists."""
        framework = request.framework or (
            current.design.framework if current else DEFAULT_FRAMEWORK
        )
        system = request.design_system or (
            current.design.design_system if current else DEFAULT_DESIGN_SYSTEM
        )
        if not self._design.is_framework_available(framework):
            raise ValidationException(f"Framework '{framework}' is not available.")
        if self._design.design_system(system) is None:
            raise ValidationException(f"Design system '{system}' is not registered.")
        if request.theme_preset and self._design.theme(request.theme_preset) is None:
            raise ValidationException(f"Theme preset '{request.theme_preset}' is not registered.")

        design = DesignConfig(framework=framework, design_system=system)
        if current is not None and not (request.theme_preset or request.design_system):
            return current.theme, design
        preset = request.theme_preset or (current.theme.preset if current else None)
        if preset is not None and self._design.theme(preset) is not None:
            return self._design.build_theme(preset, system), design
        if current is not None:
            return current.theme, design
        # A new UI with no stated look gets a palette picked for it.
        return self._design.build_theme(self._design.pick_theme(self._rng).id, system), design

    # --- Mutate -----------------------------------------------------------------

    async def mutate(
        self,
        principal: Principal,
        request: MutateUIRequest,
        progress: ProgressReporter | None = None,
    ) -> ProposalRead:
        workspace = await self._workspaces.get(principal, request.workspace_id)
        current = await self._current(workspace)
        ensure_current(workspace, request.base_version_id, current)
        if current is None:
            raise ValidationException("This workspace has no UI yet. Generate one first.")
        document = to_document(current)
        context = await validation_context(self._data_provider)

        if request.operations is not None:
            outcome = self._mutator.inspect(document, request.operations, context)
            return await self._operations_proposal(workspace, document, outcome, "Changes checked.")

        assert request.instruction is not None
        self._ensure_selectable(document, request.selected_component_id)
        self._ensure_screen(document, request.active_screen_id)
        history = await self._load_history(workspace.id)
        versions = await self._versions.list_for_workspace(
            workspace.id, limit=VERSIONS_SHOWN_TO_MODEL
        )
        await self._record(workspace.id, MessageRole.USER, request.instruction)
        plan = await self._mutation_planner.plan(
            UIMutationInput(
                instruction=request.instruction,
                document=document,
                selected_component_id=request.selected_component_id,
                versions=[
                    VersionInfo(
                        version_number=version.version_number,
                        description=version.description,
                        source=version.source,
                        created_at=version.created_at,
                        is_current=version.id == current.id,
                    )
                    for version in versions
                ],
                history=history,
                datasets=list(context.datasets.values()),
                validation_context=context,
                progress=progress,
                active_screen_id=request.active_screen_id,
                workspace_id=workspace.id,
            )
        )
        await report(progress, ProgressStage.FINISHING)
        proposal = await self._plan_proposal(workspace, document, plan)
        await self._record_proposal(proposal)
        return proposal

    @staticmethod
    def _ensure_selectable(document: UIDocument, component_id: str | None) -> None:
        if component_id is None:
            return
        if find_node(dump_document(document)["page"], component_id) is None:
            raise ValidationException(f"Selected component '{component_id}' does not exist.")

    @staticmethod
    def _ensure_screen(document: UIDocument, screen_id: str | None) -> None:
        if screen_id is not None and screen_id not in {s.id for s in screens(document.page)}:
            raise ValidationException(f"Screen '{screen_id}' does not exist.")

    async def regenerate_screen(
        self,
        principal: Principal,
        workspace_id: uuid.UUID,
        screen_id: str,
        instruction: str,
        progress: ProgressReporter | None = None,
    ) -> ProposalRead:
        """Propose a fresh design of one screen of the current application."""
        redesign = getattr(self._mutation_planner, "redesign_screen", None)
        workspace = await self._workspaces.get(principal, workspace_id)
        current = await self._current(workspace)
        if current is None or redesign is None:
            raise ValidationException(
                "This workspace has no application to regenerate a screen of."
            )
        document = to_document(current)
        if document.application is None:
            raise ValidationException("Only applications have screens to regenerate.")
        self._ensure_screen(document, screen_id)
        context = await validation_context(self._data_provider)
        await self._record(workspace.id, MessageRole.USER, instruction)
        plan = await redesign(
            UIMutationInput(
                instruction=instruction,
                document=document,
                selected_component_id=None,
                versions=[],
                history=await self._load_history(workspace.id),
                datasets=list(context.datasets.values()),
                validation_context=context,
                progress=progress,
                active_screen_id=screen_id,
                workspace_id=workspace.id,
            ),
            screen_id,
            instruction,
        )
        proposal = await self._plan_proposal(workspace, document, plan)
        await self._record_proposal(proposal)
        return proposal

    async def _plan_proposal(
        self, workspace: Workspace, current: UIDocument, plan: UIMutationOutput
    ) -> ProposalRead:
        metadata = ProposalMetadata(
            provider=plan.provider,
            model=plan.model,
            prompt_version=plan.prompt_version,
            repair_attempts=plan.repair_attempts,
            schema_version=UI_SCHEMA_VERSION,
        )
        if plan.kind is MutationPlanKind.OPERATIONS and plan.outcome is not None:
            proposal = await self._operations_proposal(
                workspace, current, plan.outcome, plan.message
            )
            return proposal.model_copy(update={"metadata": metadata})

        target: UIVersion | None = None
        if plan.version_number is not None:
            target = await self._versions.get_by_number(workspace.id, plan.version_number)
        target_document = to_document(target) if target else None
        if target_document is None:
            kind, changes = ProposalKind.MESSAGE, []
        elif plan.kind is MutationPlanKind.COMPARE:
            # "Compare with version N": what changed from N to now.
            kind, changes = ProposalKind.COMPARE, self._changes(target_document, current)
        else:
            kind, changes = ProposalKind.RESTORE, self._changes(current, target_document)
        return ProposalRead(
            proposal_id=uuid.uuid4(),
            kind=kind,
            workspace_id=workspace.id,
            base_version_id=workspace.current_version_id,
            message=plan.message,
            steps=[],
            document=target_document,
            data=await self._data.resolve(target_document, workspace.id) if target_document else {},
            changes=changes,
            affected_component_ids=[],
            target_version=to_summary(target, workspace.current_version_id) if target else None,
            validation=_VALID,
            metadata=metadata,
        )

    async def _operations_proposal(
        self, workspace: Workspace, current: UIDocument, outcome: MutationOutcome, message: str
    ) -> ProposalRead:
        document = outcome.document
        affected = [cid for step in outcome.steps for cid in step.affected_component_ids]
        return ProposalRead(
            proposal_id=uuid.uuid4(),
            kind=ProposalKind.MUTATE,
            workspace_id=workspace.id,
            base_version_id=workspace.current_version_id,
            message=message,
            steps=[
                ProposalStep(
                    operation=step.operation,
                    summary=step.summary,
                    affected_component_ids=list(step.affected_component_ids),
                )
                for step in outcome.steps
            ],
            document=document,
            data=await self._data.resolve(document, workspace.id) if document else {},
            changes=self._changes(current, document) if document else [],
            affected_component_ids=list(dict.fromkeys(affected)),
            target_version=None,
            validation=ValidationResult(
                valid=outcome.is_valid, issues=_issue_reads(outcome.issues)
            ),
            metadata=ProposalMetadata(schema_version=UI_SCHEMA_VERSION),
            application=self.summarise(document) if document else None,
        )

    # --- Shared -----------------------------------------------------------------

    @staticmethod
    def _changes(old: UIDocument | None, new: UIDocument | None) -> list[ChangeRead]:
        if old is None or new is None:
            return []
        return to_change_reads(diff_documents(dump_document(old), dump_document(new)))

    async def _current(self, workspace: Workspace) -> UIVersion | None:
        if workspace.current_version_id is None:
            return None
        return await self._versions.get(workspace.id, workspace.current_version_id)

    async def _load_history(self, workspace_id: uuid.UUID) -> list[ConversationTurn]:
        messages = await self._conversations.recent(workspace_id, limit=HISTORY_TURNS)
        return [
            ConversationTurn(role=message.role.value, content=message.content)
            for message in messages
            if message.role in _HISTORY_ROLES
        ]

    async def _record(self, workspace_id: uuid.UUID, role: MessageRole, content: str) -> None:
        # Committed immediately: the request is kept even if the model call fails.
        await self._conversations.add(workspace_id=workspace_id, role=role, content=content)
        await self._uow.commit()

    async def _record_proposal(self, proposal: ProposalRead) -> None:
        await self._conversations.add(
            workspace_id=proposal.workspace_id,
            role=MessageRole.ASSISTANT,
            content=proposal.message,
            details={"proposal_id": str(proposal.proposal_id), "kind": proposal.kind.value},
        )
        await self._uow.commit()
        logger.info(
            "ui_proposal_created",
            extra={
                "kind": proposal.kind.value,
                "provider": proposal.metadata.provider,
                "model": proposal.metadata.model,
                "steps": len(proposal.steps),
                "repair_attempts": proposal.metadata.repair_attempts,
            },
        )


class UISchemaInspectionService:
    """Read-only views of the UI vocabulary: validation and the registries."""

    def __init__(
        self,
        *,
        validator: UISchemaValidator,
        registry: ComponentRegistry,
        allowed_actions: Collection[ActionType],
        design: DesignRegistry,
        data_provider: DataProvider,
        patterns: PatternRegistry,
    ) -> None:
        self._patterns = patterns
        self._validator = validator
        self._registry = registry
        self._allowed_actions = sorted(action.value for action in allowed_actions)
        self._design = design
        self._data_provider = data_provider

    async def validate(self, document: object) -> ValidateUIResponse:
        context = await validation_context(self._data_provider)
        report = self._validator.inspect_document(document, context)
        return ValidateUIResponse(
            valid=report.is_valid, issues=_issue_reads(report.issues), document=report.document
        )

    def catalog(self) -> ComponentCatalogResponse:
        return ComponentCatalogResponse(
            schema_version=UI_SCHEMA_VERSION,
            components=[
                ComponentRead(
                    type=definition.type,
                    category=definition.category,
                    description=definition.description,
                    accepts_children=definition.accepts_children,
                    variants=list(definition.variants),
                    example=dict(definition.example),
                )
                for definition in self._registry.definitions()
            ],
            allowed_actions=self._allowed_actions,
            json_schema=UIDocument.model_json_schema(),
        )

    def frameworks(self) -> FrameworkCatalogResponse:
        return FrameworkCatalogResponse(
            default_framework=DEFAULT_FRAMEWORK,
            default_design_system=DEFAULT_DESIGN_SYSTEM,
            frameworks=[
                FrameworkRead(id=f.id, name=f.name, status=f.status, description=f.description)
                for f in self._design.frameworks()
            ],
            design_systems=[
                DesignSystemRead(
                    id=s.id,
                    name=s.name,
                    description=s.description,
                    tokens=s.tokens,
                    mood=list(s.mood),
                    suited_for=list(s.suited_for),
                    imagery=s.imagery,
                    effects=[effect.value for effect in s.effects],
                    palettes=list(s.palettes),
                    navigation=list(s.navigation),
                )
                for s in self._design.design_systems()
            ],
        )

    def themes(self) -> ThemeCatalogResponse:
        return ThemeCatalogResponse(
            default_theme=self._design.default_theme(),
            presets=[
                ThemePresetRead(id=p.id, name=p.name, description=p.description, theme=p.theme)
                for p in self._design.themes()
            ],
        )

    def patterns(self) -> PatternCatalogResponse:
        """The design knowledge library the planning stages draw on."""
        return PatternCatalogResponse(
            patterns=[
                PatternRead(
                    id=p.id,
                    component=p.component,
                    variant=p.variant,
                    category=p.category.value,
                    purpose=p.purpose,
                    screen_types=[t.value for t in p.screen_types],
                    suited_for=list(p.suited_for),
                    density=p.density.value,
                    characteristics=list(p.characteristics),
                    needs_data=p.needs_data,
                    image=p.image.value,
                    effects=[effect.value for effect in p.effects],
                    responsive=p.responsive,
                    frameworks=list(p.frameworks),
                )
                for p in self._patterns.patterns()
            ],
            compositions=[
                CompositionRead(
                    id=c.id,
                    name=c.name,
                    screen_type=c.screen_type.value,
                    suited_for=list(c.suited_for),
                    patterns=list(c.patterns),
                    note=c.note,
                )
                for c in self._patterns.compositions()
            ],
            effects=[
                EffectRead(id=e.id.value, name=e.name, description=e.description, use_for=e.use_for)
                for e in self._design.effects()
            ],
            icons=list(self._design.icons()),
        )

    def capabilities(self) -> CapabilitiesResponse:
        definitions = self._registry.definitions()
        return CapabilitiesResponse(
            schema_version=UI_SCHEMA_VERSION,
            components=[definition.type for definition in definitions],
            chart_types=[chart_type.value for chart_type in ChartType],
            layout=LayoutCapabilities(
                model="flow-grid",
                columns=GRID_COLUMNS,
                heights=[height.value for height in HeightPreset],
                containers=[d.type for d in definitions if d.accepts_children],
            ),
            interactions=[
                ComponentType.TABS,
                ComponentType.MODAL,
                ComponentType.FORM,
                ComponentType.KANBAN,
                ComponentType.COMMAND,
                ComponentType.FAQ,
            ],
            actions=self._allowed_actions,
            operations=[operation.value for operation in OperationType],
            version_operations=[operation.value for operation in VersionOperationType],
            style_tones=[tone.value for tone in ColorRole],
            theme_tokens=[*Theme.model_fields, *(f"colors.{c}" for c in ThemeColors.model_fields)],
            component_variants={d.type.value: list(d.variants) for d in definitions if d.variants},
            surface_variants=[variant.value for variant in SurfaceVariant],
            button_variants=[variant.value for variant in ButtonVariant],
            effects=[effect.value for effect in Effect],
            screen_types=[screen_type.value for screen_type in ScreenType],
            navigation_styles=[style.value for style in NavigationStyle],
            fonts=[font.value for font in FontFamily],
        )
