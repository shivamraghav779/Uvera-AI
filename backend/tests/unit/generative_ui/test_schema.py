import pytest
from pydantic import ValidationError

from app.domains.generative_ui.schemas import (
    ChartComponent,
    ComponentType,
    MetricComponent,
    PageComponent,
)
from tests.support import sample_ui, text_page


def test_valid_page_parses_into_typed_components() -> None:
    page = PageComponent.model_validate(sample_ui())

    kinds = [component.type for component in page.components]
    assert kinds == [
        ComponentType.SECTION,
        ComponentType.SELECT,
        ComponentType.CHART,
        ComponentType.TABLE,
    ]
    assert isinstance(page.components[2], ChartComponent)


def test_unknown_component_type_is_rejected() -> None:
    document = text_page({"type": "iframe", "id": "frame", "src": "https://example.com"})

    with pytest.raises(ValidationError) as error:
        PageComponent.model_validate(document)

    assert "does not match any of the expected tags" in str(error.value)


@pytest.mark.parametrize(
    "extra_field",
    ["onClick", "dangerouslySetInnerHTML", "script", "className"],
)
def test_fields_outside_the_schema_are_rejected(extra_field: str) -> None:
    component = {"type": "text", "id": "note", "content": "Hi", extra_field: "alert(1)"}

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        PageComponent.model_validate(text_page(component))


def test_page_cannot_be_nested() -> None:
    with pytest.raises(ValidationError):
        PageComponent.model_validate(text_page(text_page()))


@pytest.mark.parametrize("missing", ["chart_type", "x_key", "y_keys"])
def test_chart_requires_its_core_fields(missing: str) -> None:
    chart = {
        "type": "chart",
        "id": "sales",
        "chart_type": "bar",
        "x_key": "region",
        "y_keys": ["revenue"],
        "data": [{"region": "North", "revenue": 1}],
    }
    del chart[missing]

    with pytest.raises(ValidationError, match=missing):
        PageComponent.model_validate(text_page(chart))


def test_metric_supports_trend_and_description() -> None:
    metric = MetricComponent.model_validate(
        {
            "type": "metric",
            "id": "revenue",
            "title": "Revenue",
            "value": "₹4.8 Cr",
            "layout": {"span": 3},
            "style": {"tone": "success"},
            "trend": {"direction": "up", "value": "+12%"},
            "description": "Q3 total",
        }
    )

    assert metric.trend is not None
    assert metric.trend.direction == "up"


def test_button_requires_label_and_action() -> None:
    with pytest.raises(ValidationError, match="action"):
        PageComponent.model_validate(text_page({"type": "button", "id": "go", "label": "Go"}))


def test_form_requires_fields_and_submit_action() -> None:
    form = {"type": "form", "id": "feedback", "fields": []}

    with pytest.raises(ValidationError) as error:
        PageComponent.model_validate(text_page(form))

    message = str(error.value)
    assert "submit_action" in message
    assert "fields" in message


def test_unknown_action_type_is_rejected() -> None:
    button = {
        "type": "button",
        "id": "danger",
        "label": "Run",
        "action": {"type": "execute_sql", "payload": {"sql": "DROP TABLE users"}},
    }

    with pytest.raises(ValidationError, match="action"):
        PageComponent.model_validate(text_page(button))


@pytest.mark.parametrize("bad_id", ["", "1abc", "has space", "a" * 65, "<script>"])
def test_component_ids_are_constrained(bad_id: str) -> None:
    with pytest.raises(ValidationError):
        PageComponent.model_validate(text_page({"type": "divider", "id": bad_id}))
