"""Built-in action handlers.

Each handler does one bounded thing with a validated payload. Data actions
read through ``DataProvider``; record actions change an application's own data
through ``RecordWriter``. Nothing here evaluates model-supplied code.
"""

import csv
import io
import operator
from collections.abc import Callable, Mapping
from typing import Any, Protocol

from app.ai.search.base import SearchProvider, SearchQuery
from app.core.exceptions import ActionPayloadException, ProviderNotConfiguredException
from app.domains.actions.registry import ActionHandler, ActionRegistry, ActionResult
from app.domains.actions.schemas import (
    ActionType,
    DatasetActionPayload,
    ExportFormat,
    ExportPayload,
    FilterOperator,
    FilterPayload,
    GeneratePayload,
    NavigatePayload,
    RecordCreatePayload,
    RecordDeletePayload,
    RecordPayload,
    RecordUpdatePayload,
    RefreshPayload,
    SearchPayload,
    SortDirection,
    SortPayload,
    SubmitPayload,
)
from app.domains.common import DataRow, Scalar
from app.domains.data_sources.providers.base import DataProvider
from app.domains.data_sources.schemas import DatasetSnapshot
from app.utils.json import to_compact_json

MAX_RESULT_ROWS = 500


class RecordWriter(Protocol):
    """Changes the records of the application a request is acting on."""

    async def create(self, name: str, values: Mapping[str, Scalar]) -> list[DataRow]: ...

    async def update(
        self, name: str, record_id: str, values: Mapping[str, Scalar]
    ) -> list[DataRow]: ...

    async def delete(self, name: str, record_id: str) -> list[DataRow]: ...


def _contains(cell: Scalar, expected: Scalar) -> bool:
    return str(expected).lower() in str(cell).lower()


def _ordered(compare: Callable[[Any, Any], Any]) -> Callable[[Scalar, Scalar], bool]:
    """Ordering comparison; raises TypeError for incomparable operands."""
    return lambda cell, expected: bool(compare(cell, expected))


_COMPARATORS: dict[FilterOperator, Callable[[Scalar, Scalar], bool]] = {
    FilterOperator.EQUALS: operator.eq,
    FilterOperator.NOT_EQUALS: operator.ne,
    FilterOperator.CONTAINS: _contains,
    FilterOperator.GREATER_THAN: _ordered(operator.gt),
    FilterOperator.GREATER_OR_EQUAL: _ordered(operator.ge),
    FilterOperator.LESS_THAN: _ordered(operator.lt),
    FilterOperator.LESS_OR_EQUAL: _ordered(operator.le),
}


def _rows_result(payload: DatasetActionPayload, rows: list[DataRow]) -> ActionResult:
    return {"dataset": payload.dataset, "target": payload.target, "rows": rows}


class _DatasetHandler[PayloadT: DatasetActionPayload](ActionHandler[PayloadT]):
    def __init__(self, data_provider: DataProvider) -> None:
        self._data_provider = data_provider

    async def _load(
        self, payload: DatasetActionPayload, field: str | None = None
    ) -> DatasetSnapshot:
        snapshot = await self._data_provider.fetch(payload.dataset, limit=MAX_RESULT_ROWS)
        if field is not None and field not in snapshot.descriptor.field_names:
            raise ActionPayloadException(f"Dataset '{payload.dataset}' has no field '{field}'.")
        return snapshot


class FilterHandler(_DatasetHandler[FilterPayload]):
    action_type = ActionType.FILTER
    description = "Return the rows of a dataset that match a condition on one field."
    payload_model = FilterPayload

    async def handle(self, payload: FilterPayload) -> ActionResult:
        snapshot = await self._load(payload, payload.field)
        matches = _COMPARATORS[payload.operator]
        try:
            rows = [row for row in snapshot.rows if matches(row[payload.field], payload.value)]
        except TypeError:
            raise ActionPayloadException(
                f"Value is not comparable with field '{payload.field}'."
            ) from None
        return _rows_result(payload, rows)


class SortHandler(_DatasetHandler[SortPayload]):
    action_type = ActionType.SORT
    description = "Return the rows of a dataset ordered by one field."
    payload_model = SortPayload

    async def handle(self, payload: SortPayload) -> ActionResult:
        snapshot = await self._load(payload, payload.field)
        descending = payload.direction is SortDirection.DESCENDING

        def sort_key(row: DataRow) -> tuple[bool, float, str]:
            cell = row[payload.field]
            if isinstance(cell, int | float) and not isinstance(cell, bool):
                return (cell is None, float(cell), "")
            return (cell is None, 0.0, str(cell))

        return _rows_result(payload, sorted(snapshot.rows, key=sort_key, reverse=descending))


class RefreshHandler(_DatasetHandler[RefreshPayload]):
    action_type = ActionType.REFRESH
    description = "Reload the current rows of a dataset."
    payload_model = RefreshPayload

    async def handle(self, payload: RefreshPayload) -> ActionResult:
        return _rows_result(payload, (await self._load(payload)).rows)


class ExportHandler(_DatasetHandler[ExportPayload]):
    action_type = ActionType.EXPORT
    description = "Export a dataset as CSV or JSON text."
    payload_model = ExportPayload

    async def handle(self, payload: ExportPayload) -> ActionResult:
        snapshot = await self._load(payload)
        if payload.format is ExportFormat.JSON:
            content, media_type = to_compact_json(snapshot.rows), "application/json"
        else:
            content, media_type = _to_csv(snapshot), "text/csv"
        return {
            "dataset": payload.dataset,
            "filename": f"{payload.dataset}.{payload.format.value}",
            "media_type": media_type,
            "content": content,
        }


