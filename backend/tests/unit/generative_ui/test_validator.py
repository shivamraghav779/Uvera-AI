from typing import Any

import pytest

from app.core.exceptions import UIValidationException
from app.domains.actions.schemas import ActionType
from app.domains.generative_ui.design_registry import build_default_design_registry
from app.domains.generative_ui.registry import build_default_registry
from app.domains.generative_ui.schemas import ComponentType
from app.domains.generative_ui.semantic_rules import ValidationLimits
from app.domains.generative_ui.validator import (
    UISchemaValidator,
    ValidationContext,
    ValidationStage,
)
from tests.support import default_theme, sample_document, text_page

Issue = tuple[ValidationStage, str, str]


def _issues(
    validator: UISchemaValidator,
    page: dict[str, Any] | None = None,
    context: ValidationContext | None = None,
    **document_overrides: Any,
) -> list[Issue]:
    """Issues for a document around ``page``; component paths are relative to the page."""
    document = sample_document(page or text_page(), **document_overrides)
    report = validator.inspect_document(document, context)
    assert report.document is None, "an invalid document must never yield a UI"
    return [
        (issue.stage, issue.path.removeprefix("page."), issue.message) for issue in report.issues
    ]


def _chart(**overrides: Any) -> dict[str, Any]:
    chart = {
        "type": "chart",
        "id": "sales",
        "chart_type": "bar",
        "x_key": "region",
        "y_keys": ["revenue"],
        "data_source": {"dataset": "sales_by_region"},
    }
    return chart | overrides


def _validator(**kwargs: Any) -> UISchemaValidator:
    arguments: dict[str, Any] = {
        "registry": build_default_registry(),
        "allowed_actions": frozenset(ActionType),
        "design": build_default_design_registry(),
    }
    return UISchemaValidator(**(arguments | kwargs))


def test_valid_document_is_accepted_and_normalised(
    validator: UISchemaValidator, validation_context: ValidationContext
) -> None:
    report = validator.inspect_document(sample_document(), validation_context)

    assert report.is_valid
    assert report.document is not None
    assert report.document.page.id == "page", "defaults are filled in"
    chart = report.document.page.components[2]
    assert (chart.layout.span, chart.layout.height) == (12, "auto")


def test_document_requires_page_theme_and_design(validator: UISchemaValidator) -> None:
    report = validator.inspect_document({"page": text_page()})

    assert {issue.path for issue in report.issues} == {"theme", "design"}
    assert {issue.stage for issue in report.issues} == {ValidationStage.SCHEMA}


def test_unknown_component_is_rejected_with_its_location(validator: UISchemaValidator) -> None:
    [(stage, path, message)] = _issues(validator, text_page({"type": "carousel", "id": "slides"}))

    assert stage is ValidationStage.SCHEMA
    assert path == "components.0"
    assert message.startswith("Unknown type 'carousel'. Allowed here: screen, hero,")
    assert "section, card," in message


def test_component_missing_from_registry_is_rejected() -> None:
    """A type the schema knows can still be switched off by the registry."""
    registry = build_default_registry().restricted_to([ComponentType.PAGE, ComponentType.TEXT])

    issues = _issues(_validator(registry=registry), text_page({"type": "divider", "id": "line"}))

    assert issues[0][:2] == (ValidationStage.REGISTRY, "components.0")
    assert "divider" in issues[0][2]


def test_action_missing_from_allowlist_is_rejected() -> None:
    button = {
        "type": "button",
        "id": "export",
        "label": "Export",
        "action": {"type": "export", "payload": {"dataset": "sales_by_region"}},
    }

    issues = _issues(_validator(allowed_actions={ActionType.FILTER}), text_page(button))

    assert issues == [
        (
            ValidationStage.REGISTRY,
            "components.0.action.type",
            "Action 'export' is not an allowed action.",
        )
    ]


def test_duplicate_ids_are_rejected(validator: UISchemaValidator) -> None:
    page = text_page(
        {"type": "divider", "id": "same"},
        {"type": "card", "id": "card", "children": [{"type": "divider", "id": "same"}]},
    )

    assert [path for _, path, _ in _issues(validator, page)] == [
        "components.0.id",
        "components.1.children.0.id",
    ]


