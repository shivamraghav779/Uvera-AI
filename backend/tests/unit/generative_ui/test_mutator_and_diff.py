from typing import Any

import pytest
from pydantic import TypeAdapter, ValidationError

from app.core.exceptions import UIValidationException
from app.domains.data_sources.providers.base import EmptyDataProvider
from app.domains.data_sources.providers.mock import MockSalesDataProvider
from app.domains.generative_ui.design_registry import build_default_design_registry
from app.domains.generative_ui.diff import ChangeKind, diff_documents
from app.domains.generative_ui.mutation_engine import apply_operations
from app.domains.generative_ui.mutator import DocumentMutator
from app.domains.generative_ui.operations import (
    OPERATION_EXAMPLES,
    VERSION_OPERATION_EXAMPLES,
    AssistantOperation,
    DocumentOperation,
)
from app.domains.generative_ui.renderer import UIDataResolver, bound_datasets
from app.domains.generative_ui.validator import ValidationContext, ValidationStage
from tests.support import canonical_document, parsed_document, text_page

OPERATION = TypeAdapter(DocumentOperation)
ASSISTANT_OPERATION = TypeAdapter(AssistantOperation)


def _ops(*raw: dict[str, Any]) -> list[Any]:
    return [OPERATION.validate_python(operation) for operation in raw]


def _changes(old: dict[str, Any], *raw: dict[str, Any]) -> list[tuple[ChangeKind, str]]:
    new = apply_operations(old, list(raw))
    return [(change.kind, change.summary) for change in diff_documents(old, new)]


# --- Operation contract ---------------------------------------------------------


@pytest.mark.parametrize(
    ("_", "example"), OPERATION_EXAMPLES, ids=lambda v: v.get("type") if isinstance(v, dict) else ""
)
def test_every_documented_operation_example_is_valid(_: str, example: dict[str, Any]) -> None:
    """Examples are shown to the model; a broken one would teach it invalid output."""
    assert OPERATION.validate_python(example).type == example["type"]


def test_version_operations_are_only_accepted_from_the_assistant() -> None:
    for _, example in VERSION_OPERATION_EXAMPLES:
        assert ASSISTANT_OPERATION.validate_python(example).type == example["type"]
        with pytest.raises(ValidationError):
            OPERATION.validate_python(example)


