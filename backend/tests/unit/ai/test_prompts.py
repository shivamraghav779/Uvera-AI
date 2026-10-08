import re

import pytest

from app.ai.llm.base import LLMRole
from app.ai.prompts.actions import ActionGuideEntry, render_actions_guide
from app.ai.prompts.intent import build_intent_messages
from app.ai.prompts.ui_planner import (
    UI_GENERATION_PROMPT,
    build_repair_messages,
    build_ui_generation_messages,
)
from app.domains.data_sources.providers.mock import MockSalesDataProvider
from app.domains.generative_ui.intent import UIIntent
from app.domains.generative_ui.planner import (
    ComponentRecommendation,
    ConversationTurn,
    UIPlan,
)
from app.domains.generative_ui.registry import build_default_registry
from app.domains.generative_ui.schemas import ComponentType
from app.domains.generative_ui.validator import ValidationIssue, ValidationStage

ACTIONS = [ActionGuideEntry("filter", "Filter a dataset.", ("target", "dataset", "field"))]
PLAN = UIPlan(
    intent=UIIntent.COMPARISON,
    title="Regional comparison",
    required_data=["sales_by_region"],
    recommended_components=[
        ComponentRecommendation(type=ComponentType.CHART, purpose="Compare regions")
    ],
    notes=["Keep it short."],
)


async def _messages(**overrides: object) -> tuple[str, str]:
    snapshot = await MockSalesDataProvider().fetch("sales_by_region")
    arguments: dict[str, object] = {
        "user_request": "Compare sales across regions",
        "plan": PLAN,
        "history": [ConversationTurn("user", "Earlier question")],
        "datasets": [snapshot],
        "components": build_default_registry().definitions(),
        "actions": ACTIONS,
    }
    system, user = build_ui_generation_messages(**(arguments | overrides))  # type: ignore[arg-type]
    assert (system.role, user.role) == (LLMRole.SYSTEM, LLMRole.USER)
    return system.content, user.content


@pytest.mark.parametrize(
    "required_instruction",
    [
        "generating a UI Schema",
        "Never write code of any kind",
        'Use only the component types listed under "Registered components"',
        "The output must conform to the UI Schema",
        "Never output colours or CSS",
        "never use generic ids",
        "Never invent a component type",
        "Return exactly one JSON object",
        "Prefer simple structures",
        'Use only data listed under "Available data"',
        'Use only the action types listed under "Allowed actions"',
    ],
)
def test_system_prompt_states_every_required_rule(required_instruction: str) -> None:
    assert required_instruction in UI_GENERATION_PROMPT.system


def test_prompt_is_versioned() -> None:
    assert re.fullmatch(r"\d+\.\d+\.\d+", UI_GENERATION_PROMPT.version)


async def test_system_message_lists_every_registered_component_and_allowed_action() -> None:
    system, _ = await _messages()

    for definition in build_default_registry().definitions():
        assert f"- {definition.type.value}: " in system
    assert "- filter: Filter a dataset. Payload fields: target, dataset, field." in system


async def test_user_message_carries_request_plan_data_and_history() -> None:
    _, user = await _messages()

    assert user.rstrip().endswith("User request\nCompare sales across regions")
    assert "Intent: comparison" in user
    assert "- chart: Compare regions" in user
    assert 'dataset "sales_by_region"' in user
    assert '"region":"North"' in user
    assert "user: Earlier question" in user


async def test_only_registered_components_are_offered() -> None:
    restricted = build_default_registry().restricted_to([ComponentType.PAGE, ComponentType.TEXT])

    system, _ = await _messages(components=restricted.definitions())

    assert "- text: " in system
    assert "- chart: " not in system


async def test_missing_data_is_stated_explicitly() -> None:
    _, user = await _messages(datasets=[])

    assert "Available data\n(none" in user


def test_no_actions_are_offered_when_none_are_allowed() -> None:
    assert "No actions are available" in render_actions_guide([])


async def test_repair_messages_append_rejected_output_and_findings() -> None:
    original = build_ui_generation_messages(
        user_request="x", plan=PLAN, history=[], datasets=[], components=[], actions=[]
    )
    issue = ValidationIssue(ValidationStage.SCHEMA, "components.0", "Unknown type 'carousel'")

    repaired = build_repair_messages(original, '{"type": "carousel"}', [issue])

    assert repaired[:2] == original
    assert (repaired[2].role, repaired[2].content) == (LLMRole.ASSISTANT, '{"type": "carousel"}')
    assert "- [schema] components.0: Unknown type 'carousel'" in repaired[3].content
    assert "one JSON object" in repaired[3].content


async def test_intent_prompt_lists_intents_and_dataset_names() -> None:
    datasets = await MockSalesDataProvider().list_datasets()

    system, user = build_intent_messages(
        user_request="Compare sales across regions", history=[], datasets=datasets
    )

    assert "Never invent names" in system.content
    for intent in UIIntent:
        assert f"- {intent.value}: " in user.content
    assert "- sales_by_region: " in user.content
