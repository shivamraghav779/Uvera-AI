"""An application is a document with screens and an application section; both are validated."""

from collections.abc import Callable
from typing import Any

import pytest

from app.domains.generative_ui.application import (
    build_graph,
    image_refs,
    match_route,
    resolve_route,
    route_params,
    unreachable_screens,
)
from app.domains.generative_ui.document import UIDocument
from app.domains.generative_ui.mutation_engine import MutationError, apply_operations
from app.domains.generative_ui.validator import UISchemaValidator
from tests.support import sample_application, sample_document, text_page

Document = dict[str, Any]
Change = Callable[[Document], None]


def _screen(document: Document, screen_id: str) -> dict[str, Any]:
    return next(s for s in document["page"]["components"] if s["id"] == screen_id)


async def _messages(validator: UISchemaValidator, change: Change) -> list[tuple[str, str]]:
    document = await sample_application()
    change(document)
    report = validator.inspect_document(document)
    assert report.document is None, "an invalid application must never yield a UI"
    return [(issue.path, issue.message) for issue in report.issues]


async def test_the_sample_application_is_valid_and_has_its_parts(
    validator: UISchemaValidator,
) -> None:
    document = validator.validate_document(await sample_application())

    assert document.application is not None
    assert [screen.id for screen in document.page.components][:3] == [
        "dashboard", "jobs", "job_new",
    ]  # fmt: skip
    assert document.application.navigation.home == "dashboard"
    assert {entity.name for entity in document.application.entities} >= {"jobs", "candidates"}
    assert document.application.assets[0].url.startswith("/api/v1/assets/")
    assert document.design.design_system == "premium_saas"


async def test_component_ids_are_unique_across_screens(validator: UISchemaValidator) -> None:
    document = validator.validate_document(await sample_application())
    ids = [
        node["id"]
        for screen in document.model_dump(mode="json")["page"]["components"]
        for node in screen["children"]
    ]

    assert len(ids) == len(set(ids))
    assert all(node_id.split("_")[0] in {"dashboard", "jobs", "job", "candidates", "candidate",
                                         "pipeline", "interviews"} for node_id in ids)  # fmt: skip


def _nest_a_screen(document: Document) -> None:
    dashboard = _screen(document, "dashboard")
    dashboard["children"].append(
        {"type": "screen", "id": "inner", "title": "Inner", "route": "/inner",
         "children": [{"type": "text", "id": "inner_text", "content": "x"}]}
    )  # fmt: skip


def _mix_screens_and_components(document: Document) -> None:
    document["page"]["components"].append({"type": "text", "id": "stray", "content": "x"})


def _clash_routes(document: Document) -> None:
    _screen(document, "jobs")["route"] = "/candidates/:id"


def _unknown_home(document: Document) -> None:
    document["application"]["navigation"]["home"] = "nowhere"


def _parameterised_nav_item(document: Document) -> None:
    document["application"]["navigation"]["items"][0]["screen_id"] = "candidate_detail"


def _unknown_record_field(document: Document) -> None:
    document["application"]["entities"][0]["records"][0]["salary"] = 1


def _duplicate_record_id(document: Document) -> None:
    records = document["application"]["entities"][0]["records"]
    records[1]["id"] = records[0]["id"]


def _unknown_asset(document: Document) -> None:
    _screen(document, "dashboard")["children"][-1]["image"] = "missing_image"


def _unknown_route(document: Document) -> None:
    button = _screen(document, "jobs")["children"][1]
    button["action"]["payload"]["to"] = "/nowhere"


def _unknown_param(document: Document) -> None:
    header = _screen(document, "candidate_detail")["children"][0]
    header["data_source"]["where"][0]["param"] = "jobId"


def _unknown_entity_in_action(document: Document) -> None:
    form = _screen(document, "job_new")["children"][0]
    form["submit_action"]["payload"]["entity"] = "invoices"


def _unknown_binding_field(document: Document) -> None:
    board = _screen(document, "pipeline")["children"][0]
    board["group_by"] = "seniority"


def _external_asset_url(document: Document) -> None:
    document["application"]["assets"][0]["url"] = "https://example.org/x.png"


def _script_in_application_text(document: Document) -> None:
    document["application"]["description"] = "<script>alert(1)</script>"


@pytest.mark.parametrize(
    ("change", "path", "fragment"),
    [
        (_nest_a_screen, "page.components.0.children.4", "directly under the page"),
        (_mix_screens_and_components, "page.components", "either screens only"),
        (_clash_routes, "page.components.4.route", "clashes with screen 'jobs'"),
        (_unknown_home, "application.navigation.home", "is not a screen"),
        (_parameterised_nav_item, "application.navigation.items.0.screen_id", "parameters"),
        (_unknown_record_field, "application.entities.0.records.0", "Unknown field(s) salary"),
        (_duplicate_record_id, "application.entities.0.records", "is used 2 times"),
        (_unknown_asset, "page.components.0.children.3.image", "is not an asset"),
        (_unknown_route, "page.components.1.children.1.action.payload.to", "not a screen of"),
        (_unknown_param, "page.components.4.children.0.data_source.where.0.param", "parameter"),
        (_unknown_entity_in_action, "page.components.2.children.0.submit_action.payload.entity",
         "is not an entity"),
        (_unknown_binding_field, "page.components.5.children.0", "has no field 'seniority'"),
        (_external_asset_url, "application.assets.0.url", "String should match pattern"),
        (_script_in_application_text, "application.description", "only plain text"),
    ],
    ids=lambda value: getattr(value, "__name__", None),
)  # fmt: skip
async def test_broken_applications_are_rejected_with_the_place_and_reason(
    validator: UISchemaValidator, change: Change, path: str, fragment: str
) -> None:
    issues = await _messages(validator, change)

    assert any(p == path and fragment in message for p, message in issues), issues


