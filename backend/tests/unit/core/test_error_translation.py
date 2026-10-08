"""Every kind of low-level failure must surface as a coded application error."""

import pytest
from sqlalchemy.exc import (
    DataError,
    IntegrityError,
    InterfaceError,
    NoResultFound,
    OperationalError,
    ProgrammingError,
)
from sqlalchemy.exc import TimeoutError as PoolTimeoutError

from app.ai.llm.http import failure_kind_for_status
from app.core.exceptions import (
    AppException,
    ErrorCode,
    LLMException,
    LLMFailureKind,
)
from app.middleware.error_handler import translate_database_error


def _dbapi(error_class: type, connection_invalidated: bool = False) -> Exception:
    return error_class(  # type: ignore[no-any-return]
        "SELECT secret FROM t",
        {"p": 1},
        Exception("driver detail"),
        connection_invalidated=connection_invalidated,
    )


@pytest.mark.parametrize(
    ("error", "code", "status"),
    [
        (_dbapi(IntegrityError), ErrorCode.CONFLICT, 409),
        (_dbapi(OperationalError), ErrorCode.DATABASE_UNAVAILABLE, 503),
        (_dbapi(InterfaceError), ErrorCode.DATABASE_UNAVAILABLE, 503),
        (PoolTimeoutError("QueuePool limit reached"), ErrorCode.DATABASE_UNAVAILABLE, 503),
        (
            _dbapi(ProgrammingError, connection_invalidated=True),
            ErrorCode.DATABASE_UNAVAILABLE,
            503,
        ),
        (_dbapi(ProgrammingError), ErrorCode.DATABASE_ERROR, 500),
        (_dbapi(DataError), ErrorCode.DATABASE_ERROR, 500),
        (NoResultFound("no row"), ErrorCode.DATABASE_ERROR, 500),
    ],
    ids=lambda value: type(value).__name__ if isinstance(value, Exception) else str(value),
)
def test_database_errors_map_to_coded_application_errors(
    error: Exception, code: ErrorCode, status: int
) -> None:
    translated = translate_database_error(error)  # type: ignore[arg-type]

    assert (translated.code, translated.status_code) == (code, status)
    assert "SELECT" not in translated.message and "driver detail" not in translated.message
    if status == 503:
        assert translated.headers == {"Retry-After": "5"}, "transient failures say when to retry"


@pytest.mark.parametrize(
    ("status", "kind", "retryable"),
    [
        (400, LLMFailureKind.BAD_REQUEST, False),
        (401, LLMFailureKind.AUTHENTICATION, False),
        (403, LLMFailureKind.AUTHENTICATION, False),
        (404, LLMFailureKind.BAD_REQUEST, False),
        (408, LLMFailureKind.TIMEOUT, True),
        (429, LLMFailureKind.RATE_LIMITED, True),
        (500, LLMFailureKind.UNAVAILABLE, True),
        (503, LLMFailureKind.UNAVAILABLE, True),
    ],
)
def test_llm_http_statuses_are_classified(
    status: int, kind: LLMFailureKind, retryable: bool
) -> None:
    error = LLMException(provider="p", model="m", kind=failure_kind_for_status(status), reason="x")

    assert (error.kind, error.retryable) == (kind, retryable)


def test_every_application_error_has_a_distinct_purpose() -> None:
    """Each concrete exception class maps to a code and an HTTP status a client can act on."""

    def subclasses(cls: type) -> list[type]:
        return [sub for child in cls.__subclasses__() for sub in (child, *subclasses(child))]

    for exception_class in subclasses(AppException):
        assert isinstance(exception_class.code, ErrorCode), exception_class
        assert 400 <= exception_class.status_code <= 599, exception_class
        assert exception_class.default_message, exception_class


@pytest.mark.parametrize("sqlstate", ["42P01", "42703"])
def test_missing_table_or_column_says_migrations_are_needed(sqlstate: str) -> None:
    driver_error = Exception('relation "users" does not exist')
    driver_error.sqlstate = sqlstate  # type: ignore[attr-defined]
    error = ProgrammingError("SELECT secret FROM users", {"p": 1}, driver_error)

    translated = translate_database_error(error)

    assert (translated.code, translated.status_code) == (ErrorCode.DATABASE_SCHEMA_OUTDATED, 503)
    assert "alembic upgrade head" in translated.message
    assert "SELECT" not in translated.message and "users" not in translated.message
