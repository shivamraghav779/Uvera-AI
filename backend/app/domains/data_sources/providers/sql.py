"""Datasets defined as read-only SQL queries against an external PostgreSQL database."""

from dataclasses import dataclass

import asyncpg  # type: ignore[import-untyped]

from app.core.exceptions import DataSourceException, ResourceNotFoundException
from app.core.logging import get_logger
from app.domains.common import DataRow
from app.domains.data_sources.providers.base import DataProvider
from app.domains.data_sources.providers.rows import MAX_ROWS, describe, normalise_rows, snapshot
from app.domains.data_sources.schemas import DatasetDescriptor, DatasetSnapshot

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class QueryDataset:
    name: str
    description: str
    query: str


class PostgresQueryDataProvider(DataProvider):
    """Runs each dataset's query in a READ ONLY transaction with a timeout and a row cap.

    The connection string comes from a secret reference, never from the stored
    configuration. Queries are restricted to a single SELECT at registration
    time, and the transaction mode makes the database enforce it too.
    """

    def __init__(self, *, dsn: str, datasets: list[QueryDataset], timeout_seconds: float) -> None:
        self._dsn = dsn
        self._datasets = {dataset.name: dataset for dataset in datasets}
        self._timeout = timeout_seconds
        self._cache: dict[str, list[DataRow]] = {}

    async def list_datasets(self) -> list[DatasetDescriptor]:
        return [
            describe(dataset.name, dataset.description, await self._load(dataset))
            for dataset in self._datasets.values()
        ]

    async def fetch(self, dataset: str, *, limit: int | None = None) -> DatasetSnapshot:
        definition = self._datasets.get(dataset)
        if definition is None:
            raise ResourceNotFoundException.for_resource("Dataset", dataset)
        rows = await self._load(definition)
        return snapshot(definition.name, definition.description, rows, limit)

    async def _load(self, dataset: QueryDataset) -> list[DataRow]:
        if dataset.name not in self._cache:
            self._cache[dataset.name] = await self._query(dataset)
        return self._cache[dataset.name]

    async def _query(self, dataset: QueryDataset) -> list[DataRow]:
        statement = f"SELECT * FROM ({dataset.query}) AS dataset LIMIT {MAX_ROWS}"
        try:
            connection = await asyncpg.connect(self._dsn, timeout=self._timeout)
            try:
                async with connection.transaction(readonly=True):
                    records = await connection.fetch(statement, timeout=self._timeout)
            finally:
                await connection.close()
        except (TimeoutError, asyncpg.PostgresError, asyncpg.InterfaceError, OSError) as exc:
            # Driver messages may include SQL or host details: log the class only.
            logger.warning(
                "data_source_query_failed",
                extra={"dataset": dataset.name, "error_type": type(exc).__name__},
            )
            raise DataSourceException(
                f"The query for dataset '{dataset.name}' could not be run."
            ) from None
        return normalise_rows(dict(record) for record in records)
