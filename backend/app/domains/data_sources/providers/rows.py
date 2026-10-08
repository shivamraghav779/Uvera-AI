"""Turns whatever a source returns into the flat, typed rows the UI works with."""

import json
from collections.abc import Iterable, Mapping

from app.core.exceptions import DataSourceException
from app.domains.common import DataRow, Scalar
from app.domains.data_sources.schemas import (
    DatasetDescriptor,
    DatasetField,
    DatasetSnapshot,
    FieldKind,
)

MAX_ROWS = 500
MAX_FIELDS = 40
MAX_FIELD_NAME_LENGTH = 64


def _to_scalar(value: object) -> Scalar:
    if value is None or isinstance(value, str | int | float | bool):
        return value
    # Nested structures, dates, decimals...: keep them readable rather than dropping them.
    return json.dumps(value, default=str) if isinstance(value, dict | list) else str(value)


def normalise_rows(records: Iterable[object]) -> list[DataRow]:
    """Flat rows with scalar values and bounded size. Raises if records are not objects."""
    rows: list[DataRow] = []
    for record in records:
        if not isinstance(record, Mapping):
            raise DataSourceException("The data source did not return a list of records.")
        row = {
            str(key)[:MAX_FIELD_NAME_LENGTH]: _to_scalar(value)
            for key, value in list(record.items())[:MAX_FIELDS]
        }
        rows.append(row)
        if len(rows) >= MAX_ROWS:
            break
    return rows


def _kind(rows: list[DataRow], name: str) -> FieldKind:
    values = [row.get(name) for row in rows if row.get(name) is not None]
    numeric = values and all(isinstance(v, int | float) and not isinstance(v, bool) for v in values)
    return FieldKind.NUMBER if numeric else FieldKind.STRING


def column_names(rows: list[DataRow]) -> list[str]:
    """Field names in first-seen order."""
    return list(dict.fromkeys(key for row in rows for key in row))


def describe(
    name: str, description: str, rows: list[DataRow], columns: list[str] | None = None
) -> DatasetDescriptor:
    """Infer a dataset's fields from its rows. ``columns`` fixes their order when known."""
    names = columns or column_names(rows)
    fields = [DatasetField(name=field, kind=_kind(rows, field)) for field in names]
    return DatasetDescriptor(name=name, description=description, fields=fields)


def snapshot(
    name: str,
    description: str,
    rows: list[DataRow],
    limit: int | None,
    columns: list[str] | None = None,
) -> DatasetSnapshot:
    descriptor = describe(name, description, rows, columns)
    return DatasetSnapshot(descriptor=descriptor, rows=rows if limit is None else rows[:limit])
