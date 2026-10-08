from app.core.exceptions import DataSourceException, ResourceNotFoundException
from app.core.logging import get_logger
from app.domains.data_sources.providers.base import DataProvider
from app.domains.data_sources.schemas import DatasetDescriptor, DatasetSnapshot

logger = get_logger(__name__)


class CompositeDataProvider(DataProvider):
    """Presents several providers as one catalogue of datasets.

    A source that cannot be reached is skipped when listing (and logged), so one
    broken connection does not take every other dataset down with it. Fetching
    a dataset from a broken source still fails loudly.
    """

    def __init__(self, providers: list[DataProvider]) -> None:
        self._providers = providers
        self._owners: dict[str, DataProvider] | None = None

    async def list_datasets(self) -> list[DatasetDescriptor]:
        descriptors: dict[str, DatasetDescriptor] = {}
        owners: dict[str, DataProvider] = {}
        for provider in self._providers:
            try:
                listed = await provider.list_datasets()
            except DataSourceException:
                logger.warning("data_source_skipped", extra={"provider": type(provider).__name__})
                continue
            for descriptor in listed:
                # First provider wins; names are kept unique when sources are registered.
                if descriptor.name not in descriptors:
                    descriptors[descriptor.name] = descriptor
                    owners[descriptor.name] = provider
        self._owners = owners
        return list(descriptors.values())

    async def fetch(self, dataset: str, *, limit: int | None = None) -> DatasetSnapshot:
        if self._owners is None:
            await self.list_datasets()
        owner = (self._owners or {}).get(dataset)
        if owner is None:
            raise ResourceNotFoundException.for_resource("Dataset", dataset)
        return await owner.fetch(dataset, limit=limit)
