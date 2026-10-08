"""Google Programmable Search (Custom Search JSON API) implementation."""

import httpx
from pydantic import SecretStr

from app.ai.search.base import MAX_SEARCH_RESULTS, SearchProvider, SearchQuery, SearchResult
from app.core.exceptions import SearchException
from app.core.logging import get_logger

logger = get_logger(__name__)

GOOGLE_SEARCH_URL = "https://customsearch.googleapis.com/customsearch/v1"


class GoogleSearchProvider(SearchProvider):
    def __init__(
        self,
        *,
        api_key: SecretStr,
        engine_id: str,
        client: httpx.AsyncClient,
        timeout_seconds: float = 10.0,
        url: str = GOOGLE_SEARCH_URL,
    ) -> None:
        self._api_key = api_key
        self._engine_id = engine_id
        self._client = client
        self._timeout = timeout_seconds
        self._url = url

    @property
    def name(self) -> str:
        return "google"

    async def search(self, query: SearchQuery) -> list[SearchResult]:
        params: dict[str, str | int] = {
            "cx": self._engine_id,
            "q": _compose_query(query),
            "num": min(max(query.num_results, 1), MAX_SEARCH_RESULTS),
        }
        # The key travels in a header, not the query string, so it cannot end up in URL logs.
        headers = {"X-Goog-Api-Key": self._api_key.get_secret_value()}
        try:
            response = await self._client.get(
                self._url, params=params, headers=headers, timeout=self._timeout
            )
        except httpx.HTTPError as exc:
            self._log_failure(type(exc).__name__, None)
            raise SearchException() from None
        if response.is_error:
            self._log_failure("http_status", response.status_code)
            raise SearchException()
        return _parse_results(response)

    def _log_failure(self, reason: str, status: int | None) -> None:
        logger.error(
            "search_request_failed",
            extra={"provider": self.name, "reason": reason, "upstream_status": status},
        )


def _compose_query(query: SearchQuery) -> str:
    if not query.include_domains:
        return query.query
    sites = " OR ".join(f"site:{domain}" for domain in query.include_domains)
    return f"{query.query} ({sites})"


def _parse_results(response: httpx.Response) -> list[SearchResult]:
    try:
        items = response.json().get("items", [])
        return [
            SearchResult(
                title=str(item["title"]),
                url=str(item["link"]),
                snippet=str(item.get("snippet", "")),
            )
            for item in items
        ]
    except (ValueError, KeyError, TypeError, AttributeError):
        raise SearchException("The search provider returned an unexpected response.") from None
