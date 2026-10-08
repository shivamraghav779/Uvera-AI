import uuid

import httpx
import pytest


@pytest.fixture
async def messages_url(client: httpx.AsyncClient) -> str:
    workspace = (await client.post("/api/v1/workspaces", json={})).json()["data"]
    return f"/api/v1/workspaces/{workspace['id']}/messages"


async def test_messages_are_stored_and_returned_in_order(
    client: httpx.AsyncClient, messages_url: str
) -> None:
    first = await client.post(messages_url, json={"content": "Show me sales"})
    await client.post(messages_url, json={"role": "assistant", "content": "Here you go"})
    await client.post(messages_url, json={"content": "Now by region"})

    listed = (await client.get(messages_url)).json()["data"]

    assert first.status_code == 201
    assert first.json()["data"]["role"] == "user", "role defaults to user"
    assert [(m["role"], m["content"]) for m in listed] == [
        ("user", "Show me sales"),
        ("assistant", "Here you go"),
        ("user", "Now by region"),
    ]


@pytest.mark.parametrize(
    "payload",
    [{"content": ""}, {"content": "   "}, {"role": "robot", "content": "hi"}, {}],
)
async def test_invalid_messages_are_rejected(
    client: httpx.AsyncClient, messages_url: str, payload: dict[str, str]
) -> None:
    response = await client.post(messages_url, json=payload)

    assert response.status_code == 422
    assert (await client.get(messages_url)).json()["data"] == []


async def test_messages_require_an_existing_workspace(client: httpx.AsyncClient) -> None:
    url = f"/api/v1/workspaces/{uuid.uuid4()}/messages"

    assert (await client.post(url, json={"content": "hi"})).status_code == 404
    assert (await client.get(url)).status_code == 404
