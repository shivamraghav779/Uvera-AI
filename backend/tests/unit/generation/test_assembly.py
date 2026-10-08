"""Plans become consistent parts of a document: blueprint, design, data, screens."""

from typing import Any

import pytest

from app.domains.assets.schemas import AssetDecision
from app.domains.generation.assembly import (
    ScreenContext,
    blueprint_from_document,
    build_entities,
    build_navigation,
    build_screen,
    ensure_unique_ids,
    normalise_screen_plans,
    placeholder_screen,
    plan_assets,
    resolve_design,
)
from app.domains.generation.blueprint import (
    ApplicationBlueprint,
    AssetBrief,
    DataPlan,
    DesignPlan,
    ScreenBrief,
    ScreenPlan,
    normalise_blueprint,
    slug,
)
from app.domains.generative_ui.color import contrast_ratio
from app.domains.generative_ui.design_registry import build_default_design_registry
from app.domains.generative_ui.document import ThemeMode
from app.domains.generative_ui.pattern_registry import build_default_pattern_registry
from app.domains.generative_ui.schemas import ScreenType, ScreenWidth
from app.domains.generative_ui.validator import MIN_TEXT_CONTRAST
from scripts import sample_app
from tests.support import sample_application_document

DESIGN = build_default_design_registry()
PATTERNS = build_default_pattern_registry()


def _blueprint(**overrides: Any) -> ApplicationBlueprint:
    return normalise_blueprint(
        ApplicationBlueprint.model_validate(sample_app.BLUEPRINT | overrides), max_screens=10
    )


def test_slug_makes_identifiers() -> None:
    assert slug("Candidate Details!") == "candidate_details"
    assert slug("42 things", "screen") == "screen_42_things"
    assert slug("", "item") == "item"


def test_blueprint_ids_routes_and_references_are_made_consistent() -> None:
    blueprint = _blueprint(
        home="Not A Screen",
        screens=[
            {"id": "Home Page", "name": "Home", "route": "/", "type": "landing"},
            {"id": "home_page", "name": "Duplicate id", "route": "/dup"},
            {"id": "detail", "name": "Detail", "route": "/items/:itemId", "in_navigation": True,
             "entity": "ghosts"},
            {"id": "clash", "name": "Clash", "route": "/items/:otherId"},
            {"id": "weird", "name": "Weird", "route": "items/<script>/ok"},
        ],
    )  # fmt: skip

    by_id = {screen.id: screen for screen in blueprint.screens}
    assert list(by_id) == ["home_page", "home_page_2", "detail", "clash", "weird"]
    assert by_id["detail"].in_navigation is False, "a route with parameters is not a menu item"
    assert by_id["detail"].entity is None, "unknown entities are dropped"
    assert by_id["clash"].route == "/clash", "two routes of the same shape cannot coexist"
    assert by_id["weird"].route == "/items/ok", "unsafe segments are removed"
    assert blueprint.home == "home_page", "home falls back to the first static screen"


def test_blueprint_is_capped_and_entities_are_cleaned() -> None:
    blueprint = normalise_blueprint(
        ApplicationBlueprint.model_validate(
            sample_app.BLUEPRINT
            | {
                "entities": [
                    {"name": "Open Roles", "label": "Roles", "title_field": "missing",
                     "fields": [{"key": "id", "label": "Id"}, {"key": "Job Title", "label": "T"},
                                {"key": "job_title", "label": "Again"},
                                {"key": "owner", "label": "Owner", "type": "reference",
                                 "references": "nobody"}]},
                    {"name": "empty", "label": "Empty", "fields": []},
                ]
            }
        ),
        max_screens=3,
    )  # fmt: skip

    assert len(blueprint.screens) == 3
    [entity] = blueprint.entities
    assert (entity.name, entity.title_field) == ("open_roles", "job_title")
    assert [f.key for f in entity.fields] == ["job_title", "owner"], "id and duplicates removed"
    assert entity.fields[1].type.value == "text", "a reference to nothing is plain text"


# --- Design ----------------------------------------------------------------------------


def test_design_plan_resolves_to_style_tokens_and_palette() -> None:
    resolved = resolve_design(
        DesignPlan.model_validate(sample_app.DESIGN), DESIGN, framework="shadcn"
    )

    assert resolved.design.design_system == "premium_saas"
    assert resolved.theme.preset == "indigo_mist"
    assert resolved.theme.typography.heading_font.value == "geometric"  # type: ignore[union-attr]
    assert [effect.value for effect in resolved.direction.effects] == ["reveal", "hover_lift"]


def test_unknown_style_and_palette_fall_back_to_the_catalogue() -> None:
    plan = DesignPlan(style="vaporwave", summary="luxury hotel", palette="nope")

    resolved = resolve_design(plan, DESIGN, framework="shadcn")

    assert resolved.design.design_system == "luxury", "retrieved from the brief"
    assert resolved.theme.preset in DESIGN.design_system("luxury").palettes  # type: ignore[union-attr]


