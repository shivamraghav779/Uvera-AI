import json
import logging
from datetime import UTC, datetime
from typing import Any

import pytest

from app.ai.llm.base import GenerationOptions
from app.ai.orchestration.agent import GenerativeUIAgent
from app.ai.orchestration.executor import GenerationTask, UIGenerationExecutor
from app.ai.orchestration.mutation import UIMutationExecutor
from app.ai.orchestration.planner import PlanningRequest, RequestPlanner
from app.core.exceptions import LLMProvidersExhaustedException, UIGenerationException
from app.domains.data_sources.providers.mock import MockSalesDataProvider
from app.domains.generative_ui.contracts import (
    MutationPlanKind,
    UIGenerationInput,
    UIMutationInput,
    VersionInfo,
)
from app.domains.generative_ui.design_registry import build_default_design_registry
from app.domains.generative_ui.intent import KeywordIntentClassifier, UIIntent
from app.domains.generative_ui.mutator import DocumentMutator
from app.domains.generative_ui.planner import UIPlan, UIPlanner
from app.domains.generative_ui.registry import build_default_registry
from app.domains.generative_ui.validator import UISchemaValidator, ValidationContext
from tests.support import (
    ScriptedLLMProvider,
    generation_json,
    intent_json,
    parsed_document,
    plan_json,
    text_page,
)

DESIGN = build_default_design_registry()
INVALID_UI = generation_json(text_page({"type": "carousel", "id": "slides"}))
PLAN = UIPlan(
    intent=UIIntent.COMPARISON,
    title="Sales",
    required_data=["sales_by_region"],
    recommended_components=[],
    notes=[],
)
MOVE = {"type": "MOVE", "target": "regional_breakdown", "before": "regional_sales"}


def _planner(llm: ScriptedLLMProvider) -> RequestPlanner:
    return RequestPlanner(llm, UIPlanner(), KeywordIntentClassifier())


def _executor(
    llm: ScriptedLLMProvider, validator: UISchemaValidator, *, max_repair_attempts: int = 1
) -> UIGenerationExecutor:
    return UIGenerationExecutor(
        llm=llm,
        validator=validator,
        registry=build_default_registry(),
        design=DESIGN,
        actions=[],
        options=GenerationOptions(),
        max_repair_attempts=max_repair_attempts,
    )


def _task(context: ValidationContext) -> GenerationTask:
    return GenerationTask(
        user_request="Compare sales across regions",
        plan=PLAN,
        history=[],
        datasets=[],
        validation_context=context,
        base_theme=DESIGN.default_theme(),
        design=DESIGN.default_design(),
    )


async def _planning_request() -> PlanningRequest:
    return PlanningRequest(
        user_request="Compare sales across regions",
        history=[],
        datasets=await MockSalesDataProvider().list_datasets(),
        available_components=build_default_registry().types(),
    )


# --- Intent planning ------------------------------------------------------------


async def test_planner_uses_the_models_intent_analysis(llm: ScriptedLLMProvider) -> None:
    llm.script(intent_json("trend", "sales_by_month"))

    plan = await _planner(llm).plan(await _planning_request())

    assert plan.intent is UIIntent.TREND
    assert plan.required_data == ["sales_by_month"]


@pytest.mark.parametrize("bad_output", ["not json", '{"intent": "world_domination"}'])
async def test_planner_falls_back_to_keywords_when_intent_output_is_unusable(
    llm: ScriptedLLMProvider, bad_output: str, caplog: pytest.LogCaptureFixture
) -> None:
    llm.script(bad_output)

    with caplog.at_level(logging.WARNING):
        plan = await _planner(llm).plan(await _planning_request())

    assert plan.intent is UIIntent.COMPARISON
    assert "sales_by_region" in plan.required_data
    assert "intent_analysis_invalid" in [record.message for record in caplog.records]


async def test_planner_does_not_hide_provider_failures(llm: ScriptedLLMProvider) -> None:
    llm.script(LLMProvidersExhaustedException())

    with pytest.raises(LLMProvidersExhaustedException):
        await _planner(llm).plan(await _planning_request())


# --- Generation -----------------------------------------------------------------


async def test_executor_combines_the_generated_page_with_theme_and_design(
    llm: ScriptedLLMProvider, validator: UISchemaValidator, validation_context: ValidationContext
) -> None:
    llm.script(generation_json())

    generated = await _executor(llm, validator).execute(_task(validation_context))

    assert generated.document.page.title == "Sales by Region"
    assert generated.document.theme == DESIGN.default_theme()
    assert generated.document.design.framework == "shadcn"
    assert (generated.provider, generated.repair_attempts) == ("scripted", 0)