def test_screens_need_an_application_section(validator: UISchemaValidator) -> None:
    screen = {"type": "screen", "id": "home", "title": "Home", "route": "/",
              "children": [{"type": "text", "id": "t", "content": "x"}]}  # fmt: skip

    report = validator.inspect_document(sample_document(text_page(screen)))

    assert [issue.message for issue in report.issues] == [
        "Screens need an 'application' section describing the product."
    ]


# --- Routes and the screen graph ------------------------------------------------------


def test_routes_match_and_resolve() -> None:
    routes = {"jobs": "/jobs", "job_new": "/jobs/new", "job": "/jobs/:jobId"}

    assert route_params("/a/:x/b/:y") == ["x", "y"]
    assert match_route("/jobs/:jobId", "/jobs/j-1") == {"jobId": "j-1"}
    assert match_route("/jobs/:jobId", "/jobs") is None
    assert resolve_route(routes, "/jobs/new") == "job_new", "a static route wins"
    assert resolve_route(routes, "/jobs/j-1") == "job"
    assert resolve_route(routes, "/jobs/:jobId") == "job", "a route pattern names its screen"
    assert resolve_route(routes, "/nowhere") is None


async def test_graph_links_screens_by_navigation_actions_and_shared_data() -> None:
    document = UIDocument.model_validate(await sample_application())

    graph = build_graph(document)
    edges = {(edge.source, edge.target, edge.kind.value) for edge in graph.edges}

    assert [node.id for node in graph.nodes if node.is_home] == ["dashboard"]
    assert ("candidates", "candidate_detail", "action") in edges, "rows open the record"
    assert ("job_new", "jobs", "action") in edges, "creating a job returns to the list"
    assert ("dashboard", "pipeline", "navigation") in edges
    assert any(kind == "data" for _, _, kind in edges)
    assert unreachable_screens(document) == []


async def test_a_screen_nothing_leads_to_is_reported_unreachable() -> None:
    raw = await sample_application()
    # Remove the only way to the create-job screen.
    _screen(raw, "jobs")["children"][1]["action"]["payload"]["to"] = "/candidates"

    assert unreachable_screens(UIDocument.model_validate(raw)) == ["job_new"]


def test_image_refs_find_assets_but_not_record_field_maps() -> None:
    node = {
        "type": "hero", "image": "hero_image",
        "items": [{"image": "tile_1"}, {"avatar": "face_1"}],
        "fields": {"image": "photo", "avatar": True},
    }  # fmt: skip

    assert sorted(asset for _, asset in image_refs(node)) == ["face_1", "hero_image", "tile_1"]


# --- Application-level operations -----------------------------------------------------


async def test_set_navigation_changes_only_what_it_names() -> None:
    document = await sample_application()

    result = apply_operations(document, [{"type": "SET_NAVIGATION", "style": "topbar"}])

    assert result["application"]["navigation"]["style"] == "topbar"
    assert (
        result["application"]["navigation"]["items"]
        == document["application"]["navigation"]["items"]
    )
    assert result["page"] == document["page"], "the screens are untouched"
    assert document["application"]["navigation"]["style"] == "sidebar", "input is not modified"


async def test_update_application_merges_descriptive_fields_only() -> None:
    document = await sample_application()

    renamed = apply_operations(
        document, [{"type": "UPDATE_APPLICATION", "props": {"name": "Hireflow", "goals": None}}]
    )
    assert renamed["application"]["name"] == "Hireflow"
    assert "goals" not in renamed["application"]

    with pytest.raises(MutationError, match="cannot change 'entities'"):
        apply_operations(document, [{"type": "UPDATE_APPLICATION", "props": {"entities": []}}])


async def test_assets_and_entities_are_upserted_by_key() -> None:
    document = await sample_application()
    asset = {**document["application"]["assets"][0], "id": "second", "alt": "Another"}
    replaced = {**document["application"]["assets"][0], "alt": "Replaced"}
    jobs = {**document["application"]["entities"][0], "label": "Roles"}

    result = apply_operations(
        document,
        [
            {"type": "ADD_ASSETS", "assets": [asset, replaced]},
            {"type": "UPSERT_ENTITIES", "entities": [jobs]},
        ],
    )

    assert [a["id"] for a in result["application"]["assets"]] == ["hiring_team", "second"]
    assert result["application"]["assets"][0]["alt"] == "Replaced"
    assert result["application"]["entities"][0]["label"] == "Roles"
    assert len(result["application"]["entities"]) == len(document["application"]["entities"])


async def test_deleting_a_screen_keeps_the_navigation_consistent() -> None:
    document = await sample_application()

    without_jobs = apply_operations(document, [{"type": "DELETE", "target": "jobs"}])
    without_home = apply_operations(document, [{"type": "DELETE", "target": "dashboard"}])

    nav = without_jobs["application"]["navigation"]
    assert "jobs" not in [item["screen_id"] for item in nav["items"]]
    assert without_home["application"]["navigation"]["home"] == "jobs", "the next screen is home"


def test_application_operations_are_refused_for_a_single_view() -> None:
    document = sample_document()

    with pytest.raises(MutationError, match="not an application"):
        apply_operations(document, [{"type": "SET_NAVIGATION", "style": "topbar"}])
