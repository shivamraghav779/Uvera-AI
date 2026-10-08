import httpx
import pytest
from pydantic import SecretStr

from app.ai.search.base import SearchQuery, SearchResult
from app.ai.search.google import GoogleSearchProvider
from app.core.exceptions import SearchException

API_KEY = "google-secret-key"
RESULTS = {
    "items": [
        {"title": "FastAPI", "link": "https://fastapi.tiangolo.com", "snippet": "Web framework"},
        {"title": "No snippet", "link": "https://example.com"},
    ]
}


def _provider(handler: httpx.MockTransport) -> GoogleSearchProvider:
    return GoogleSearchProvider(
        api_key=SecretStr(API_KEY),
        engine_id="engine-1",
        client=httpx.AsyncClient(transport=handler),
    )


async def test_search_returns_structured_results_and_keeps_the_key_out_of_the_url() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json=RESULTS)

    results = await _provider(httpx.MockTransport(handler)).search(
        SearchQuery("fastapi docs", num_results=2)
    )

    assert results == [
        SearchResult("FastAPI", "https://fastapi.tiangolo.com", "Web framework"),
        SearchResult("No snippet", "https://example.com", ""),
    ]
    [request] = seen
    assert dict(request.url.params) == {"cx": "engine-1", "q": "fastapi docs", "num": "2"}
    assert API_KEY not in str(request.url)
    assert request.headers["x-goog-api-key"] == API_KEY


async def test_domain_filter_and_result_cap_are_applied() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={})

    query = SearchQuery("pricing", num_results=50, include_domains=("a.com", "b.org"))
    results = await _provider(httpx.MockTransport(handler)).search(query)

    assert results == []
    assert seen[0].url.params["q"] == "pricing (site:a.com OR site:b.org)"
    assert seen[0].url.params["num"] == "10"


@pytest.mark.parametrize("status", [403, 500])
async def test_upstream_errors_become_search_exceptions(status: int) -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(status, json={"error": API_KEY}))

    with pytest.raises(SearchException) as error:
        await _provider(transport).search(SearchQuery("anything"))

    assert API_KEY not in error.value.message