def test_unknown_dataset_is_rejected(
    validator: UISchemaValidator, validation_context: ValidationContext
) -> None:
    page = text_page(_chart(data_source={"dataset": "payroll"}))

    [(stage, path, message)] = _issues(validator, page, validation_context)

    assert stage is ValidationStage.SEMANTIC
    assert path == "components.0.data_source.dataset"
    assert "sales_by_region" in message, "the message should list what is available"


def test_field_missing_from_bound_dataset_is_rejected(
    validator: UISchemaValidator, validation_context: ValidationContext
) -> None:
    [(_, _, message)] = _issues(validator, text_page(_chart(y_keys=["profit"])), validation_context)

    assert message == "Dataset 'sales_by_region' has no field 'profit'."


def test_chart_without_any_data_is_rejected(validator: UISchemaValidator) -> None:
    [(_, path, message)] = _issues(validator, text_page(_chart(data_source=None)))

    assert path == "components.0"
    assert message.startswith("No data")


def test_chart_with_complete_inline_rows_is_accepted(validator: UISchemaValidator) -> None:
    page = text_page(_chart(data_source=None, data=[{"region": "North", "revenue": 10}]))

    assert validator.inspect_document(sample_document(page)).is_valid


@pytest.mark.parametrize(
    ("metric", "expected"),
    [
        ({}, "Metric has no value"),
        ({"data_source": {"dataset": "payroll", "field": "x"}}, "Unknown dataset 'payroll'"),
        (
            {"data_source": {"dataset": "sales_summary", "field": "profit"}},
            "has no field 'profit'",
        ),
        (
            {"data_source": {"dataset": "sales_summary", "field": "top_region"}},
            "'sum' needs a numeric field",
        ),
    ],
)
def test_metric_must_have_a_resolvable_value(
    validator: UISchemaValidator,
    validation_context: ValidationContext,
    metric: dict[str, Any],
    expected: str,
) -> None:
    page = text_page({"type": "metric", "id": "kpi", "title": "KPI", **metric})

    [(_, _, message)] = _issues(validator, page, validation_context)

    assert expected in message


def test_text_metric_can_use_a_non_numeric_aggregate(
    validator: UISchemaValidator, validation_context: ValidationContext
) -> None:
    binding = {"dataset": "sales_summary", "field": "top_region", "aggregate": "first"}
    page = text_page({"type": "metric", "id": "kpi", "title": "Top", "data_source": binding})

    assert validator.inspect_document(sample_document(page), validation_context).is_valid


@pytest.mark.parametrize(
    "content",
    [
        "<script>alert(1)</script>",
        "Click javascript:alert(1)",
        '<img src=x onerror="steal()">',
        "<iframe src='https://evil.example'></iframe>",
    ],
)
def test_markup_and_script_urls_are_rejected(validator: UISchemaValidator, content: str) -> None:
    [(stage, path, _)] = _issues(
        validator, text_page({"type": "text", "id": "note", "content": content})
    )

    assert (stage, path) == (ValidationStage.SEMANTIC, "components.0.content")


def test_ordinary_prose_about_code_is_not_flagged(validator: UISchemaValidator) -> None:
    page = text_page(
        {"type": "text", "id": "note", "content": "Revenue > target; see the script for Q3."}
    )

    assert validator.inspect_document(sample_document(page)).is_valid


def test_action_target_must_reference_a_component(validator: UISchemaValidator) -> None:
    button = {
        "type": "button",
        "id": "refresh",
        "label": "Refresh",
        "action": {"type": "refresh", "payload": {"dataset": "x", "target": "missing_chart"}},
    }

    [(_, path, message)] = _issues(validator, text_page(button))

    assert path == "components.0.action.payload.target"
    assert "missing_chart" in message


