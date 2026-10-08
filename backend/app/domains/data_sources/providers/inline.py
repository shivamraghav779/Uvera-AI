"""Datasets whose rows are stored with the data source (uploaded CSV/JSON)."""

import csv
import io
import json

from app.core.exceptions import ResourceNotFoundException, ValidationException
from app.domains.common import DataRow, Scalar
from app.domains.data_sources.providers.base import DataProvider
from app.domains.data_sources.providers.rows import describe, normalise_rows, snapshot
from app.domains.data_sources.schemas import DatasetDescriptor, DatasetSnapshot


def _coerce(cell: str) -> Scalar:
    """CSV cells are text; recover numbers and blanks."""
    text = cell.strip()
    if text == "":
        return None
    try:
        number = float(text)
    except ValueError:
        return text
    return (
        int(number)
        if number.is_integer() and "." not in text and "e" not in text.lower()
        else number
    )


def parse_csv(content: str) -> list[DataRow]:
    reader = csv.DictReader(io.StringIO(content))
    if not reader.fieldnames:
        raise ValidationException("The CSV has no header row.")
    records = [
        {key: _coerce(value or "") for key, value in record.items() if key} for record in reader
    ]
    return _require_rows(normalise_rows(records))


def parse_json(content: str) -> list[DataRow]:
    try:
        records = json.loads(content)
    except ValueError:
        raise ValidationException("The content is not valid JSON.") from None
    if not isinstance(records, list):
        raise ValidationException("JSON content must be a list of records.")
    return _require_rows(normalise_rows(records))


def _require_rows(rows: list[DataRow]) -> list[DataRow]:
    if not rows:
        raise ValidationException("The content contains no rows.")
    return rows


class InlineDataProvider(DataProvider):
    def __init__(
        self, name: str, description: str, rows: list[DataRow], columns: list[str] | None = None
    ) -> None:
        self._name = name
        self._description = description
        self._rows = rows
        self._columns = columns

    async def list_datasets(self) -> list[DatasetDescriptor]:
        return [describe(self._name, self._description, self._rows, self._columns)]

    async def fetch(self, dataset: str, *, limit: int | None = None) -> DatasetSnapshot:
        if dataset != self._name:
            raise ResourceNotFoundException.for_resource("Dataset", dataset)
        rows = [dict(row) for row in self._rows]
        return snapshot(self._name, self._description, rows, limit, self._columns)
