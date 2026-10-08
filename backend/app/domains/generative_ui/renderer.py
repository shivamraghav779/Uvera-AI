"""Resolves a document's data bindings into rows.

Components store bindings (dataset names), never rows. Rows come from two
places and travel next to the document, keyed by dataset:

    shared datasets     the caller's data sources, read through ``DataProvider``
    application data    the application's own entities: the sample records kept
                        in the document, with the changes people have made while
                        using the application (``WorkspaceRecord``) laid on top
"""

import uuid
from collections.abc import Sequence
from typing import Protocol

from app.core.exceptions import ResourceNotFoundException
from app.core.logging import get_logger
from app.domains.common import DataRow
from app.domains.data_sources.providers.base import DataProvider
from app.domains.generative_ui.application import bound_dataset_names, entity_rows
from app.domains.generative_ui.document import PRIMARY_KEY, Entity, UIDocument

logger = get_logger(__name__)

MAX_ROWS_PER_DATASET = 500

DataMap = dict[str, list[DataRow]]


class RecordChange(Protocol):
    """A stored change to one record of an application entity."""

    entity: str
    record_key: str
    data: dict[str, object]
    deleted: bool


class RecordChangeSource(Protocol):
    async def list_for_workspace(self, workspace_id: uuid.UUID) -> Sequence[RecordChange]: ...


def bound_datasets(document: UIDocument) -> list[str]:
    """Names of every dataset the document binds to, in first-use order."""
    return bound_dataset_names(document.page.model_dump(mode="json"))


def apply_changes(entity: Entity, changes: Sequence[RecordChange]) -> list[DataRow]:
    """The entity's sample records with stored changes applied.

    Changed records keep their position; created ones follow in creation order.
    Fields the entity no longer declares are dropped, so an old change can never
    put an unknown field in front of a component.
    """
    keys = {PRIMARY_KEY, *(field.key for field in entity.fields)}
    rows = {str(row[PRIMARY_KEY]): row for row in entity_rows(entity)}
    for change in changes:
        if change.entity != entity.name:
            continue
        if change.deleted:
            rows.pop(change.record_key, None)
            continue
        values = {key: value for key, value in change.data.items() if key in keys}
        base = rows.get(change.record_key) or dict.fromkeys(
            (PRIMARY_KEY, *(field.key for field in entity.fields if field.key != PRIMARY_KEY))
        )
        rows[change.record_key] = {**base, **values, PRIMARY_KEY: change.record_key}  # type: ignore[dict-item]
    return list(rows.values())


class UIDataResolver:
    def __init__(
        self,
        data_provider: DataProvider,
        records: RecordChangeSource | None = None,
        *,
        row_limit: int = MAX_ROWS_PER_DATASET,
    ) -> None:
        self._data_provider = data_provider
        self._records = records
        self._row_limit = row_limit

    async def resolve(self, document: UIDocument, workspace_id: uuid.UUID | None = None) -> DataMap:
        """Rows for every bound dataset. Components project the fields they need."""
        entities = await self.entity_rows(document, workspace_id)
        data: DataMap = {}
        for name in bound_datasets(document):
            data[name] = entities[name] if name in entities else await self._rows(name)
        return data

    async def entity_rows(self, document: UIDocument, workspace_id: uuid.UUID | None) -> DataMap:
        """Current rows of every entity of the application (empty for a single view)."""
        if document.application is None:
            return {}
        changes: Sequence[RecordChange] = ()
        if self._records is not None and workspace_id is not None:
            changes = await self._records.list_for_workspace(workspace_id)
        return {
            entity.name: apply_changes(entity, changes)[: self._row_limit]
            for entity in document.application.entities
        }

    async def _rows(self, dataset: str) -> list[DataRow]:
        try:
            return (await self._data_provider.fetch(dataset, limit=self._row_limit)).rows
        except ResourceNotFoundException:
            # A saved version may bind data that has since been disconnected. The UI
            # must still load; the component renders its empty state.
            logger.warning("bound_dataset_unavailable", extra={"dataset": dataset})
            return []
