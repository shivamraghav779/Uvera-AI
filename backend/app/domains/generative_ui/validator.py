"""Gatekeeper between untrusted UI documents and everything else.

Pipeline: Pydantic schema -> component/action registries -> semantic rules ->
theme/design rules. A document that fails any stage is never returned as a UI.
(JSON parsing of raw model output happens in the AI executor, which reports
failures with the same ``ValidationIssue`` type.)
"""

import re
from collections.abc import Collection, Mapping
from dataclasses import dataclass, field
from enum import StrEnum

from pydantic import ValidationError
from pydantic_core import ErrorDetails

from app.core.exceptions import UIValidationException
from app.core.logging import get_logger
from app.domains.actions.schemas import ActionType
from app.domains.data_sources.schemas import DatasetDescriptor
from app.domains.generative_ui.application import entity_datasets
from app.domains.generative_ui.color import contrast_ratio
from app.domains.generative_ui.design_registry import DesignRegistry
from app.domains.generative_ui.document import UIDocument
from app.domains.generative_ui.registry import ComponentRegistry
from app.domains.generative_ui.semantic_rules import (
    SEMANTIC_RULES,
    RuleInput,
    SemanticRule,
    ValidationLimits,
)
from app.domains.generative_ui.tree import ComponentNode, action_specs, walk

logger = get_logger(__name__)

MAX_REPORTED_ISSUES = 25
# WCAG AA for body text.
MIN_TEXT_CONTRAST = 4.5
_UNKNOWN_TAG_ERROR = "union_tag_invalid"
_QUOTED_NAME = re.compile(r"'([A-Za-z_]+)'")
_PAGE_PATH = "page"


class ValidationStage(StrEnum):
    PARSING = "json_parsing"
    SCHEMA = "schema"
    OPERATION = "operation"
    REGISTRY = "registry"
    SEMANTIC = "semantic"


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    stage: ValidationStage
    path: str
    message: str

    def to_detail(self) -> dict[str, str]:
        return {"stage": self.stage.value, "path": self.path, "message": self.message}


@dataclass(frozen=True, slots=True)
class ValidationContext:
    """What a document is allowed to reference."""

    datasets: Mapping[str, DatasetDescriptor] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ValidationReport:
    document: UIDocument | None
    issues: tuple[ValidationIssue, ...]

    @property
    def is_valid(self) -> bool:
        return self.document is not None and not self.issues


