import pytest

from app.ai.search.base import SearchProvider, SearchQuery, SearchResult
from app.core.exceptions import (
    ActionNotAllowedException,
    ActionPayloadException,
    ProviderNotConfiguredException,
    ResourceNotFoundException,
)
from app.domains.actions.handlers import NavigateHandler, build_default_action_registry
from app.domains.actions.registry import ActionRegistry
from app.domains.actions.schemas import ActionType
from app.domains.data_sources.providers.mock import MockSalesDataProvider


class StubSearchProvider(SearchProvider):
    def __init__(self) -> None:
        self.queries: list[SearchQuery] = []

    @property
    def name(self) -> str:
        return "stub"

    async def search(self, query: SearchQuery) -> list[SearchResult]:
        self.queries.append(query)
        return [SearchResult("Title", "https://example.com", "Snippet")]


@pytest.fixture
def registry() -> ActionRegistry:
    return build_default_action_registry(MockSalesDataProvider(), search_provider=None)


def test_default_registry_allows_exactly_the_documented_actions(registry: ActionRegistry) -> None:
    assert registry.allowed_types() == frozenset(ActionType)


@pytest.mark.parametrize("action_type", ["delete_database", "eval", "__import__", "FILTER", ""])
async def test_unknown_actions_are_rejected(registry: ActionRegistry, action_type: str) -> None:
    with pytest.raises(ActionNotAllowedException) as error:
        await registry.execute(action_type, {})

    assert error.value.code == "ACTION_NOT_ALLOWED"


async def test_an_action_exists_only_once_registered() -> None:
    registry = ActionRegistry()
    with pytest.raises(ActionNotAllowedException):
        registry.get("navigate")

    registry.register(NavigateHandler())  # type: ignore[arg-type]

    assert await registry.execute("navigate", {"to": "/reports"}) == {"navigate_to": "/reports"}


def test_registering_the_same_action_twice_fails(registry: ActionRegistry) -> None:
    with pytest.raises(ValueError, match="already registered"):
        registry.register(NavigateHandler())  # type: ignore[arg-type]


async def test_payload_is_validated_before_the_handler_runs(registry: ActionRegistry) -> None:
    with pytest.raises(ActionPayloadException) as error:
        await registry.execute("filter", {"dataset": "sales_by_region", "unexpected": 1})

    paths = {detail["path"] for detail in error.value.details}
    assert paths == {"field", "value", "unexpected"}


async def test_filter_returns_matching_rows(registry: ActionRegistry) -> None:
    result = await registry.execute(
        "filter",
        {"dataset": "sales_by_region", "field": "region", "value": "North", "target": "chart"},
    )

    assert [row["region"] for row in result["rows"]] == ["North"]
    assert result["target"] == "chart"


async def test_filter_supports_numeric_comparison(registry: ActionRegistry) -> None:
    result = await registry.execute(
        "filter",
        {"dataset": "sales_by_region", "field": "revenue", "operator": "gt", "value": 4_500_000},
    )

    assert {row["region"] for row in result["rows"]} == {"North", "West"}


async def test_filter_rejects_unknown_fields_and_incomparable_values(
    registry: ActionRegistry,
) -> None:
    with pytest.raises(ActionPayloadException, match="no field 'profit'"):
        await registry.execute(
            "filter", {"dataset": "sales_by_region", "field": "profit", "value": 1}
        )
    with pytest.raises(ActionPayloadException, match="not comparable"):
        await registry.execute(
            "filter",
            {"dataset": "sales_by_region", "field": "revenue", "operator": "gt", "value": "high"},
        )


async def test_sort_orders_rows(registry: ActionRegistry) -> None:
    result = await registry.execute(
        "sort", {"dataset": "sales_by_region", "field": "revenue", "direction": "desc"}
    )

    revenues = [row["revenue"] for row in result["rows"]]
    assert revenues == sorted(revenues, reverse=True)
    assert result["rows"][0]["region"] == "North"


async def test_unknown_dataset_is_reported_as_not_found(registry: ActionRegistry) -> None:
    with pytest.raises(ResourceNotFoundException):
        await registry.execute("refresh", {"dataset": "payroll"})


async def test_export_produces_csv(registry: ActionRegistry) -> None:
    result = await registry.execute("export", {"dataset": "sales_by_region"})

    lines = result["content"].splitlines()
    assert lines[0] == "region,revenue,orders"
    assert len(lines) == 5
    assert result["filename"] == "sales_by_region.csv"


@pytest.mark.parametrize("destination", ["javascript:alert(1)", "//evil.example/x", "ftp://x"])
async def test_navigate_rejects_unsafe_destinations(
    registry: ActionRegistry, destination: str
) -> None:
    with pytest.raises(ActionPayloadException):
        await registry.execute("navigate", {"to": destination})


async def test_search_requires_a_configured_provider(registry: ActionRegistry) -> None:
    with pytest.raises(ProviderNotConfiguredException):
        await registry.execute("search", {"query": "fastapi"})


async def test_search_delegates_to_the_search_provider() -> None:
    search = StubSearchProvider()
    registry = build_default_action_registry(MockSalesDataProvider(), search)

    result = await registry.execute(
        "search", {"query": "fastapi", "num_results": 3, "domains": ["example.com"]}
    )

    assert search.queries == [SearchQuery("fastapi", 3, ("example.com",))]
    assert result["results"] == [
        {"title": "Title", "url": "https://example.com", "snippet": "Snippet"}
    ]
