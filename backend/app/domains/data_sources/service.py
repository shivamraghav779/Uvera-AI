import uuid
from typing import Any

from pydantic import ValidationError

from app.core.exceptions import ConflictException, ResourceNotFoundException, ValidationException
from app.core.logging import get_logger
from app.core.security import Principal
from app.database.unit_of_work import UnitOfWork
from app.domains.data_sources.models import DataSource
from app.domains.data_sources.providers.base import DataProvider
from app.domains.data_sources.providers.factory import DataProviderFactory
from app.domains.data_sources.providers.inline import parse_csv, parse_json
from app.domains.data_sources.providers.rows import column_names
from app.domains.data_sources.repository import DataSourceRepository
from app.domains.data_sources.schemas import (
    CONFIG_MODELS,
    DatasetDescriptor,
    DataSourceCreate,
    DataSourceRead,
    DataSourceType,
    FileUploadConfig,
    PostgresConfig,
    RestApiConfig,
    UploadFormat,
)

logger = get_logger(__name__)

MAX_SOURCES_PER_USER = 50


def dataset_names(source: DataSource) -> list[str]:
    """Datasets a stored source provides, read from its configuration."""
    config: dict[str, Any] = source.configuration
    if source.type == DataSourceType.POSTGRESQL:
        return [item["name"] for item in config.get("datasets", [])]
    return [config["dataset"]] if "dataset" in config else []


def to_read(source: DataSource) -> DataSourceRead:
    # The configuration itself is not returned: it can hold uploaded rows or internal URLs.
    return DataSourceRead(
        id=source.id,
        name=source.name,
        type=DataSourceType(source.type),
        datasets=dataset_names(source),
        created_at=source.created_at,
        updated_at=source.updated_at,
    )


class DataSourceService:
    """Registers data sources and exposes the datasets they provide.

    A source is only stored after it has been read successfully once, so a
    registered source is known to have worked.
    """

    def __init__(
        self,
        repository: DataSourceRepository,
        factory: DataProviderFactory,
        catalogue: DataProvider,
        uow: UnitOfWork,
    ) -> None:
        self._repository = repository
        self._factory = factory
        # Everything the caller can already read (demo data plus their sources).
        self._catalogue = catalogue
        self._uow = uow

    async def create(self, principal: Principal, payload: DataSourceCreate) -> DataSourceRead:
        stored = self._stored_configuration(payload)
        candidate = DataSource(
            user_id=principal.user_id,
            name=payload.name,
            type=payload.type.value,
            configuration=stored,
        )
        await self._ensure_unique_datasets(dataset_names(candidate))
        # Proves the source is reachable and returns usable rows before anything is saved.
        await self._factory.build(candidate).list_datasets()

        source = await self._repository.create(
            user_id=principal.user_id,
            name=payload.name,
            type=payload.type.value,
            configuration=stored,
        )
        await self._uow.commit()
        logger.info("data_source_registered", extra={"type": payload.type.value})
        return to_read(source)

    async def list_data_sources(self, principal: Principal) -> list[DataSourceRead]:
        sources = await self._repository.list_for_user(
            principal.user_id, limit=MAX_SOURCES_PER_USER
        )
        return [to_read(source) for source in sources]

    async def list_datasets(self) -> list[DatasetDescriptor]:
        return await self._catalogue.list_datasets()

    async def delete(self, principal: Principal, data_source_id: uuid.UUID) -> None:
        source = await self._repository.get(data_source_id)
        if source is None or source.user_id != principal.user_id:
            raise ResourceNotFoundException.for_resource("Data source", data_source_id)
        await self._repository.delete(source)
        await self._uow.commit()

    @staticmethod
    def _stored_configuration(payload: DataSourceCreate) -> dict[str, Any]:
        """Validate type-specific settings and return the form kept in the database."""
        try:
            config = CONFIG_MODELS[payload.type].model_validate(payload.configuration)
        except ValidationError as exc:
            details = [
                {"path": ".".join(["configuration", *map(str, e["loc"])]), "message": e["msg"]}
                for e in exc.errors(include_url=False, include_input=False)
            ]
            raise ValidationException(
                "The data source configuration is invalid.", details=details
            ) from None
        if isinstance(config, FileUploadConfig):
            parse = parse_csv if config.format is UploadFormat.CSV else parse_json
            # The parsed rows are stored; the raw upload is not.
            rows = parse(config.content)
            return {
                "dataset": config.dataset,
                "description": config.description,
                # Kept separately: the JSON column does not preserve key order.
                "columns": column_names(rows),
                "rows": rows,
            }
        if isinstance(config, RestApiConfig | PostgresConfig):
            return config.model_dump(mode="json")
        return {}

    async def _ensure_unique_datasets(self, names: list[str]) -> None:
        existing = {descriptor.name for descriptor in await self._catalogue.list_datasets()}
        clashes = sorted(existing.intersection(names))
        if clashes or len(set(names)) != len(names):
            raise ConflictException(
                f"Dataset name already in use: {', '.join(clashes) or 'duplicate names'}. "
                "Dataset names must be unique."
            )
