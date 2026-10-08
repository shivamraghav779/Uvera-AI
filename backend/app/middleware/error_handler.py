"""Centralised error handling: every failure leaves as the same JSON envelope."""

from collections.abc import Sequence
from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import (
    DBAPIError,
    DisconnectionError,
    IntegrityError,
    InterfaceError,
    OperationalError,
    SQLAlchemyError,
)
from sqlalchemy.exc import TimeoutError as PoolTimeoutError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.api.schemas import ErrorBody, ErrorResponse
from app.core.context import get_request_id
from app.core.exceptions import (
    AppException,
    ConflictException,
    DatabaseException,
    DatabaseSchemaOutdatedException,
    DatabaseUnavailableException,
    ErrorCode,
    ErrorDetail,
    LLMException,
    ServiceUnavailableException,
)
from app.core.logging import get_logger

logger = get_logger(__name__)

_SERVER_ERROR = 500
_HTTP_STATUS_CODES: dict[int, ErrorCode] = {
    401: ErrorCode.AUTHENTICATION_REQUIRED,
    403: ErrorCode.PERMISSION_DENIED,
    404: ErrorCode.RESOURCE_NOT_FOUND,
    409: ErrorCode.CONFLICT,
    429: ErrorCode.RATE_LIMIT_EXCEEDED,
    503: ErrorCode.SERVICE_UNAVAILABLE,
}
# Driver-level failures that mean "cannot talk to the database right now".
_CONNECTIVITY_ERRORS = (OperationalError, InterfaceError, DisconnectionError, PoolTimeoutError)


def error_response(
    *,
    status_code: int,
    code: str,
    message: str,
    details: Sequence[ErrorDetail] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    body = ErrorResponse(
        error=ErrorBody(
            code=code,
            message=message,
            request_id=get_request_id(),
            details=[dict(detail) for detail in details] if details else None,
        )
    )
    return JSONResponse(
        status_code=status_code, content=body.model_dump(exclude_none=True), headers=headers
    )


def app_error_response(exc: AppException) -> JSONResponse:
    return error_response(
        status_code=exc.status_code,
        code=exc.code.value,
        message=exc.message,
        details=exc.details,
        headers=exc.headers,
    )


# PostgreSQL: undefined_table, undefined_column. The code is ahead of the migrations.
_MISSING_SCHEMA_SQLSTATES = frozenset({"42P01", "42703"})


def translate_database_error(error: SQLAlchemyError) -> AppException:
    """Map a SQLAlchemy/driver error to the application error a client should see.

    Driver messages can contain SQL and values, so they are logged by the
    caller and never placed in the response.
    """
    if isinstance(error, IntegrityError):
        # Unique/foreign-key/check violation: the request clashes with stored data.
        return ConflictException()
    if isinstance(error, _CONNECTIVITY_ERRORS):
        return DatabaseUnavailableException()
    if isinstance(error, DBAPIError) and error.connection_invalidated:
        return DatabaseUnavailableException()
    if getattr(getattr(error, "orig", None), "sqlstate", None) in _MISSING_SCHEMA_SQLSTATES:
        return DatabaseSchemaOutdatedException()
    return DatabaseException()


async def _handle_app_exception(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, AppException)
    fields: dict[str, object] = {"code": exc.code.value, "status_code": exc.status_code}
    if isinstance(exc, LLMException):
        fields |= {
            "provider": exc.provider,
            "model": exc.model,
            "failure_kind": exc.kind.value,
            "reason": exc.reason,
        }
    log = logger.error if exc.status_code >= _SERVER_ERROR else logger.warning
    log("request_failed", extra=fields)
    return app_error_response(exc)


async def _handle_database_error(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, SQLAlchemyError)
    translated = translate_database_error(exc)
    constraint = getattr(getattr(exc, "orig", None), "constraint_name", None)
    logger.error(
        "database_error",
        extra={
            "code": translated.code.value,
            "error_type": type(exc).__name__,
            "driver_error_type": type(getattr(exc, "orig", None)).__name__,
            "constraint": constraint,
        },
        # Full detail (including the statement) goes to the log only.
        exc_info=translated.status_code == _SERVER_ERROR,
    )
    return app_error_response(translated)


async def _handle_connection_error(request: Request, exc: Exception) -> JSONResponse:
    """A dependency refused or dropped a connection outside any wrapped call (e.g. the
    database driver failing before SQLAlchemy could wrap the error)."""
    logger.error("dependency_unreachable", extra={"error_type": type(exc).__name__})
    return app_error_response(ServiceUnavailableException())


async def _handle_request_validation(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    # Inputs are deliberately not echoed back or logged.
    details = [
        {"path": ".".join(str(part) for part in error["loc"]), "message": error["msg"]}
        for error in exc.errors()
    ]
    logger.warning("request_validation_failed", extra={"issue_count": len(details)})
    return error_response(
        status_code=422,
        code=ErrorCode.VALIDATION_ERROR.value,
        message="The request is invalid.",
        details=details,
    )


async def _handle_http_exception(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, StarletteHTTPException)
    code = _HTTP_STATUS_CODES.get(exc.status_code, ErrorCode.HTTP_ERROR)
    response = error_response(
        status_code=exc.status_code,
        code=code.value,
        message=HTTPStatus(exc.status_code).phrase,
    )
    if exc.headers:
        response.headers.update(exc.headers)
    return response


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppException, _handle_app_exception)
    app.add_exception_handler(SQLAlchemyError, _handle_database_error)
    app.add_exception_handler(ConnectionError, _handle_connection_error)
    app.add_exception_handler(TimeoutError, _handle_connection_error)
    app.add_exception_handler(RequestValidationError, _handle_request_validation)
    app.add_exception_handler(StarletteHTTPException, _handle_http_exception)


class UnhandledErrorMiddleware:
    """Last line of defence: turns unexpected exceptions into a generic 500.

    It sits inside the request-id and logging middleware so the response still
    carries the request id. Stack traces go to the log, never to the client.
    """

    def __init__(self, app: ASGIApp, *, expose_error_type: bool = False) -> None:
        self._app = app
        self._expose_error_type = expose_error_type

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return

        response_started = False

        async def track_start(message: Message) -> None:
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self._app(scope, receive, track_start)
        except Exception as exc:
            logger.exception("unhandled_exception", extra={"error_type": type(exc).__name__})
            if response_started:
                raise
            details = [{"type": type(exc).__name__}] if self._expose_error_type else None
            response = error_response(
                status_code=_SERVER_ERROR,
                code=ErrorCode.INTERNAL_ERROR.value,
                message="An unexpected error occurred.",
                details=details,
            )
            await response(scope, receive, send)
