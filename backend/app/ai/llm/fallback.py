"""Tries providers in order until one answers."""

from collections.abc import AsyncIterator, Awaitable, Callable, Sequence

from app.ai.llm.base import GenerationOptions, LLMChunk, LLMMessage, LLMProvider, LLMResponse
from app.core.exceptions import LLMException, LLMProvidersExhaustedException
from app.core.logging import get_logger

logger = get_logger(__name__)

ProviderCall = Callable[[LLMProvider], Awaitable[LLMResponse]]


class FallbackLLMProvider(LLMProvider):
    """A provider chain: primary first, then each fallback.

    Every failure is logged with provider metadata, and the response names the
    provider that actually answered, so a fallback is never silent. If all
    providers fail, ``LLMProvidersExhaustedException`` lists each failure.
    """

    def __init__(self, providers: Sequence[LLMProvider]) -> None:
        if not providers:
            raise ValueError("At least one provider is required.")
        self._providers = tuple(providers)

    @property
    def name(self) -> str:
        return self._providers[0].name

    @property
    def model(self) -> str:
        return self._providers[0].model

    async def generate_text(
        self, messages: Sequence[LLMMessage], options: GenerationOptions | None = None
    ) -> LLMResponse:
        return await self._first_success(lambda p: p.generate_text(messages, options))

    async def generate_structured(
        self, messages: Sequence[LLMMessage], options: GenerationOptions | None = None
    ) -> LLMResponse:
        return await self._first_success(lambda p: p.generate_structured(messages, options))

    async def stream_text(
        self,
        messages: Sequence[LLMMessage],
        options: GenerationOptions | None = None,
        *,
        json_mode: bool = False,
    ) -> AsyncIterator[LLMChunk]:
        """Stream from the first provider that starts answering.

        Falling back is only possible before the first chunk: once text has been
        handed to the caller, a failure is reported rather than restarting the
        answer with a different model.
        """
        failures: list[dict[str, object]] = []
        for position, provider in enumerate(self._providers):
            started = False
            try:
                async for chunk in provider.stream_text(messages, options, json_mode=json_mode):
                    started = True
                    yield chunk
                return
            except LLMException as exc:
                failures.append(self._record(exc, position, mid_stream=started))
                if started:
                    break
        raise LLMProvidersExhaustedException(details=failures)

    async def _first_success(self, call: ProviderCall) -> LLMResponse:
        failures: list[dict[str, object]] = []
        for position, provider in enumerate(self._providers):
            try:
                return await call(provider)
            except LLMException as exc:
                failures.append(self._record(exc, position))
        raise LLMProvidersExhaustedException(details=failures)

    def _record(
        self, exc: LLMException, position: int, *, mid_stream: bool = False
    ) -> dict[str, object]:
        """Log one provider failure and return its client-safe description."""
        failure: dict[str, object] = {
            "provider": exc.provider,
            "model": exc.model,
            "kind": exc.kind.value,
            "reason": exc.reason,
        }
        if exc.retry_after_seconds is not None:
            failure["retry_after_seconds"] = exc.retry_after_seconds
        logger.error(
            "llm_provider_failed",
            extra={
                **failure,
                "upstream_status": exc.upstream_status,
                "will_fall_back": not mid_stream and position < len(self._providers) - 1,
            },
        )
        return failure
