"""Generation stage: plan + data -> model output -> validated document (bounded repair)."""

from collections.abc import Sequence
from dataclasses import dataclass

from app.ai.llm.base import GenerationOptions, LLMMessage, LLMProvider, LLMResponse
from app.ai.orchestration.completion import complete_structured
from app.ai.prompts.actions import ActionGuideEntry
from app.ai.prompts.ui_planner import (
    UI_GENERATION_PROMPT,
    build_repair_messages,
    build_ui_generation_messages,
)
from app.core.exceptions import UIGenerationException
from app.core.logging import get_logger
from app.domains.data_sources.schemas import DatasetSnapshot
from app.domains.generative_ui.contracts import ProgressReporter, ProgressStage, report
from app.domains.generative_ui.design_registry import DesignRegistry, merge_theme
from app.domains.generative_ui.document import DesignConfig, Theme, UIDocument
from app.domains.generative_ui.planner import ConversationTurn, UIPlan
from app.domains.generative_ui.registry import ComponentRegistry
from app.domains.generative_ui.validator import (
    UISchemaValidator,
    ValidationContext,
    ValidationIssue,
    ValidationReport,
    ValidationStage,
)
from app.utils.json import parse_json_document

logger = get_logger(__name__)

_PAGE_KEY = "page"
_THEME_PRESET_KEY = "theme_preset"


@dataclass(frozen=True, slots=True)
class GenerationTask:
    user_request: str
    plan: UIPlan
    history: Sequence[ConversationTurn]
    datasets: Sequence[DatasetSnapshot]
    validation_context: ValidationContext
    base_theme: Theme
    design: DesignConfig
    progress: ProgressReporter | None = None


@dataclass(frozen=True, slots=True)
class GeneratedUI:
    document: UIDocument
    provider: str
    model: str
    prompt_version: str
    repair_attempts: int


def rejected(stage: ValidationStage, path: str, message: str) -> ValidationReport:
    return ValidationReport(document=None, issues=(ValidationIssue(stage, path, message),))


class UIGenerationExecutor:
    """Calls the model and accepts its output only once the validator does.

    Invalid output is sent back with the validator's findings at most
    ``max_repair_attempts`` times; after that the request fails. Unvalidated
    output never leaves this class.
    """

    def __init__(
        self,
        *,
        llm: LLMProvider,
        validator: UISchemaValidator,
        registry: ComponentRegistry,
        design: DesignRegistry,
        actions: Sequence[ActionGuideEntry],
        options: GenerationOptions,
        max_repair_attempts: int,
        log_prompts: bool = False,
    ) -> None:
        self._llm = llm
        self._validator = validator
        self._registry = registry
        self._design = design
        self._actions = actions
        self._options = options
        self._max_repair_attempts = max_repair_attempts
        self._log_prompts = log_prompts

    async def execute(self, task: GenerationTask) -> GeneratedUI:
        messages = build_ui_generation_messages(
            user_request=task.user_request,
            plan=task.plan,
            history=task.history,
            datasets=task.datasets,
            components=self._registry.definitions(),
            actions=self._actions,
            theme_presets=self._design.themes(),
        )
        for attempt in range(self._max_repair_attempts + 1):
            response = await self._call_model(messages, task.progress)
            await report(task.progress, ProgressStage.VALIDATING)
            outcome = self._interpret(response.content, task)
            if outcome.document is not None and outcome.is_valid:
                return GeneratedUI(
                    document=outcome.document,
                    provider=response.provider,
                    model=response.model,
                    prompt_version=UI_GENERATION_PROMPT.version,
                    repair_attempts=attempt,
                )
            logger.warning(
                "ui_generation_rejected",
                extra={
                    "provider": response.provider,
                    "model": response.model,
                    "attempt": attempt + 1,
                    "issue_count": len(outcome.issues),
                    "will_retry": attempt < self._max_repair_attempts,
                },
            )
            if attempt < self._max_repair_attempts:
                await report(task.progress, ProgressStage.REPAIRING)
            messages = build_repair_messages(messages, response.content, outcome.issues)
        raise UIGenerationException(details=[issue.to_detail() for issue in outcome.issues])

    def _interpret(self, raw: str, task: GenerationTask) -> ValidationReport:
        """Model output -> document assembled with the task's theme and design -> validation."""
        try:
            payload = parse_json_document(raw)
        except ValueError as exc:
            return rejected(ValidationStage.PARSING, "", f"Output is not valid JSON: {exc}")
        if not isinstance(payload, dict) or _PAGE_KEY not in payload:
            return rejected(ValidationStage.SCHEMA, "", 'Output must be an object with a "page".')

        theme = task.base_theme.model_dump(mode="json", exclude_none=True)
        preset_id = payload.get(_THEME_PRESET_KEY)
        if preset_id is not None:
            preset = self._design.theme(str(preset_id))
            if preset is None:
                names = ", ".join(p.id for p in self._design.themes())
                message = f"Unknown theme preset '{preset_id}'. Use null or one of: {names}."
                return rejected(ValidationStage.SCHEMA, _THEME_PRESET_KEY, message)
            colours = preset.theme.model_dump(mode="json", include={"preset", "mode", "colors"})
            theme = merge_theme(theme, colours)

        document = {
            _PAGE_KEY: payload[_PAGE_KEY],
            "theme": theme,
            "design": task.design.model_dump(mode="json"),
        }
        return self._validator.inspect_document(document, task.validation_context)

    async def _call_model(
        self, messages: Sequence[LLMMessage], progress: ProgressReporter | None
    ) -> LLMResponse:
        if self._log_prompts:
            logger.debug("llm_prompt", extra={"messages": [m.content for m in messages]})
        response = await complete_structured(self._llm, messages, self._options, progress)
        if self._log_prompts:
            logger.debug("llm_output", extra={"content": response.content})
        return response
