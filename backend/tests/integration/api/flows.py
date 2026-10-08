"""Shared steps for API tests that walk through the propose -> approve -> persist flow."""

import asyncio
from typing import Any

import httpx

from tests.support import ScriptedLLMProvider, generation_json, intent_json, plan_json

API = "/api/v1"


async def create_workspace(client: httpx.AsyncClient, title: str | None = None) -> dict[str, Any]:
    response = await client.post(
        f"{API}/workspaces", json={} if title is None else {"title": title}
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]  # type: ignore[no-any-return]


async def propose_generation(
    client: httpx.AsyncClient, llm: ScriptedLLMProvider, workspace_id: str, **request: Any
) -> dict[str, Any]:
    llm.script(intent_json("comparison", "sales_by_region", "sales_summary"), generation_json())
    # A fixed look keeps flows repeatable; without one a new UI gets a random palette.
    body = {
        "workspace_id": workspace_id,
        "instruction": "Create a sales dashboard",
        "theme_preset": "blue_white",
        **request,
    }
    response = await client.post(f"{API}/ui/generate", json=body)
    assert response.status_code == 200, response.text
    return response.json()["data"]  # type: ignore[no-any-return]


async def save_version(client: httpx.AsyncClient, workspace_id: str, **body: Any) -> httpx.Response:
    return await client.post(f"{API}/workspaces/{workspace_id}/versions", json=body)


async def approve_generation(
    client: httpx.AsyncClient, llm: ScriptedLLMProvider, workspace_id: str
) -> dict[str, Any]:
    """Generate a UI and approve it; returns the stored first version."""
    proposal = await propose_generation(client, llm, workspace_id)
    response = await save_version(
        client,
        workspace_id,
        base_version_id=proposal.get("base_version_id"),
        source="ai_generation",
        proposal_id=proposal["proposal_id"],
        document=proposal["document"],
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]  # type: ignore[no-any-return]


async def propose_edit(
    client: httpx.AsyncClient,
    llm: ScriptedLLMProvider,
    workspace_id: str,
    base_version_id: str,
    instruction: str,
    *operations: dict[str, Any],
    **request: Any,
) -> dict[str, Any]:
    llm.script(plan_json(f"Done: {instruction}", *operations))
    body = {
        "workspace_id": workspace_id,
        "base_version_id": base_version_id,
        "instruction": instruction,
        **request,
    }
    response = await client.post(f"{API}/ui/mutate", json=body)
    assert response.status_code == 200, response.text
    return response.json()["data"]  # type: ignore[no-any-return]


async def approve_edit(
    client: httpx.AsyncClient,
    llm: ScriptedLLMProvider,
    workspace_id: str,
    base_version_id: str,
    instruction: str,
    *operations: dict[str, Any],
) -> dict[str, Any]:
    """Ask for an edit and approve it; returns the stored new version."""
    proposal = await propose_edit(
        client, llm, workspace_id, base_version_id, instruction, *operations
    )
    response = await save_version(
        client,
        workspace_id,
        base_version_id=base_version_id,
        source="ai_mutation",
        proposal_id=proposal["proposal_id"],
        instruction=instruction,
        operations=[step["operation"] for step in proposal["steps"]],
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]  # type: ignore[no-any-return]


async def get_version(
    client: httpx.AsyncClient, workspace_id: str, version_id: str
) -> dict[str, Any]:
    response = await client.get(f"{API}/workspaces/{workspace_id}/versions/{version_id}")
    assert response.status_code == 200, response.text
    return response.json()["data"]  # type: ignore[no-any-return]


async def list_versions(client: httpx.AsyncClient, workspace_id: str) -> list[dict[str, Any]]:
    response = await client.get(f"{API}/workspaces/{workspace_id}/versions")
    assert response.status_code == 200, response.text
    return response.json()["data"]  # type: ignore[no-any-return]


JOBS = f"{API}/generation/jobs"
ACTIVE = {"queued", "running"}


async def start_job(
    client: httpx.AsyncClient, workspace_id: str, instruction: str, **body: Any
) -> httpx.Response:
    return await client.post(
        JOBS, json={"workspace_id": workspace_id, "instruction": instruction, **body}
    )


async def finished_job(client: httpx.AsyncClient, job_id: str) -> dict[str, Any]:
    """Poll a job until it leaves the queue and stops running."""
    for _ in range(2000):
        response = await client.get(f"{JOBS}/{job_id}")
        assert response.status_code == 200, response.text
        job: dict[str, Any] = response.json()["data"]
        if job["status"] not in ACTIVE:
            return job
        await asyncio.sleep(0.005)
    raise AssertionError("the job did not finish")


async def build_application(
    client: httpx.AsyncClient,
    workspace_id: str,
    instruction: str = "Build me a recruitment platform",
) -> dict[str, Any]:
    """Run a build job to completion; returns the ready job (its proposal is unsaved)."""
    started = await start_job(client, workspace_id, instruction)
    assert started.status_code == 202, started.text
    job = await finished_job(client, started.json()["data"]["id"])
    assert job["status"] == "ready", job
    return job


async def approve_application(client: httpx.AsyncClient, workspace_id: str) -> dict[str, Any]:
    """Build the sample application and approve it; returns the stored first version."""
    proposal = (await build_application(client, workspace_id))["proposal"]
    response = await save_version(
        client,
        workspace_id,
        base_version_id=None,
        source="ai_generation",
        proposal_id=proposal["proposal_id"],
        document=proposal["document"],
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]  # type: ignore[no-any-return]


async def ask(
    client: httpx.AsyncClient,
    workspace_id: str,
    base_version_id: str,
    instruction: str,
    **body: Any,
) -> dict[str, Any]:
    response = await client.post(
        f"{API}/ui/mutate",
        json={
            "workspace_id": workspace_id,
            "base_version_id": base_version_id,
            "instruction": instruction,
            **body,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["data"]  # type: ignore[no-any-return]


async def approve(
    client: httpx.AsyncClient, workspace_id: str, base_version_id: str, proposal: dict[str, Any]
) -> dict[str, Any]:
    response = await save_version(
        client,
        workspace_id,
        base_version_id=base_version_id,
        source="ai_mutation",
        proposal_id=proposal["proposal_id"],
        operations=[step["operation"] for step in proposal["steps"]],
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]  # type: ignore[no-any-return]


async def act(
    client: httpx.AsyncClient, workspace_id: str, action_type: str, **payload: Any
) -> httpx.Response:
    return await client.post(
        f"{API}/actions/execute",
        json={"workspace_id": workspace_id, "action_type": action_type, "payload": payload},
    )
