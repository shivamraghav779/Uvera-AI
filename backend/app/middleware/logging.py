"""Logs the start and completion of every HTTP request."""

import time

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.logging import get_logger

logger = get_logger("app.request")


class RequestLoggingMiddleware:
    """Records method, path, status and duration. Bodies and query strings are never logged."""

    def __init__(self, app: ASGIApp) -> None:
        self._app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return

        request_fields = {"method": scope["method"], "path": scope["path"]}
        status_code: int | None = None

        async def capture_status(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        logger.info("request_started", extra=request_fields)
        started = time.perf_counter()
        try:
            await self._app(scope, receive, capture_status)
        finally:
            logger.info(
                "request_completed",
                extra={
                    **request_fields,
                    "status_code": status_code,
                    "duration_ms": round((time.perf_counter() - started) * 1000, 1),
                },
            )
