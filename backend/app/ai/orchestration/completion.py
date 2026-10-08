"""One model call, with or without live progress."""

from collections.abc import Sequence

from app.ai.llm.base import GenerationOptions, LLMMessage, LLMProvider, LLMResponse
from app.domains.generative_ui.contracts import ProgressEvent, ProgressReporter, ProgressStage

# Report after roughly this many new characters, not for every token.
PROGRESS_INTERVAL_CHARACTERS = 160


async def complete_structured(
    llm: LLMProvider,
    messages: Sequence[LLMMessage],
    options: GenerationOptions,
    progress: ProgressReporter | None,
) -> LLMResponse:
    """Get a JSON completion.

    Without a progress reporter this is a single request/response call. With
    one, the completion is streamed and the reporter is told how much has
    arrived; the caller still receives the complete text, which it must
    validate as a whole. Partial output is never interpreted.
    """
    if progress is None:
        return await llm.generate_structured(messages, options)

    await progress(ProgressEvent(ProgressStage.GENERATING, characters=0))
    parts: list[str] = []
    received = reported = 0
    provider, model = llm.name, llm.model
    async for chunk in llm.stream_text(messages, options, json_mode=True):
        parts.append(chunk.text)
        received += len(chunk.text)
        provider, model = chunk.provider, chunk.model
        if received - reported >= PROGRESS_INTERVAL_CHARACTERS:
            reported = received
            await progress(ProgressEvent(ProgressStage.GENERATING, characters=received))
    return LLMResponse(content="".join(parts), provider=provider, model=model)