def test_a_stated_mode_outranks_a_palette_of_the_other_mode() -> None:
    plan = DesignPlan(style="premium_saas", palette="indigo_mist", mode=ThemeMode.DARK)

    assert resolve_design(plan, DESIGN, framework="shadcn").theme.mode is ThemeMode.DARK


def test_unreadable_colour_overrides_are_ignored_and_readable_ones_kept() -> None:
    base = {"style": "modern_minimal", "palette": "blue_white"}
    unreadable = DesignPlan.model_validate(base | {"colors": {"foreground": "#F8FAFC"}})
    readable = DesignPlan.model_validate(base | {"colors": {"primary": "#0F766E"}})

    kept = resolve_design(unreadable, DESIGN, framework="shadcn").theme
    changed = resolve_design(readable, DESIGN, framework="shadcn").theme

    assert kept.preset == "blue_white"
    assert contrast_ratio(kept.colors.foreground, kept.colors.background) >= MIN_TEXT_CONTRAST
    assert (changed.colors.primary, changed.preset) == ("#0F766E", None)


def test_user_preferences_win_over_the_director() -> None:
    plan = DesignPlan.model_validate(sample_app.DESIGN)

    resolved = resolve_design(
        plan, DESIGN, framework="material", forced_style="editorial", forced_palette="warm_sand"
    )

    assert (resolved.design.design_system, resolved.design.framework) == ("editorial", "material")
    assert resolved.theme.preset == "warm_sand"


def test_invalid_token_overrides_are_dropped_one_by_one() -> None:
    plan = DesignPlan.model_validate(
        {"style": "modern_minimal", "tokens": {"radius": "enormous", "density": "compact"}}
    )

    theme = resolve_design(plan, DESIGN, framework="shadcn").theme

    assert (theme.radius.value, theme.density.value) == ("md", "compact")


# --- Data ------------------------------------------------------------------------------


def test_records_are_typed_limited_to_declared_fields_and_given_ids() -> None:
    blueprint = _blueprint()
    jobs = next(entity for entity in blueprint.entities if entity.name == "jobs")
    plan = DataPlan.model_validate(
        {"entities": [{"name": "Jobs", "records": [
            {"id": "j1", "title": "Designer", "openings": "3", "secret": "x"},
            {"title": "Engineer", "openings": "many", "posted_on": 20260101},
            {"id": "j1", "title": "Duplicate id"},
        ]}]}
    )  # fmt: skip

    [entity] = build_entities([jobs], plan)

    first, second, third = entity.records
    assert first["openings"] == 3 and "secret" not in first
    assert second["id"] == "job-002" and second["openings"] is None
    assert second["posted_on"] == "20260101"
    assert third["id"] != first["id"], "ids stay unique"
    assert set(first) == {
        "id",
        "title",
        "department",
        "location",
        "status",
        "openings",
        "posted_on",
    }


# --- Screen plans and assets -------------------------------------------------------------


def test_screen_plans_keep_known_patterns_and_fill_gaps_from_the_catalogue() -> None:
    blueprint = _blueprint()
    plans = normalise_screen_plans(
        [ScreenPlan.model_validate(
            {"screen_id": "dashboard", "width": "wide",
             "sections": [{"pattern": "stats.strip"}, {"pattern": "carousel.fancy"},
                          {"pattern": "chart", "entity": "ghosts"}]}
        )],
        blueprint,
        PATTERNS,
    )  # fmt: skip

    assert [s.pattern for s in plans["dashboard"].sections] == ["stats.strip", "chart"]
    assert plans["dashboard"].sections[1].entity is None
    assert set(plans) == {screen.id for screen in blueprint.screens}, "every screen has a plan"
    assert plans["job_new"].width is ScreenWidth.NARROW, "forms default to a narrow column"
    assert plans["pipeline"].sections, "an unplanned screen starts from a catalogue composition"


def test_asset_plans_are_filtered_named_and_capped() -> None:
    blueprint = _blueprint()
    briefs = [
        AssetBrief(id="Hero Image", decision=AssetDecision.SEARCH, query="team at work",
                   screen_id="dashboard", width=5000, height=10),
        AssetBrief(id="hero image", prompt="duplicate id"),
        AssetBrief(id="icon", decision=AssetDecision.ICON, prompt="an icon"),
        AssetBrief(id="chart", decision=AssetDecision.DATA_VISUALIZATION, prompt="a chart"),
        AssetBrief(id="empty"),
        AssetBrief(id="third", prompt="a third image", screen_id="nowhere"),
        AssetBrief(id="fourth", prompt="over the limit"),
    ]  # fmt: skip

    planned, by_id = plan_assets(briefs, blueprint, limit=2)

    assert [asset.id for asset in planned] == ["hero_image", "third"]
    assert (planned[0].width, planned[0].height) == (1920, 256), "sizes are clamped"
    assert planned[0].alt == "team at work" and planned[1].screen_id is None
    assert set(by_id) == {"hero_image", "third"}


