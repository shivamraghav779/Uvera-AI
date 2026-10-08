"""The version engine: approve -> persist -> reload, restore, compare, stale writes."""

import uuid
from typing import Any

import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from tests.integration.api.flows import (
    API,
    approve_edit,
    approve_generation,
    create_workspace,
    get_version,
    list_versions,
    propose_edit,
    propose_generation,
    save_version,
)
from tests.support import ScriptedLLMProvider, sample_document, text_page

DARK = {"type": "SET_THEME", "preset": "slate_dark"}
MOVE_REVENUE = {"type": "MOVE", "target": "revenue_metric", "after": "orders_metric"}
TABLE_TO_CHART = {
    "type": "REPLACE",
    "target": "regional_breakdown",
    "component": {
        "type": "chart",
        "id": "regional_breakdown",
        "title": "Breakdown",
        "chart_type": "bar",
        "x_key": "region",
        "y_keys": ["revenue"],
        "data_source": {"dataset": "sales_by_region"},
    },
}


@pytest.fixture
async def workspace_id(client: httpx.AsyncClient) -> str:
    return str((await create_workspace(client))["id"])


async def _build_history(
    client: httpx.AsyncClient, llm: ScriptedLLMProvider, workspace_id: str
) -> list[dict[str, Any]]:
    """The journey from the brief: dashboard -> dark -> move revenue -> table to chart."""
    v1 = await approve_generation(client, llm, workspace_id)
    v2 = await approve_edit(client, llm, workspace_id, v1["id"], "Make it dark", DARK)
    v3 = await approve_edit(client, llm, workspace_id, v2["id"], "Move revenue right", MOVE_REVENUE)
    v4 = await approve_edit(
        client, llm, workspace_id, v3["id"], "Table to bar chart", TABLE_TO_CHART
    )
    return [v1, v2, v3, v4]


async def _restore(
    client: httpx.AsyncClient, workspace_id: str, version_id: str, base_version_id: str
) -> httpx.Response:
    return await client.post(
        f"{API}/workspaces/{workspace_id}/versions/{version_id}/restore",
        json={"base_version_id": base_version_id},
    )


# --- Approve and persist ----------------------------------------------------------


async def test_approved_generation_is_persisted_and_reloads_exactly(
    client: httpx.AsyncClient, llm: ScriptedLLMProvider, workspace_id: str
) -> None:
    proposal = await propose_generation(client, llm, workspace_id)

    saved = await save_version(
        client,
        workspace_id,
        base_version_id=None,
        source="ai_generation",
        proposal_id=proposal["proposal_id"],
        instruction="Create a sales dashboard",
        document=proposal["document"],
    )

    assert saved.status_code == 201, saved.text
    version = saved.json()["data"]
    assert (version["version_number"], version["is_current"]) == (1, True)
    assert "parent_version_id" not in version
    assert version["source"] == "ai_generation"
    assert version["description"] == "Generated “Sales by Region”"
    assert version["metadata"] == {
        "proposal_id": proposal["proposal_id"],
        "instruction": "Create a sales dashboard",
    }
    assert version["document"] == proposal["document"]

    # "Close the browser and come back": everything is read again from the API.
    workspace = (await client.get(f"{API}/workspaces/{workspace_id}")).json()["data"]
    reloaded = await get_version(client, workspace_id, workspace["current_version_id"])
    assert reloaded["document"] == proposal["document"], "the approved UI loads exactly as it was"
    assert reloaded["data"] == proposal["data"]


async def test_each_approved_edit_appends_a_version_linked_to_its_parent(
    client: httpx.AsyncClient, llm: ScriptedLLMProvider, workspace_id: str
) -> None:
    v1, v2, v3, v4 = await _build_history(client, llm, workspace_id)

    history = await list_versions(client, workspace_id)

    assert [v["version_number"] for v in history] == [4, 3, 2, 1], "newest first"
    assert [v["is_current"] for v in history] == [True, False, False, False]
    assert [v.get("parent_version_id") for v in history] == [v3["id"], v2["id"], v1["id"], None]
    assert [v["source"] for v in history] == ["ai_mutation"] * 3 + ["ai_generation"]
    assert [v["description"] for v in history[:3]] == [
        "Replace “Breakdown” with a bar chart",
        "Move “Revenue” after “Orders”",
        "Change theme to slate_dark",
    ]
    assert v4["metadata"]["instruction"] == "Table to bar chart"
    assert v4["metadata"]["operations"][0]["type"] == "REPLACE"


