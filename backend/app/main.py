"""Application factory and ASGI entry point (``uvicorn app.main:app``)."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from functools import partial

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.dependencies import RateLimiters
from app.api.jobs import execute_generation_job, fail_interrupted_jobs
from app.api.router import api_router
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging, get_logger
from app.database.connection import Database
from app.domains.generation.service import InProcessJobRunner
from app.middleware.error_handler import UnhandledErrorMiddleware, register_exception_handlers
from app.middleware.logging import RequestLoggingMiddleware
from app.middleware.request_id import REQUEST_ID_HEADER, RequestIDMiddleware

logger = get_logger(__name__)

OPENAPI_TAGS = [
    {"name": "Health", "description": "Liveness and dependency status."},
    {"name": "Authentication", "description": "Accounts and access tokens."},
    {"name": "Workspaces", "description": "Persistent UIs built by conversation and editing."},
    {
        "name": "Versions",
        "description": "Immutable history of a workspace: save, restore, compare.",
    },
    {"name": "Conversations", "description": "Messages exchanged within a workspace."},
    {"name": "Generative UI", "description": "Propose, validate and describe UI documents."},
    {
        "name": "Generation",
        "description": "Background jobs that build complete applications from an idea.",
    },
    {"name": "Assets", "description": "Images generated or found for a workspace."},
    {"name": "Data Sources", "description": "Registered sources of data for generated UIs."},
    {"name": "Actions", "description": "Execution of allowlisted UI actions."},
]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Create shared resources once per process and release them on shutdown."""
    settings: Settings = app.state.settings
    app.state.database = Database(
        settings.database_url,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
    )
    app.state.http_client = httpx.AsyncClient()
    runner = InProcessJobRunner(partial(execute_generation_job, app))
    app.state.job_runner = runner
    await fail_interrupted_jobs(app.state.database)
    logger.info(
        "application_started",
        extra={
            "environment": settings.app_env.value,
            "default_llm_provider": settings.default_llm_provider.value,
        },
    )
    try:
        yield
    finally:
        await runner.shutdown()
        await app.state.http_client.aclose()
        await app.state.database.dispose()


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level, settings.log_format)

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Turns a product idea into a complete, validated application document (screens, "
            "navigation, data, design) rendered by a predefined React component registry. "
            "The model never produces executable code."
        ),
        openapi_tags=OPENAPI_TAGS,
        lifespan=lifespan,
    )
    app.state.settings = settings
    # Request budgets live for the life of the process, shared by every request.
    app.state.rate_limiters = RateLimiters.from_settings(settings)

    # Added innermost-first: the last middleware added is the first to see a request.
    app.add_middleware(UnhandledErrorMiddleware, expose_error_type=not settings.is_production)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=[REQUEST_ID_HEADER, "Retry-After"],
    )
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(RequestIDMiddleware)

    register_exception_handlers(app)
    app.include_router(api_router)
    return app


app = create_app()
