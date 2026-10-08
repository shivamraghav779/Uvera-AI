"""Application exception hierarchy.

Every failure a client can see is an ``AppException`` with a stable,
machine-readable ``code`` and an HTTP status. Lower layers translate what they
catch into one of these as close to the source as possible:

    database driver errors   -> ``translate_database_error`` (middleware/error_handler.py)
    LLM HTTP/transport errors -> ``LLMException`` with an ``LLMFailureKind`` (ai/llm/http.py)
    search / data source I/O  -> ``SearchException`` / ``DataSourceException``
    bad or expired tokens     -> ``AuthenticationException`` subclasses

Anything that is *not* an ``AppException`` when it reaches the edge is an
unexpected failure: it is logged with its stack trace and reported to the
client as a generic ``INTERNAL_ERROR``.
"""

from collections.abc import Mapping, Sequence
from enum import StrEnum
from typing import ClassVar

ErrorDetail = Mapping[str, object]


class ErrorCode(StrEnum):
    # Generic
    INTERNAL_ERROR = "INTERNAL_ERROR"
    HTTP_ERROR = "HTTP_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    CONFLICT = "CONFLICT"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    # Identity and access
    AUTHENTICATION_REQUIRED = "AUTHENTICATION_REQUIRED"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    INVALID_TOKEN = "INVALID_TOKEN"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    EMAIL_ALREADY_REGISTERED = "EMAIL_ALREADY_REGISTERED"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    # Database
    DATABASE_ERROR = "DATABASE_ERROR"
    DATABASE_SCHEMA_OUTDATED = "DATABASE_SCHEMA_OUTDATED"
    DATABASE_UNAVAILABLE = "DATABASE_UNAVAILABLE"
    STORED_DATA_INVALID = "STORED_DATA_INVALID"
    # External providers
    PROVIDER_ERROR = "PROVIDER_ERROR"
    PROVIDER_NOT_CONFIGURED = "PROVIDER_NOT_CONFIGURED"
    LLM_ERROR = "LLM_ERROR"
    LLM_ALL_PROVIDERS_FAILED = "LLM_ALL_PROVIDERS_FAILED"
    SEARCH_ERROR = "SEARCH_ERROR"
    DATA_SOURCE_ERROR = "DATA_SOURCE_ERROR"
    ASSET_ERROR = "ASSET_ERROR"
    REFERENCE_IMPORT_ERROR = "REFERENCE_IMPORT_ERROR"
    GENERATION_JOB_FAILED = "GENERATION_JOB_FAILED"
    # Generative UI
    UI_SCHEMA_INVALID = "UI_SCHEMA_INVALID"
    VERSION_CONFLICT = "VERSION_CONFLICT"
    ACTION_NOT_ALLOWED = "ACTION_NOT_ALLOWED"
    ACTION_PAYLOAD_INVALID = "ACTION_PAYLOAD_INVALID"


class AppException(Exception):  # noqa: N818 - public name fixed by the API contract
    status_code: ClassVar[int] = 500
    code: ClassVar[ErrorCode] = ErrorCode.INTERNAL_ERROR
    default_message: ClassVar[str] = "An unexpected error occurred."

    def __init__(
        self,
        message: str | None = None,
        *,
        details: Sequence[ErrorDetail] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> None:
        self.message = message or self.default_message
        self.details: tuple[ErrorDetail, ...] = tuple(details or ())
        # Extra response headers, e.g. Retry-After or WWW-Authenticate.
        self.headers: dict[str, str] = dict(headers or {})
        super().__init__(self.message)


# --- Requests -------------------------------------------------------------------


class ValidationException(AppException):
    status_code = 422
    code = ErrorCode.VALIDATION_ERROR
    default_message = "The request is invalid."


class ResourceNotFoundException(AppException):
    status_code = 404
    code = ErrorCode.RESOURCE_NOT_FOUND
    default_message = "The requested resource was not found."

    @classmethod
    def for_resource(cls, resource: str, identifier: object) -> "ResourceNotFoundException":
        return cls(f"{resource} '{identifier}' was not found.")


class ConflictException(AppException):
    """The request is well-formed but clashes with the current state."""

    status_code = 409
    code = ErrorCode.CONFLICT
    default_message = "The change conflicts with existing data."


# --- Identity and access --------------------------------------------------------

_BEARER_CHALLENGE = {"WWW-Authenticate": "Bearer"}


class AuthenticationException(AppException):
    status_code = 401
    code = ErrorCode.AUTHENTICATION_REQUIRED
    default_message = "Authentication is required."

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message, headers=_BEARER_CHALLENGE)


class InvalidCredentialsException(AuthenticationException):
    code = ErrorCode.INVALID_CREDENTIALS
    # Deliberately does not say whether the email or the password was wrong.
    default_message = "Incorrect email or password."


class InvalidTokenException(AuthenticationException):
    code = ErrorCode.INVALID_TOKEN
    default_message = "The access token is invalid."


class TokenExpiredException(AuthenticationException):
    code = ErrorCode.TOKEN_EXPIRED
    default_message = "The access token has expired. Sign in again."


class PermissionDeniedException(AppException):
    status_code = 403
    code = ErrorCode.PERMISSION_DENIED
    default_message = "You are not allowed to do this."


class EmailAlreadyRegisteredException(ConflictException):
    code = ErrorCode.EMAIL_ALREADY_REGISTERED
    default_message = "An account with this email already exists."


