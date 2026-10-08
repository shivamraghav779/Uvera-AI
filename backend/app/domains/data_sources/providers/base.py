"""The contract every source of dataset rows implements."""

from abc import ABC, abstractmethod

from app.core.exceptions import ResourceNotFoundException
from app.domains.data_sources.schemas import DatasetDescriptor, DatasetSnapshot


class DataProvider(ABC):
    """Read-only access to named datasets.

    The planner, validator, renderer and action handlers depend on this
    interface only, so the mock provider can be replaced by SQL queries,
    uploaded files or external APIs without touching them.
    """

    @abstractmethod
    async def list_datasets(self) -> list[DatasetDescriptor]:
        """Describe every dataset that can currently be read."""

    @abstractmethod
    async def fetch(self, dataset: str, *, limit: int | None = None) -> DatasetSnapshot:
        """Return rows of ``dataset``; raise ``ResourceNotFoundException`` if unknown."""


class EmptyDataProvider(DataProvider):
    """Used when no data source is available: there is nothing to read."""

    async def list_datasets(self) -> list[DatasetDescriptor]:
        return []

    async def fetch(self, dataset: str, *, limit: int | None = None) -> DatasetSnapshot:
        raise ResourceNotFoundException.for_resource("Dataset", dataset)