@pytest.mark.parametrize("destination", ["javascript:alert(1)", "//evil.example", "http://x.y"])
def test_navigate_destination_must_be_safe(validator: UISchemaValidator, destination: str) -> None:
    button = {
        "type": "button",
        "id": "go",
        "label": "Go",
        "action": {"type": "navigate", "payload": {"to": destination}},
    }

    paths = [path for _, path, _ in _issues(validator, text_page(button))]

    assert "components.0.action.payload.to" in paths


def test_size_limits_protect_the_frontend() -> None:
    validator = _validator(limits=ValidationLimits(max_depth=2, max_components=3))
    nested = {
        "type": "card",
        "id": "outer",
        "children": [{"type": "card", "id": "inner", "children": [{"type": "divider", "id": "d"}]}],
    }

    messages = [message for _, _, message in _issues(validator, text_page(nested))]

    assert any("components; the limit is 3" in message for message in messages)
    assert any("Nesting depth 4 exceeds the limit of 2" in message for message in messages)


@pytest.mark.parametrize(
    "layout", [{"span": 0}, {"span": 13}, {"height": "900px"}, {"x": 4, "y": 2}, {"width": "50%"}]
)
def test_layout_accepts_only_grid_spans_and_height_presets(
    validator: UISchemaValidator, layout: dict[str, Any]
) -> None:
    issues = _issues(validator, text_page({"type": "divider", "id": "line", "layout": layout}))

    assert {stage for stage, _, _ in issues} == {ValidationStage.SCHEMA}


@pytest.mark.parametrize(
    "style", [{"tone": "#ff0000"}, {"color": "red"}, {"css": "position:fixed"}, {"tone": "blue"}]
)
def test_style_accepts_only_tokens_never_css(
    validator: UISchemaValidator, style: dict[str, Any]
) -> None:
    issues = _issues(validator, text_page({"type": "divider", "id": "line", "style": style}))

    assert {stage for stage, _, _ in issues} == {ValidationStage.SCHEMA}


@pytest.mark.parametrize(
    "color",
    ["red", "#FFF", "rgb(0,0,0)", "#12345G", "url(javascript:alert(1))", "#000000; background:red"],
)
def test_theme_colours_must_be_six_digit_hex(validator: UISchemaValidator, color: str) -> None:
    theme = default_theme()
    theme["colors"]["primary"] = color

    [(stage, path, _)] = _issues(validator, theme=theme)

    assert (stage, path) == (ValidationStage.SCHEMA, "theme.colors.primary")


def test_theme_rejects_unknown_tokens(validator: UISchemaValidator) -> None:
    theme = default_theme() | {"custom_css": "body{display:none}"}

    [(stage, path, _)] = _issues(validator, theme=theme)

    assert (stage, path) == (ValidationStage.SCHEMA, "theme.custom_css")


def test_unreadable_theme_is_rejected(validator: UISchemaValidator) -> None:
    theme = default_theme()
    theme["colors"]["foreground"] = "#F1F5F9"  # near-white text on a white surface

    issues = _issues(validator, theme=theme)

    assert {path for _, path, _ in issues} == {"theme.colors.foreground"}
    assert all("contrast" in message for _, _, message in issues)


@pytest.mark.parametrize(
    ("design", "path"),
    [
        ({"framework": "mui", "design_system": "modern_minimal"}, "design.framework"),
        ({"framework": "bootstrap", "design_system": "modern_minimal"}, "design.framework"),
        ({"framework": "shadcn", "design_system": "neon"}, "design.design_system"),
    ],
)
def test_design_must_reference_available_framework_and_design_system(
    validator: UISchemaValidator, design: dict[str, str], path: str
) -> None:
    [(stage, issue_path, _)] = _issues(validator, design=design)

    assert (stage, issue_path) == (ValidationStage.REGISTRY, path)


def test_validate_document_raises_with_structured_details(validator: UISchemaValidator) -> None:
    with pytest.raises(UIValidationException) as error:
        validator.validate_document(sample_document(text_page({"type": "carousel", "id": "s"})))

    assert error.value.code == "UI_SCHEMA_INVALID"
    assert error.value.details[0]["stage"] == "schema"
    assert error.value.details[0]["path"] == "page.components.0"
