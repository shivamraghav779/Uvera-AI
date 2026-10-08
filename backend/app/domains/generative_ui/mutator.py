"""Operations -> validated document.

``DocumentMutator`` is the only way a document changes through operations,
whether they came from the model or from the editor:

    normalise (expand presets) -> apply (mutation engine) -> validate (full pipeline)
"""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel

from app.core.exceptions import UIValidationException
from app.domains.generative_ui.design_registry import DesignRegistry, merge_theme
from app.domains.generative_ui.document import ThemePatch, UIDocument, dump_document
from app.domains.generative_ui.mutation_engine import (
    MutationError,
    affected_component_ids,
    apply_operations,
    describe_operation,
    find_node,
)
from app.domains.generative_ui.operations import (
    ReplaceOperation,
    SetDesignSystemOperation,
    SetThemeOperation,
    dump_operation,
)
from app.domains.generative_ui.schemas import LayoutSpec
from app.domains.generative_ui.validator import (
    UISchemaValidator,
    ValidationContext,
    ValidationIssue,
    ValidationStage,
)


@dataclass(frozen=True, slots=True)
class MutationStep:
    operation: dict[str, Any]
    summary: str
    affected_component_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class MutationOutcome:
    steps: tuple[MutationStep, ...]
    document: UIDocument | None
    issues: tuple[ValidationIssue, ...]

    @property
    def is_valid(self) -> bool:
        return self.document is not None and not self.issues

    @property
    def operations(self) -> list[dict[str, Any]]:
        return [step.operation for step in self.steps]


def _operation_issue(index: int, message: str) -> ValidationIssue:
    return ValidationIssue(ValidationStage.OPERATION, f"operations.{index}", message)


class DocumentMutator:
    def __init__(self, validator: UISchemaValidator, design: DesignRegistry) -> None:
        self._validator = validator
        self._design = design

    def inspect(
        self,
        document: UIDocument,
        operations: Sequence[BaseModel],
        context: ValidationContext | None = None,
    ) -> MutationOutcome:
        """Apply ``operations`` to ``document`` without raising.

        Each operation is normalised and described against the state left by
        the operations before it.
        """
        current = dump_document(document)
        steps: list[MutationStep] = []
        for index, operation in enumerate(operations):
            try:
                normalised = self._normalise(index, operation, current)
                summary = describe_operation(normalised, current)
                current = apply_operations(current, [normalised])
            except MutationError as exc:
                return MutationOutcome((), None, (_operation_issue(index, exc.message),))
            steps.append(
                MutationStep(normalised, summary, tuple(affected_component_ids(normalised)))
            )
        report = self._validator.inspect_document(current, context)
        return MutationOutcome(tuple(steps), report.document, report.issues)

    def apply(
        self,
        document: UIDocument,
        operations: Sequence[BaseModel],
        context: ValidationContext | None = None,
    ) -> MutationOutcome:
        outcome = self.inspect(document, operations, context)
        if not outcome.is_valid:
            raise UIValidationException(
                "The operations do not produce a valid UI.",
                details=[issue.to_detail() for issue in outcome.issues],
            )
        return outcome

    def _normalise(
        self, index: int, operation: BaseModel, document: dict[str, Any]
    ) -> dict[str, Any]:
        """Make an operation self-contained so any engine applies it identically."""
        raw = dump_operation(operation)
        if isinstance(operation, SetThemeOperation) and operation.preset is not None:
            preset = self._design.theme(operation.preset)
            if preset is None:
                raise MutationError(index, f"Unknown theme preset '{operation.preset}'.")
            colours = {"mode": preset.theme.mode.value, "colors": preset.theme.colors.model_dump()}
            raw["tokens"] = merge_theme(colours, raw.get("tokens") or {})
            if any(raw["tokens"][key] != colours[key] for key in colours):
                del raw["preset"]  # customised: no longer the preset's exact colours
        elif isinstance(operation, SetDesignSystemOperation):
            system = self._design.design_system(operation.design_system)
            if system is None:
                raise MutationError(index, f"Unknown design system '{operation.design_system}'.")
            raw["tokens"] = _dump_patch(system.tokens)
        elif isinstance(operation, ReplaceOperation):
            _inherit_layout(raw, operation, document)
        return raw


def _dump_patch(patch: ThemePatch) -> dict[str, Any]:
    return patch.model_dump(mode="json", exclude_none=True)


def _inherit_layout(
    raw: dict[str, Any], operation: ReplaceOperation, document: dict[str, Any]
) -> None:
    """A replacement keeps the size of what it replaces unless it states its own."""
    if "layout" in operation.component.model_fields_set:
        return
    target = find_node(document["page"], operation.target)
    layout = (target or {}).get("layout") or LayoutSpec().model_dump(mode="json")
    raw["component"] = {**raw["component"], "layout": layout}
