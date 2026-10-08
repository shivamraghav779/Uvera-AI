"""Provider tests run against httpx.MockTransport: no network, no real credentials."""

import json
import logging
from collections.abc import Callable
from typing import Any

import httpx
import pytest
from pydantic import SecretStr

from app.ai.llm.base import GenerationOptions, LLMMessage, LLMProvider, LLMRole
from app.ai.llm.cohere import CohereProvider
from app.ai.llm.fallback import FallbackLLMProvider
from app.ai.llm.groq import GroqProvider
from app.core.exceptions import LLMException, LLMProvidersExhaustedException

API_KEY = "sk-test-secret-value"
MESSAGES = [LLMMessage(LLMRole.SYSTEM, "Be brief."), LLMMessage(LLMRole.USER, "Hello")]
GROQ_BODY = {
    "choices": [{"message": {"role": "assistant", "content": '{"ok": true}'}}],
    "usage": {"prompt_tokens": 12, "completion_tokens": 5},
}
COHERE_BODY = {
    "message": {"role": "assistant", "content": [{"type": "text", "text": '{"ok": true}'}]},
    "usage": {"tokens": {"input_tokens": 12.0, "output_tokens": 5.0}},
}

Handler = Callable[[httpx.Request], httpx.Response]


def _client(handler: Handler) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


def _respond(status: int, body: Any, seen: list[httpx.Request] | None = None) -> Handler:
    def handler(request: httpx.Request) -> httpx.Response:
        if seen is not None:
            seen.append(request)
        return httpx.Response(status, json=body)

    return handler


def _groq(handler: Handler) -> GroqProvider:
    return GroqProvider(
        api_key=SecretStr(API_KEY),
        model="llama-test",
        base_url="https://groq.test/openai/v1",
        client=_client(handler),
        timeout_seconds=5,
    )


def _cohere(handler: Handler) -> CohereProvider:
    return CohereProvider(
        api_key=SecretStr(API_KEY),
        model="command-test",
        base_url="https://cohere.test/v2",
        client=_client(handler),
        timeout_seconds=5,
    )


async def test_groq_sends_openai_style_request_and_parses_response() -> None:
    seen: list[httpx.Request] = []
    provider = _groq(_respond(200, GROQ_BODY, seen))

    response = await provider.generate_structured(MESSAGES, GenerationOptions(0.1, 500))

    [request] = seen
    payload = json.loads(request.content)
    assert str(request.url) == "https://groq.test/openai/v1/chat/completions"
    assert request.headers["authorization"] == f"Bearer {API_KEY}"
    assert payload == {
        "model": "llama-test",
        "messages": [
            {"role": "system", "content": "Be brief."},
            {"role": "user", "content": "Hello"},
        ],
        "temperature": 0.1,
        "max_completion_tokens": 500,
        "response_format": {"type": "json_object"},
    }
    assert (response.content, response.provider, response.model) == (
        '{"ok": true}',
        "groq",
        "llama-test",
    )
    assert response.usage.prompt_tokens == 12


async def test_groq_text_generation_does_not_request_json_mode() -> None:
    seen: list[httpx.Request] = []
    provider = _groq(_respond(200, GROQ_BODY, seen))

    await provider.generate_text(MESSAGES)

    assert "response_format" not in json.loads(seen[0].content)


async def test_cohere_sends_v2_chat_request_and_parses_response() -> None:
    seen: list[httpx.Request] = []
    provider = _cohere(_respond(200, COHERE_BODY, seen))

    response = await provider.generate_structured(MESSAGES, GenerationOptions(0.3, 800))

    payload = json.loads(seen[0].content)
    assert str(seen[0].url) == "https://cohere.test/v2/chat"
    assert payload["max_tokens"] == 800
    assert payload["response_format"] == {"type": "json_object"}
    assert response.content == '{"ok": true}'
    assert response.provider == "cohere"
    assert (response.usage.prompt_tokens, response.usage.completion_tokens) == (12, 5)


@pytest.mark.parametrize("build", [_groq, _cohere])
@pytest.mark.parametrize(
    ("status", "body", "expected_reason"),
    [
        (401, {"error": {"message": f"Invalid API key {API_KEY}"}}, "HTTP 401"),
        (500, {"error": "boom"}, "HTTP 500"),
        (200, {"unexpected": "shape"}, "unexpected response shape"),
    ],
)
async def test_provider_failures_become_llm_exceptions_without_leaking_secrets(
    build: Callable[[Handler], LLMProvider], status: int, body: Any, expected_reason: str
) -> None:
    provider = build(_respond(status, body))

    with pytest.raises(LLMException) as error:
        await provider.generate_structured(MESSAGES)

    assert error.value.reason == expected_reason
    assert error.value.provider == provider.name
    assert API_KEY not in f"{error.value!s} {error.value.reason} {error.value.message}"


async def test_timeouts_are_reported_as_llm_exceptions() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("slow", request=request)

    with pytest.raises(LLMException) as error:
        await _groq(handler).generate_text(MESSAGES)

    assert error.value.reason == "timeout"


async def test_empty_completion_is_a_failure() -> None:
    body = {"choices": [{"message": {"content": "  "}}]}

    with pytest.raises(LLMException) as error:
        await _groq(_respond(200, body)).generate_text(MESSAGES)

    assert error.value.reason == "empty completion"


async def test_fallback_uses_next_provider_and_reports_who_answered(
    caplog: pytest.LogCaptureFixture,
) -> None:
    chain = FallbackLLMProvider(
        [_groq(_respond(503, {"error": "down"})), _cohere(_respond(200, COHERE_BODY))]
    )

    with caplog.at_level(logging.ERROR):
        response = await chain.generate_structured(MESSAGES)

    assert response.provider == "cohere"
    [failure] = [record for record in caplog.records if record.message == "llm_provider_failed"]
    assert (failure.provider, failure.upstream_status, failure.will_fall_back) == (  # type: ignore[attr-defined]
        "groq",
        503,
        True,
    )


async def test_fallback_raises_controlled_error_when_every_provider_fails() -> None:
    chain = FallbackLLMProvider(
        [_groq(_respond(500, {})), _cohere(_respond(429, {"message": "rate limited"}))]
    )

    with pytest.raises(LLMProvidersExhaustedException) as error:
        await chain.generate_structured(MESSAGES)

    assert error.value.code == "LLM_ALL_PROVIDERS_FAILED"
    assert [(d["provider"], d["kind"], d["reason"]) for d in error.value.details] == [
        ("groq", "unavailable", "HTTP 500"),
        ("cohere", "rate_limited", "HTTP 429"),
    ]


async def test_fallback_does_not_call_later_providers_after_success() -> None:
    seen: list[httpx.Request] = []
    chain = FallbackLLMProvider(
        [_groq(_respond(200, GROQ_BODY)), _cohere(_respond(200, COHERE_BODY, seen))]
    )

    response = await chain.generate_text(MESSAGES)

    assert response.provider == "groq"
    assert seen == []
