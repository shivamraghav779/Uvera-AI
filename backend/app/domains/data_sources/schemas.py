import re
import uuid
from datetime import datetime
from enum import StrEnum
from typing import Annotated

from pydantic import AfterValidator, BaseModel, Field, JsonValue, field_validator

from app.core.security import find_sensitive_keys
from app.domains.common import DataRow, StrictModel


class DataSourceType(StrEnum):
    MOCK = "mock"
    POSTGRESQL = "postgresql"
    REST_API = "rest_api"
    FILE_UPLOAD = "file_upload"


DatasetName = Annotated[
    str,
    Field(
        pattern=r"^[a-z][a-z0-9_]{0,63}$",
        description="Lower-case identifier the UI refers to, e.g. `support_tickets`.",
    ),
]
SecretRef = Annotated[
    str,
    Field(
        pattern=r"^[A-Za-z][A-Za-z0-9_]{0,63}$",
        description=(
            "Name of a secret held by the server (environment variable "
            "`DATASOURCE_SECRET_<NAME>`). The secret itself is never stored or returned."
        ),
    ),
]
MAX_UPLOAD_CHARACTERS = 1_000_000


class UploadFormat(StrEnum):
    CSV = "csv"
    JSON = "json"


class FileUploadConfig(StrictModel):
    """Rows pasted or uploaded as CSV or JSON. Parsed once and stored with the source."""

    dataset: DatasetName
    description: str = Field(default="Uploaded dataset.", max_length=300)
    format: UploadFormat = UploadFormat.CSV
    content: str = Field(min_length=1, max_length=MAX_UPLOAD_CHARACTERS)


class RestApiConfig(StrictModel):
    """A JSON API returning a list of records (optionally nested under `records_path`)."""

    dataset: DatasetName
    description: str = Field(default="Records from a REST API.", max_length=300)
    url: str = Field(max_length=2000, pattern=r"^https://", description="HTTPS only.")
    records_path: str | None = Field(default=None, max_length=200, examples=["data.items"])
    credentials_ref: SecretRef | None = None
    auth_scheme: str = Field(default="Bearer", pattern=r"^[A-Za-z]{1,20}$")


def _require_single_select(query: str) -> str:
    statement = query.strip().rstrip(";").strip()
    if ";" in statement:
        raise ValueError("Only a single statement is allowed.")
    if not re.match(r"(?is)^(select|with)\b", statement):
        raise ValueError("Only SELECT queries are allowed.")
    return statement


class QueryDatasetConfig(StrictModel):
    name: DatasetName
    description: str = Field(default="Result of a SQL query.", max_length=300)
    query: Annotated[
        str, Field(min_length=1, max_length=5000), AfterValidator(_require_single_select)
    ]


class PostgresConfig(StrictModel):
    """Read-only queries against an external PostgreSQL database."""

    credentials_ref: SecretRef = Field(description="Secret holding the connection string (DSN).")
    datasets: list[QueryDatasetConfig] = Field(min_length=1, max_length=20)


class MockConfig(StrictModel):
    pass


CONFIG_MODELS: dict[DataSourceType, type[StrictModel]] = {
    DataSourceType.FILE_UPLOAD: FileUploadConfig,
    DataSourceType.REST_API: RestApiConfig,
    DataSourceType.POSTGRESQL: PostgresConfig,
    DataSourceType.MOCK: MockConfig,
}


class DataSourceCreate(StrictModel):
    name: str = Field(min_length=1, max_length=120, examples=["Support tickets"])
    type: DataSourceType
    configuration: dict[str, JsonValue] = Field(
        default_factory=dict,
        description=(
            "Settings for the chosen type (see FileUploadConfig, RestApiConfig, PostgresConfig). "
            "Credentials are never accepted here: reference a server-side secret with "
            "`credentials_ref`."
        ),
        examples=[
            {"dataset": "tickets", "format": "csv", "content": "id,status\n1,open\n2,closed"},
            {
                "dataset": "orders",
                "url": "https://api.example.com/orders",
                "credentials_ref": "ORDERS_API",
            },
        ],
    )

    @field_validator("configuration")
    @classmethod
    def _reject_secrets(cls, value: dict[str, JsonValue]) -> dict[str, JsonValue]:
        offending = sorted(find_sensitive_keys(value))
        if offending:
            raise ValueError(
                "Secrets must not be stored in data source configuration "
                f"(offending keys: {', '.join(offending)}). Use a secret reference instead."
            )
        return value


class DataSourceRead(BaseModel):
    id: uuid.UUID
    name: str
    type: DataSourceType
    datasets: list[str] = Field(description="Names of the datasets this source provides.")
    created_at: datetime
    updated_at: datetime


class FieldKind(StrEnum):
    STRING = "string"
    NUMBER = "number"


class DatasetField(StrictModel):
    name: str
    kind: FieldKind


class DatasetDescriptor(StrictModel):
    """What a dataset contains, without its rows."""

    name: str
    description: str
    fields: list[DatasetField]

    @property
    def field_names(self) -> frozenset[str]:
        return frozenset(field.name for field in self.fields)


class DatasetSnapshot(StrictModel):
    """A dataset's descriptor together with (possibly truncated) rows."""

    descriptor: DatasetDescriptor
    rows: list[DataRow]