def _to_csv(snapshot: DatasetSnapshot) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=[field.name for field in snapshot.descriptor.fields])
    writer.writeheader()
    writer.writerows(snapshot.rows)
    return buffer.getvalue()


class NavigateHandler(ActionHandler[NavigatePayload]):
    action_type = ActionType.NAVIGATE
    description = (
        "Go to a screen of the application by its route ('/jobs', or '/jobs/:jobId' from a "
        "record's card or row, which fills the parameter with that record's id; add "
        "from_field to take the id from another field of the record), or open an https link."
    )
    payload_model = NavigatePayload

    async def handle(self, payload: NavigatePayload) -> ActionResult:
        # The destination was validated by the payload model; the client performs the move.
        return {"navigate_to": payload.to}


class SubmitHandler(ActionHandler[SubmitPayload]):
    action_type = ActionType.SUBMIT
    description = "Submit the values of a form."
    payload_model = SubmitPayload

    async def handle(self, payload: SubmitPayload) -> ActionResult:
        # ActionService stores every executed action; submissions are read back through
        # GET /workspaces/{id}/submissions.
        return {"form_id": payload.form_id, "accepted_fields": sorted(payload.values)}


class GenerateHandler(ActionHandler[GeneratePayload]):
    action_type = ActionType.GENERATE
    description = "Ask for a new UI to be generated from a follow-up request."
    payload_model = GeneratePayload

    async def handle(self, payload: GeneratePayload) -> ActionResult:
        # A UI change must go through the proposal -> approval flow, so this action does
        # not generate anything itself: it validates and records the request, and the
        # client hands `instruction` to the assistant, which returns a proposal.
        return {"instruction": payload.message}


class SearchHandler(ActionHandler[SearchPayload]):
    action_type = ActionType.SEARCH
    description = "Search the web and return titles, URLs and snippets."
    payload_model = SearchPayload

    def __init__(self, search_provider: SearchProvider | None) -> None:
        self._search_provider = search_provider

    async def handle(self, payload: SearchPayload) -> ActionResult:
        if self._search_provider is None:
            raise ProviderNotConfiguredException("No search provider is configured.")
        results = await self._search_provider.search(
            SearchQuery(
                query=payload.query,
                num_results=payload.num_results,
                include_domains=tuple(payload.domains),
            )
        )
        return {
            "query": payload.query,
            "results": [
                {"title": item.title, "url": item.url, "snippet": item.snippet} for item in results
            ],
        }


class _RecordHandler[PayloadT: RecordPayload](ActionHandler[PayloadT]):
    def __init__(self, records: RecordWriter | None) -> None:
        self._records = records

    @property
    def _writer(self) -> RecordWriter:
        if self._records is None:
            raise ActionPayloadException("This workspace has no application data to change.")
        return self._records

    @staticmethod
    def _result(payload: RecordPayload, rows: list[DataRow]) -> ActionResult:
        # The whole entity is returned: every component bound to it refreshes.
        return {"dataset": payload.entity, "rows": rows, "navigate_to": payload.navigate_to}


class RecordCreateHandler(_RecordHandler[RecordCreatePayload]):
    action_type = ActionType.RECORD_CREATE
    description = (
        "Add a record to an application entity (use as a form's submit_action; the form's "
        "field names must be the entity's field keys). Schema payload: entity, navigate_to."
    )
    payload_model = RecordCreatePayload

    async def handle(self, payload: RecordCreatePayload) -> ActionResult:
        return self._result(payload, await self._writer.create(payload.entity, payload.values))


class RecordUpdateHandler(_RecordHandler[RecordUpdatePayload]):
    action_type = ActionType.RECORD_UPDATE
    description = (
        "Change fields of one record. Schema payload: entity, set_field and set_value (the "
        "change), key_param (route parameter holding the record id, when not run from a "
        "record's own card or row), navigate_to. As a form's submit_action the form values "
        "are the change."
    )
    payload_model = RecordUpdatePayload

    async def handle(self, payload: RecordUpdatePayload) -> ActionResult:
        rows = await self._writer.update(payload.entity, payload.record_id, payload.values)
        return self._result(payload, rows)


class RecordDeleteHandler(_RecordHandler[RecordDeletePayload]):
    action_type = ActionType.RECORD_DELETE
    description = "Remove one record. Schema payload: entity, key_param, navigate_to."
    payload_model = RecordDeletePayload

    async def handle(self, payload: RecordDeletePayload) -> ActionResult:
        return self._result(payload, await self._writer.delete(payload.entity, payload.record_id))


def build_default_action_registry(
    data_provider: DataProvider,
    search_provider: SearchProvider | None,
    records: RecordWriter | None = None,
) -> ActionRegistry:
    registry = ActionRegistry()
    for handler in (
        FilterHandler(data_provider),
        SortHandler(data_provider),
        RefreshHandler(data_provider),
        ExportHandler(data_provider),
        NavigateHandler(),
        SubmitHandler(),
        GenerateHandler(),
        SearchHandler(search_provider),
        RecordCreateHandler(records),
        RecordUpdateHandler(records),
        RecordDeleteHandler(records),
    ):
        registry.register(handler)  # type: ignore[arg-type]
    return registry
