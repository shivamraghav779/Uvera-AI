"""Dependency wiring: the composition root of the application.

Routes ask for services; this module decides which concrete repositories,
providers and registries those services receive. Tests replace individual
providers through ``app.dependency_overrides``.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import timedelta
from typing import Annotated

import httpx
from fastapi import Depends, FastAPI, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.llm.base import GenerationOptions, LLMProvider
from app.ai.llm.factory import LLMFactory
from app.ai.orchestration.agent import GenerativeUIAgent
from app.ai.orchestration.application.editing import ApplicationEditor
from app.ai.orchestration.application.pipeline import (
    ApplicationBuildAgent,
    ApplicationGenerator,
    PipelineSettings,
    ScreenWorkbench,
)
from app.ai.orchestration.application.runner import StageRunner
from app.ai.orchestration.application.stages import (
    ApplicationPlanner,
    AssetPlanner,
    DataPlanner,
    DesignDirector,
    InteractionPlanner,
    ScreenGenerator,
    ScreenPlanner,
)
from app.ai.orchestration.executor import UIGenerationExecutor
from app.ai.orchestration.mutation import UIMutationExecutor
from app.ai.orchestration.planner import RequestPlanner
from app.ai.prompts.actions import ActionGuideEntry
from app.ai.search.base import SearchProvider
from app.ai.search.google import GoogleSearchProvider
from app.core.config import ImageGenerationProvider, ImageSearchProvider, Settings
from app.core.exceptions import AuthenticationException, DataSourceException, InvalidTokenException
from app.core.logging import get_logger
from app.core.rate_limit import SlidingWindowRateLimiter
from app.core.security import (
    Authenticator,
    BearerTokenAuthenticator,
    Principal,
    TokenService,
    bearer_token,
)
from app.database.connection import Database
from app.domains.actions.handlers import RecordWriter, build_default_action_registry
from app.domains.actions.registry import ActionRegistry
from app.domains.actions.repository import UIActionRepository
from app.domains.actions.service import ActionService
from app.domains.assets.providers import (
    ImageProvider,
    InternalImageProvider,
    OpenverseImageProvider,
    PollinationsImageProvider,
    UnsplashImageProvider,
)
from app.domains.assets.repository import AssetRepository
from app.domains.assets.service import AssetEngine, AssetService
from app.domains.conversation.repository import ConversationRepository
from app.domains.conversation.service import ConversationService
from app.domains.data_sources.providers.base import DataProvider, EmptyDataProvider
from app.domains.data_sources.providers.composite import CompositeDataProvider
from app.domains.data_sources.providers.factory import DataProviderFactory, EnvSecretResolver
from app.domains.data_sources.providers.mock import MockSalesDataProvider
from app.domains.data_sources.providers.rest import allow_any_host, reject_private_hosts
from app.domains.data_sources.repository import DataSourceRepository
from app.domains.data_sources.service import MAX_SOURCES_PER_USER, DataSourceService
from app.domains.generation.quality import DesignQualityEvaluator
from app.domains.generation.repository import GenerationJobRepository
from app.domains.generation.service import GenerationJobService, JobRunner
from app.domains.generative_ui.design_registry import DesignRegistry, build_default_design_registry
from app.domains.generative_ui.intent import KeywordIntentClassifier
from app.domains.generative_ui.mutator import DocumentMutator
from app.domains.generative_ui.pattern_registry import (
    PatternRegistry,
    build_default_pattern_registry,
)
from app.domains.generative_ui.planner import UIPlanner
from app.domains.generative_ui.registry import (
    ComponentCategory,
    ComponentRegistry,
    build_default_registry,
)
from app.domains.generative_ui.repository import UIVersionRepository
from app.domains.generative_ui.service import (
    ApplicationQueryService,
    GenerativeUIService,
    UISchemaInspectionService,
)
from app.domains.generative_ui.validator import UISchemaValidator
from app.domains.generative_ui.versioning import VersionService
from app.domains.records.repository import WorkspaceRecordRepository
from app.domains.references.repository import ReferenceRepository
from app.domains.references.service import ReferenceLibrary
from app.domains.users.repository import UserRepository
from app.domains.users.service import AuthService
from app.domains.workspaces.repository import WorkspaceRepository
from app.domains.workspaces.service import WorkspaceService

logger = get_logger(__name__)

# --- Infrastructure -----------------------------------------------------------


def get_app_settings(request: Request) -> Settings:
    settings: Settings = request.app.state.settings
    return settings


def get_database(request: Request) -> Database:
    database: Database = request.app.state.database
    return database


def get_http_client(request: Request) -> httpx.AsyncClient:
    client: httpx.AsyncClient = request.app.state.http_client
    return client


async def get_db_session(
    database: Annotated[Database, Depends(get_database)],
) -> AsyncIterator[AsyncSession]:
    """One session per request. Services commit; anything uncommitted is rolled back."""
    async with database.session() as session:
        yield session


SettingsDep = Annotated[Settings, Depends(get_app_settings)]
DbSession = Annotated[AsyncSession, Depends(get_db_session)]
HttpClient = Annotated[httpx.AsyncClient, Depends(get_http_client)]

# --- Identity -----------------------------------------------------------------


def get_token_service(settings: SettingsDep) -> TokenService:
    return TokenService(
        settings.token_signing_key, timedelta(minutes=settings.access_token_ttl_minutes)
    )


TokenServiceDep = Annotated[TokenService, Depends(get_token_service)]


def get_authenticator(settings: SettingsDep, tokens: TokenServiceDep) -> Authenticator:
    return BearerTokenAuthenticator(tokens, required=settings.auth_required)


async def get_current_principal(
    request: Request,
    authenticator: Annotated[Authenticator, Depends(get_authenticator)],
    db: DbSession,
) -> Principal:
    """Who the request acts as. Raises 401 unless the caller is allowed in."""
    principal = await authenticator.authenticate(request.headers)
    # A valid signature is not enough: the account must still exist.
    if principal.user_id is not None and await UserRepository(db).get(principal.user_id) is None:
        raise InvalidTokenException()
    return principal


CurrentPrincipal = Annotated[Principal, Depends(get_current_principal)]


def get_auth_service(db: DbSession, tokens: TokenServiceDep) -> AuthService:
    return AuthService(UserRepository(db), tokens, db)


# --- Rate limiting ------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class RateLimiters:
    """The application's request budgets. Created once per process (see ``create_app``)."""

    general: SlidingWindowRateLimiter
    ai: SlidingWindowRateLimiter
    auth: SlidingWindowRateLimiter

    @classmethod
    def from_settings(cls, settings: Settings) -> "RateLimiters":
        return cls(
            general=SlidingWindowRateLimiter(settings.rate_limit_per_minute),
            ai=SlidingWindowRateLimiter(settings.ai_rate_limit_per_minute),
            auth=SlidingWindowRateLimiter(settings.auth_rate_limit_per_minute),
        )


