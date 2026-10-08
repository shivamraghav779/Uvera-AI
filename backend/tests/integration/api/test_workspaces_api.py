import uuid

import httpx

from tests.integration.api.flows import approve_generation, create_workspace
from tests.support import ScriptedLLMProvider

WORKSPACES = "/api/v1/workspaces"


async def test_create_and_fetch_workspace(client: httpx.AsyncClient) -> None:
    created = await create_workspace(client, "Q3 review")

    fetched = (await client.get(f"{WORKSPACES}/{created['id']}")).json()

    assert fetched == {"success": True, "data": created}
    assert created["title"] == "Q3 review"
    assert (created["current_version_id"], created["current_version_number"]) == (None, None)
    assert uuid.UUID(created["id"])
    assert created["created_at"].endswith(("Z", "+00:00")), "timestamps are timezone-aware"


async def test_workspace_points_at_its_current_version(
    client: httpx.AsyncClient, llm: ScriptedLLMProvider
) -> None:
    workspace = await create_workspace(client)

    version = await approve_generation(client, llm, workspace["id"])

    refreshed = (await client.get(f"{WORKSPACES}/{workspace['id']}")).json()["data"]
    assert refreshed["current_version_id"] == version["id"]
    assert refreshed["current_version_number"] == 1
    assert refreshed["title"] == "Sales by Region", "untitled workspaces take the UI title"


async def test_workspaces_are_listed_most_recently_changed_first(
    client: httpx.AsyncClient, llm: ScriptedLLMProvider
) -> None:
    first, second, third = [await create_workspace(client, f"Workspace {n}") for n in (1, 2, 3)]
    await approve_generation(client, llm, first["id"])

    everything = (await client.get(WORKSPACES)).json()["data"]
    page = (await client.get(WORKSPACES, params={"limit": 1, "offset": 1})).json()["data"]

    assert [item["id"] for item in everything] == [first["id"], third["id"], second["id"]]
    assert [item["id"] for item in page] == [third["id"]]


async def test_rename_workspace(client: httpx.AsyncClient) -> None:
    workspace = await create_workspace(client)

    renamed = await client.patch(f"{WORKSPACES}/{workspace['id']}", json={"title": "Board deck"})
    blank = await client.patch(f"{WORKSPACES}/{workspace['id']}", json={"title": "  "})

    assert renamed.json()["data"]["title"] == "Board deck"
    assert blank.status_code == 422


async def test_delete_removes_workspace_versions_and_messages(
    client: httpx.AsyncClient, llm: ScriptedLLMProvider
) -> None:
    workspace = await create_workspace(client)
    await approve_generation(client, llm, workspace["id"])

    deleted = await client.delete(f"{WORKSPACES}/{workspace['id']}")

    assert deleted.status_code == 204
    for path in ("", "/messages", "/versions"):
        assert (await client.get(f"{WORKSPACES}/{workspace['id']}{path}")).status_code == 404


async def test_unknown_workspace_returns_error_envelope(client: httpx.AsyncClient) -> None:
    missing = uuid.uuid4()

    for response in (
        await client.get(f"{WORKSPACES}/{missing}"),
        await client.delete(f"{WORKSPACES}/{missing}"),
    ):
        assert response.status_code == 404
        error = response.json()["error"]
        assert error["code"] == "RESOURCE_NOT_FOUND"
        assert str(missing) in error["message"]
        assert error["request_id"] == response.headers["x-request-id"]


async def test_invalid_input_is_rejected(client: httpx.AsyncClient) -> None:
    malformed_id = await client.get(f"{WORKSPACES}/not-a-uuid")
    unknown_field = await client.post(WORKSPACES, json={"title": "ok", "owner": "someone-else"})
    oversized = await client.get(WORKSPACES, params={"limit": 10_000})

    for response in (malformed_id, unknown_field, oversized):
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "VALIDATION_ERROR"
