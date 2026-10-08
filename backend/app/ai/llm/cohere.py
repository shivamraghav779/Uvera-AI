"""Cohere provider (v2 chat API)."""

from collections.abc import Sequence
from typing import Any

from app.ai.llm.base import GenerationOptions, LLMMessage, TokenUsage
from app.ai.llm.http import JSON_OBJECT_RESPONSE_FORMAT, HttpChatProvider, serialize_messages

_TEXT_BLOCK = "text"
_CONTENT_DELTA = "content-delta"


class CohereProvider(HttpChatProvider):
    @property
    def name(self) -> str:
        return "cohere"

    @property
    def _chat_path(self) -> str:
        return "/chat"

    def _build_payload(
        self, messages: Sequence[LLMMessage], options: GenerationOptions, *, json_mode: bool
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": serialize_messages(messages),
            "temperature": options.temperature,
            "max_tokens": options.max_tokens,
        }
        if json_mode:
            payload["response_format"] = JSON_OBJECT_RESPONSE_FORMAT
        return payload

    def _parse_stream_event(self, event: Any) -> str | None:
        if event.get("type") != _CONTENT_DELTA:
            return None
        text: str | None = event["delta"]["message"]["content"].get("text")
        return text

    def _parse_response(self, body: Any) -> tuple[str, TokenUsage]:
        blocks = body["message"]["content"]
        content = "".join(block["text"] for block in blocks if block.get("type") == _TEXT_BLOCK)
        tokens = (body.get("usage") or {}).get("tokens") or {}
        return content, TokenUsage(
            prompt_tokens=_as_int(tokens.get("input_tokens")),
            completion_tokens=_as_int(tokens.get("output_tokens")),
        )


def _as_int(value: object) -> int | None:
    # Cohere reports token counts as floats.
    return int(value) if isinstance(value, int | float) else None
