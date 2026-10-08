"""Streaming and retry behaviour of the real provider classes, over a mocked transport."""

import json
import logging
from collections.abc import Callable
from typing import Any

import httpx
import pytest
from pydantic import SecretStr

from app.ai.llm.base import LLMMessage, LLMProvider, LLMRole
from app.ai.llm.cohere import CohereProvider
from app.ai.llm.fallback import FallbackLLMProvider
from app.ai.llm.groq import GroqProvider
from app.ai.orchestration.completion import complete_structured
from app.core.exceptions import LLMException, LLMFailureKind, LLMProvidersExhaustedException
from app.domains.generative_ui.contracts import ProgressEvent, ProgressStage

MESSAGES = [LLMMessage(LLMRole.USER, "Hello")]
GROQ_OK = {"choices": [{"message": {"content": '{"ok": true}'}}]}

Handler = Callable[[httpx.Request], httpx.Response]


def _provider(cls: type[Any], handler: Handler, **kwargs: Any) -> Any:
    return cls(
        api_key=SecretStr("sk-test"),
        model="test-model",
        base_url="https://llm.test",
        client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
        timeout_seconds=5,
        retry_backoff_seconds=0,
        **kwargs,
    )


def _sse(*events: str) -> httpx.Response:
    body = "".join(f"{event}\n\n" for event in events)
    return httpx.Response(200, text=body, headers={"content-type": "text/event-stream"})


def _groq_delta(text: str | None) -> str:
    return "data: " + json.dumps({"choices": [{"delta": {"content": text} if text else {}}]})


def _cohere_delta(text: str) -> str:
    event = {"type": "content-delta", "delta": {"message": {"content": {"text": text}}}}
    return "event: content-delta\ndata: " + json.dumps(event)


async def _collect(provider: LLMProvider, **kwargs: Any) -> list[tuple[str, str]]:
    return [
        (chunk.text, chunk.provider) async for chunk in provider.stream_text(MESSAGES, **kwargs)
    ]


# --- Streaming --------------------------------------------------------------------


