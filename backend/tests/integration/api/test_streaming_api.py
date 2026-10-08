"""Server-sent progress for proposals: same result as the plain endpoints, plus live stages."""

import json
import uuid
from typing import Any

import httpx

from tests.integration.api.flows import API, approve_generation, create_workspace, list_versions
from tests.support import ScriptedLLMProvider, generation_json, intent_json, plan_json, text_page

Event = tuple[str, dict[str, Any]]


async def _stream(client: httpx.AsyncClient, path: str, body: dict[str, Any]) -> list[Event]:
    events: list[Event] = []
    async with client.stream("POST", f"{API}{path}", json=body) as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        name = ""
        async for line in response.aiter_lines():
            if line.startswith("event: "):
                name = line.removeprefix("event: ")
            elif line.startswith("data: "):
                events.append((name, json.loads(line.removeprefix("data: "))))
    return events


def _stages(events: list[Event]) -> list[str]:
    stages = [data["stage"] for name, data in events if name == "progress"]
    return [stage for index, stage in enumerate(stages) if index == 0 or stages[index - 1] != stage]


async def test_generation_reports_each_stage_then_the_proposal(
    client: httpx.AsyncClient, llm: ScriptedLLMProvider
) -> None:
    workspace = await create_workspace(client)
    llm.script(intent_json("comparison", "sales_by_region", "sales_summary"), generation_json())

    events = await _stream(
        client, "/ui/generate/stream", {"workspace_id": workspace["id"], "instruction": "Sales"}
    )

    assert _stages(events) == ["understanding", "planning", "generating", "validating", "finishing"]
    assert [name for name, _ in events].count("proposal") == 1 and events[-1][0] == "proposal"
    envelope = events[-1][1]
    assert envelope["success"] is True
    assert envelope["data"]["kind"] == "generate"
    assert envelope["data"]["document"]["page"]["title"] == "Sales by Region"
    assert envelope["data"]["data"]["sales_by_region"], "data travels with the proposal"
    generating = [
        d["characters"] for n, d in events if n == "progress" and d["stage"] == "generating"
    ]
    assert generating[0] == 0 and generating[-1] > 0, "progress is counted, content is not leaked"
    assert "regional_sales" not in json.dumps([d for n, d in events if n == "progress"])
    assert await list_versions(client, workspace["id"]) == [], "streaming saves nothing either"


async def test_edit_stream_reports_repair_and_returns_validated_operations(
    client: httpx.AsyncClient, llm: ScriptedLLMProvider
) -> None:
    workspace = await create_workspace(client)
    v1 = await approve_generation(client, llm, workspace["id"])
    llm.script(
        plan_json("x", {"type": "DELETE", "target": "ghost"}),
        plan_json("Made it dark.", {"type": "SET_THEME", "preset": "slate_dark"}),
    )

    events = await _stream(
        client,
        "/ui/mutate/stream",
        {
            "workspace_id": workspace["id"],
            "base_version_id": v1["id"],
            "instruction": "Make it dark",
        },
    )

    assert _stages(events) == [
        "generating", "validating", "repairing", "generating", "validating", "finishing",
    ]  # fmt: skip
    proposal = events[-1][1]["data"]
    assert proposal["metadata"]["repair_attempts"] == 1
    assert proposal["document"]["theme"]["mode"] == "dark"
    assert [step["operation"]["type"] for step in proposal["steps"]] == ["SET_THEME"]


async def test_failures_arrive_as_one_error_event_with_the_standard_envelope(
    client: httpx.AsyncClient, llm: ScriptedLLMProvider
) -> None:
    workspace = await create_workspace(client)
    bad = generation_json(text_page({"type": "iframe", "id": "x"}))
    llm.script(intent_json(), bad, bad)

    invalid = await _stream(
        client, "/ui/generate/stream", {"workspace_id": workspace["id"], "instruction": "x"}
    )
    missing = await _stream(
        client, "/ui/generate/stream", {"workspace_id": str(uuid.uuid4()), "instruction": "x"}
    )

    name, envelope = invalid[-1]
    assert name == "error"
    assert envelope["success"] is False
    assert envelope["error"]["code"] == "UI_SCHEMA_INVALID"
    assert envelope["error"]["details"][0]["stage"] == "schema"
    assert "proposal" not in [n for n, _ in invalid]
    assert (
        missing == [("error", missing[0][1])]
        and missing[0][1]["error"]["code"] == "RESOURCE_NOT_FOUND"
    )


async def test_stream_refuses_a_stale_base_like_the_plain_endpoint(
    client: httpx.AsyncClient, llm: ScriptedLLMProvider
) -> None:
    workspace = await create_workspace(client)
    await approve_generation(client, llm, workspace["id"])
    calls = len(llm.calls)

    events = await _stream(
        client,
        "/ui/mutate/stream",
        {"workspace_id": workspace["id"], "base_version_id": str(uuid.uuid4()), "instruction": "x"},
    )

    assert events[-1][1]["error"]["code"] == "VERSION_CONFLICT"
    assert len(llm.calls) == calls


async def test_invalid_stream_requests_fail_before_streaming(client: httpx.AsyncClient) -> None:
    response = await client.post(f"{API}/ui/generate/stream", json={"instruction": "x"})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