async def test_theme_change_leaves_the_component_tree_untouched(
    client: httpx.AsyncClient, llm: ScriptedLLMProvider, workspace_id: str
) -> None:
    v1 = await approve_generation(client, llm, workspace_id)

    v2 = await approve_edit(client, llm, workspace_id, v1["id"], "Make it dark", DARK)

    assert v2["document"]["theme"]["mode"] == "dark"
    assert v2["document"]["page"] == v1["document"]["page"]


async def test_framework_change_keeps_the_same_semantic_ui(
    client: httpx.AsyncClient, llm: ScriptedLLMProvider, workspace_id: str
) -> None:
    v1 = await approve_generation(client, llm, workspace_id)

    v2 = await approve_edit(
        client,
        llm,
        workspace_id,
        v1["id"],
        "Use a Material style",
        {"type": "SET_FRAMEWORK", "framework": "material"},
        {"type": "SET_DESIGN_SYSTEM", "design_system": "material"},
    )

    assert v2["document"]["design"] == {"framework": "material", "design_system": "material"}
    assert v2["document"]["page"] == v1["document"]["page"], "no component was regenerated"
    assert v2["document"]["theme"]["colors"] == v1["document"]["theme"]["colors"]
    assert v2["document"]["theme"]["shadows"] == "medium"


async def test_manual_edits_are_saved_through_the_same_engine(
    client: httpx.AsyncClient, llm: ScriptedLLMProvider, workspace_id: str
) -> None:
    v1 = await approve_generation(client, llm, workspace_id)

    saved = await save_version(
        client,
        workspace_id,
        base_version_id=v1["id"],
        operations=[
            {"type": "RESIZE", "target": "regional_sales", "span": 7},
            {"type": "RESIZE", "target": "regional_breakdown", "span": 5},
        ],
    )

    version = saved.json()["data"]
    assert saved.status_code == 201
    assert (version["source"], version["version_number"]) == ("manual_edit", 2)
    spans = [c["layout"]["span"] for c in version["document"]["page"]["components"][2:]]
    assert spans == [7, 5]


# --- Server-side validation of what clients send ------------------------------------


@pytest.mark.parametrize(
    "document",
    [
        sample_document(text_page({"type": "iframe", "id": "x", "src": "https://evil.example"})),
        sample_document(text_page({"type": "text", "id": "t", "content": "<script>x()</script>"})),
        sample_document(design={"framework": "mui", "design_system": "modern_minimal"}),
        {"page": text_page()},
    ],
    ids=["unknown-component", "script-content", "unavailable-framework", "missing-theme"],
)
async def test_invalid_documents_are_never_persisted(
    client: httpx.AsyncClient, workspace_id: str, document: dict[str, Any]
) -> None:
    response = await save_version(client, workspace_id, base_version_id=None, document=document)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "UI_SCHEMA_INVALID"
    assert await list_versions(client, workspace_id) == []


@pytest.mark.parametrize(
    ("operations", "status"),
    [
        ([{"type": "DELETE", "target": "ghost"}], 422),
        ([{"type": "EXEC", "code": "x"}], 422),
        ([{"type": "UPDATE", "target": "regional_sales", "props": {"onClick": "x()"}}], 422),
        ([{"type": "RESTORE_VERSION", "version_number": 1}], 422),
    ],
)
async def test_invalid_operations_are_never_persisted(
    client: httpx.AsyncClient,
    llm: ScriptedLLMProvider,
    workspace_id: str,
    operations: list[dict[str, Any]],
    status: int,
) -> None:
    v1 = await approve_generation(client, llm, workspace_id)

    response = await save_version(
        client, workspace_id, base_version_id=v1["id"], operations=operations
    )

    assert response.status_code == status
    assert len(await list_versions(client, workspace_id)) == 1


async def test_a_version_needs_exactly_one_of_document_and_operations(
    client: httpx.AsyncClient, workspace_id: str
) -> None:
    neither = await save_version(client, workspace_id, base_version_id=None)
    both = await save_version(
        client, workspace_id, base_version_id=None, document=sample_document(), operations=[DARK]
    )
    fake_restore = await save_version(
        client, workspace_id, base_version_id=None, source="restore", document=sample_document()
    )

    assert [r.status_code for r in (neither, both, fake_restore)] == [422, 422, 422]