async def test_groq_stream_yields_text_deltas_and_requests_streaming() -> None:
    seen: list[dict[str, Any]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(json.loads(request.content))
        return _sse(
            ": keep-alive",
            _groq_delta(None),
            _groq_delta('{"ok"'),
            _groq_delta(": true}"),
            "data: [DONE]",
        )

    chunks = await _collect(_provider(GroqProvider, handler), json_mode=True)

    assert chunks == [('{"ok"', "groq"), (": true}", "groq")]
    assert seen[0]["stream"] is True
    assert seen[0]["response_format"] == {"type": "json_object"}


async def test_cohere_stream_reads_content_delta_events_only() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return _sse(
            'event: message-start\ndata: {"type": "message-start"}',
            _cohere_delta("Hel"),
            _cohere_delta("lo"),
            'event: message-end\ndata: {"type": "message-end"}',
        )

    assert await _collect(_provider(CohereProvider, handler)) == [
        ("Hel", "cohere"),
        ("lo", "cohere"),
    ]


@pytest.mark.parametrize(
    ("response", "kind"),
    [
        (httpx.Response(429, json={}), LLMFailureKind.RATE_LIMITED),
        (httpx.Response(401, json={}), LLMFailureKind.AUTHENTICATION),
        (_sse("data: {not json"), LLMFailureKind.BAD_RESPONSE),
        (_sse("data: [DONE]"), LLMFailureKind.BAD_RESPONSE),
    ],
    ids=["rate-limited", "unauthorised", "garbled-event", "empty-stream"],
)
async def test_stream_failures_are_classified(
    response: httpx.Response, kind: LLMFailureKind
) -> None:
    with pytest.raises(LLMException) as error:
        await _collect(_provider(GroqProvider, lambda request: response))

    assert error.value.kind is kind


async def test_stream_falls_back_before_the_first_chunk() -> None:
    chain = FallbackLLMProvider(
        [
            _provider(GroqProvider, lambda request: httpx.Response(503, json={})),
            _provider(CohereProvider, lambda request: _sse(_cohere_delta("Hi"))),
        ]
    )

    assert await _collect(chain) == [("Hi", "cohere")]


async def test_stream_does_not_restart_with_another_model_mid_answer() -> None:
    def broken(request: httpx.Request) -> httpx.Response:
        return _sse(_groq_delta("partial"), "data: {not json")

    cohere_calls: list[httpx.Request] = []

    def cohere(request: httpx.Request) -> httpx.Response:
        cohere_calls.append(request)
        return _sse(_cohere_delta("different answer"))

    chain = FallbackLLMProvider(
        [_provider(GroqProvider, broken), _provider(CohereProvider, cohere)]
    )
    received: list[str] = []

    with pytest.raises(LLMProvidersExhaustedException) as error:
        async for chunk in chain.stream_text(MESSAGES):
            received.append(chunk.text)

    assert received == ["partial"]
    assert cohere_calls == [], "a half-delivered answer is never continued by a second model"
    assert error.value.details[0]["kind"] == "bad_response"


async def test_structured_completion_streams_only_when_progress_is_wanted() -> None:
    requests: list[dict[str, Any]] = []
    text = json.dumps({"message": "x" * 400, "operations": []})

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        requests.append(body)
        if body.get("stream"):
            pieces = [text[i : i + 50] for i in range(0, len(text), 50)]
            return _sse(*(_groq_delta(piece) for piece in pieces), "data: [DONE]")
        return httpx.Response(200, json={"choices": [{"message": {"content": text}}]})

    provider = _provider(GroqProvider, handler)
    events: list[ProgressEvent] = []

    async def progress(event: ProgressEvent) -> None:
        events.append(event)

    plain = await complete_structured(provider, MESSAGES, provider_options(), None)
    streamed = await complete_structured(provider, MESSAGES, provider_options(), progress)

    assert plain.content == streamed.content == text, "the caller always gets the complete text"
    assert [r.get("stream", False) for r in requests] == [False, True]
    assert {event.stage for event in events} == {ProgressStage.GENERATING}
    counts = [event.characters for event in events]
    assert counts[0] == 0 and counts == sorted(counts) and counts[-1] <= len(text)
    assert len(events) < len(text) / 50, "progress is throttled, not sent per token"


def provider_options() -> Any:
    from app.ai.llm.base import GenerationOptions

    return GenerationOptions()


# --- Retries ----------------------------------------------------------------------


def _sequence(*responses: httpx.Response | Exception) -> tuple[Handler, list[httpx.Request]]:
    queue, seen = list(responses), []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        response = queue.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    return handler, seen


@pytest.mark.parametrize(
    "first",
    [
        httpx.Response(429, json={}),
        httpx.Response(503, json={}),
        httpx.ReadTimeout("slow"),
        httpx.ConnectError("refused"),
    ],
    ids=["rate-limited", "unavailable", "timeout", "connection"],
)
async def test_transient_failures_are_retried(
    first: httpx.Response | Exception, caplog: pytest.LogCaptureFixture
) -> None:
    handler, seen = _sequence(first, httpx.Response(200, json=GROQ_OK))

    with caplog.at_level(logging.WARNING):
        response = await _provider(GroqProvider, handler, max_retries=1).generate_structured(
            MESSAGES
        )

    assert response.content == '{"ok": true}'
    assert len(seen) == 2
    assert "llm_call_retried" in [record.message for record in caplog.records]


@pytest.mark.parametrize("status", [400, 401, 403, 404, 422])
async def test_permanent_failures_are_not_retried(status: int) -> None:
    handler, seen = _sequence(httpx.Response(status, json={}), httpx.Response(200, json=GROQ_OK))

    with pytest.raises(LLMException) as error:
        await _provider(GroqProvider, handler, max_retries=3).generate_structured(MESSAGES)

    assert len(seen) == 1
    assert not error.value.retryable


async def test_retries_are_bounded_and_then_the_fallback_takes_over() -> None:
    groq, groq_seen = _sequence(*[httpx.Response(503, json={})] * 3)
    cohere_body = {"message": {"content": [{"type": "text", "text": "from cohere"}]}}
    chain = FallbackLLMProvider(
        [
            _provider(GroqProvider, groq, max_retries=2),
            _provider(CohereProvider, lambda request: httpx.Response(200, json=cohere_body)),
        ]
    )

    response = await chain.generate_text(MESSAGES)

    assert len(groq_seen) == 3, "one attempt plus two retries"
    assert (response.provider, response.content) == ("cohere", "from cohere")
