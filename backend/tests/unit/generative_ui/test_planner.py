import pytest

from app.domains.data_sources.providers.mock import MockSalesDataProvider
from app.domains.data_sources.schemas import DatasetDescriptor
from app.domains.generative_ui.intent import IntentAnalysis, KeywordIntentClassifier, UIIntent
from app.domains.generative_ui.planner import ConversationTurn, PlanningContext, UIPlanner
from app.domains.generative_ui.registry import build_default_registry
from app.domains.generative_ui.schemas import ComponentType


@pytest.fixture
async def datasets() -> list[DatasetDescriptor]:
    return await MockSalesDataProvider().list_datasets()


def _context(
    datasets: list[DatasetDescriptor],
    *,
    intent: UIIntent = UIIntent.COMPARISON,
    required_data: list[str] | None = None,
    components: tuple[ComponentType, ...] | None = None,
    history: tuple[ConversationTurn, ...] = (),
) -> PlanningContext:
    return PlanningContext(
        user_request="Compare sales across regions",
        intent=IntentAnalysis(
            intent=intent,
            title="Regional comparison",
            required_data=["sales_by_region"] if required_data is None else required_data,
        ),
        history=history,
        datasets=datasets,
        available_components=components or build_default_registry().types(),
    )


def test_comparison_plan_recommends_metrics_chart_table_and_filter(
    datasets: list[DatasetDescriptor],
) -> None:
    plan = UIPlanner().plan(_context(datasets))

    assert plan.intent is UIIntent.COMPARISON
    assert plan.required_data == ["sales_by_region"]
    assert [item.type for item in plan.recommended_components] == [
        ComponentType.METRIC,
        ComponentType.CHART,
        ComponentType.TABLE,
        ComponentType.SELECT,
    ]


def test_unavailable_data_is_dropped_and_noted(datasets: list[DatasetDescriptor]) -> None:
    plan = UIPlanner().plan(_context(datasets, required_data=["sales_by_region", "payroll"]))

    assert plan.required_data == ["sales_by_region"]
    assert any("payroll" in note for note in plan.notes)


def test_without_data_no_data_driven_component_is_recommended(
    datasets: list[DatasetDescriptor],
) -> None:
    plan = UIPlanner().plan(_context(datasets, intent=UIIntent.TREND, required_data=[]))

    assert [item.type for item in plan.recommended_components] == [ComponentType.ALERT]


def test_recommendations_respect_the_available_components(
    datasets: list[DatasetDescriptor],
) -> None:
    allowed = (ComponentType.PAGE, ComponentType.TABLE)

    plan = UIPlanner().plan(_context(datasets, components=allowed))

    assert [item.type for item in plan.recommended_components] == [ComponentType.TABLE]


def test_follow_up_requests_are_flagged(datasets: list[DatasetDescriptor]) -> None:
    history = (ConversationTurn(role="user", content="Show sales"),)

    plan = UIPlanner().plan(_context(datasets, history=history))

    assert any("follow-up" in note for note in plan.notes)


@pytest.mark.parametrize(
    ("request_text", "expected_intent", "expected_dataset"),
    [
        ("Compare sales across regions", UIIntent.COMPARISON, "sales_by_region"),
        ("How did revenue trend over the months?", UIIntent.TREND, "sales_by_month"),
        ("Give me a form to collect feedback", UIIntent.DATA_ENTRY, None),
        ("Tell me a joke", UIIntent.GENERAL, None),
    ],
)
def test_keyword_classifier(
    datasets: list[DatasetDescriptor],
    request_text: str,
    expected_intent: UIIntent,
    expected_dataset: str | None,
) -> None:
    analysis = KeywordIntentClassifier().classify(request_text, datasets)

    assert analysis.intent is expected_intent
    if expected_dataset is None:
        assert analysis.required_data == []
    else:
        assert expected_dataset in analysis.required_data
