import uuid

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.actions.models import UIAction

EXECUTE = "/api/v1/actions/execute"


@pytest.fixture
async def workspace_id(client: httpx.AsyncClient) -> str:
    return str((await client.post("/api/v1/workspaces", json={})).json()["data"]["id"])


async def test_allowed_action_is_executed_and_recorded(
    client: httpx.AsyncClient, workspace_id: str, db_session: AsyncSession
) -> None:
    payload = {"dataset": "sales_by_region", "field": "region", "value": "South"}

    response = await client.post(
        EXECUTE, json={"workspace_id": workspace_id, "action_type": "filter", "payload": payload}
    )

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["action_type"] == "filter"
    assert [row["region"] for row in data["result"]["rows"]] == ["South"]
    [record] = (await db_session.scalars(select(UIAction))).all()
    assert (str(record.id), record.action_type, record.payload) == (
        data["action_id"],
        "filter",
        payload,
    )


@pytest.mark.parametrize("action_type", ["execute_sql", "eval", "shell"])
async def test_unknown_action_is_rejected_and_not_recorded(
    client: httpx.AsyncClient, workspace_id: str, db_session: AsyncSession, action_type: str
) -> None:
    response = await client.post(
        EXECUTE,
        json={"workspace_id": workspace_id, "action_type": action_type, "payload": {"code": "1+1"}},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "ACTION_NOT_ALLOWED"
    assert (await db_session.scalars(select(UIAction))).all() == []


async def test_invalid_action_payload_is_rejected(
    client: httpx.AsyncClient, workspace_id: str
) -> None:
    response = await client.post(
        EXECUTE,
        json={
            "workspace_id": workspace_id,
            "action_type": "navigate",
            "payload": {"to": "javascript:x"},
        },
    )

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "ACTION_PAYLOAD_INVALID"
    assert error["details"][0]["path"] == "to"


async def test_search_action_reports_missing_provider(
    client: httpx.AsyncClient, workspace_id: str
) -> None:
    response = await client.post(
        EXECUTE,
        json={
            "workspace_id": workspace_id,
            "action_type": "search",
            "payload": {"query": "fastapi"},
        },
    )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "PROVIDER_NOT_CONFIGURED"


async def test_actions_require_an_existing_workspace(client: httpx.AsyncClient) -> None:
    response = await client.post(
        EXECUTE,
        json={
            "workspace_id": str(uuid.uuid4()),
            "action_type": "refresh",
            "payload": {"dataset": "sales_by_region"},
        },
    )

    assert response.status_code == 404


async def test_form_submissions_are_stored_and_can_be_read_back(
    client: httpx.AsyncClient, workspace_id: str
) -> None:
    for name in ("Ana", "Ben"):
        response = await client.post(
            EXECUTE,
            json={
                "workspace_id": workspace_id,
                "action_type": "submit",
                "payload": {"form_id": "feedback_form", "values": {"name": name, "rating": 5}},
            },
        )
        assert response.status_code == 200, response.text
    await client.post(
        EXECUTE,
        json={
            "workspace_id": workspace_id,
            "action_type": "refresh",
            "payload": {"dataset": "sales_by_region"},
        },
    )

    listed = await client.get(f"/api/v1/workspaces/{workspace_id}/submissions")

    submissions = listed.json()["data"]
    assert [(s["form_id"], s["values"]) for s in submissions] == [
        ("feedback_form", {"name": "Ben", "rating": 5}),
        ("feedback_form", {"name": "Ana", "rating": 5}),
    ], "newest first; other actions are not submissions"
    assert submissions[0]["submitted_at"]


async def test_generate_action_hands_the_instruction_back_for_the_proposal_flow(
    client: httpx.AsyncClient, workspace_id: str
) -> None:
    response = await client.post(
        EXECUTE,
        json={
            "workspace_id": workspace_id,
            "action_type": "generate",
            "payload": {"message": "Add a chart of orders by month"},
        },
    )

    assert response.json()["data"]["result"] == {"instruction": "Add a chart of orders by month"}
    versions = await client.get(f"/api/v1/workspaces/{workspace_id}/versions")
    assert versions.json()["data"] == [], "an action never changes the UI by itself"
