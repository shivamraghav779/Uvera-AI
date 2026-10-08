"""UI planning: decide what kind of interface answers a request.

The planner is deterministic domain logic. It turns an intent and the available
data/components into a ``UIPlan`` that later guides the model; it never talks
to a model itself.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from pydantic import BaseModel

from app.domains.data_sources.schemas import DatasetDescriptor
from app.domains.generative_ui.intent import IntentAnalysis, UIIntent
from app.domains.generative_ui.schemas import ComponentType


@dataclass(frozen=True, slots=True)
class ConversationTurn:
    role: str
    content: str


class ComponentRecommendation(BaseModel):
    type: ComponentType
    purpose: str


class UIPlan(BaseModel):
    intent: UIIntent
    title: str
    required_data: list[str]
    recommended_components: list[ComponentRecommendation]
    notes: list[str]


@dataclass(frozen=True, slots=True)
class PlanningContext:
    user_request: str
    intent: IntentAnalysis
    history: Sequence[ConversationTurn]
    datasets: Sequence[DatasetDescriptor]
    available_components: Sequence[ComponentType]
    # Free-form facts about the caller (locale, role, ...) forwarded as plan notes.
    context: Mapping[str, str] = field(default_factory=dict)


def _recommend(component_type: ComponentType, purpose: str) -> ComponentRecommendation:
    return ComponentRecommendation(type=component_type, purpose=purpose)


_METRICS = _recommend(ComponentType.METRIC, "Headline figures")
_TABLE = _recommend(ComponentType.TABLE, "Detailed rows behind the figures")
_FILTER = _recommend(ComponentType.SELECT, "Filter to narrow the view")

_BLUEPRINTS: Mapping[UIIntent, tuple[ComponentRecommendation, ...]] = {
    UIIntent.OVERVIEW: (
        _METRICS,
        _recommend(ComponentType.CHART, "Main performance chart"),
        _TABLE,
    ),
    UIIntent.COMPARISON: (
        _METRICS,
        _recommend(ComponentType.CHART, "Bar chart comparing the items side by side"),
        _TABLE,
        _FILTER,
    ),
    UIIntent.TREND: (_METRICS, _recommend(ComponentType.CHART, "Line chart over time"), _TABLE),
    UIIntent.BREAKDOWN: (
        _recommend(ComponentType.CHART, "Bar or pie chart showing each part's share"),
        _TABLE,
        _FILTER,
    ),
    UIIntent.DETAIL: (_TABLE, _FILTER),
    UIIntent.DATA_ENTRY: (_recommend(ComponentType.FORM, "Collect the requested input"),),
    UIIntent.STATUS: (
        _recommend(ComponentType.PROGRESS, "Progress towards the goal"),
        _recommend(ComponentType.TIMELINE, "Steps or events so far"),
    ),
    UIIntent.GENERAL: (_recommend(ComponentType.TEXT, "Answer in plain text"),),
}
_DATA_DRIVEN = frozenset({ComponentType.METRIC, ComponentType.CHART, ComponentType.TABLE})
_FALLBACK = _recommend(ComponentType.ALERT, "Explain that no matching data is available")


class UIPlanner:
    def plan(self, context: PlanningContext) -> UIPlan:
        required_data, unknown_data = self._select_datasets(context)
        return UIPlan(
            intent=context.intent.intent,
            title=context.intent.title,
            required_data=required_data,
            recommended_components=self._recommend_components(context, bool(required_data)),
            notes=self._notes(context, unknown_data),
        )

    @staticmethod
    def _select_datasets(context: PlanningContext) -> tuple[list[str], list[str]]:
        """Split requested datasets into those that exist and those that do not."""
        available = {dataset.name for dataset in context.datasets}
        requested = list(dict.fromkeys(context.intent.required_data))
        return (
            [name for name in requested if name in available],
            [name for name in requested if name not in available],
        )

    @staticmethod
    def _recommend_components(
        context: PlanningContext, has_data: bool
    ) -> list[ComponentRecommendation]:
        usable = [
            item
            for item in _BLUEPRINTS[context.intent.intent]
            if item.type in context.available_components
            and (has_data or item.type not in _DATA_DRIVEN)
        ]
        if usable:
            return usable
        return [_FALLBACK] if _FALLBACK.type in context.available_components else []

    @staticmethod
    def _notes(context: PlanningContext, unknown_data: list[str]) -> list[str]:
        notes = [f"{key}: {value}" for key, value in context.context.items()]
        if unknown_data:
            notes.append(f"Requested data that is not available: {', '.join(unknown_data)}.")
        if context.history:
            notes.append("This is a follow-up; keep it consistent with the conversation so far.")
        return notes
