"""Edits act at the level the request addresses: application, screen or component."""

import json
from typing import Any

from app.ai.orchestration.application.editing import (
    application_outline,
    screen_of,
)
from app.domains.generative_ui.contracts import (
    MutationPlanKind,
    UIMutationInput,
    UIMutationOutput,
)
from app.domains.generative_ui.document import UIDocument, dump_document
from app.domains.generative_ui.validator import ValidationContext
from scripts.sample_build import SAMPLE_WORKSPACE_ID, build_stack
from tests.support import (
    ScriptedLLMProvider,
    plan_json,
    sample_application_document,
    sample_document,
)

ROUTER = "You route an edit request"
GENERATOR = "You are a senior product designer"
DIRECTOR = "You are the design director"
EDITOR = "You are the editing engine"


async def _edit(
    llm: ScriptedLLMProvider, instruction: str, **overrides: Any
) -> tuple[UIDocument, UIMutationOutput]:
    document = overrides.pop("document", None) or await sample_application_document()
    request = UIMutationInput(
        instruction=instruction,
        document=document,
        selected_component_id=overrides.pop("selected_component_id", None),
        versions=[],
        history=[],
        datasets=[],
        validation_context=overrides.pop("validation_context", None) or ValidationContext(),
        active_screen_id=overrides.pop("active_screen_id", "dashboard"),
        workspace_id=SAMPLE_WORKSPACE_ID,
    )
    return document, await build_stack(llm).editor.plan(request)


def _operation_types(output: UIMutationOutput) -> list[str]:
    assert output.outcome is not None
    return [operation["type"] for operation in output.outcome.operations]


def _screens(document: UIDocument) -> dict[str, Any]:
    return {s["id"]: s for s in dump_document(document)["page"]["components"]}


async def test_restyling_the_application_changes_design_and_no_screen() -> None:
    llm = ScriptedLLMProvider()

    before, output = await _edit(llm, "Make the entire application more premium")

    assert output.kind is MutationPlanKind.OPERATIONS
    assert _operation_types(output) == ["SET_DESIGN_SYSTEM", "SET_THEME", "UPDATE_APPLICATION"]
    after = output.outcome.document  # type: ignore[union-attr]
    assert after is not None
    assert after.design.design_system == "luxury" and after.theme.preset == "stone_ink"
    assert after.theme.typography.heading_font.value == "serif"  # type: ignore[union-attr]
    assert after.application.design_direction.style == "luxury"  # type: ignore[union-attr]
    assert _screens(after) == _screens(before), "no screen was regenerated or changed"
    assert not llm.stage_calls(GENERATOR)
    [director] = llm.stage_calls(DIRECTOR)
    assert "Current design direction" in director[1].content
    assert "Make the entire application more premium" in director[1].content


async def test_dark_mode_is_a_restyle_too() -> None:
    _, output = await _edit(ScriptedLLMProvider(), "Change the application to dark mode")

    after = output.outcome.document  # type: ignore[union-attr]
    assert after is not None and after.theme.mode.value == "dark"


async def test_redesigning_a_screen_replaces_that_screen_only() -> None:
    llm = ScriptedLLMProvider()

    before, output = await _edit(llm, "Redesign the dashboard")

    assert _operation_types(output) == ["REPLACE"]
    assert output.message == "I redesigned “Dashboard”. The other screens are untouched."
    old, new = _screens(before), _screens(output.outcome.document)  # type: ignore[union-attr, arg-type]
    assert new["dashboard"] != old["dashboard"]
    assert [c["type"] for c in new["dashboard"]["children"]] == [
        "stats",
        "chart",
        "collection",
        "chart",
    ]
    assert {k: v for k, v in new.items() if k != "dashboard"} == {
        k: v for k, v in old.items() if k != "dashboard"
    }
    [generator] = llm.stage_calls(GENERATOR)
    assert "Current version of this screen" in generator[1].content
    assert "Change requested\nRedesign the dashboard" in generator[1].content
    after = output.outcome.document  # type: ignore[union-attr]
    assert (
        after is not None
        and after.theme == before.theme
        and after.application == before.application
    )