# --- Stale-version protection -------------------------------------------------------


async def test_write_based_on_a_stale_version_does_not_overwrite_newer_work(
    client: httpx.AsyncClient, llm: ScriptedLLMProvider, workspace_id: str
) -> None:
    v1 = await approve_generation(client, llm, workspace_id)
    # Two clients prepare changes against V1.
    slow_proposal = await propose_edit(client, llm, workspace_id, v1["id"], "Make it dark", DARK)
    v2 = await approve_edit(client, llm, workspace_id, v1["id"], "Move revenue", MOVE_REVENUE)

    stale = await save_version(
        client,
        workspace_id,
        base_version_id=v1["id"],
        source="ai_mutation",
        operations=[step["operation"] for step in slow_proposal["steps"]],
    )

    assert stale.status_code == 409
    error = stale.json()["error"]
    assert error["code"] == "VERSION_CONFLICT"
    assert error["details"] == [{"current_version_id": v2["id"], "current_version_number": 2}], (
        "the client is told what to reload"
    )
    history = await list_versions(client, workspace_id)
    assert [v["id"] for v in history] == [v2["id"], v1["id"]]
    current = await get_version(client, workspace_id, v2["id"])
    assert current["document"]["theme"]["mode"] == "light", "V2 was not overwritten"


async def test_first_version_cannot_be_created_twice(
    client: httpx.AsyncClient, llm: ScriptedLLMProvider, workspace_id: str
) -> None:
    await approve_generation(client, llm, workspace_id)

    again = await save_version(
        client, workspace_id, base_version_id=None, document=sample_document()
    )

    assert again.status_code == 409


async def test_restore_also_requires_the_current_base(
    client: httpx.AsyncClient, llm: ScriptedLLMProvider, workspace_id: str
) -> None:
    v1, v2, *_ = await _build_history(client, llm, workspace_id)

    response = await _restore(client, workspace_id, v1["id"], base_version_id=v2["id"])

    assert response.status_code == 409
    assert len(await list_versions(client, workspace_id)) == 4


# --- Restore --------------------------------------------------------------------------


async def test_restore_appends_a_copy_and_leaves_history_untouched(
    client: httpx.AsyncClient, llm: ScriptedLLMProvider, workspace_id: str
) -> None:
    v1, v2, v3, v4 = await _build_history(client, llm, workspace_id)
    before = {v["id"]: await get_version(client, workspace_id, v["id"]) for v in (v1, v2, v3, v4)}

    response = await _restore(client, workspace_id, v3["id"], base_version_id=v4["id"])

    assert response.status_code == 201, response.text
    v5 = response.json()["data"]
    assert (v5["version_number"], v5["is_current"], v5["source"]) == (5, True, "restore")
    assert v5["id"] not in before, "a new version, not a reused row"
    assert v5["parent_version_id"] == v4["id"]
    assert v5["description"] == "Restored from Version 3"
    assert v5["metadata"] == {
        "restored_from_version_id": v3["id"],
        "restored_from_version_number": 3,
    }
    assert v5["document"] == v3["document"]
    table = v5["document"]["page"]["components"][3]
    assert table["type"] == "table", "the state from before the table was replaced"

    history = await list_versions(client, workspace_id)
    assert [v["version_number"] for v in history] == [5, 4, 3, 2, 1]
    for version_id, original in before.items():
        unchanged = await get_version(client, workspace_id, version_id)
        original["is_current"] = False
        assert unchanged == original, "V1-V4 are exactly as they were"


async def test_editing_continues_from_a_restored_version(
    client: httpx.AsyncClient, llm: ScriptedLLMProvider, workspace_id: str
) -> None:
    v1, _, _, v4 = await _build_history(client, llm, workspace_id)
    v5 = (await _restore(client, workspace_id, v1["id"], base_version_id=v4["id"])).json()["data"]

    v6 = await approve_edit(client, llm, workspace_id, v5["id"], "Dark again", DARK)

    assert (v6["version_number"], v6["parent_version_id"]) == (6, v5["id"])
    assert v6["document"]["page"] == v1["document"]["page"]


