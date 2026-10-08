"""Reading and changing the data of one workspace's application.

The store knows the application's entities (from the workspace's current
version) and keeps user-made changes in ``WorkspaceRecord`` rows. It validates
every write against the entity's declared fields, so an action can never add a
field, touch another entity or write a value of the wrong shape.
"""

import uuid
from collections.abc import Mapping

from app.core.exceptions import ActionPayloadException, ResourceNotFoundException
from app.domains.common import DataRow, Scalar
from app.domains.data_sources.providers.base import DataProvider
from app.domains.data_sources.providers.rows import snapshot
from app.domains.data_sources.schemas import DatasetDescriptor, DatasetSnapshot
from app.domains.generative_ui.application import entity_descriptor
from app.domains.generative_ui.document import (
    PRIMARY_KEY,
    ApplicationSpec,
    Entity,
    EntityField,
    EntityFieldType,
)
from app.domains.generative_ui.renderer import apply_changes
from app.domains.records.repository import WorkspaceRecordRepository

MAX_RECORDS_PER_ENTITY = 500
MAX_TEXT_LENGTH = 4000
_NUMERIC = frozenset({EntityFieldType.NUMBER, EntityFieldType.CURRENCY, EntityFieldType.PERCENT})


def _coerce(field: EntityField, value: Scalar) -> Scalar:
    """Bring a submitted value into the shape the field stores, or reject it."""
    if value is None or value == "":
        return None
    if field.type in _NUMERIC:
        if isinstance(value, bool):
            raise ActionPayloadException(f"'{field.label}' must be a number.")
        if isinstance(value, int | float):
            return value
        try:
            number = float(str(value).replace(",", ""))
        except ValueError:
            raise ActionPayloadException(f"'{field.label}' must be a number.") from None
        return int(number) if number.is_integer() else number
    if field.type is EntityFieldType.BOOLEAN:
        return (
            value if isinstance(value, bool) else str(value).lower() in {"true", "yes", "1", "on"}
        )
    text = str(value)
    if len(text) > MAX_TEXT_LENGTH:
        raise ActionPayloadException(f"'{field.label}' is too long.")
    if field.type is EntityFieldType.STATUS and field.options and text not in field.options:
        allowed = ", ".join(field.options)
        raise ActionPayloadException(f"'{field.label}' must be one of: {allowed}.")
    return text


class RecordStore:
    def __init__(
        self,
        workspace_id: uuid.UUID,
        application: ApplicationSpec,
        repository: WorkspaceRecordRepository,
    ) -> None:
        self._workspace_id = workspace_id
        self._entities = {entity.name: entity for entity in application.entities}
        self._repository = repository

    def entities(self) -> list[Entity]:
        return list(self._entities.values())

    def entity(self, name: str) -> Entity:
        entity = self._entities.get(name)
        if entity is None:
            known = ", ".join(sorted(self._entities)) or "none"
            raise ActionPayloadException(
                f"'{name}' is not an entity of this application. Entities: {known}."
            )
        return entity

    async def rows(self, name: str) -> list[DataRow]:
        changes = await self._repository.list_for_workspace(self._workspace_id)
        return apply_changes(self.entity(name), changes)

    async def create(self, name: str, values: Mapping[str, Scalar]) -> list[DataRow]:
        entity = self.entity(name)
        rows = await self.rows(name)
        if len(rows) >= MAX_RECORDS_PER_ENTITY:
            raise ActionPayloadException(f"'{entity.label}' cannot hold more records.")
        record_key = f"{name[:3]}-{uuid.uuid4().hex[:8]}"
        cleaned = self._clean(entity, values)
        # A created record stores every field so it reads the same if the entity's
        # sample records change in a later version.
        complete = {f.key: cleaned.get(f.key) for f in entity.fields if f.key != PRIMARY_KEY}
        await self._repository.upsert(
            workspace_id=self._workspace_id, entity=name, record_key=record_key, values=complete
        )
        return await self.rows(name)

    async def update(
        self, name: str, record_id: str, values: Mapping[str, Scalar]
    ) -> list[DataRow]:
        entity = self.entity(name)
        await self._require(name, record_id)
        await self._repository.upsert(
            workspace_id=self._workspace_id,
            entity=name,
            record_key=record_id,
            values=self._clean(entity, values),
        )
        return await self.rows(name)

    async def delete(self, name: str, record_id: str) -> list[DataRow]:
        await self._require(name, record_id)
        await self._repository.upsert(
            workspace_id=self._workspace_id,
            entity=name,
            record_key=record_id,
            values={},
            deleted=True,
        )
        return await self.rows(name)

    async def _require(self, name: str, record_id: str) -> None:
        if not any(str(row[PRIMARY_KEY]) == record_id for row in await self.rows(name)):
            raise ResourceNotFoundException.for_resource("Record", record_id)

    @staticmethod
    def _clean(entity: Entity, values: Mapping[str, Scalar]) -> dict[str, Scalar]:
        fields = {field.key: field for field in entity.fields if field.key != PRIMARY_KEY}
        unknown = sorted(set(values) - set(fields) - {PRIMARY_KEY})
        if unknown:
            raise ActionPayloadException(
                f"Entity '{entity.name}' has no field(s): {', '.join(unknown)}."
            )
        return {key: _coerce(fields[key], value) for key, value in values.items() if key in fields}


class ApplicationDataProvider(DataProvider):
    """An application's entities as datasets, so data actions work on them."""

    def __init__(self, store: RecordStore) -> None:
        self._store = store

    async def list_datasets(self) -> list[DatasetDescriptor]:
        return [entity_descriptor(entity) for entity in self._store.entities()]

    async def fetch(self, dataset: str, *, limit: int | None = None) -> DatasetSnapshot:
        entity = next((e for e in self._store.entities() if e.name == dataset), None)
        if entity is None:
            raise ResourceNotFoundException.for_resource("Dataset", dataset)
        descriptor = entity_descriptor(entity)
        columns = [field.name for field in descriptor.fields]
        return snapshot(
            dataset, descriptor.description, await self._store.rows(dataset), limit, columns
        )