@pytest.mark.parametrize(
    "operation",
    [
        {"type": "EXECUTE", "code": "fetch('/steal')"},
        {"type": "MOVE", "target": "a", "position": {"x": 9, "y": 0}},
        {"type": "MOVE", "target": "a", "before": "b", "after": "c"},
        {"type": "RESIZE", "target": "a"},
        {"type": "RESIZE", "target": "a", "span": 14},
        {"type": "STYLE", "target": "a", "style": {"css": "color:red"}},
        {"type": "SET_THEME"},
        {"type": "SET_THEME", "tokens": {"colors": {"primary": "blue"}}},
        {"type": "CREATE", "component": {"type": "script", "id": "x", "src": "evil.js"}},
        {
            "type": "REPLACE",
            "target": "a",
            "component": {"type": "page", "title": "x", "components": []},
        },
    ],
)
def test_malformed_operations_are_rejected_by_the_schema(operation: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        OPERATION.validate_python(operation)


# --- Mutator: normalise -> apply -> validate ---------------------------------------


def test_valid_operations_produce_a_validated_document(
    mutator: DocumentMutator, validation_context: ValidationContext
) -> None:
    outcome = mutator.apply(
        parsed_document(),
        _ops(
            {"type": "MOVE", "target": "regional_breakdown", "before": "regional_sales"},
            {"type": "RESIZE", "target": "regional_sales", "span": 6},
        ),
        validation_context,
    )

    assert outcome.document is not None
    assert [c.id for c in outcome.document.page.components][2:] == [
        "regional_breakdown",
        "regional_sales",
    ]
    assert [step.summary for step in outcome.steps] == [
        "Move “Breakdown” before “regional_sales”",
        "Resize “regional_sales” to 6 of 12 columns wide",
    ]
    assert outcome.steps[0].affected_component_ids == ("regional_breakdown",)


def test_theme_preset_is_expanded_into_explicit_tokens(
    mutator: DocumentMutator, validation_context: ValidationContext
) -> None:
    outcome = mutator.apply(
        parsed_document(), _ops({"type": "SET_THEME", "preset": "slate_dark"}), validation_context
    )

    [operation] = outcome.operations
    assert operation["preset"] == "slate_dark"
    assert operation["tokens"]["mode"] == "dark"
    assert operation["tokens"]["colors"]["background"] == "#0B1120"
    assert outcome.document is not None
    assert outcome.document.theme.mode == "dark"
    assert outcome.document.theme.radius == "md", "shape tokens are not part of a colour preset"
    assert outcome.document.page == parsed_document().page, "the page is untouched"

    resubmitted = mutator.apply(parsed_document(), _ops(operation), validation_context)
    assert resubmitted.operations == [operation], "normalised operations are stable"
    assert resubmitted.document == outcome.document


def test_customised_preset_loses_the_preset_label(mutator: DocumentMutator) -> None:
    custom = {
        "type": "SET_THEME",
        "preset": "slate_dark",
        "tokens": {"colors": {"primary": "#38BDF8"}},
    }

    outcome = mutator.apply(parsed_document(text_page()), _ops(custom))

    assert outcome.document is not None
    assert outcome.document.theme.preset is None
    assert outcome.document.theme.colors.primary == "#38BDF8"
    assert outcome.document.theme.colors.background == "#0B1120"


def test_design_system_is_expanded_and_keeps_colours(
    mutator: DocumentMutator, validation_context: ValidationContext
) -> None:
    before = parsed_document()

    outcome = mutator.apply(
        before,
        _ops({"type": "SET_DESIGN_SYSTEM", "design_system": "compact_pro"}),
        validation_context,
    )

    assert outcome.operations[0]["tokens"]["density"] == "compact"
    assert outcome.document is not None
    assert outcome.document.design.design_system == "compact_pro"
    assert outcome.document.theme.density == "compact"
    assert outcome.document.theme.colors == before.theme.colors


def test_replacement_inherits_the_layout_of_what_it_replaces(
    mutator: DocumentMutator, validation_context: ValidationContext
) -> None:
    chart = {
        "type": "chart",
        "id": "regional_breakdown",
        "chart_type": "bar",
        "x_key": "region",
        "y_keys": ["revenue"],
        "data_source": {"dataset": "sales_by_region"},
    }

    outcome = mutator.apply(
        parsed_document(),
        _ops(
            {"type": "RESIZE", "target": "regional_breakdown", "span": 5, "height": "lg"},
            {"type": "REPLACE", "target": "regional_breakdown", "component": chart},
        ),
        validation_context,
    )

    assert outcome.document is not None
    replaced = outcome.document.page.components[3]
    assert (replaced.type, replaced.layout.span, replaced.layout.height) == ("chart", 5, "lg")


@pytest.mark.parametrize(
    ("operation", "stage", "fragment"),
    [
        ({"type": "DELETE", "target": "ghost"}, ValidationStage.OPERATION, "does not exist"),
        (
            {"type": "SET_THEME", "preset": "neon"},
            ValidationStage.OPERATION,
            "Unknown theme preset",
        ),
        (
            {"type": "SET_DESIGN_SYSTEM", "design_system": "brutal"},
            ValidationStage.OPERATION,
            "Unknown design system",
        ),
        ({"type": "SET_FRAMEWORK", "framework": "mui"}, ValidationStage.REGISTRY, "not available"),
        (
            {"type": "CREATE", "component": {"type": "divider", "id": "kpis"}},
            ValidationStage.SEMANTIC,
            "Duplicate id",
        ),
        (
            {"type": "UPDATE", "target": "regional_sales", "props": {"onClick": "alert(1)"}},
            ValidationStage.SCHEMA,
            "Extra inputs",
        ),
        (
            {"type": "UPDATE", "target": "regional_sales", "props": {"y_keys": ["profit"]}},
            ValidationStage.SEMANTIC,
            "no field 'profit'",
        ),
        (
            {"type": "DELETE", "target": "regional_sales"},
            ValidationStage.SEMANTIC,
            "Action target 'regional_sales'",
        ),
    ],
)
def test_operations_yielding_an_invalid_document_are_rejected(
    mutator: DocumentMutator,
    validation_context: ValidationContext,
    operation: dict[str, Any],
    stage: ValidationStage,
    fragment: str,
) -> None:
    outcome = mutator.inspect(parsed_document(), _ops(operation), validation_context)

    assert outcome.document is None
    assert not outcome.is_valid
    assert (outcome.issues[0].stage, fragment in outcome.issues[0].message) == (stage, True)
    with pytest.raises(UIValidationException):
        mutator.apply(parsed_document(), _ops(operation), validation_context)


# --- Diff -----------------------------------------------------------------------


def test_identical_documents_have_no_changes() -> None:
    assert diff_documents(canonical_document(), canonical_document()) == []


def test_diff_reports_each_kind_of_change() -> None:
    chart = {
        "type": "chart",
        "id": "regional_breakdown",
        "chart_type": "bar",
        "x_key": "region",
        "y_keys": ["revenue"],
        "data_source": {"dataset": "sales_by_region"},
    }
    dark = {"mode": "dark", "colors": {"background": "#000000", "foreground": "#FFFFFF"}}

    changes = _changes(
        canonical_document(),
        {"type": "SET_THEME", "tokens": dark},
        {"type": "SET_FRAMEWORK", "framework": "material"},
        {"type": "REPLACE", "target": "regional_breakdown", "component": chart},
        {"type": "DELETE", "target": "orders_metric"},
        {"type": "CREATE", "component": {"type": "divider", "id": "line", "label": "End"}},
        {"type": "RESIZE", "target": "regional_sales", "span": 6},
        {"type": "STYLE", "target": "revenue_metric", "style": {"tone": "success"}},
        {"type": "UPDATE", "target": "regional_sales", "props": {"chart_type": "line"}},
        {"type": "MOVE", "target": "region_filter", "parent_id": "kpis"},
    )

    assert changes == [
        (ChangeKind.THEME, "Theme changed from light to dark"),
        (ChangeKind.THEME, "Colours changed: background, foreground"),
        (ChangeKind.FRAMEWORK, "Framework changed from shadcn to material"),
        (ChangeKind.RESTYLED, "“Revenue” restyled"),
        (ChangeKind.MOVED, "“Region” moved to another container"),
        (ChangeKind.RESIZED, "“regional_sales” resized"),
        (ChangeKind.UPDATED, "“regional_sales” updated (chart_type)"),
        (ChangeKind.REPLACED, "Table “regional_breakdown” replaced with bar chart"),
        (ChangeKind.ADDED, "Divider “End” added"),
        (ChangeKind.REMOVED, "Metric “Orders” removed"),
    ]


def test_diff_reports_reordering_once_per_container() -> None:
    order = ["regional_breakdown", "regional_sales", "region_filter", "kpis"]

    changes = _changes(
        canonical_document(), {"type": "REORDER", "parent_id": "page", "order": order}
    )

    assert changes == [(ChangeKind.MOVED, "Items reordered in “Sales by Region”")]


def test_removing_a_container_is_reported_as_one_change() -> None:
    changes = _changes(canonical_document(), {"type": "DELETE", "target": "kpis"})

    assert changes == [(ChangeKind.REMOVED, "Section “kpis” removed")]


# --- Data bindings ----------------------------------------------------------------


async def test_bindings_resolve_to_rows_keyed_by_dataset() -> None:
    document = parsed_document()

    data = await UIDataResolver(MockSalesDataProvider()).resolve(document)

    assert bound_datasets(document) == ["sales_summary", "sales_by_region"]
    assert set(data) == {"sales_summary", "sales_by_region"}
    assert len(data["sales_by_region"]) == 4
    assert document == parsed_document(), "rows are never written into the document"


async def test_unavailable_dataset_resolves_to_no_rows_instead_of_failing() -> None:
    data = await UIDataResolver(EmptyDataProvider()).resolve(parsed_document())

    assert data == {"sales_summary": [], "sales_by_region": []}


def test_every_theme_preset_and_design_system_combination_is_valid(
    mutator: DocumentMutator,
) -> None:
    design = build_default_design_registry()

    for preset in design.themes():
        for system in design.design_systems():
            outcome = mutator.inspect(
                parsed_document(text_page()),
                _ops(
                    {"type": "SET_THEME", "preset": preset.id},
                    {"type": "SET_DESIGN_SYSTEM", "design_system": system.id},
                ),
            )
            assert outcome.issues == (), (preset.id, system.id, outcome.issues)
