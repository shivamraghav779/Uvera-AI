"""Development-only demo data: quarterly sales by region, month and product."""

from collections import defaultdict
from collections.abc import Sequence
from itertools import product

from app.core.exceptions import ResourceNotFoundException
from app.domains.common import DataRow
from app.domains.data_sources.providers.base import DataProvider
from app.domains.data_sources.schemas import (
    DatasetDescriptor,
    DatasetField,
    DatasetSnapshot,
    FieldKind,
)

# Deterministic inputs the demo records are derived from.
_REGION_BASE_REVENUE = {
    "North": 1_800_000,
    "South": 1_350_000,
    "East": 1_120_000,
    "West": 1_560_000,
}
_MONTH_FACTOR = {"2025-07": 0.94, "2025-08": 1.00, "2025-09": 1.09}
_PRODUCT_SHARE_AND_PRICE = {
    "Laptops": (0.52, 62_000),
    "Phones": (0.34, 28_000),
    "Accessories": (0.14, 1_900),
}

_REVENUE = DatasetField(name="revenue", kind=FieldKind.NUMBER)
_ORDERS = DatasetField(name="orders", kind=FieldKind.NUMBER)


def _string(name: str) -> DatasetField:
    return DatasetField(name=name, kind=FieldKind.STRING)


def _build_records() -> list[DataRow]:
    records: list[DataRow] = []
    for region, month, item in product(
        _REGION_BASE_REVENUE, _MONTH_FACTOR, _PRODUCT_SHARE_AND_PRICE
    ):
        share, unit_price = _PRODUCT_SHARE_AND_PRICE[item]
        revenue = round(_REGION_BASE_REVENUE[region] * _MONTH_FACTOR[month] * share)
        records.append(
            {
                "region": region,
                "month": month,
                "product": item,
                "revenue": revenue,
                "orders": max(revenue // unit_price, 1),
            }
        )
    return records


def _totals_by(records: Sequence[DataRow], dimension: str) -> list[DataRow]:
    revenue: dict[str, int] = defaultdict(int)
    orders: dict[str, int] = defaultdict(int)
    for record in records:
        key = str(record[dimension])
        revenue[key] += int(record["revenue"] or 0)
        orders[key] += int(record["orders"] or 0)
    return [{dimension: key, "revenue": revenue[key], "orders": orders[key]} for key in revenue]


def _summary(records: Sequence[DataRow]) -> list[DataRow]:
    by_region = _totals_by(records, "region")
    total_revenue = sum(int(row["revenue"] or 0) for row in by_region)
    total_orders = sum(int(row["orders"] or 0) for row in by_region)
    top_region = max(by_region, key=lambda row: int(row["revenue"] or 0))
    return [
        {
            "period": "Q3 2025",
            "total_revenue": total_revenue,
            "total_orders": total_orders,
            "average_order_value": round(total_revenue / total_orders),
            "top_region": top_region["region"],
        }
    ]


def _build_datasets() -> dict[str, DatasetSnapshot]:
    records = _build_records()

    def dataset(
        name: str, description: str, fields: list[DatasetField], rows: list[DataRow]
    ) -> DatasetSnapshot:
        descriptor = DatasetDescriptor(name=name, description=description, fields=fields)
        return DatasetSnapshot(descriptor=descriptor, rows=rows)

    datasets = [
        dataset(
            "sales_summary",
            "Headline sales totals for the quarter (single row).",
            [
                _string("period"),
                DatasetField(name="total_revenue", kind=FieldKind.NUMBER),
                DatasetField(name="total_orders", kind=FieldKind.NUMBER),
                DatasetField(name="average_order_value", kind=FieldKind.NUMBER),
                _string("top_region"),
            ],
            _summary(records),
        ),
        dataset(
            "sales_by_region",
            "Revenue and order totals per sales region.",
            [_string("region"), _REVENUE, _ORDERS],
            _totals_by(records, "region"),
        ),
        dataset(
            "sales_by_month",
            "Revenue and order totals per month (trend over time).",
            [_string("month"), _REVENUE, _ORDERS],
            _totals_by(records, "month"),
        ),
        dataset(
            "sales_by_product",
            "Revenue and order totals per product line.",
            [_string("product"), _REVENUE, _ORDERS],
            _totals_by(records, "product"),
        ),
        dataset(
            "sales_records",
            "Detailed sales records by region, month and product.",
            [_string("region"), _string("month"), _string("product"), _REVENUE, _ORDERS],
            records,
        ),
    ]
    return {item.descriptor.name: item for item in datasets}


class MockSalesDataProvider(DataProvider):
    """Serves a fixed demo dataset (INR). Never enabled in production."""

    def __init__(self) -> None:
        self._datasets = _build_datasets()

    async def list_datasets(self) -> list[DatasetDescriptor]:
        return [snapshot.descriptor for snapshot in self._datasets.values()]

    async def fetch(self, dataset: str, *, limit: int | None = None) -> DatasetSnapshot:
        snapshot = self._datasets.get(dataset)
        if snapshot is None:
            raise ResourceNotFoundException.for_resource("Dataset", dataset)
        rows = snapshot.rows if limit is None else snapshot.rows[:limit]
        return DatasetSnapshot(descriptor=snapshot.descriptor, rows=[dict(row) for row in rows])