# --- Screens ---------------------------------------------------------------------------

CONTEXT = ScreenContext(
    routes={"dashboard": "/", "jobs": "/jobs", "candidate_detail": "/candidates/:candidateId"},
    home_route="/",
    asset_ids=frozenset({"hero"}),
    entity_names=frozenset({"jobs"}),
)
BRIEF = ScreenBrief(id="jobs", name="Jobs", route="/jobs", type=ScreenType.LISTING)
PLAN = ScreenPlan(screen_id="jobs")


def _build(*children: dict[str, Any]) -> dict[str, Any]:
    return build_screen(BRIEF, PLAN, list(children), CONTEXT, {"page", "jobs"})


def test_ids_are_namespaced_and_references_follow() -> None:
    screen = _build(
        {"type": "select", "id": "filter", "name": "status", "label": "Status",
         "options": [{"label": "Open", "value": "Open"}],
         "on_change": {"type": "filter", "payload": {"dataset": "jobs", "field": "status",
                                                     "target": "table"}}},
        {"type": "table", "id": "table", "columns": [{"key": "title", "label": "Title"}],
         "data_source": {"dataset": "jobs"}},
        {"type": "text", "id": "table", "content": "same id again",
         "visible_when": {"field": "filter", "operator": "is_set"}},
    )  # fmt: skip

    select, table, text = screen["children"]
    assert [select["id"], table["id"], text["id"]] == ["jobs_filter", "jobs_table", "jobs_table_2"]
    assert select["on_change"]["payload"]["target"] == "jobs_table"
    assert text["visible_when"]["field"] == "jobs_filter"
    assert (screen["id"], screen["route"], screen["screen_type"]) == ("jobs", "/jobs", "listing")


def test_dangling_images_and_broken_actions_are_repaired_or_removed() -> None:
    screen = _build(
        {"type": "hero", "id": "hero", "title": "Roles", "image": "missing",
         "actions": [
             {"label": "Go", "action": {"type": "navigate", "payload": {"to": "/job"}}},
             {"label": "Break", "action": {"type": "record_delete", "payload": {"entity": "x"}}},
         ]},
        {"type": "image", "id": "picture", "image": "missing"},
        {"type": "image", "id": "kept", "image": "hero", "caption": None},
        {"type": "button", "id": "dead", "label": "Dead",
         "action": {"type": "record_update", "payload": {"entity": "ghosts"}}},
        {"type": "table", "id": "t", "columns": [{"key": "title", "label": "Title"}],
         "data_source": {"dataset": "jobs"},
         "row_action": {"type": "record_delete", "payload": {"entity": "ghosts"}}},
        {"type": "form", "id": "f",
         "fields": [{"type": "input", "id": "a", "name": "a", "label": "A"}],
         "submit_action": {"type": "record_create", "payload": {"entity": "ghosts"}}},
        "not a component",
    )  # fmt: skip

    hero, kept, table, form = screen["children"]
    assert "image" not in hero, "an unknown asset is not referenced"
    assert [a["action"]["payload"]["to"] for a in hero["actions"]] == ["/jobs"], (
        "a near-miss route is corrected; an action on an unknown entity is dropped"
    )
    assert kept["image"] == "hero" and "caption" not in kept
    assert "row_action" not in table, "an optional action that cannot work is removed"
    assert form["submit_action"] == {"type": "submit", "payload": {}}, "the form stays usable"


def test_marketing_screens_do_not_repeat_their_title() -> None:
    plan = ScreenPlan(screen_id="jobs", width=ScreenWidth.FULL)

    screen = build_screen(
        BRIEF, plan, [{"type": "text", "id": "t", "content": "x"}], CONTEXT, set()
    )

    assert (screen["width"], screen["show_title"]) == ("full", False)


def test_ids_are_unique_across_independently_built_screens() -> None:
    first = {"id": "job", "children": [{"id": "job_details_list", "type": "list"}]}
    second = {"id": "job_details", "children": [
        {"id": "job_details_list", "type": "list"},
        {"id": "job_details_button", "type": "button",
         "action": {"type": "refresh", "payload": {"target": "job_details_list"}}},
    ]}  # fmt: skip

    ensure_unique_ids([first, second])

    renamed = second["children"][0]["id"]
    assert renamed == "job_details_list_2"
    assert second["children"][1]["action"]["payload"]["target"] == renamed


