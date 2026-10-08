"""Validation and registry endpoints."""

from typing import Any

import httpx
import pytest

from tests.support import (
    application_with,
    running_client,
    sample_application,
    sample_document,
    stateless_app,
    text_page,
)

UI = "/api/v1/ui"
PRIMITIVE_CATEGORIES = {"layout", "data_display", "input", "feedback"}


async def test_catalogues_are_public_and_need_no_database() -> None:
    """The UI vocabulary is static: readable without signing in, even with the database down."""
    async with running_client(stateless_app(auth_required=True)) as client:
        for path in ("components", "frameworks", "themes", "capabilities", "patterns"):
            response = await client.get(f"{UI}/{path}")
            assert response.status_code == 200, (path, response.text)


async def _validate(client: httpx.AsyncClient, document: dict[str, Any]) -> dict[str, Any]:
    response = await client.post(f"{UI}/validate", json={"document": document})
    assert response.status_code == 200, response.text
    return response.json()["data"]  # type: ignore[no-any-return]


async def _get(client: httpx.AsyncClient, path: str) -> dict[str, Any]:
    response = await client.get(f"{UI}/{path}")
    assert response.status_code == 200, response.text
    return response.json()["data"]  # type: ignore[no-any-return]


async def test_valid_document_is_accepted_and_normalised(client: httpx.AsyncClient) -> None:
    result = await _validate(client, sample_document())

    assert result["valid"] is True
    assert result["issues"] == []
    assert result["document"]["page"]["id"] == "page", "defaults are filled in"
    assert result["document"]["page"]["components"][2]["layout"] == {"span": 12, "height": "auto"}


@pytest.mark.parametrize(
    ("page", "stage", "path"),
    [
        (text_page({"type": "video", "id": "clip", "src": "x.mp4"}), "schema", "page.components.0"),
        (
            text_page(
                {"type": "button", "id": "b", "label": "x", "action": {"type": "drop_tables"}}
            ),
            "schema",
            "page.components.0.button.action.type",
        ),
        (
            text_page({"type": "text", "id": "xss", "content": "<script>fetch('/steal')</script>"}),
            "semantic",
            "page.components.0.content",
        ),
    ],
    ids=["unknown-component", "unknown-action", "script"],
)
async def test_invalid_documents_are_rejected(
    client: httpx.AsyncClient, page: dict[str, Any], stage: str, path: str
) -> None:
    result = await _validate(client, sample_document(page))

    assert result["valid"] is False
    assert "document" not in result
    assert (result["issues"][0]["stage"], result["issues"][0]["path"]) == (stage, path)


async def test_component_catalogue_describes_the_registry(client: httpx.AsyncClient) -> None:
    data = await _get(client, "components")

    assert data["schema_version"] == "3.0"
    assert len(data["components"]) == 41
    assert data["allowed_actions"] == [
        "export", "filter", "generate", "navigate", "record_create", "record_delete",
        "record_update", "refresh", "search", "sort", "submit",
    ]  # fmt: skip
    hero = next(c for c in data["components"] if c["type"] == "hero")
    assert (hero["category"], hero["variants"][0]) == ("pattern", "split")
    chart = next(c for c in data["components"] if c["type"] == "chart")
    assert chart["category"] == "data_display"
    assert data["json_schema"]["title"] == "UIDocument"


async def test_every_catalogue_example_passes_validation_inside_a_page(
    client: httpx.AsyncClient,
) -> None:
    components = (await _get(client, "components"))["components"]
    examples = {component["type"]: component["example"] for component in components}

    # Pattern and record examples describe parts of the sample application (its entities,
    # routes and images), so they are validated inside it.
    primitive = {c["type"] for c in components if c["category"] in PRIMITIVE_CATEGORIES}
    for component_type, example in examples.items():
        if component_type == "page":
            document = sample_document(example)
        elif component_type == "select":
            # The select example filters the chart example, so they are validated together.
            document = sample_document(text_page(example, examples["chart"]))
        elif component_type in primitive:
            document = sample_document(text_page(example))
        elif component_type == "screen":
            # The example is the sample application's own candidates screen, simplified.
            document = await sample_application()
            screens = document["page"]["components"]
            screens[[s["id"] for s in screens].index(example["id"])] = example
        else:
            document = await application_with(example)
        result = await _validate(client, document)
        assert result["valid"], (component_type, result["issues"])


async def test_frameworks_and_design_systems_are_described_as_metadata(
    client: httpx.AsyncClient,
) -> None:
    data = await _get(client, "frameworks")

    assert (data["default_framework"], data["default_design_system"]) == (
        "shadcn",
        "modern_minimal",
    )
    statuses = {framework["id"]: framework["status"] for framework in data["frameworks"]}
    assert statuses["shadcn"] == statuses["material"] == "available"
    assert statuses["mui"] == "planned"
    compact = next(s for s in data["design_systems"] if s["id"] == "compact_pro")
    assert compact["tokens"]["density"] == "compact"
    assert "colors" not in compact["tokens"], "design systems never carry colours"


async def test_theme_presets_are_complete_valid_themes(client: httpx.AsyncClient) -> None:
    data = await _get(client, "themes")

    assert data["default_theme"]["preset"] == "blue_white"
    assert {preset["id"] for preset in data["presets"]} >= {"blue_white", "slate_dark"}
    for preset in data["presets"]:
        document = sample_document(text_page(), theme=preset["theme"])
        result = await _validate(client, document)
        assert result["valid"], (preset["id"], result["issues"])


async def test_capabilities_describe_what_a_ui_can_contain(client: httpx.AsyncClient) -> None:
    data = await _get(client, "capabilities")

    assert data["layout"] == {
        "model": "flow-grid",
        "columns": 12,
        "heights": ["auto", "sm", "md", "lg", "xl"],
        "containers": ["page", "section", "card", "tabs", "modal", "form", "screen"],
    }
    assert {"line", "bar", "area", "pie", "donut"} <= set(data["chart_types"])
    assert {"CREATE", "DELETE", "MOVE", "RESIZE", "STYLE", "UPDATE", "REORDER", "GROUP",
            "UNGROUP", "REPLACE"} <= set(data["operations"])  # fmt: skip
    assert data["version_operations"] == ["RESTORE_VERSION", "COMPARE_VERSIONS"]
    assert "colors.primary" in data["theme_tokens"]
    assert len(data["components"]) == 41
    assert {"SET_NAVIGATION", "UPDATE_APPLICATION", "ADD_ASSETS", "UPSERT_ENTITIES"} <= set(
        data["operations"]
    )
    assert data["component_variants"]["hero"] == [
        "split", "centered", "immersive", "editorial", "product",
    ]  # fmt: skip
    assert "glass" in data["surface_variants"] and "gradient" in data["button_variants"]
    assert {"spotlight", "marquee", "counter"} <= set(data["effects"])
    assert {"landing", "dashboard", "detail"} <= set(data["screen_types"])
    assert data["navigation_styles"] == ["sidebar", "topbar", "bottom", "minimal", "none"]