def _client_address(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _caller_key(request: Request, tokens: TokenService) -> str:
    """Budget key: the signed-in user if the token verifies, otherwise the client address."""
    token = bearer_token(request.headers)
    if token is not None:
        try:
            return f"user:{tokens.verify(token)}"
        except AuthenticationException:
            pass
    return f"ip:{_client_address(request)}"


async def enforce_rate_limit(request: Request, tokens: TokenServiceDep) -> None:
    limiters: RateLimiters = request.app.state.rate_limiters
    await limiters.general.check(_caller_key(request, tokens))


async def enforce_ai_rate_limit(request: Request, tokens: TokenServiceDep) -> None:
    """Model calls cost money and time; they get a smaller budget of their own."""
    limiters: RateLimiters = request.app.state.rate_limiters
    await limiters.ai.check(_caller_key(request, tokens))


async def enforce_auth_rate_limit(request: Request) -> None:
    """Sign-in and registration are limited per client address to slow down guessing."""
    limiters: RateLimiters = request.app.state.rate_limiters
    await limiters.auth.check(f"ip:{_client_address(request)}")


# --- Providers and registries -------------------------------------------------


def get_llm_provider(settings: SettingsDep, http_client: HttpClient) -> LLMProvider:
    return LLMFactory(settings, http_client).create_default()


def get_search_provider(settings: SettingsDep, http_client: HttpClient) -> SearchProvider | None:
    if settings.google_api_key is None or settings.google_search_engine_id is None:
        return None
    return GoogleSearchProvider(
        api_key=settings.google_api_key,
        engine_id=settings.google_search_engine_id,
        client=http_client,
    )


def get_data_provider_factory(
    settings: SettingsDep, http_client: HttpClient
) -> DataProviderFactory:
    return DataProviderFactory(
        http_client=http_client,
        secrets=EnvSecretResolver(),
        timeout_seconds=settings.data_source_timeout_seconds,
        allow_private_hosts=settings.data_source_allow_private_hosts,
    )


DataProviderFactoryDep = Annotated[DataProviderFactory, Depends(get_data_provider_factory)]


async def build_data_provider(
    settings: Settings, factory: DataProviderFactory, db: AsyncSession, principal: Principal
) -> DataProvider:
    """Everything the caller can read: their registered sources, plus demo data if enabled."""
    providers: list[DataProvider] = [MockSalesDataProvider()] if settings.mock_data_enabled else []
    sources = await DataSourceRepository(db).list_for_user(
        principal.user_id, limit=MAX_SOURCES_PER_USER
    )
    for source in sources:
        try:
            providers.append(factory.build(source))
        except DataSourceException:
            # E.g. its secret is no longer configured. The other sources still work.
            logger.warning("data_source_unusable", extra={"type": source.type})
    return CompositeDataProvider(providers)


async def get_data_provider(
    settings: SettingsDep,
    factory: DataProviderFactoryDep,
    db: DbSession,
    principal: CurrentPrincipal,
) -> DataProvider:
    return await build_data_provider(settings, factory, db, principal)


def get_component_registry() -> ComponentRegistry:
    return build_default_registry()


def get_design_registry() -> DesignRegistry:
    return build_default_design_registry()


def get_pattern_registry() -> PatternRegistry:
    return build_default_pattern_registry()


LLMProviderDep = Annotated[LLMProvider, Depends(get_llm_provider)]
SearchProviderDep = Annotated[SearchProvider | None, Depends(get_search_provider)]
DataProviderDep = Annotated[DataProvider, Depends(get_data_provider)]
ComponentRegistryDep = Annotated[ComponentRegistry, Depends(get_component_registry)]
DesignRegistryDep = Annotated[DesignRegistry, Depends(get_design_registry)]
PatternRegistryDep = Annotated[PatternRegistry, Depends(get_pattern_registry)]


def get_action_registry(
    data_provider: DataProviderDep, search_provider: SearchProviderDep
) -> ActionRegistry:
    return build_default_action_registry(data_provider, search_provider)


ActionRegistryDep = Annotated[ActionRegistry, Depends(get_action_registry)]


def get_ui_validator(
    registry: ComponentRegistryDep, actions: ActionRegistryDep, design: DesignRegistryDep
) -> UISchemaValidator:
    return UISchemaValidator(registry, actions.allowed_types(), design)


UIValidatorDep = Annotated[UISchemaValidator, Depends(get_ui_validator)]


def get_document_mutator(validator: UIValidatorDep, design: DesignRegistryDep) -> DocumentMutator:
    return DocumentMutator(validator, design)


DocumentMutatorDep = Annotated[DocumentMutator, Depends(get_document_mutator)]

# --- Services -----------------------------------------------------------------


def get_workspace_service(db: DbSession) -> WorkspaceService:
    return WorkspaceService(WorkspaceRepository(db), UIVersionRepository(db), db)


WorkspaceServiceDep = Annotated[WorkspaceService, Depends(get_workspace_service)]


def get_conversation_service(db: DbSession, workspaces: WorkspaceServiceDep) -> ConversationService:
    return ConversationService(ConversationRepository(db), workspaces, db)


def get_data_source_service(
    db: DbSession, factory: DataProviderFactoryDep, data_provider: DataProviderDep
) -> DataSourceService:
    return DataSourceService(DataSourceRepository(db), factory, data_provider, db)


def get_action_service(
    db: DbSession,
    data_provider: DataProviderDep,
    search_provider: SearchProviderDep,
    workspaces: WorkspaceServiceDep,
) -> ActionService:
    def build_registry(provider: DataProvider, records: RecordWriter | None) -> ActionRegistry:
        return build_default_action_registry(provider, search_provider, records)

    return ActionService(
        build_registry=build_registry,
        data_provider=data_provider,
        repository=UIActionRepository(db),
        workspaces=workspaces,
        versions=UIVersionRepository(db),
        records=WorkspaceRecordRepository(db),
        uow=db,
    )


def get_version_service(
    db: DbSession,
    workspaces: WorkspaceServiceDep,
    validator: UIValidatorDep,
    mutator: DocumentMutatorDep,
    data_provider: DataProviderDep,
) -> VersionService:
    return VersionService(
        workspaces=workspaces,
        versions=UIVersionRepository(db),
        validator=validator,
        mutator=mutator,
        data_provider=data_provider,
        uow=db,
        records=WorkspaceRecordRepository(db),
    )


def get_application_query_service(
    db: DbSession, workspaces: WorkspaceServiceDep, design: DesignRegistryDep
) -> ApplicationQueryService:
    return ApplicationQueryService(
        workspaces=workspaces, versions=UIVersionRepository(db), design=design
    )


def get_ui_inspection_service(
    validator: UIValidatorDep,
    registry: ComponentRegistryDep,
    actions: ActionRegistryDep,
    design: DesignRegistryDep,
    data_provider: DataProviderDep,
    patterns: PatternRegistryDep,
) -> UISchemaInspectionService:
    """Validation against the caller's own datasets. Requires a signed-in caller."""
    return UISchemaInspectionService(
        validator=validator,
        registry=registry,
        allowed_actions=actions.allowed_types(),
        design=design,
        data_provider=data_provider,
        patterns=patterns,
    )


def get_ui_catalogue_service(
    registry: ComponentRegistryDep, design: DesignRegistryDep, patterns: PatternRegistryDep
) -> UISchemaInspectionService:
    """The public vocabulary (components, themes, frameworks). Touches no user data."""
    actions = build_default_action_registry(EmptyDataProvider(), None).allowed_types()
    return UISchemaInspectionService(
        validator=UISchemaValidator(registry, actions, design),
        registry=registry,
        allowed_actions=actions,
        design=design,
        data_provider=EmptyDataProvider(),
        patterns=patterns,
    )


_SINGLE_VIEW_CATEGORIES = frozenset(
    {
        ComponentCategory.LAYOUT,
        ComponentCategory.DATA_DISPLAY,
        ComponentCategory.INPUT,
        ComponentCategory.FEEDBACK,
    }
)


def _action_guide(actions: ActionRegistry) -> list[ActionGuideEntry]:
    return [
        ActionGuideEntry(
            type=handler.action_type.value,
            description=handler.description,
            payload_fields=tuple(handler.payload_model.model_fields),
        )
        for handler in actions.handlers()
    ]


def _generation_options(settings: Settings) -> GenerationOptions:
    return GenerationOptions(
        temperature=settings.llm_temperature, max_tokens=settings.llm_max_output_tokens
    )


def get_ui_generator(
    settings: SettingsDep,
    llm: LLMProviderDep,
    validator: UIValidatorDep,
    registry: ComponentRegistryDep,
    design: DesignRegistryDep,
    actions: ActionRegistryDep,
    data_provider: DataProviderDep,
) -> GenerativeUIAgent:
    executor = UIGenerationExecutor(
        llm=llm,
        validator=validator,
        # A single view is built from primitives; patterns and screens belong to applications.
        registry=registry.restricted_to(
            d.type for d in registry.definitions() if d.category in _SINGLE_VIEW_CATEGORIES
        ),
        design=design,
        actions=_action_guide(actions),
        options=_generation_options(settings),
        max_repair_attempts=settings.llm_max_repair_attempts,
        log_prompts=settings.log_prompts,
    )
    return GenerativeUIAgent(
        planner=RequestPlanner(llm, UIPlanner(), KeywordIntentClassifier()),
        executor=executor,
        data_provider=data_provider,
        registry=registry,
    )


# --- Assets ---------------------------------------------------------------------


def _image_providers(
    settings: Settings, http_client: httpx.AsyncClient
) -> tuple[ImageProvider | None, ImageProvider | None]:
    """The configured generation and search providers (either may be absent)."""
    timeout = settings.asset_timeout_seconds
    check_host = (
        allow_any_host if settings.data_source_allow_private_hosts else reject_private_hosts
    )
    generator: ImageProvider | None = None
    if settings.image_generation_provider is ImageGenerationProvider.POLLINATIONS:
        generator = PollinationsImageProvider(
            http_client, timeout_seconds=timeout, check_host=check_host
        )
    choice, key = settings.image_search_provider, settings.unsplash_access_key
    searcher: ImageProvider | None = None
    if choice is ImageSearchProvider.UNSPLASH or (choice is ImageSearchProvider.AUTO and key):
        if key is not None:
            searcher = UnsplashImageProvider(
                http_client, key, timeout_seconds=timeout, check_host=check_host
            )
    elif choice in (ImageSearchProvider.OPENVERSE, ImageSearchProvider.AUTO):
        searcher = OpenverseImageProvider(
            http_client, timeout_seconds=timeout, check_host=check_host
        )
    return generator, searcher


def get_asset_engine(settings: SettingsDep, http_client: HttpClient, db: DbSession) -> AssetEngine:
    generator, searcher = _image_providers(settings, http_client)
    return AssetEngine(
        repository=AssetRepository(db),
        internal=InternalImageProvider(),
        generator=generator,
        searcher=searcher,
        uow=db,
    )


AssetEngineDep = Annotated[AssetEngine, Depends(get_asset_engine)]


def get_asset_service(
    db: DbSession, engine: AssetEngineDep, workspaces: WorkspaceServiceDep
) -> AssetService:
    return AssetService(engine=engine, repository=AssetRepository(db), workspaces=workspaces)


def get_public_asset_service(db: DbSession, engine: AssetEngineDep) -> AssetService:
    """Serves asset bytes. Needs no caller identity: assets are addressed by unguessable id."""
    return AssetService(
        engine=engine,
        repository=AssetRepository(db),
        workspaces=WorkspaceService(WorkspaceRepository(db), UIVersionRepository(db), db),
    )


# --- Reference components --------------------------------------------------------


def get_reference_library(db: DbSession) -> ReferenceLibrary:
    return ReferenceLibrary(ReferenceRepository(db), db)


# --- Application generation -----------------------------------------------------


@dataclass(frozen=True, slots=True)
class ApplicationStack:
    """The application builder and the level-aware editor, sharing their stages."""

    builder: ApplicationBuildAgent
    editor: ApplicationEditor


def build_application_stack(
    *,
    settings: Settings,
    llm: LLMProvider,
    validator: UISchemaValidator,
    mutator: DocumentMutator,
    registry: ComponentRegistry,
    design: DesignRegistry,
    patterns: PatternRegistry,
    actions: ActionRegistry,
    assets: AssetEngine,
) -> ApplicationStack:
    """Wire the generation pipeline: one runner, the specialised stages, the pipeline."""
    # Long answers need longer than a conversational call is allowed.
    timeout = max(settings.llm_timeout_seconds, settings.app_generation_timeout_seconds)
    plan_options = GenerationOptions(
        temperature=settings.llm_temperature,
        max_tokens=settings.app_generation_max_output_tokens,
        timeout_seconds=timeout,
    )
    # Screens benefit from a little more variety than plans do.
    screen_options = GenerationOptions(
        temperature=min(settings.llm_temperature + 0.3, 1.0),
        max_tokens=settings.app_generation_max_output_tokens,
        timeout_seconds=timeout,
    )
    runner = StageRunner(
        llm,
        options=plan_options,
        max_repair_attempts=settings.llm_max_repair_attempts,
        rate_limit_retries=settings.llm_rate_limit_retries,
        rate_limit_wait_seconds=settings.llm_rate_limit_wait_seconds,
    )
    router = StageRunner(
        llm,
        options=GenerationOptions(temperature=0.0, max_tokens=300),
        max_repair_attempts=0,
        rate_limit_retries=settings.llm_rate_limit_retries,
        rate_limit_wait_seconds=settings.llm_rate_limit_wait_seconds,
    )
    guide = _action_guide(actions)
    planner = ApplicationPlanner(
        runner.limited_to(3500), design, max_screens=settings.app_max_screens
    )
    director = DesignDirector(runner.limited_to(1500), design)
    data_planner = DataPlanner(runner, records_per_entity=settings.app_records_per_entity)
    screen_planner = ScreenPlanner(runner.limited_to(4500), patterns)
    workbench = ScreenWorkbench(
        ScreenGenerator(
            runner,
            registry=registry,
            patterns=patterns,
            design=design,
            actions=guide,
            options=screen_options,
        ),
        validator,
    )
    generator = ApplicationGenerator(
        planner=planner,
        director=director,
        data_planner=data_planner,
        screen_planner=screen_planner,
        asset_planner=AssetPlanner(runner.limited_to(3000)),
        interaction_planner=InteractionPlanner(runner.limited_to(2500)),
        workbench=workbench,
        assets=assets,
        evaluator=DesignQualityEvaluator(design),
        validator=validator,
        design=design,
        settings=PipelineSettings(
            max_assets=settings.app_max_assets,
            screen_concurrency=settings.app_screen_concurrency,
            refinement_passes=settings.app_refinement_passes,
        ),
    )
    direct = UIMutationExecutor(
        llm=llm,
        mutator=mutator,
        registry=registry,
        design=design,
        actions=guide,
        options=_generation_options(settings),
        max_repair_attempts=settings.llm_max_repair_attempts,
    )
    editor = ApplicationEditor(
        direct=direct,
        router=router,
        planner=planner,
        director=director,
        data_planner=data_planner,
        screen_planner=screen_planner,
        workbench=workbench,
        mutator=mutator,
        design=design,
    )
    return ApplicationStack(builder=ApplicationBuildAgent(generator), editor=editor)


def get_application_stack(
    settings: SettingsDep,
    llm: LLMProviderDep,
    validator: UIValidatorDep,
    mutator: DocumentMutatorDep,
    registry: ComponentRegistryDep,
    design: DesignRegistryDep,
    patterns: PatternRegistryDep,
    actions: ActionRegistryDep,
    assets: AssetEngineDep,
) -> ApplicationStack:
    return build_application_stack(
        settings=settings,
        llm=llm,
        validator=validator,
        mutator=mutator,
        registry=registry,
        design=design,
        patterns=patterns,
        actions=actions,
        assets=assets,
    )


def get_generative_ui_service(
    db: DbSession,
    workspaces: WorkspaceServiceDep,
    generator: Annotated[GenerativeUIAgent, Depends(get_ui_generator)],
    stack: Annotated[ApplicationStack, Depends(get_application_stack)],
    mutator: DocumentMutatorDep,
    data_provider: DataProviderDep,
    design: DesignRegistryDep,
) -> GenerativeUIService:
    return GenerativeUIService(
        generator=generator,
        mutation_planner=stack.editor,
        builder=stack.builder,
        workspaces=workspaces,
        conversations=ConversationRepository(db),
        versions=UIVersionRepository(db),
        mutator=mutator,
        data_provider=data_provider,
        design=design,
        uow=db,
        records=WorkspaceRecordRepository(db),
    )


@asynccontextmanager
async def generative_ui_service_scope(
    app: FastAPI, principal: Principal
) -> AsyncIterator[GenerativeUIService]:
    """A ``GenerativeUIService`` with its own database session.

    Streamed responses and background jobs outlive the request that started
    them, so they build the service here and keep the session open for exactly
    as long as the work runs. Wiring is the same as ``get_generative_ui_service``;
    overrides registered on the app (tests) are honoured for the LLM provider
    and the HTTP client.
    """
    settings: Settings = app.state.settings
    client_override = app.dependency_overrides.get(get_http_client)
    http_client: httpx.AsyncClient = client_override() if client_override else app.state.http_client
    database: Database = app.state.database
    llm_override = app.dependency_overrides.get(get_llm_provider)
    llm = llm_override() if llm_override else get_llm_provider(settings, http_client)
    registry, design = get_component_registry(), get_design_registry()
    patterns = get_pattern_registry()
    async with database.session() as db:
        factory = get_data_provider_factory(settings, http_client)
        data_provider = await build_data_provider(settings, factory, db, principal)
        actions = get_action_registry(data_provider, get_search_provider(settings, http_client))
        validator = get_ui_validator(registry, actions, design)
        mutator = get_document_mutator(validator, design)
        stack = build_application_stack(
            settings=settings,
            llm=llm,
            validator=validator,
            mutator=mutator,
            registry=registry,
            design=design,
            patterns=patterns,
            actions=actions,
            assets=get_asset_engine(settings, http_client, db),
        )
        yield get_generative_ui_service(
            db,
            get_workspace_service(db),
            get_ui_generator(settings, llm, validator, registry, design, actions, data_provider),
            stack,
            mutator,
            data_provider,
            design,
        )


# --- Generation jobs ------------------------------------------------------------


def get_job_runner(request: Request) -> JobRunner:
    runner: JobRunner = request.app.state.job_runner
    return runner


def get_generation_job_service(
    db: DbSession,
    workspaces: WorkspaceServiceDep,
    runner: Annotated[JobRunner, Depends(get_job_runner)],
) -> GenerationJobService:
    return GenerationJobService(
        repository=GenerationJobRepository(db), workspaces=workspaces, runner=runner, uow=db
    )


# --- Shared request parameters --------------------------------------------------


class Pagination:
    def __init__(
        self,
        limit: Annotated[int, Query(ge=1, le=200, description="Maximum items to return.")] = 50,
        offset: Annotated[int, Query(ge=0, description="Items to skip.")] = 0,
    ) -> None:
        self.limit = limit
        self.offset = offset


PaginationDep = Annotated[Pagination, Depends()]
