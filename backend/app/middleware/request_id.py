"""Assigns every HTTP request an id, exposed to logs, errors and the response."""

import re
import uuid

from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.context import request_id_var

REQUEST_ID_HEADER = "X-Request-ID"
# Client-supplied ids are accepted only in this shape so they cannot inject log content.
_ACCEPTABLE_ID = re.compile(r"^[A-Za-z0-9._-]{8,64}$")


def _resolve_request_id(scope: Scope) -> str:
    supplied = Headers(scope=scope).get(REQUEST_ID_HEADER)
    if supplied and _ACCEPTABLE_ID.fullmatch(supplied):
        return supplied
    return uuid.uuid4().hex


class RequestIDMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self._app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return

        request_id = _resolve_request_id(scope)
        token = request_id_var.set(request_id)

        async def send_with_request_id(message: Message) -> None:
            if message["type"] == "http.response.start":
                MutableHeaders(scope=message)[REQUEST_ID_HEADER] = request_id
            await send(message)

        try:
            await self._app(scope, receive, send_with_request_id)
        finally:
            request_id_var.reset(token)
