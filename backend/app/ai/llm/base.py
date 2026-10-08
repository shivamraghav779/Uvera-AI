"""Provider-agnostic language model contract.

Nothing outside ``app.ai.llm`` knows which vendor is in use. A provider only
knows how to talk to its model API: no HTTP routes, database or UI concepts.
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass
from enum import StrEnum


class LLMRole(StrEnum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass(frozen=True, slots=True)
class LLMMessage:
    role: LLMRole
    content: str


@dataclass(frozen=True, slots=True)
class GenerationOptions:
    temperature: float = 0.2
    max_tokens: int = 4096
    # Overrides the provider's request timeout for calls known to produce long output.
    timeout_seconds: float | None = None


@dataclass(frozen=True, slots=True)
class TokenUsage:
    prompt_tokens: int | None = None
    completion_tokens: int | None = None


@dataclass(frozen=True, slots=True)
class LLMResponse:
    content: str
    # The provider/model that actually answered (relevant when a fallback served the call).
    provider: str
    model: str
    usage: TokenUsage = TokenUsage()


@dataclass(frozen=True, slots=True)
class LLMChunk:
    """A piece of a streamed completion."""

    text: str
    provider: str
    model: str


class LLMProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Stable provider identifier, e.g. ``"groq"``."""

    @property
    @abstractmethod
    def model(self) -> str:
        """Model identifier used for requests."""

    @abstractmethod
    async def generate_text(
        self, messages: Sequence[LLMMessage], options: GenerationOptions | None = None
    ) -> LLMResponse:
        """Return free-form text. Raises ``LLMException`` on failure."""

    @abstractmethod
    async def generate_structured(
        self, messages: Sequence[LLMMessage], options: GenerationOptions | None = None
    ) -> LLMResponse:
        """Return text that is a single JSON object (provider JSON mode).

        The content is still untrusted: callers must parse and validate it.
        Raises ``LLMException`` on failure.
        """

    @abstractmethod
    def stream_text(
        self,
        messages: Sequence[LLMMessage],
        options: GenerationOptions | None = None,
        *,
        json_mode: bool = False,
    ) -> AsyncIterator[LLMChunk]:
        """Yield the completion as text chunks while the model produces them.

        With ``json_mode`` the concatenated chunks form one JSON object.
        Raises ``LLMException`` on failure, possibly after some chunks.
        """
