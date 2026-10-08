"""Builds the provider that reads a registered data source."""

import os
from typing import Any, Protocol

import httpx

from app.core.exceptions import DataSourceException
from app.domains.data_sources.models import DataSource
from app.domains.data_sources.providers.base import DataProvider, EmptyDataProvider
from app.domains.data_sources.providers.inline import InlineDataProvider
from app.domains.data_sources.providers.rest import (
    HostCheck,
    RestApiDataProvider,
    allow_any_host,
    reject_private_hosts,
)
from app.domains.data_sources.providers.sql import PostgresQueryDataProvider, QueryDataset
from app.domains.data_sources.schemas import DataSourceType

SECRET_ENV_PREFIX = "DATASOURCE_SECRET_"


class SecretResolver(Protocol):
    def resolve(self, reference: str) -> str | None:
        """The secret behind ``reference``, or ``None`` if the server does not hold it."""
        ...


class EnvSecretResolver:
    """Reads data source secrets from ``DATASOURCE_SECRET_<REFERENCE>`` environment variables.

    Secrets therefore never enter the application database. Swap this for a
    secret-manager client without touching the providers.
    """

    def resolve(self, reference: str) -> str | None:
        return os.environ.get(f"{SECRET_ENV_PREFIX}{reference.upper()}") or None


class DataProviderFactory:
    def __init__(
        self,
        *,
        http_client: httpx.AsyncClient,
        secrets: SecretResolver,
        timeout_seconds: float,
        allow_private_hosts: bool = False,
    ) -> None:
        self._http_client = http_client
        self._secrets = secrets
        self._timeout = timeout_seconds
        self._check_host: HostCheck = (
            allow_any_host if allow_private_hosts else reject_private_hosts
        )

    def build(self, source: DataSource) -> DataProvider:
        """Provider for one stored source. ``configuration`` is in the stored form."""
        config: dict[str, Any] = source.configuration
        kind = DataSourceType(source.type)
        if kind is DataSourceType.FILE_UPLOAD:
            return InlineDataProvider(
                config["dataset"], config["description"], config["rows"], config.get("columns")
            )
        if kind is DataSourceType.REST_API:
            return self._rest(config)
        if kind is DataSourceType.POSTGRESQL:
            return self._postgres(config)
        # A registered "mock" source adds nothing: demo data is switched on by configuration.
        return EmptyDataProvider()

    def _secret(self, reference: str) -> str:
        secret = self._secrets.resolve(reference)
        if secret is None:
            raise DataSourceException(
                f"The server has no secret named '{reference}'. "
                f"Set the environment variable {SECRET_ENV_PREFIX}{reference.upper()}."
            )
        return secret

    def _rest(self, config: dict[str, Any]) -> DataProvider:
        headers = {"Accept": "application/json"}
        if config.get("credentials_ref"):
            headers["Authorization"] = (
                f"{config['auth_scheme']} {self._secret(config['credentials_ref'])}"
            )
        return RestApiDataProvider(
            name=config["dataset"],
            description=config["description"],
            url=config["url"],
            records_path=config.get("records_path"),
            headers=headers,
            client=self._http_client,
            timeout_seconds=self._timeout,
            check_host=self._check_host,
        )

    def _postgres(self, config: dict[str, Any]) -> DataProvider:
        return PostgresQueryDataProvider(
            dsn=self._secret(config["credentials_ref"]),
            datasets=[
                QueryDataset(item["name"], item["description"], item["query"])
                for item in config["datasets"]
            ],
            timeout_seconds=self._timeout,
        )