async def test_executor_applies_a_theme_preset_chosen_by_the_model(
    llm: ScriptedLLMProvider, validator: UISchemaValidator, validation_context: ValidationContext
) -> None:
    llm.script(generation_json(theme_preset="slate_dark"))

    theme = (await _executor(llm, validator).execute(_task(validation_context))).document.theme

    assert (theme.preset, theme.mode) == ("slate_dark", "dark")
    assert theme.colors.background == "#0B1120"
    assert theme.radius == DESIGN.default_theme().radius, "shape comes from the design system"


@pytest.mark.parametrize(
    ("first_output", "expected_feedback"),
    [
        (INVALID_UI, "carousel"),
        ("definitely not json", "not valid JSON"),
        (json.dumps({"components": []}), 'object with a \\"page\\"'),
        (generation_json(theme_preset="neon"), "Unknown theme preset 'neon'"),
    ],
)
async def test_executor_repairs_invalid_output_using_validator_findings(
    llm: ScriptedLLMProvider,
    validator: UISchemaValidator,
    validation_context: ValidationContext,
    first_output: str,
    expected_feedback: str,
) -> None:
    llm.script(first_output, generation_json())

    generated = await _executor(llm, validator).execute(_task(validation_context))

    assert generated.repair_attempts == 1
    repair_call = llm.calls[1]
    assert repair_call[-2].content == first_output
    assert expected_feedback.replace('\\"', '"') in repair_call[-1].content


async def test_executor_gives_up_after_the_configured_repairs(
    llm: ScriptedLLMProvider, validator: UISchemaValidator, validation_context: ValidationContext
) -> None:
    llm.script(INVALID_UI, "still not json")

    with pytest.raises(UIGenerationException) as error:
        await _executor(llm, validator).execute(_task(validation_context))

    assert len(llm.calls) == 2
    assert error.value.status_code == 502
    assert error.value.details[0]["stage"] == "json_parsing"


async def test_agent_runs_every_stage(
    llm: ScriptedLLMProvider, validator: UISchemaValidator
) -> None:
    agent = GenerativeUIAgent(
        planner=_planner(llm),
        executor=_executor(llm, validator),
        data_provider=MockSalesDataProvider(),
        registry=build_default_registry(),
    )
    llm.script(intent_json("comparison", "sales_by_region", "sales_summary"), generation_json())

    output = await agent.generate(
        UIGenerationInput(
            "Compare sales across regions",
            history=[],
            base_theme=DESIGN.default_theme(),
            design=DESIGN.default_design(),
        )
    )

    assert output.intent is UIIntent.COMPARISON
    generation_prompt = llm.calls[1][1].content
    assert 'dataset "sales_by_region"' in generation_prompt, "planned data reaches the model"
    assert 'dataset "sales_by_month"' not in generation_prompt, "unplanned data does not"
    chart = output.document.page.components[2]
    assert chart.data_source is not None and chart.data == [], "bindings stay bindings"  # type: ignore[union-attr]


# --- Mutation -------------------------------------------------------------------


def _mutation_executor(
    llm: ScriptedLLMProvider, mutator: DocumentMutator, *, max_repair_attempts: int = 1
) -> UIMutationExecutor:
    return UIMutationExecutor(
        llm=llm,
        mutator=mutator,
        registry=build_default_registry(),
        design=DESIGN,
        actions=[],
        options=GenerationOptions(),
        max_repair_attempts=max_repair_attempts,
    )


def _version(number: int, description: str, *, current: bool = False) -> VersionInfo:
    created = datetime(2026, 10, number, 9, 30, tzinfo=UTC)
    return VersionInfo(number, description, "ai_mutation", created, current)


def _mutation_input(
    context: ValidationContext, instruction: str = "Put the table above the chart", **kw: Any
) -> UIMutationInput:
    arguments: dict[str, Any] = {
        "instruction": instruction,
        "document": parsed_document(),
        "selected_component_id": None,
        "versions": [
            _version(3, "Added regional chart", current=True),
            _version(2, "Changed theme to dark"),
            _version(1, "Generated “Sales by Region”"),
        ],
        "history": [],
        "datasets": list(context.datasets.values()),
        "validation_context": context,
    }
    return UIMutationInput(**(arguments | kw))


async def test_edit_returns_validated_operations_and_resulting_document(
    llm: ScriptedLLMProvider, mutator: DocumentMutator, validation_context: ValidationContext
) -> None:
    llm.script(plan_json("I'll put the table above the chart.", MOVE))

    output = await _mutation_executor(llm, mutator).plan(_mutation_input(validation_context))

    assert output.kind is MutationPlanKind.OPERATIONS
    assert output.message == "I'll put the table above the chart."
    assert output.outcome is not None and output.outcome.document is not None
    assert output.outcome.operations == [MOVE]
    assert [c.id for c in output.outcome.document.page.components][2:] == [
        "regional_breakdown",
        "regional_sales",
    ]


