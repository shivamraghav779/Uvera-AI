"""The design review: what it flags, and what it leaves alone."""

from collections.abc import Callable
from typing import Any

from app.domains.generation.quality import (
    DesignQualityEvaluator,
    QualityCategory,
    QualityReport,
    Severity,
    refinement_briefs,
)
from app.domains.generative_ui.design_registry import build_default_design_registry
from app.domains.generative_ui.document import UIDocument
from tests.support import sample_application

EVALUATOR = DesignQualityEvaluator(build_default_design_registry())
Document = dict[str, Any]


async def _review(change: Callable[[Document], None] | None = None) -> QualityReport:
    document = await sample_application()
    if change is not None:
        change(document)
    return EVALUATOR.evaluate(UIDocument.model_validate(document))


def _screen(document: Document, screen_id: str) -> dict[str, Any]:
    return next(s for s in document["page"]["components"] if s["id"] == screen_id)


def _categories(report: QualityReport, screen_id: str | None = None) -> set[QualityCategory]:
    return {issue.category for issue in report.issues if issue.screen_id == screen_id}


async def test_a_well_composed_application_scores_high_with_nothing_major() -> None:
    report = await _review()

    assert report.score >= 90
    assert not [issue for issue in report.issues if issue.severity is Severity.MAJOR]
    assert report.screens_to_refine == []


async def test_placeholder_wording_is_a_major_content_finding() -> None:
    def spoil(document: Document) -> None:
        media = _screen(document, "dashboard")["children"][-1]
        media["title"] = "Feature 1"
        media["body"] = "Lorem ipsum dolor sit amet."

    report = await _review(spoil)

    [issue] = [i for i in report.issues if i.category is QualityCategory.CONTENT]
    assert issue.severity is Severity.MAJOR and issue.screen_id == "dashboard"
    assert "feature 1" in issue.message and "lorem ipsum" in issue.message
    assert report.screens_to_refine == ["dashboard"]


async def test_a_dashboard_that_opens_with_a_table_has_weak_hierarchy() -> None:
    def table_first(document: Document) -> None:
        dashboard = _screen(document, "dashboard")
        table = {"type": "table", "id": "dashboard_first_table",
                 "columns": [{"key": "title", "label": "Role"}],
                 "data_source": {"dataset": "jobs"}}  # fmt: skip
        dashboard["children"].insert(0, table)

    assert QualityCategory.HIERARCHY in _categories(await _review(table_first), "dashboard")


async def test_repeating_one_component_is_flagged_as_lack_of_variety() -> None:
    def repeat(document: Document) -> None:
        screen = _screen(document, "candidates")
        screen["children"] = [
            {"type": "card", "id": f"candidates_card_{n}", "title": f"Group {n}",
             "children": [{"type": "text", "id": f"candidates_text_{n}", "content": "Notes"}]}
            for n in range(5)
        ]  # fmt: skip

    report = await _review(repeat)

    assert QualityCategory.VARIETY in _categories(report, "candidates")
    assert QualityCategory.COMPLETENESS in _categories(report, "candidates"), "and shows no data"


async def test_an_unlinked_screen_is_a_navigation_finding_for_the_application() -> None:
    def unlink(document: Document) -> None:
        _screen(document, "jobs")["children"][1]["action"]["payload"]["to"] = "/candidates"

    report = await _review(unlink)

    [issue] = [i for i in report.issues if i.category is QualityCategory.NAVIGATION]
    assert issue.screen_id is None and "Create job" in issue.message


async def test_effects_outside_the_style_and_in_excess_are_flagged() -> None:
    def glow(document: Document) -> None:
        for child in _screen(document, "dashboard")["children"]:
            child["style"] = {"effects": ["glow", "marquee"]}

    report = await _review(glow)

    messages = [i.message for i in report.issues if i.category is QualityCategory.EFFECTS]
    assert any("do not belong to this style" in m for m in messages)
    assert any("uses 8 effects" in m for m in messages)


async def test_an_image_led_direction_without_images_is_flagged() -> None:
    def drop_image(document: Document) -> None:
        del _screen(document, "dashboard")["children"][-1]["image"]

    assert QualityCategory.IMAGERY in _categories(await _review(drop_image))


async def test_one_rich_component_can_be_a_whole_screen() -> None:
    report = await _review()

    assert not report.for_screen("pipeline"), "a board on its own is a complete screen"


async def test_refinement_briefs_cover_the_worst_screens_with_what_to_fix() -> None:
    def spoil(document: Document) -> None:
        for screen_id in ("dashboard", "candidates"):
            _screen(document, screen_id)["children"][-1]["title"] = "Lorem ipsum"
        dashboard = _screen(document, "dashboard")
        dashboard["children"].insert(
            0, {"type": "table", "id": "dashboard_t", "columns": [{"key": "title", "label": "T"}],
                "data_source": {"dataset": "jobs"}}
        )  # fmt: skip

    report = await _review(spoil)
    briefs = refinement_briefs(report, limit=1)

    assert [brief.screen_id for brief in briefs] == ["dashboard"], "most findings first"
    assert "Placeholder wording" in briefs[0].as_text()
    assert "Open a dashboard with headline figures" in briefs[0].as_text()


def test_field_names_shown_as_content_are_a_major_finding() -> None:
    from app.domains.generation.quality import _field_names_as_content

    written = {
        "type": "gallery",
        "items": [
            {
                "title": "title",
                "subtitle": "Lisbon",
                "meta": [{"label": "Type", "value": "project_type"}],
            },
            {"title": "Harbour House", "subtitle": "location"},
        ],
    }
    bound = {
        "type": "collection",
        "data_source": {"dataset": "projects"},
        "fields": {"title": "title", "subtitle": "location"},
    }

    assert sorted(_field_names_as_content(written)) == ["project_type", "title"]
    assert list(_field_names_as_content(bound)) == []
