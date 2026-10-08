"""Server-sent events for long-running proposal requests.

The client gets `progress` events while the model works, then exactly one
terminal event: `proposal` (the same envelope the non-streaming endpoint
returns) or `error` (the standard error envelope). The model's partial output
is never forwarded: only how far along it is.
"""

import asyncio
import json
from collections.abc import AsyncIterator, Awaitable, Callable

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from sqlalchemy.exc import SQLAlchemyError

from app.api.dependencies import generative_ui_service_scope
from app.api.schemas import ApiResponse, ErrorBody, ErrorResponse
from app.core.context import get_request_id
from app.core.exceptions import AppException, ErrorCode
from app.core.logging import get_logger
from app.core.security import Principal
from app.domains.generative_ui.contracts import ProgressEvent, ProgressReporter, ProposalRead
from app.domains.generative_ui.service import GenerativeUIService
from app.middleware.error_handler import translate_database_error

logger = get_logger(__name__)

ProposalRun = Callable[[GenerativeUIService, ProgressReporter], Awaitable[ProposalRead]]

EVENT_PROGRESS = "progress"
EVENT_PROPOSAL = "proposal"
EVENT_ERROR = "error"
_SSE_HEADERS = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}


def encode_event(event: str, data: object) -> bytes:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n".encode()


def _error_event(error: AppException) -> bytes:
    body = ErrorResponse(
        error=ErrorBody(
            code=error.code.value,
            message=error.message,
            request_id=get_request_id(),
            details=[dict(detail) for detail in error.details] or None,
        )
    )
    return encode_event(EVENT_ERROR, body.model_dump(exclude_none=True))


def _to_app_exception(error: Exception) -> AppException:
    """The same translation the HTTP exception handlers apply."""
    if isinstance(error, AppException):
        return error
    if isinstance(error, SQLAlchemyError):
        return translate_database_error(error)
    logger.exception("unhandled_exception", extra={"error_type": type(error).__name__})
    failure = AppException()
    assert failure.code is ErrorCode.INTERNAL_ERROR
    return failure


async def _events(app: FastAPI, principal: Principal, run: ProposalRun) -> AsyncIterator[bytes]:
    queue: asyncio.Queue[bytes | None] = asyncio.Queue()

    async def progress(event: ProgressEvent) -> None:
        payload = {"stage": event.stage.value, "characters": event.characters}
        await queue.put(encode_event(EVENT_PROGRESS, payload))

    async def work() -> None:
        try:
            async with generative_ui_service_scope(app, principal) as service:
                proposal = await run(service, progress)
            envelope = ApiResponse(data=proposal).model_dump(mode="json", exclude_none=True)
            await queue.put(encode_event(EVENT_PROPOSAL, envelope))
        except Exception as exc:
            error = _to_app_exception(exc)
            logger.warning("stream_failed", extra={"code": error.code.value})
            await queue.put(_error_event(error))
        finally:
            await queue.put(None)

    task = asyncio.create_task(work())
    try:
        while (item := await queue.get()) is not None:
            yield item
    finally:
        # The client went away: stop paying for a model call nobody will see.
        if not task.done():
            task.cancel()


def proposal_stream(app: FastAPI, principal: Principal, run: ProposalRun) -> StreamingResponse:
    return StreamingResponse(
        _events(app, principal, run), media_type="text/event-stream", headers=_SSE_HEADERS
    )