def test_a_failed_screen_gets_a_stand_in_that_says_so() -> None:
    screen = placeholder_screen(BRIEF, "It could not be generated this time.")

    assert (screen["id"], screen["route"]) == ("jobs", "/jobs")
    assert screen["children"][0]["type"] == "alert"
    assert "regenerate “Jobs”" in screen["children"][0]["message"]


# --- Round trip --------------------------------------------------------------------------


async def test_a_document_yields_the_blueprint_it_was_built_from() -> None:
    document = await sample_application_document()

    blueprint = blueprint_from_document(document)

    assert [screen.id for screen in blueprint.screens] == [
        s["id"] for s in sample_app.BLUEPRINT["screens"]
    ]
    assert {s.id for s in blueprint.screens if s.in_navigation} == {
        "dashboard", "jobs", "candidates", "pipeline", "interviews",
    }  # fmt: skip
    assert blueprint.screen("candidate_detail").entity == "candidates"  # type: ignore[union-attr]
    assert build_navigation(blueprint).home == "dashboard"


@pytest.mark.parametrize("screen_id", ["dashboard", "pipeline", "candidate_detail"])
async def test_blueprint_screens_keep_their_routes(screen_id: str) -> None:
    document = await sample_application_document()
    expected = next(s for s in sample_app.BLUEPRINT["screens"] if s["id"] == screen_id)

    assert blueprint_from_document(document).screen(screen_id).route == expected["route"]  # type: ignore[union-attr]


def test_small_schema_slips_are_repaired_without_guessing() -> None:
    screen = _build(
        {"type": "hero", "id": "hero", "title": "T" * 250, "tagline": "not a field",
         "style": {"surface": "shiny", "tone": "primary", "effects": ["reveal"] * 5},
         "actions": [{"label": "Go", "icon_position": "left",
                      "action": {"type": "navigate", "payload": {"to": "/jobs"}}}]},
        {"type": "stats", "id": "kpis", "variant": "ribbon",
         "items": [{"label": "Open", "value": 3, "colour": "red"}]},
        {"type": "chart", "id": "broken", "x_key": "a", "y_keys": ["b"],
         "data_source": {"dataset": "jobs"}},
    )  # fmt: skip

    hero, stats, chart = screen["children"]
    assert "tagline" not in hero and "icon_position" not in hero["actions"][0]
    assert hero["style"] == {"tone": "primary", "effects": ["reveal"] * 3}, (
        "an unknown token is dropped, an over-long list is cut, valid tokens stay"
    )
    assert len(hero["title"]) == 200 and hero["title"].endswith("…")
    assert "variant" not in stats, "an unknown variant falls back to the default"
    assert "colour" not in stats["items"][0]
    assert "chart_type" not in chart, "a missing required field is not invented"


def test_a_list_or_object_written_into_a_cell_becomes_one_value() -> None:
    from app.domains.generation.blueprint import EntityRecords

    plan = EntityRecords.model_validate(
        {
            "name": "people",
            "records": [
                {
                    "id": "p-1",
                    "skills": ["Rust", "Go", None],
                    "address": {"city": "Porto", "country": "Portugal"},
                    "age": 41,
                    "active": True,
                    "photo": None,
                }
            ],
        }
    )

    assert plan.records == [
        {
            "id": "p-1",
            "skills": "Rust, Go",
            "address": "Porto, Portugal",
            "age": 41,
            "active": True,
            "photo": None,
        }
    ]


def test_pointless_section_wrappers_are_removed_from_a_screen() -> None:
    from app.domains.generation.assembly import unwrap_bare_sections

    hero = {
        "type": "hero",
        "id": "hero",
        "title": "Spaces that last",
        "style": {"effects": ["reveal"]},
    }
    wrapped_hero = {
        "type": "section",
        "id": "s1",
        "variant": "full_bleed",
        "layout": {"span": 12, "height": "auto"},
        "style": {"priority": "primary", "effects": ["parallax", "reveal"]},
        "children": [hero],
    }
    loose = {
        "type": "section",
        "id": "s2",
        "children": [{"type": "stats", "id": "a"}, {"type": "chart", "id": "b"}],
    }
    titled = {
        "type": "section",
        "id": "s3",
        "title": "Our work",
        "children": [{"type": "gallery", "id": "g"}],
    }
    styled_group = {
        "type": "section",
        "id": "s4",
        "variant": "band",
        "children": [{"type": "text", "id": "t1"}, {"type": "text", "id": "t2"}],
    }

    result = unwrap_bare_sections([wrapped_hero, loose, titled, styled_group])

    assert [node["id"] for node in result] == ["hero", "a", "b", "s3", "s4"]
    assert result[0]["style"] == {"priority": "primary", "effects": ["parallax", "reveal"]}
    assert result[0]["layout"] == {"span": 12, "height": "auto"}
    assert hero["style"] == {"effects": ["reveal"]}, "the input is not modified"
