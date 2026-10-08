"""Shared fixtures.

Integration tests need PostgreSQL. They use TEST_DATABASE_URL, whose schema is
dropped and rebuilt with the Alembic migrations once per run; they are skipped
when the server cannot be reached.
"""

import asyncio
import os
from collections.abc import AsyncIterator
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx
import pytest
from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.api.dependencies import get_llm_provider
from app.domains.actions.schemas import ActionType
from app.domains.data_sources.providers.mock import MockSalesDataProvider
from app.domains.generative_ui.design_registry import build_default_design_registry
from app.domains.generative_ui.mutator import DocumentMutator
from app.domains.generative_ui.registry import build_default_registry
from app.domains.generative_ui.validator import UISchemaValidator, ValidationContext
from app.main import create_app
from tests.support import ScriptedLLMProvider, make_settings, running_client

BACKEND_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TEST_DATABASE_URL = (
    "postgresql+asyncpg://postgres:postgres@localhost:5432/generative_ui_test"
)
MAINTENANCE_DATABASE = "postgres"
APPLICATION_TABLES = (
    "users, workspaces, data_sources, conversations, ui_versions, ui_actions, "
    "workspace_records, assets, generation_jobs, reference_components"
)


def _test_database_url() -> str:
    url = os.environ.get("TEST_DATABASE_URL", DEFAULT_TEST_DATABASE_URL)
    database = make_url(url).database or ""
    if "test" not in database:
        raise RuntimeError(
            f"Refusing to run against database '{database}': the integration tests wipe "
            "their database, so TEST_DATABASE_URL must name one containing 'test'."
        )
    return url


async def _create_database_if_missing(url: str) -> None:
    target = make_url(url)
    engine = create_async_engine(
        target.set(database=MAINTENANCE_DATABASE), isolation_level="AUTOCOMMIT", poolclass=NullPool
    )
    async with engine.connect() as connection:
        exists = await connection.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": target.database}
        )
        if not exists:
            await connection.execute(text(f'CREATE DATABASE "{target.database}"'))
    await engine.dispose()


async def _reset_schema(url: str) -> None:
    await _create_database_if_missing(url)
    engine = create_async_engine(url, poolclass=NullPool)
    async with engine.begin() as connection:
        await connection.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        await connection.execute(text("CREATE SCHEMA public"))
    await engine.dispose()


def alembic_config(url: str) -> Config:
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
    config.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
    config.attributes["configure_logging"] = False
    return config


def _prepare_database(url: str) -> None:
    asyncio.run(_reset_schema(url))
    command.upgrade(alembic_config(url), "head")


@pytest.fixture(scope="session")
def database_url() -> str:
    """A freshly migrated test database, or a skip when PostgreSQL is unavailable."""
    url = _test_database_url()
    # Alembic's async env calls asyncio.run(); a worker thread keeps that away
    # from the event loop pytest-asyncio manages.
    with ThreadPoolExecutor(max_workers=1) as executor:
        try:
            executor.submit(_prepare_database, url).result()
        except (OSError, DBAPIError) as exc:
            pytest.skip(f"PostgreSQL is not reachable at TEST_DATABASE_URL ({type(exc).__name__}).")
    return url


@pytest.fixture
async def db_engine(database_url: str) -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine(database_url, poolclass=NullPool)
    yield engine
    try:
        async with engine.begin() as connection:
            await connection.execute(text(f"TRUNCATE {APPLICATION_TABLES} CASCADE"))
    except SQLAlchemyError:  # a test may have dropped the tables on purpose
        pass
    await engine.dispose()


@pytest.fixture
async def db_session(db_engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    async with AsyncSession(db_engine, expire_on_commit=False) as session:
        yield session


@pytest.fixture
def llm() -> ScriptedLLMProvider:
    return ScriptedLLMProvider()


@pytest.fixture
def app(database_url: str, db_engine: AsyncEngine, llm: ScriptedLLMProvider) -> FastAPI:
    """The real application wired to the test database and a scripted LLM."""
    application = create_app(make_settings(database_url=database_url))
    application.dependency_overrides[get_llm_provider] = lambda: llm
    return application


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    async with running_client(app) as http_client:
        yield http_client


@pytest.fixture
def validator() -> UISchemaValidator:
    return UISchemaValidator(
        build_default_registry(), frozenset(ActionType), build_default_design_registry()
    )


@pytest.fixture
def mutator(validator: UISchemaValidator) -> DocumentMutator:
    return DocumentMutator(validator, build_default_design_registry())


@pytest.fixture
async def validation_context() -> ValidationContext:
    datasets = await MockSalesDataProvider().list_datasets()
    return ValidationContext(datasets={dataset.name: dataset for dataset in datasets})
