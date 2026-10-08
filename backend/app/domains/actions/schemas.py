"""Action contracts: the allowlisted action types and their payloads."""

import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, JsonValue, field_validator

from app.domains.common import Scalar, StrictModel


class ActionType(StrEnum):
    FILTER = "filter"
    SORT = "sort"
    REFRESH = "refresh"
    NAVIGATE = "navigate"
    SUBMIT = "submit"
    SEARCH = "search"
    GENERATE = "generate"
    EXPORT = "export"
    RECORD_CREATE = "record_create"
    RECORD_UPDATE = "record_update"
    RECORD_DELETE = "record_delete"


class FilterOperator(StrEnum):
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    GREATER_THAN = "gt"
    GREATER_OR_EQUAL = "gte"
    LESS_THAN = "lt"
    LESS_OR_EQUAL = "lte"


class SortDirection(StrEnum):
    ASCENDING = "asc"
    DESCENDING = "desc"


class ExportFormat(StrEnum):
    CSV = "csv"
    JSON = "json"


class ActionPayload(StrictModel):
    """Base payload. ``target`` names the UI component the result applies to."""

    target: str | None = Field(default=None, max_length=64)


class DatasetActionPayload(ActionPayload):
    dataset: str = Field(min_length=1, max_length=64)


class FilterPayload(DatasetActionPayload):
    field: str = Field(min_length=1, max_length=64)
    operator: FilterOperator = FilterOperator.EQUALS
    value: Scalar


class SortPayload(DatasetActionPayload):
    field: str = Field(min_length=1, max_length=64)
    direction: SortDirection = SortDirection.ASCENDING


class RefreshPayload(DatasetActionPayload):
    pass


class ExportPayload(DatasetActionPayload):
    format: ExportFormat = ExportFormat.CSV


def is_safe_navigation_target(destination: str) -> bool:
    """Allow in-app paths and https links; never script or protocol-relative URLs."""
    if destination.startswith("/"):
        return not destination.startswith("//")
    return destination.startswith("https://")


class NavigatePayload(ActionPayload):
    to: str = Field(min_length=1, max_length=2000)
    from_field: str | None = Field(default=None, max_length=64)

    @field_validator("to")
    @classmethod
    def _require_safe_destination(cls, value: str) -> str:
        if not is_safe_navigation_target(value):
            raise ValueError("Destination must be an in-app path ('/...') or an https URL.")
        return value


class SubmitPayload(ActionPayload):
    form_id: str = Field(min_length=1, max_length=64)
    values: dict[str, Scalar] = Field(default_factory=dict)


class SearchPayload(ActionPayload):
    query: str = Field(min_length=1, max_length=400)
    num_results: int = Field(default=5, ge=1, le=10)
    domains: list[str] = Field(default_factory=list, max_length=10)


class GeneratePayload(ActionPayload):
    message: str = Field(min_length=1, max_length=8000)


class RecordPayload(ActionPayload):
    """Addresses the records of one application entity."""

    entity: str = Field(min_length=1, max_length=64)
    navigate_to: str | None = Field(default=None, max_length=200)

    @field_validator("navigate_to")
    @classmethod
    def _require_in_app_destination(cls, value: str | None) -> str | None:
        if value is not None and not (value.startswith("/") and not value.startswith("//")):
            raise ValueError("navigate_to must be an in-app path ('/...').")
        return value


class RecordCreatePayload(RecordPayload):
    values: dict[str, Scalar] = Field(default_factory=dict, max_length=60)


class RecordUpdatePayload(RecordPayload):
    record_id: str = Field(min_length=1, max_length=128)
    values: dict[str, Scalar] = Field(min_length=1, max_length=60)


class RecordDeletePayload(RecordPayload):
    record_id: str = Field(min_length=1, max_length=128)


class ActionExecuteRequest(BaseModel):
    workspace_id: uuid.UUID
    # Deliberately a plain string: the action registry, not the request schema,
    # decides what is allowed.
    action_type: str = Field(min_length=1, max_length=64, examples=["filter"])
    payload: dict[str, JsonValue] = Field(
        default_factory=dict,
        examples=[{"dataset": "sales_by_region", "field": "region", "value": "North"}],
    )


class FormSubmissionRead(BaseModel):
    """One stored form submission."""

    id: uuid.UUID
    form_id: str
    values: dict[str, Scalar]
    submitted_at: datetime


class ActionExecuteResponse(BaseModel):
    action_id: uuid.UUID
    workspace_id: uuid.UUID
    action_type: ActionType
    result: dict[str, Any]
