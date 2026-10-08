"""Groq provider (OpenAI-compatible chat completions API)."""

from collections.abc import Sequence
from typing import Any

from app.ai.llm.base import GenerationOptions, LLMMessage, TokenUsage
from app.ai.llm.http import JSON_OBJECT_RESPONSE_FORMAT, HttpChatProvider, serialize_messages


class GroqProvider(HttpChatProvider):
    @property
    def name(self) -> str:
        return "groq"

    @property
    def _chat_path(self) -> str:
        return "/chat/completions"

    def _build_payload(
        self, messages: Sequence[LLMMessage], options: GenerationOptions, *, json_mode: bool
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": serialize_messages(messages),
            "temperature": options.temperature,
            "max_completion_tokens": options.max_tokens,
        }
        if json_mode:
            payload["response_format"] = JSON_OBJECT_RESPONSE_FORMAT
        return payload

    def _parse_stream_event(self, event: Any) -> str | None:
        choices = event.get("choices") or []
        return choices[0].get("delta", {}).get("content") if choices else None

    def _parse_response(self, body: Any) -> tuple[str, TokenUsage]:
        content = body["choices"][0]["message"]["content"]
        usage = body.get("usage") or {}
        return str(content or ""), TokenUsage(
            prompt_tokens=usage.get("prompt_tokens"),
            completion_tokens=usage.get("completion_tokens"),
        )
