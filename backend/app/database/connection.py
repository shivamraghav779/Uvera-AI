"""Async database engine and session management."""

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.logging import get_logger

logger = get_logger(__name__)


class Database:
    """Owns the engine for the lifetime of the application.

    One instance is created at startup and stored on ``app.state``; nothing is
    kept in module globals.
    """

    def __init__(self, url: str, *, pool_size: int = 5, max_overflow: int = 10) -> None:
        self._engine = create_async_engine(
            url, pool_size=pool_size, max_overflow=max_overflow, pool_pre_ping=True
        )
        self._session_factory = async_sessionmaker(self._engine, expire_on_commit=False)

    def session(self) -> AsyncSession:
        return self._session_factory()

    async def ping(self) -> bool:
        try:
            async with self._engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
        except (SQLAlchemyError, OSError) as exc:
            logger.warning("database_ping_failed", extra={"error_type": type(exc).__name__})
            return False
        return True

    async def dispose(self) -> None:
        await self._engine.dispose()
