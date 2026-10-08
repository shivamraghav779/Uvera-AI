"""Provider-agnostic web search contract."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

MAX_SEARCH_RESULTS = 10


@dataclass(frozen=True, slots=True)
class SearchQuery:
    query: str
    num_results: int = 5
    # Restrict results to these domains (e.g. "example.com"); empty means anywhere.
    include_domains: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class SearchResult:
    title: str
    url: str
    snippet: str


class SearchProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Stable identifier of the provider, e.g. ``"google"``."""

    @abstractmethod
    async def search(self, query: SearchQuery) -> list[SearchResult]:
        """Run the query; raise ``SearchException`` when the provider fails."""
