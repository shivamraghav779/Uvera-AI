"""Runs one structured model call for a pipeline stage: call, parse, repair.

Every stage of application generation asks the model for one JSON object and
turns it into a typed plan. This is the shared loop around that: the output is
parsed by the stage; if it is unusable the findings go back to the model a
bounded number of times; rate limits and timeouts are waited out a bounded
number of times, because a pipeline of many calls will meet them on small
provider plans.
"""

import asyncio
from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace

from pydantic import ValidationError

from app.ai.llm.base import GenerationOptions, LLMMessage, LLMProvider, LLMResponse
from app.ai.prompts.base import PromptTemplate
from app.ai.prompts.ui_planner import build_repair_messages
from app.core.exceptions import LLMException, LLMProvidersExhaustedException, UIGenerationException
from app.core.logging import get_logger
from app.domains.generative_ui.validator import ValidationIssue, ValidationStage, schema_issues
from app.utils.json import parse_json_document

logger = get_logger(__name__)

# Failures that another attempt a little later can get past.
_TRANSIENT = frozenset({"rate_limited", "timeout", "unavailable", "transport"})
MAX_WAIT_SECONDS = 90.0


class StageRejectedError(Exception):
    """A stage's parser found the model's output unusable; carries what to tell the model."""

    def __init__(self, issues: Sequence[ValidationIssue]) -> None:
        super().__init__("stage output rejected")
        self.issues = tuple(issues)


def reject(path: str, message: str) -> StageRejectedError:
    return StageRejectedError([ValidationIssue(ValidationStage.SCHEMA, path, message)])


@dataclass(frozen=True, slots=True)
class StageResult[T]:
    value: T
    provider: str
    model: str
    prompt_version: str
    repair_attempts: int


def wait_before_retry(error: Exception) -> float | None:
    """Seconds a provider asked to wait (0 if it did not say), or ``None`` when
    trying again cannot help (bad credentials, a refused request)."""
    if isinstance(error, LLMException):
        if error.kind.value not in _TRANSIENT:
            return None
        return error.retry_after_seconds or 0.0
    if isinstance(error, LLMProvidersExhaustedException):
        transient = [d for d in error.details if d.get("kind") in _TRANSIENT]
        if not transient:
            return None
        waits = [float(d.get("retry_after_seconds") or 0.0) for d in transient]  # type: ignore[arg-type]
        # The provider that frees up first is the one worth waiting for.
        return min(waits)
    return None


class StageRunner:
    def __init__(
        self,
        llm: LLMProvider,
        *,
        options: GenerationOptions,
        max_repair_attempts: int,
        rate_limit_retries: int = 0,
        rate_limit_wait_seconds: float = 0,
        sleep: Callable[[float], "asyncio.Future[None] | object"] = asyncio.sleep,
    ) -> None:
        self._llm = llm
        self._options = options
        self._max_repair_attempts = max_repair_attempts
        self._rate_limit_retries = rate_limit_retries
        self._rate_limit_wait = rate_limit_wait_seconds
        self._sleep = sleep

    def limited_to(self, max_tokens: int) -> "StageRunner":
        """The same runner asking for at most ``max_tokens`` of output.

        Stages with short answers should not reserve a long answer's budget:
        providers count the requested maximum against per-minute limits.
        """
        options = replace(self._options, max_tokens=min(max_tokens, self._options.max_tokens))
        return StageRunner(
            self._llm,
            options=options,
            max_repair_attempts=self._max_repair_attempts,
            rate_limit_retries=self._rate_limit_retries,
            rate_limit_wait_seconds=self._rate_limit_wait,
            sleep=self._sleep,
        )

    async def run[T](
        self,
        prompt: PromptTemplate,
        messages: Sequence[LLMMessage],
        parse: Callable[[object], T],
        *,
        options: GenerationOptions | None = None,
    ) -> StageResult[T]:
        """Call the model and return ``parse``'s result.

        ``parse`` receives the decoded JSON and either returns a value or raises
        ``StageRejectedError`` / ``pydantic.ValidationError``. Raises
        ``UIGenerationException`` when the output is still unusable after repairs.
        """
        conversation = list(messages)
        issues: tuple[ValidationIssue, ...] = ()
        for attempt in range(self._max_repair_attempts + 1):
            response = await self._call(conversation, options or self._options)
            try:
                value = parse(self._decode(response.content))
            except StageRejectedError as rejected:
                issues = rejected.issues
            except ValidationError as error:
                issues = tuple(schema_issues(error))
            else:
                return StageResult(
                    value, response.provider, response.model, prompt.version, attempt
                )
            logger.warning(
                "stage_output_rejected",
                extra={
                    "stage": prompt.name,
                    "provider": response.provider,
                    "model": response.model,
                    "attempt": attempt + 1,
                    "issue_count": len(issues),
                    "first_issue": issues[0].message[:200] if issues else None,
                    "will_retry": attempt < self._max_repair_attempts,
                },
            )
            conversation = build_repair_messages(conversation, response.content, issues)
        raise UIGenerationException(
            f"The '{prompt.name}' stage could not produce usable output.",
            details=[issue.to_detail() for issue in issues],
        )

    @staticmethod
    def _decode(raw: str) -> object:
        try:
            return parse_json_document(raw)
        except ValueError as error:
            raise StageRejectedError(
                [ValidationIssue(ValidationStage.PARSING, "", f"Output is not valid JSON: {error}")]
            ) from None

    async def _call(
        self, messages: Sequence[LLMMessage], options: GenerationOptions
    ) -> LLMResponse:
        for attempt in range(self._rate_limit_retries + 1):
            try:
                return await self._llm.generate_structured(messages, options)
            except (LLMException, LLMProvidersExhaustedException) as error:
                asked = wait_before_retry(error)
                if asked is None or attempt == self._rate_limit_retries:
                    raise
                wait = min(max(self._rate_limit_wait * (attempt + 1), asked), MAX_WAIT_SECONDS)
                logger.warning(
                    "stage_waiting_for_provider",
                    extra={"attempt": attempt + 1, "wait_seconds": round(wait, 1)},
                )
                await self._sleep(wait)  # type: ignore[misc]
        raise AssertionError("unreachable")  # pragma: no cover