async def test_adding_a_screen_creates_it_with_its_data_and_a_navigation_item() -> None:
    llm = ScriptedLLMProvider()

    before, output = await _edit(llm, "Add an offers section")

    assert _operation_types(output) == ["UPSERT_ENTITIES", "CREATE", "SET_NAVIGATION"]
    after = output.outcome.document  # type: ignore[union-attr]
    assert after is not None and after.application is not None
    assert [s for s in _screens(after) if s not in _screens(before)] == ["offers"]
    assert after.application.navigation.items[-1].screen_id == "offers"
    offers = next(e for e in after.application.entities if e.name == "offers")
    assert len(offers.records) == 3 and offers.records[0]["salary"] == 92000
    untouched = {k: v for k, v in _screens(after).items() if k != "offers"}
    assert untouched == _screens(before)
    assert len(llm.stage_calls(GENERATOR)) == 1, "only the new screen was generated"


async def test_component_requests_become_operations_on_the_focused_screen() -> None:
    llm = ScriptedLLMProvider()
    llm.script(plan_json("Done", {"type": "RESIZE", "target": "jobs_table", "span": 8}))

    _, output = await _edit(llm, "Make the jobs table narrower", active_screen_id="jobs")

    assert _operation_types(output) == ["RESIZE"]
    [editor] = llm.stage_calls(EDITOR)
    system, prompt = editor[0].content, editor[1].content
    assert "Application rules" in system and "SET_NAVIGATION" in system
    assert "Application outline" in prompt and "- screen pipeline" in prompt
    current = prompt.split("Current screen\n")[1].split("\n\n")[0]
    assert json.loads(current)["id"] == "jobs", "only the focused screen is shown in full"
    assert "pipeline_board" in prompt and '"group_by"' not in current
    assert "- candidates:" in prompt, "the application's entities are available data"


async def test_a_selected_component_skips_routing() -> None:
    llm = ScriptedLLMProvider()
    llm.script(plan_json("Done", {"type": "DELETE", "target": "dashboard_this_week"}))

    _, output = await _edit(
        llm, "Remove this", selected_component_id="dashboard_this_week", active_screen_id="jobs"
    )

    assert _operation_types(output) == ["DELETE"]
    assert not llm.stage_calls(ROUTER)
    [editor] = llm.stage_calls(EDITOR)
    current = editor[1].content.split("Current screen\n")[1].split("\n\n")[0]
    assert json.loads(current)["id"] == "dashboard", "the screen holding the selection is shown"


async def test_changing_navigation_is_one_application_operation() -> None:
    llm = ScriptedLLMProvider()
    llm.script(plan_json("Top navigation it is.", {"type": "SET_NAVIGATION", "style": "topbar"}))

    before, output = await _edit(llm, "Change the sidebar to a top navigation")

    after = output.outcome.document  # type: ignore[union-attr]
    assert after is not None and after.application is not None
    assert after.application.navigation.style.value == "topbar"
    assert _screens(after) == _screens(before)


async def test_a_single_view_is_edited_directly_without_routing(
    validation_context: ValidationContext,
) -> None:
    llm = ScriptedLLMProvider()
    llm.script(plan_json("Done", {"type": "DELETE", "target": "regional_breakdown"}))
    document = UIDocument.model_validate(sample_document())

    _, output = await _edit(
        llm,
        "Remove the table",
        document=document,
        active_screen_id=None,
        validation_context=validation_context,
    )

    assert _operation_types(output) == ["DELETE"]
    assert len(llm.calls) == 1
    system = llm.calls[0][0].content
    assert "Application rules" not in system
    assert "- hero:" not in system, "a single view is offered primitives only"


async def test_outline_lists_every_screen_and_finds_a_components_screen() -> None:
    document = await sample_application_document()

    outline = application_outline(document)

    assert "Application: Hirewell (Recruitment SaaS)" in outline
    assert (
        "- screen candidate_detail “Candidate” (detail, route /candidates/:candidateId)" in outline
    )
    assert "pipeline_board (kanban)" in outline
    assert screen_of(document, "pipeline_board") == "pipeline"
    assert screen_of(document, "pipeline") == "pipeline"
    assert screen_of(document, "ghost") is None
