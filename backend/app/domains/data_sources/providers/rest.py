"""A dataset served by an HTTPS JSON API."""

import asyncio
import ipaddress
import socket
from collections.abc import Awaitable, Callable
from urllib.parse import urlsplit

import httpx

from app.core.exceptions import DataSourceException, ResourceNotFoundException
from app.core.logging import get_logger
from app.domains.common import DataRow
from app.domains.data_sources.providers.base import DataProvider
from app.domains.data_sources.providers.rows import describe, normalise_rows, snapshot
from app.domains.data_sources.schemas import DatasetDescriptor, DatasetSnapshot

logger = get_logger(__name__)

HostCheck = Callable[[str], Awaitable[None]]


async def reject_private_hosts(host: str) -> None:
    """Refuse hosts that resolve to private, loopback or link-local addresses.

    The server makes this request on a user's behalf, so without this check a
    data source could be pointed at internal services (SSRF).
    """
    try:
        infos = await asyncio.get_running_loop().getaddrinfo(host, None, type=socket.SOCK_STREAM)
    except OSError:
        raise DataSourceException(f"The host '{host}' could not be resolved.") from None
    for info in infos:
        address = ipaddress.ip_address(info[4][0])
        if not address.is_global:
            raise DataSourceException("Data sources may only call public internet addresses.")


async def allow_any_host(host: str) -> None:
    return None


def _dig(document: object, path: str | None) -> object:
    """Follow a dotted path (e.g. ``data.items``) into a JSON document."""
    for key in filter(None, (path or "").split(".")):
        if not isinstance(document, dict) or key not in document:
            raise DataSourceException(f"The response has no '{path}' to read records from.")
        document = document[key]
    return document


class RestApiDataProvider(DataProvider):
    def __init__(
        self,
        *,
        name: str,
        description: str,
        url: str,
        records_path: str | None,
        headers: dict[str, str],
        client: httpx.AsyncClient,
        timeout_seconds: float,
        check_host: HostCheck = reject_private_hosts,
    ) -> None:
        self._name = name
        self._description = description
        self._url = url
        self._records_path = records_path
        self._headers = headers
        self._client = client
        self._timeout = timeout_seconds
        self._check_host = check_host
        self._rows: list[DataRow] | None = None

    async def list_datasets(self) -> list[DatasetDescriptor]:
        return [describe(self._name, self._description, await self._load())]

    async def fetch(self, dataset: str, *, limit: int | None = None) -> DatasetSnapshot:
        if dataset != self._name:
            raise ResourceNotFoundException.for_resource("Dataset", dataset)
        return snapshot(self._name, self._description, await self._load(), limit)

    async def _load(self) -> list[DataRow]:
        # Fetched once per provider instance, i.e. once per request.
        if self._rows is None:
            self._rows = await self._request()
        return self._rows

    async def _request(self) -> list[DataRow]:
        await self._check_host(urlsplit(self._url).hostname or "")
        try:
            response = await self._client.get(
                self._url, headers=self._headers, timeout=self._timeout, follow_redirects=False
            )
        except httpx.TimeoutException:
            raise self._failure("timeout", "The data source took too long to respond.") from None
        except httpx.HTTPError as exc:
            raise self._failure(
                type(exc).__name__, "The data source could not be reached."
            ) from None
        if response.is_error or response.is_redirect:
            raise self._failure(
                f"HTTP {response.status_code}",
                f"The data source answered with HTTP {response.status_code}.",
            )
        try:
            records = _dig(response.json(), self._records_path)
        except ValueError:
            raise self._failure("not JSON", "The data source did not return JSON.") from None
        if not isinstance(records, list):
            raise self._failure("not a list", "The data source did not return a list of records.")
        return normalise_rows(records)

    def _failure(self, reason: str, message: str) -> DataSourceException:
        logger.warning(
            "data_source_request_failed", extra={"dataset": self._name, "reason": reason}
        )
        return DataSourceException(message)