async def test_edit_prompt_carries_current_ui_layout_selection_and_versions(
    llm: ScriptedLLMProvider, mutator: DocumentMutator, validation_context: ValidationContext
) -> None:
    llm.script(plan_json("ok", MOVE))
    request = _mutation_input(
        validation_context, "Make this wider", selected_component_id="regional_sales"
    )

    await _mutation_executor(llm, mutator).plan(request)

    system, user = llm.calls[0]
    assert "You never rewrite the whole document" in system.content
    for operation in ("CREATE", "MOVE", "REPLACE", "SET_THEME", "RESTORE_VERSION"):
        assert f'"type":"{operation}"' in system.content
    assert "- slate_dark (dark)" in system.content
    assert '"id":"regional_sales"' in user.content
    assert "row 1: revenue_metric (metric, span 6), orders_metric (metric, span 6)" in user.content
    assert "Selected component\nregional_sales" in user.content
    assert "- version 3 (current): Added regional chart" in user.content
    assert user.content.rstrip().endswith("User request\nMake this wider")


@pytest.mark.parametrize(
    ("bad_plan", "feedback"),
    [
        (plan_json("x", {"type": "DELETE", "target": "ghost"}), "Component 'ghost' does not exist"),
        (plan_json("x", {"type": "EVAL", "code": "alert(1)"}), "Unknown type 'EVAL'"),
        (plan_json("x", {"type": "MOVE", "target": "kpis", "x": 9, "y": 0}), "Extra inputs"),
        (
            plan_json("x", {"type": "CREATE", "component": {"type": "iframe", "id": "f"}}),
            "Unknown type 'iframe'",
        ),
        ("<div onclick='x'>", "not valid JSON"),
        (
            plan_json("x", {"type": "RESTORE_VERSION", "version_number": 9}),
            "Version 9 does not exist",
        ),
        (
            plan_json("x", {"type": "RESTORE_VERSION", "version_number": 3}),
            "already the current version",
        ),
        (
            plan_json("x", {"type": "RESTORE_VERSION", "version_number": 1}, MOVE),
            "must be the only operation",
        ),
    ],
)
async def test_invalid_edits_are_sent_back_with_the_reason(
    llm: ScriptedLLMProvider,
    mutator: DocumentMutator,
    validation_context: ValidationContext,
    bad_plan: str,
    feedback: str,
) -> None:
    llm.script(bad_plan, plan_json("Fixed.", MOVE))

    output = await _mutation_executor(llm, mutator).plan(_mutation_input(validation_context))

    assert output.repair_attempts == 1
    assert feedback in llm.calls[1][-1].content


async def test_edit_fails_when_the_model_never_produces_valid_operations(
    llm: ScriptedLLMProvider, mutator: DocumentMutator, validation_context: ValidationContext
) -> None:
    bad = plan_json("x", {"type": "DELETE", "target": "ghost"})
    llm.script(bad, bad)

    with pytest.raises(UIGenerationException) as error:
        await _mutation_executor(llm, mutator).plan(_mutation_input(validation_context))

    assert error.value.message == "Generated operations are invalid."
    assert error.value.details[0]["stage"] == "operation"


@pytest.mark.parametrize(
    ("operation", "kind"),
    [
        ({"type": "RESTORE_VERSION", "version_number": 2}, MutationPlanKind.RESTORE),
        ({"type": "COMPARE_VERSIONS", "version_number": 1}, MutationPlanKind.COMPARE),
    ],
)
async def test_version_requests_become_structured_version_operations(
    llm: ScriptedLLMProvider,
    mutator: DocumentMutator,
    validation_context: ValidationContext,
    operation: dict[str, Any],
    kind: MutationPlanKind,
) -> None:
    llm.script(plan_json("On it.", operation))

    output = await _mutation_executor(llm, mutator).plan(
        _mutation_input(validation_context, "Go back to before the chart")
    )

    assert (output.kind, output.version_number) == (kind, operation["version_number"])
    assert output.outcome is None, "the model never touches stored versions itself"


async def test_a_reply_without_operations_is_a_plain_message(
    llm: ScriptedLLMProvider, mutator: DocumentMutator, validation_context: ValidationContext
) -> None:
    llm.script(plan_json("I can't add video players; they aren't a registered component."))

    output = await _mutation_executor(llm, mutator).plan(_mutation_input(validation_context))

    assert output.kind is MutationPlanKind.MESSAGE
    assert "video players" in output.message