class UISchemaValidator:
    def __init__(
        self,
        registry: ComponentRegistry,
        allowed_actions: Collection[ActionType],
        design: DesignRegistry,
        *,
        limits: ValidationLimits | None = None,
        semantic_rules: tuple[SemanticRule, ...] = SEMANTIC_RULES,
    ) -> None:
        self._registry = registry
        self._allowed_actions = frozenset(allowed_actions)
        self._design = design
        self._limits = limits or ValidationLimits()
        self._semantic_rules = semantic_rules

    def inspect_document(
        self, payload: object, context: ValidationContext | None = None
    ) -> ValidationReport:
        """Validate a parsed document without raising."""
        try:
            document = UIDocument.model_validate(payload)
        except ValidationError as exc:
            return self._report(None, schema_issues(exc))
        nodes = tuple(walk(document.page))
        issues = self._registry_issues(nodes)
        issues += self._semantic_issues(document, nodes, context or ValidationContext())
        issues += self._design_issues(document)
        return self._report(None if issues else document, issues)

    def validate_document(
        self, payload: object, context: ValidationContext | None = None
    ) -> UIDocument:
        report = self.inspect_document(payload, context)
        if report.document is None or report.issues:
            raise UIValidationException(details=[issue.to_detail() for issue in report.issues])
        return report.document

    def _registry_issues(self, nodes: tuple[ComponentNode, ...]) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        for node in nodes:
            component = node.component
            if not self._registry.is_registered(component.type):
                message = f"Component type '{component.type.value}' is not registered."
                issues.append(_page_issue(ValidationStage.REGISTRY, node.path, message))
            for field_name, action in action_specs(component):
                if action.type not in self._allowed_actions:
                    path = f"{node.path}.{field_name}.type"
                    message = f"Action '{action.type.value}' is not an allowed action."
                    issues.append(_page_issue(ValidationStage.REGISTRY, path, message))
        return issues

    def _semantic_issues(
        self, document: UIDocument, nodes: tuple[ComponentNode, ...], context: ValidationContext
    ) -> list[ValidationIssue]:
        rule_input = RuleInput(
            page=document.page,
            nodes=nodes,
            # An application's own entities are datasets too, and win over shared ones.
            datasets={**context.datasets, **entity_datasets(document)},
            limits=self._limits,
            application=document.application,
        )
        return [
            _semantic_issue(path, message)
            for rule in self._semantic_rules
            for path, message in rule(rule_input)
        ]

    def _design_issues(self, document: UIDocument) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        design, colors = document.design, document.theme.colors
        if not self._design.is_framework_available(design.framework):
            message = f"Framework '{design.framework}' is not available."
            issues.append(ValidationIssue(ValidationStage.REGISTRY, "design.framework", message))
        if self._design.design_system(design.design_system) is None:
            message = f"Design system '{design.design_system}' is not registered."
            issues.append(
                ValidationIssue(ValidationStage.REGISTRY, "design.design_system", message)
            )
        for name, backdrop in (("background", colors.background), ("surface", colors.surface)):
            if contrast_ratio(colors.foreground, backdrop) < MIN_TEXT_CONTRAST:
                message = (
                    f"Text would be hard to read: 'foreground' needs a contrast of at least "
                    f"{MIN_TEXT_CONTRAST}:1 against '{name}'."
                )
                issues.append(
                    ValidationIssue(ValidationStage.SEMANTIC, "theme.colors.foreground", message)
                )
        return issues

    def _report(
        self, document: UIDocument | None, issues: list[ValidationIssue]
    ) -> ValidationReport:
        if issues:
            logger.warning(
                "ui_validation_failed",
                extra={
                    "issue_count": len(issues),
                    "stages": sorted({issue.stage.value for issue in issues}),
                },
            )
        return ValidationReport(document=document, issues=tuple(issues[:MAX_REPORTED_ISSUES]))


def _semantic_issue(path: str, message: str) -> ValidationIssue:
    """Rule paths are relative to the page; ``application.``/``@`` paths are document-level."""
    if path.startswith("@"):
        return ValidationIssue(ValidationStage.SEMANTIC, path[1:], message)
    if path.startswith("application."):
        return ValidationIssue(ValidationStage.SEMANTIC, path, message)
    return _page_issue(ValidationStage.SEMANTIC, path, message)


def _page_issue(stage: ValidationStage, path: str, message: str) -> ValidationIssue:
    return ValidationIssue(stage, f"{_PAGE_PATH}.{path}" if path else _PAGE_PATH, message)


def _schema_message(issue: ErrorDetails) -> str:
    """Pydantic's message, except for unknown discriminator values where a readable one is built."""
    context = issue.get("ctx") or {}
    if issue["type"] != _UNKNOWN_TAG_ERROR or "tag" not in context:
        return issue["msg"]
    allowed = ", ".join(_QUOTED_NAME.findall(str(context.get("expected_tags", ""))))
    return f"Unknown type '{context['tag']}'. Allowed here: {allowed}."


def schema_issues(error: ValidationError, prefix: str = "") -> list[ValidationIssue]:
    """Convert a Pydantic error into validation issues, without echoing input values."""
    return [
        ValidationIssue(
            ValidationStage.SCHEMA,
            ".".join([*([prefix] if prefix else []), *(str(part) for part in issue["loc"])]),
            _schema_message(issue),
        )
        for issue in error.errors(include_url=False, include_input=False)
    ]