async def test_restoring_the_current_or_an_unknown_version_is_rejected(
    client: httpx.AsyncClient, llm: ScriptedLLMProvider, workspace_id: str
) -> None:
    v1 = await approve_generation(client, llm, workspace_id)

    current = await _restore(client, workspace_id, v1["id"], base_version_id=v1["id"])
    unknown = await _restore(client, workspace_id, str(uuid.uuid4()), base_version_id=v1["id"])

    assert (current.status_code, unknown.status_code) == (422, 404)


async def test_versions_are_private_to_their_workspace(
    client: httpx.AsyncClient, llm: ScriptedLLMProvider, workspace_id: str
) -> None:
    v1 = await approve_generation(client, llm, workspace_id)
    other = await create_workspace(client)

    response = await client.get(f"{API}/workspaces/{other['id']}/versions/{v1['id']}")

    assert response.status_code == 404


async def test_database_refuses_to_rewrite_a_stored_version(
    client: httpx.AsyncClient, llm: ScriptedLLMProvider, workspace_id: str, db_session: AsyncSession
) -> None:
    v1 = await approve_generation(client, llm, workspace_id)

    with pytest.raises(DBAPIError, match="ui_versions rows are immutable"):
        await db_session.execute(
            text("UPDATE ui_versions SET ui_schema = '{}'::jsonb WHERE id = :id"), {"id": v1["id"]}
        )


# --- AI version awareness ---------------------------------------------------------------


async def test_natural_language_restore_becomes_a_proposal_the_user_approves(
    client: httpx.AsyncClient, llm: ScriptedLLMProvider, workspace_id: str
) -> None:
    _, _, v3, v4 = await _build_history(client, llm, workspace_id)

    proposal = await propose_edit(
        client,
        llm,
        workspace_id,
        v4["id"],
        "Go back to the version before I replaced the table",
        {"type": "RESTORE_VERSION", "version_number": 3},
    )

    history_shown = llm.calls[-1][1].content
    assert "- version 4 (current): Replace “Breakdown” with a bar chart" in history_shown
    assert "- version 3: Move “Revenue” after “Orders”" in history_shown
    assert proposal["kind"] == "restore"
    assert proposal["target_version"]["id"] == v3["id"]
    assert proposal["document"] == v3["document"], "previewable before anything changes"
    assert [c["summary"] for c in proposal["changes"]] == [
        "Bar chart “Breakdown” replaced with table"
    ]
    assert len(await list_versions(client, workspace_id)) == 4, "nothing restored yet"

    approved = await _restore(client, workspace_id, v3["id"], base_version_id=v4["id"])
    assert approved.json()["data"]["version_number"] == 5


async def test_natural_language_compare_lists_what_changed_since_a_version(
    client: httpx.AsyncClient, llm: ScriptedLLMProvider, workspace_id: str
) -> None:
    *_, v4 = await _build_history(client, llm, workspace_id)

    proposal = await propose_edit(
        client,
        llm,
        workspace_id,
        v4["id"],
        "Compare this with version 1",
        {"type": "COMPARE_VERSIONS", "version_number": 1},
    )

    assert proposal["kind"] == "compare"
    assert proposal["target_version"]["version_number"] == 1
    assert [c["summary"] for c in proposal["changes"]] == [
        "Theme changed from light to dark",
        "Colour palette changed",
        "Table “Breakdown” replaced with bar chart",
        "Items reordered in “kpis”",
    ]


# --- Compare endpoint -------------------------------------------------------------------


async def test_compare_defaults_to_the_current_version(
    client: httpx.AsyncClient, llm: ScriptedLLMProvider, workspace_id: str
) -> None:
    v1, v2, v3, v4 = await _build_history(client, llm, workspace_id)
    base = f"{API}/workspaces/{workspace_id}/versions"

    to_current = (await client.get(f"{base}/{v3['id']}/compare")).json()["data"]
    between = (await client.get(f"{base}/{v1['id']}/compare", params={"with": v2["id"]})).json()[
        "data"
    ]
    same = (await client.get(f"{base}/{v4['id']}/compare")).json()["data"]

    assert (
        to_current["from_version"]["version_number"],
        to_current["to_version"]["version_number"],
    ) == (3, 4)
    assert to_current["changes"] == [
        {
            "kind": "replaced",
            "summary": "Table “Breakdown” replaced with bar chart",
            "component_id": "regional_breakdown",
        }
    ]
    assert [c["kind"] for c in between["changes"]] == ["theme", "theme"]
    assert same["changes"] == []
