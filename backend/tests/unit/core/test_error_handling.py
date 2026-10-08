"""Error envelope, request ids and log hygiene. No database is needed."""

import json
import logging
from collections.abc import AsyncIterator

import httpx
import pytest
from fastapi import FastAPI
from pydantic import BaseModel

from app.core.context import request_id_var
from app.core.exceptions import LLMException, LLMFailureKind, UIGenerationException
from app.core.logging import REDACTED, JsonFormatter, redact
from tests.support import stateless_app


class _Echo(BaseModel):
    secret_note: str
    count: int


def _app(**settings_overrides: object) -> FastAPI:
    app = stateless_app(**settings_overrides)

    @app.get("/boom")
    async def boom() -> None:
        raise RuntimeError("database password is hunter2")

    @app.get("/invalid-ui")
    async def invalid_ui() -> None:
        raise UIGenerationException(details=[{"stage": "schema", "path": "x", "message": "bad"}])

    @app.get("/llm-down")
    async def llm_down() -> None:
        raise LLMException(
            provider="groq",
            model="m",
            kind=LLMFailureKind.AUTHENTICATION,
            reason="HTTP 401: key sk-123 rejected",
        )

    @app.post("/echo")
    async def echo(body: _Echo) -> _Echo:
        return body

    return app


@pytest.fixture
async def client() -> AsyncIterator[httpx.AsyncClient]:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=_app()), base_url="http://test"
    ) as http_client:
        yield http_client


async def test_app_exception_uses_the_error_envelope(client: httpx.AsyncClient) -> None:
    response = await client.get("/invalid-ui")

    assert response.status_code == 502
    assert response.json() == {
        "success": False,
        "error": {
            "code": "UI_SCHEMA_INVALID",
            "message": "Generated UI schema is invalid.",
            "request_id": response.headers["x-request-id"],
            "details": [{"stage": "schema", "path": "x", "message": "bad"}],
        },
    }


async def test_unhandled_exception_returns_generic_500_without_internals(
    client: httpx.AsyncClient, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.ERROR):
        response = await client.get("/boom")

    assert response.status_code == 500
    error = response.json()["error"]
    assert error["code"] == "INTERNAL_ERROR"
    assert error["request_id"] == response.headers["x-request-id"]
    assert "hunter2" not in response.text
    assert "Traceback" not in response.text
    assert "unhandled_exception" in [record.message for record in caplog.records], "still logged"


async def test_production_responses_do_not_reveal_the_exception_type() -> None:
    app = _app(app_env="production", enable_mock_data=None, auth_required=True, secret_key="k" * 40)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as http_client:
        response = await http_client.get("/boom")

    assert "details" not in response.json()["error"]
    assert "RuntimeError" not in response.text


async def test_upstream_error_text_is_logged_but_never_returned(
    client: httpx.AsyncClient, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.ERROR):
        response = await client.get("/llm-down")

    assert response.status_code == 502
    assert response.json()["error"]["code"] == "LLM_ERROR"
    assert "sk-123" not in response.text
    [record] = [r for r in caplog.records if r.message == "request_failed"]
    assert (record.provider, record.model) == ("groq", "m")  # type: ignore[attr-defined]


async def test_request_validation_errors_do_not_echo_input(client: httpx.AsyncClient) -> None:
    response = await client.post("/echo", json={"secret_note": "my-password", "count": "many"})

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert [detail["path"] for detail in error["details"]] == ["body.count"]
    assert "my-password" not in response.text
    assert "many" not in response.text


async def test_unknown_route_uses_the_error_envelope(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/v1/nope")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


async def test_wellformed_client_request_id_is_propagated(client: httpx.AsyncClient) -> None:
    response = await client.get("/invalid-ui", headers={"X-Request-ID": "client-trace-0001"})

    assert response.headers["x-request-id"] == "client-trace-0001"
    assert response.json()["error"]["request_id"] == "client-trace-0001"


@pytest.mark.parametrize("supplied", ["short", "bad id with spaces", "x" * 200, 'a"}\ninjected'])
async def test_malformed_client_request_id_is_replaced(
    client: httpx.AsyncClient, supplied: str
) -> None:
    response = await client.get("/invalid-ui", headers={"X-Request-ID": supplied})

    assert response.headers["x-request-id"] != supplied
    assert len(response.headers["x-request-id"]) == 32


async def test_requests_are_logged_with_status_duration_and_request_id(
    client: httpx.AsyncClient, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.INFO, logger="app.request"):
        response = await client.get("/invalid-ui?token=should-not-be-logged")

    started, completed = [r for r in caplog.records if r.name == "app.request"]
    assert started.message == "request_started"
    assert (completed.message, completed.status_code) == ("request_completed", 502)  # type: ignore[attr-defined]
    assert completed.duration_ms >= 0  # type: ignore[attr-defined]
    assert completed.path == "/invalid-ui"  # type: ignore[attr-defined]
    assert "should-not-be-logged" not in caplog.text
    assert response.headers["x-request-id"]


def test_json_log_lines_carry_request_id_and_redact_secrets() -> None:
    record = logging.LogRecord("app.test", logging.INFO, __file__, 1, "provider_called", (), None)
    record.provider = "groq"
    record.api_key = "sk-live-123"
    record.prompt_tokens = 42
    record.headers = {"Authorization": "Bearer abc", "accept": "json"}
    token = request_id_var.set("req-12345678")
    try:
        line = json.loads(JsonFormatter().format(record))
    finally:
        request_id_var.reset(token)

    assert line["event"] == "provider_called"
    assert line["request_id"] == "req-12345678"
    assert line["provider"] == "groq"
    assert line["api_key"] == REDACTED
    assert line["prompt_tokens"] == 42, "token counts are numbers, not secrets"
    assert line["headers"] == {"Authorization": REDACTED, "accept": "json"}


def test_redact_handles_nested_structures() -> None:
    payload = {"user": "ana", "auth": [{"access_token": "t", "scope": "read"}], "password": "p"}

    assert redact(payload) == {
        "user": "ana",
        "auth": [{"access_token": REDACTED, "scope": "read"}],
        "password": REDACTED,
    }
