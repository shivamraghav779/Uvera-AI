"""Edit stage: instruction + current document -> validated operations (bounded repair)."""

from collections.abc import Sequence

from pydantic import ValidationError

from app.ai.llm.base import GenerationOptions, LLMProvider
from app.ai.orchestration.completion import complete_structured
from app.ai.prompts.actions import ActionGuideEntry
from app.ai.prompts.mutation import UI_MUTATION_PROMPT, build_mutation_messages
from app.ai.prompts.ui_planner import build_repair_messages
from app.core.exceptions import UIGenerationException
from app.core.logging import get_logger
from app.domains.generative_ui.contracts import (
    MutationPlanKind,
    ProgressStage,
    UIMutationInput,
    UIMutationOutput,
    report,
)
from app.domains.generative_ui.design_registry import DesignRegistry
from app.domains.generative_ui.document import dump_document
from app.domains.generative_ui.mutator import DocumentMutator, MutationOutcome
from app.domains.generative_ui.operations import (
    AssistantPlan,
    CompareVersionsOperation,
    RestoreVersionOperation,
)
from app.domains.generative_ui.registry import ComponentRegistry
from app.domains.generative_ui.tree import screens, walk
from app.domains.generative_ui.validator import ValidationIssue, ValidationStage, schema_issues
from app.utils.json import parse_json_document

logger = get_logger(__name__)

_VersionRequest = RestoreVersionOperation | CompareVersionsOperation
# What interpreting one model reply yields: a usable result, or reasons to retry.
_Interpretation = tuple[MutationPlanKind, str, MutationOutcome | None, int | None]


class _RejectedError(Exception):
    def __init__(self, issues: Sequence[ValidationIssue]) -> None:
        super().__init__("model output rejected")
        self.issues = tuple(issues)


def _reject(stage: ValidationStage, message: str) -> _RejectedError:
    return _RejectedError([ValidationIssue(stage, "operations", message)])


class UIMutationExecutor:
    """Implements the domain's ``UIMutationPlanner`` port.

    The model's operations are parsed against the operation schema, applied by
    the mutation engine and the result is validated as a whole document. Only
    then is anything returned; otherwise the findings go back to the model.
    """

    def __init__(
        self,
        *,
        llm: LLMProvider,
        mutator: DocumentMutator,
        registry: ComponentRegistry,
        design: DesignRegistry,
        actions: Sequence[ActionGuideEntry],
        options: GenerationOptions,
        max_repair_attempts: int,
    ) -> None:
        self._llm = llm
        self._mutator = mutator
        self._registry = registry
        self._design = design
        self._actions = actions
        self._options = options
        self._max_repair_attempts = max_repair_attempts

    async def plan(self, request: UIMutationInput) -> UIMutationOutput:
        messages = build_mutation_messages(
            instruction=request.instruction,
            document=dump_document(request.document),
            selected_component_id=request.selected_component_id,
            versions=request.versions,
            history=request.history,
            datasets=request.datasets,
            components=self._registry.definitions(),
            actions=self._actions,
            design=self._design,
            focus_screen_id=self._focus(request),
            entities=request.document.application.entities if request.document.application else (),
        )
        issues: tuple[ValidationIssue, ...] = ()
        for attempt in range(self._max_repair_attempts + 1):
            response = await complete_structured(
                self._llm, messages, self._options, request.progress
            )
            await report(request.progress, ProgressStage.VALIDATING)
            try:
                kind, message, outcome, version_number = self._interpret(response.content, request)
            except _RejectedError as rejected:
                issues = rejected.issues
                logger.warning(
                    "ui_mutation_rejected",
                    extra={
                        "provider": response.provider,
                        "model": response.model,
                        "attempt": attempt + 1,
                        "issue_count": len(issues),
                        "will_retry": attempt < self._max_repair_attempts,
                    },
                )
                if attempt < self._max_repair_attempts:
                    await report(request.progress, ProgressStage.REPAIRING)
                messages = build_repair_messages(messages, response.content, issues)
                continue
            return UIMutationOutput(
                kind=kind,
                message=message,
                outcome=outcome,
                version_number=version_number,
                provider=response.provider,
                model=response.model,
                prompt_version=UI_MUTATION_PROMPT.version,
                repair_attempts=attempt,
            )
        raise UIGenerationException(
            "Generated operations are invalid.", details=[issue.to_detail() for issue in issues]
        )

    @staticmethod
    def _focus(request: UIMutationInput) -> str | None:
        """The screen an edit of an application is about: where the selection is, else
        the one on display."""
        if request.document.application is None:
            return None
        selected = request.selected_component_id
        if selected is not None:
            for screen in screens(request.document.page):
                if any(node.component.id == selected for node in walk(screen)):
                    return screen.id
        return request.active_screen_id

    def _interpret(self, raw: str, request: UIMutationInput) -> _Interpretation:
        try:
            plan = AssistantPlan.model_validate(parse_json_document(raw))
        except ValidationError as exc:
            raise _RejectedError(schema_issues(exc)) from None
        except ValueError as exc:
            raise _reject(ValidationStage.PARSING, f"Output is not valid JSON: {exc}") from None

        if not plan.operations:
            return MutationPlanKind.MESSAGE, plan.message, None, None

        version_requests = [op for op in plan.operations if isinstance(op, _VersionRequest)]
        if version_requests:
            return self._version_request(plan, version_requests[0], request)

        outcome = self._mutator.inspect(
            request.document, plan.operations, request.validation_context
        )
        if not outcome.is_valid:
            raise _RejectedError(outcome.issues)
        return MutationPlanKind.OPERATIONS, plan.message, outcome, None

    @staticmethod
    def _version_request(
        plan: AssistantPlan, operation: _VersionRequest, request: UIMutationInput
    ) -> _Interpretation:
        if len(plan.operations) != 1:
            raise _reject(
                ValidationStage.OPERATION,
                "A version operation must be the only operation in the list.",
            )
        known = {version.version_number: version for version in request.versions}
        target = known.get(operation.version_number)
        if target is None:
            available = ", ".join(str(number) for number in sorted(known)) or "none"
            raise _reject(
                ValidationStage.OPERATION,
                f"Version {operation.version_number} does not exist. Available: {available}.",
            )
        if isinstance(operation, RestoreVersionOperation):
            if target.is_current:
                raise _reject(
                    ValidationStage.OPERATION,
                    f"Version {operation.version_number} is already the current version.",
                )
            return MutationPlanKind.RESTORE, plan.message, None, operation.version_number
        return MutationPlanKind.COMPARE, plan.message, None, operation.version_number