class RateLimitExceededException(AppException):
    status_code = 429
    code = ErrorCode.RATE_LIMIT_EXCEEDED
    default_message = "Too many requests. Please slow down."

    def __init__(self, retry_after_seconds: int) -> None:
        super().__init__(headers={"Retry-After": str(max(retry_after_seconds, 1))})
        self.retry_after_seconds = retry_after_seconds


# --- Database -------------------------------------------------------------------


class DatabaseException(AppException):
    """A database operation failed for a reason the client cannot fix."""

    code = ErrorCode.DATABASE_ERROR
    default_message = "A database error occurred."


class DatabaseUnavailableException(DatabaseException):
    """The database cannot be reached or has no capacity right now. Retrying may help."""

    status_code = 503
    code = ErrorCode.DATABASE_UNAVAILABLE
    default_message = "The database is temporarily unavailable. Please try again."

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message, headers={"Retry-After": "5"})


class DatabaseSchemaOutdatedException(DatabaseException):
    """A table or column the application expects is missing: migrations have not been run."""

    status_code = 503
    code = ErrorCode.DATABASE_SCHEMA_OUTDATED
    default_message = (
        "The database schema is not up to date. An administrator needs to run the "
        "migrations (alembic upgrade head)."
    )


class StoredDataException(DatabaseException):
    """A stored record no longer matches the schema the application understands."""

    code = ErrorCode.STORED_DATA_INVALID
    default_message = "Stored data could not be read."


class ServiceUnavailableException(AppException):
    status_code = 503
    code = ErrorCode.SERVICE_UNAVAILABLE
    default_message = "A dependency is temporarily unavailable. Please try again."

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message, headers={"Retry-After": "5"})


# --- External providers -----------------------------------------------------------


class ProviderException(AppException):
    """An external provider (LLM, search, data source) failed."""

    status_code = 502
    code = ErrorCode.PROVIDER_ERROR
    default_message = "An upstream provider request failed."


class ProviderNotConfiguredException(ProviderException):
    status_code = 503
    code = ErrorCode.PROVIDER_NOT_CONFIGURED
    default_message = "The required provider is not configured."


class LLMFailureKind(StrEnum):
    """Why one call to one LLM provider failed."""

    TIMEOUT = "timeout"
    TRANSPORT = "transport"  # connection refused/reset, DNS, TLS
    RATE_LIMITED = "rate_limited"  # HTTP 429
    UNAVAILABLE = "unavailable"  # HTTP 5xx
    AUTHENTICATION = "authentication"  # HTTP 401/403: bad or revoked key
    BAD_REQUEST = "bad_request"  # other HTTP 4xx: the request itself was refused
    BAD_RESPONSE = "bad_response"  # 2xx with a body that cannot be used


_RETRYABLE_LLM_FAILURES = frozenset(
    {
        LLMFailureKind.TIMEOUT,
        LLMFailureKind.TRANSPORT,
        LLMFailureKind.RATE_LIMITED,
        LLMFailureKind.UNAVAILABLE,
    }
)


class LLMException(ProviderException):
    """A single LLM provider call failed.

    ``reason`` is kept for logs; the client-facing message stays generic so
    upstream error text is never echoed to callers.
    """

    code = ErrorCode.LLM_ERROR
    default_message = "The language model request failed."

    def __init__(
        self,
        *,
        provider: str,
        model: str,
        kind: LLMFailureKind,
        reason: str,
        upstream_status: int | None = None,
        retry_after_seconds: float | None = None,
    ) -> None:
        super().__init__()
        self.provider = provider
        self.model = model
        self.kind = kind
        self.reason = reason
        self.upstream_status = upstream_status
        # How long the provider asked callers to wait (rate limits), when it said so.
        self.retry_after_seconds = retry_after_seconds

    @property
    def retryable(self) -> bool:
        """Whether the same request might succeed if sent again."""
        return self.kind in _RETRYABLE_LLM_FAILURES


class LLMProvidersExhaustedException(ProviderException):
    code = ErrorCode.LLM_ALL_PROVIDERS_FAILED
    default_message = "All configured language model providers failed."


class SearchException(ProviderException):
    code = ErrorCode.SEARCH_ERROR
    default_message = "The search request failed."


class DataSourceException(ProviderException):
    """A connected data source could not be read."""

    code = ErrorCode.DATA_SOURCE_ERROR
    default_message = "The data source could not be read."


# --- Generative UI -----------------------------------------------------------------


class ReferenceImportException(ProviderException):
    """A source of reference components could not be read."""

    code = ErrorCode.REFERENCE_IMPORT_ERROR
    default_message = "The reference components could not be imported."


class AssetException(ProviderException):
    """An image could not be generated, found or stored."""

    code = ErrorCode.ASSET_ERROR
    default_message = "The image could not be prepared."


class UIValidationException(AppException):
    status_code = 422
    code = ErrorCode.UI_SCHEMA_INVALID
    default_message = "The UI schema is invalid."


class UIGenerationException(UIValidationException):
    """The model could not produce a valid UI schema, even after repair."""

    status_code = 502
    default_message = "Generated UI schema is invalid."


class VersionConflictException(ConflictException):
    """A write was based on a version that is no longer the workspace's current one."""

    code = ErrorCode.VERSION_CONFLICT
    default_message = "The workspace has changed since this change was prepared."


class ActionNotAllowedException(AppException):
    status_code = 403
    code = ErrorCode.ACTION_NOT_ALLOWED
    default_message = "This action is not allowed."


class ActionPayloadException(ValidationException):
    code = ErrorCode.ACTION_PAYLOAD_INVALID
    default_message = "The action payload is invalid."
