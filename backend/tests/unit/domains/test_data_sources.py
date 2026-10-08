import pytest
from pydantic import ValidationError

from app.core.exceptions import ResourceNotFoundException
from app.domains.data_sources.providers.base import EmptyDataProvider
from app.domains.data_sources.providers.mock import MockSalesDataProvider
from app.domains.data_sources.schemas import DataSourceCreate


async def test_mock_provider_describes_its_datasets() -> None:
    datasets = await MockSalesDataProvider().list_datasets()

    by_name = {dataset.name: dataset for dataset in datasets}
    assert set(by_name) == {
        "sales_summary",
        "sales_by_region",
        "sales_by_month",
        "sales_by_product",
        "sales_records",
    }
    assert by_name["sales_records"].field_names == {
        "region",
        "month",
        "product",
        "revenue",
        "orders",
    }


async def test_aggregates_are_consistent_with_the_detailed_records() -> None:
    provider = MockSalesDataProvider()
    records = (await provider.fetch("sales_records")).rows
    by_region = (await provider.fetch("sales_by_region")).rows
    [summary] = (await provider.fetch("sales_summary")).rows

    total = sum(int(row["revenue"] or 0) for row in records)
    assert len(records) == 4 * 3 * 3
    assert sum(int(row["revenue"] or 0) for row in by_region) == total
    assert summary["total_revenue"] == total
    assert summary["top_region"] == "North"


async def test_fetch_honours_limit_and_returns_copies() -> None:
    provider = MockSalesDataProvider()

    limited = await provider.fetch("sales_records", limit=5)
    limited.rows[0]["region"] = "Tampered"

    assert len(limited.rows) == 5
    assert (await provider.fetch("sales_records")).rows[0]["region"] == "North"


@pytest.mark.parametrize("provider", [MockSalesDataProvider(), EmptyDataProvider()])
async def test_unknown_dataset_raises_not_found(provider: MockSalesDataProvider) -> None:
    with pytest.raises(ResourceNotFoundException, match="payroll"):
        await provider.fetch("payroll")


async def test_empty_provider_has_no_datasets() -> None:
    assert await EmptyDataProvider().list_datasets() == []


@pytest.mark.parametrize(
    "configuration",
    [
        {"password": "hunter2"},
        {"connection": {"api_key": "abc"}},
        {"headers": [{"Authorization": "Bearer abc"}]},
        {"client-secret": "abc"},
    ],
)
def test_configuration_holding_secrets_is_rejected(configuration: dict[str, object]) -> None:
    with pytest.raises(ValidationError, match="Secrets must not be stored"):
        DataSourceCreate(name="Warehouse", type="postgresql", configuration=configuration)  # type: ignore[arg-type]


def test_secret_references_are_allowed() -> None:
    source = DataSourceCreate(
        name="Warehouse",
        type="postgresql",  # type: ignore[arg-type]
        configuration={"host": "db.internal", "port": 5432, "credentials_ref": "warehouse-ro"},
    )

    assert source.configuration["credentials_ref"] == "warehouse-ro"
