"""Changes to an application's data are validated against its entities and layered on top."""

import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

import pytest

from app.core.exceptions import ActionPayloadException, ResourceNotFoundException
from app.domains.data_sources.providers.base import EmptyDataProvider
from app.domains.generative_ui.document import ApplicationSpec
from app.domains.generative_ui.renderer import UIDataResolver, apply_changes
from app.domains.records.store import ApplicationDataProvider, RecordStore
from tests.support import sample_application_document

WORKSPACE = uuid.uuid4()


@dataclass
class _Change:
    entity: str
    record_key: str
    data: dict[str, Any] = field(default_factory=dict)
    deleted: bool = False


class MemoryRecords:
    def __init__(self) -> None:
        self.changes: list[_Change] = []

    async def list_for_workspace(self, workspace_id: uuid.UUID) -> Sequence[_Change]:
        return list(self.changes)

    async def upsert(
        self,
        *,
        workspace_id: uuid.UUID,
        entity: str,
        record_key: str,
        values: Mapping[str, object],
        deleted: bool = False,
    ) -> _Change:
        existing = next(
            (c for c in self.changes if (c.entity, c.record_key) == (entity, record_key)), None
        )
        if existing is None:
            existing = _Change(entity, record_key)
            self.changes.append(existing)
        existing.data = {**existing.data, **values}
        existing.deleted = deleted
        return existing


async def _store() -> tuple[RecordStore, MemoryRecords, ApplicationSpec]:
    application = (await sample_application_document()).application
    assert application is not None
    records = MemoryRecords()
    return RecordStore(WORKSPACE, application, records), records, application  # type: ignore[arg-type]


async def test_without_changes_the_sample_records_are_returned() -> None:
    store, _, application = await _store()

    rows = await store.rows("candidates")

    assert len(rows) == len(application.entities[1].records)
    assert rows[0]["name"] == "Amara Okafor"


async def test_updating_a_record_changes_only_that_field_of_that_record() -> None:
    store, records, _ = await _store()

    rows = await store.update("candidates", "cand-003", {"stage": "Interview"})

    by_id = {row["id"]: row for row in rows}
    assert by_id["cand-003"]["stage"] == "Interview"
    assert by_id["cand-003"]["name"] == "Mei Tanaka", "the rest of the record is kept"
    assert by_id["cand-001"]["stage"] == "Interview" and by_id["cand-002"]["stage"] == "Screening"
    assert [row["id"] for row in rows][:3] == ["cand-001", "cand-002", "cand-003"], "order is kept"
    assert [(c.entity, c.record_key, c.data) for c in records.changes] == [
        ("candidates", "cand-003", {"stage": "Interview"})
    ]


async def test_creating_a_record_types_its_values_and_gives_it_an_id() -> None:
    store, _, _ = await _store()

    rows = await store.create("jobs", {"title": "QA Engineer", "openings": "2", "status": "Open"})

    created = rows[-1]
    assert created["title"] == "QA Engineer" and created["openings"] == 2
    assert str(created["id"]).startswith("job-") and created["department"] is None
    assert len(rows) == 6


async def test_deleted_records_disappear_and_cannot_be_changed_again() -> None:
    store, _, _ = await _store()

    rows = await store.delete("jobs", "job-103")

    assert "job-103" not in [row["id"] for row in rows]
    with pytest.raises(ResourceNotFoundException):
        await store.update("jobs", "job-103", {"status": "Open"})


@pytest.mark.parametrize(
    ("entity", "values", "fragment"),
    [
        ("invoices", {"total": 1}, "is not an entity of this application"),
        ("jobs", {"salary": 1}, "has no field(s): salary"),
        ("jobs", {"openings": "many"}, "'Openings' must be a number"),
        ("jobs", {"status": "Archived"}, "'Status' must be one of: Open, Paused, Closed"),
        ("jobs", {"title": "x" * 4001}, "'Title' is too long"),
    ],
)
async def test_writes_outside_the_entitys_shape_are_refused(
    entity: str, values: dict[str, Any], fragment: str
) -> None:
    store, records, _ = await _store()

    with pytest.raises(ActionPayloadException) as error:
        await store.create(entity, values)

    assert fragment in error.value.message
    assert records.changes == [], "nothing was written"


async def test_unknown_records_cannot_be_updated() -> None:
    store, _, _ = await _store()

    with pytest.raises(ResourceNotFoundException):
        await store.update("jobs", "job-999", {"status": "Open"})


async def test_changes_to_fields_an_entity_no_longer_has_are_ignored() -> None:
    _, _, application = await _store()
    jobs = application.entities[0]
    stale = [_Change("jobs", "job-101", {"status": "Paused", "removed_field": "x"})]

    rows = apply_changes(jobs, stale)

    assert rows[0]["status"] == "Paused" and "removed_field" not in rows[0]


async def test_entities_are_datasets_for_data_actions_and_bound_components() -> None:
    store, records, _ = await _store()
    await store.update("candidates", "cand-005", {"stage": "Hired"})
    provider = ApplicationDataProvider(store)

    names = [dataset.name for dataset in await provider.list_datasets()]
    snapshot = await provider.fetch("candidates", limit=5)

    assert names == ["jobs", "candidates", "interviews", "hiring_by_month"]
    assert [field.name for field in snapshot.descriptor.fields][:3] == ["id", "name", "role"]
    assert snapshot.rows[4]["stage"] == "Hired" and len(snapshot.rows) == 5
    with pytest.raises(ResourceNotFoundException):
        await provider.fetch("sales_by_region")

    document = await sample_application_document()
    data = await UIDataResolver(EmptyDataProvider(), records).resolve(document, WORKSPACE)  # type: ignore[arg-type]
    assert set(data) == {"jobs", "candidates", "hiring_by_month", "interviews"}
    assert next(r for r in data["candidates"] if r["id"] == "cand-005")["stage"] == "Hired"
