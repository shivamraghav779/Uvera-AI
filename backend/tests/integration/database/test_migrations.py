from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import Connection, inspect
from sqlalchemy.ext.asyncio import AsyncEngine

from app.database import models  # noqa: F401
from app.database.base import Base

EXPECTED_TABLES = {
    "users",
    "workspaces",
    "conversations",
    "ui_versions",
    "data_sources",
    "ui_actions",
    "workspace_records",
    "assets",
    "generation_jobs",
    "reference_components",
    "alembic_version",
}


def _schema_drift(connection: Connection) -> list[object]:
    context = MigrationContext.configure(connection, opts={"compare_type": True})
    return list(compare_metadata(context, Base.metadata))


async def test_migrations_create_every_table(db_engine: AsyncEngine) -> None:
    async with db_engine.connect() as connection:
        tables = await connection.run_sync(lambda sync: set(inspect(sync).get_table_names()))

    assert tables == EXPECTED_TABLES


async def test_migrated_schema_matches_the_orm_models(db_engine: AsyncEngine) -> None:
    """Fails when a model changes without a matching migration."""
    async with db_engine.connect() as connection:
        drift = await connection.run_sync(_schema_drift)

    assert drift == []
