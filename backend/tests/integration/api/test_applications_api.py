"""A whole application through the API: build in the background, approve, use, edit, restore.

HTTP -> services -> pipeline -> PostgreSQL, with only the language model
replaced by the scripted sample application.
"""

import asyncio
import uuid
from collections.abc import Sequence
from typing import Any

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.ai.llm.base import LLMMessage, LLMResponse
from app.api.dependencies import get_llm_provider
from app.api.jobs import fail_interrupted_jobs
from app.core.exceptions import LLMProvidersExhaustedException
from app.database.connection import Database
from app.domains.assets.models import StoredAsset
from app.domains.generation.models import GenerationJob
from app.domains.generative_ui.models import UIVersion
from app.domains.records.models import WorkspaceRecord
from tests.integration.api.flows import (
    API,
    JOBS,
    act,
    approve,
    approve_application,
    ask,
    build_application,
    create_workspace,
    finished_job,
    get_version,
    list_versions,
    save_version,
    start_job,
)
from tests.support import ScriptedLLMProvider, generation_json, intent_json, plan_json

GENERATOR = "You are a senior product designer"


@pytest.fixture
async def workspace_id(client: httpx.AsyncClient) -> str:
    return str((await create_workspace(client))["id"])


def _screens(document: dict[str, Any]) -> dict[str, Any]:
    return {screen["id"]: screen for screen in document["page"]["components"]}


# --- Building -----------------------------------------------------------------------------


async def test_a_job_builds_a_whole_application_as_an_unsaved_proposal(
    client: httpx.AsyncClient, workspace_id: str, db_session: AsyncSession
) -> None:
    started = await start_job(client, workspace_id, "Build me a modern AI recruitment SaaS.")

    assert started.status_code == 202
    queued = started.json()["data"]
    assert (queued["status"], queued["stage"], queued["progress"]) == ("queued", "queued", 0)
    assert queued["proposal"] is None

    job = await finished_job(client, queued["id"])

    assert (job["status"], job["stage"], job["progress"]) == ("ready", "ready", 100)
    assert job["finished_at"] is not None and job["error"] is None
    proposal = job["proposal"]
    assert proposal["kind"] == "generate" and proposal.get("base_version_id") is None
    assert proposal["message"] == (
        "I've designed Hirewell: a 7-screen recruitment saas application."
    )
    summary = proposal["application"]
    assert (summary["name"], summary["navigation_style"]) == ("Hirewell", "sidebar")
    assert [s["title"] for s in summary["screens"]] == [
        "Dashboard", "Jobs", "Create job", "Candidates", "Candidate", "Pipeline", "Interviews",
    ]  # fmt: skip
    assert summary["design"]["style_name"] == "Premium SaaS"
    assert (summary["asset_count"], len(summary["entities"])) == (1, 4)
    assert "Create job" in summary["interactions"]
    assert proposal["quality"]["score"] >= 90
    assert not any(screen["failed"] for screen in summary["screens"])
    assert {"jobs", "candidates"} <= proposal["data"].keys(), "entity rows travel with it"

    assert (await db_session.scalars(select(UIVersion))).all() == [], "nothing was saved"
    assert await list_versions(client, workspace_id) == []
    messages = (await client.get(f"{API}/workspaces/{workspace_id}/messages")).json()["data"]
    assert [m["role"] for m in messages] == ["user", "assistant"]
    assert messages[1]["details"]["proposal_id"] == proposal["proposal_id"]


async def test_the_latest_job_can_be_picked_up_after_a_reload(
    client: httpx.AsyncClient, workspace_id: str
) -> None:
    assert (await client.get(JOBS, params={"workspace_id": workspace_id})).json()["data"] is None

    job = await build_application(client, workspace_id)
    latest = (await client.get(JOBS, params={"workspace_id": workspace_id})).json()["data"]

    assert latest["id"] == job["id"] and latest["proposal"]["application"]["name"] == "Hirewell"
    unknown = await client.get(f"{JOBS}/{uuid.uuid4()}")
    assert unknown.status_code == 404


async def test_approving_persists_the_application_and_a_reload_returns_it_exactly(
    client: httpx.AsyncClient, workspace_id: str
) -> None:
    proposal = (await build_application(client, workspace_id))["proposal"]

    saved = await save_version(
        client, workspace_id, base_version_id=None, source="ai_generation",
        proposal_id=proposal["proposal_id"], document=proposal["document"],
    )  # fmt: skip

    assert saved.status_code == 201, saved.text
    version = saved.json()["data"]
    assert version["version_number"] == 1
    assert version["description"] == "Generated “Hirewell” (7 screens)"
    workspace = (await client.get(f"{API}/workspaces/{workspace_id}")).json()["data"]
    assert workspace["title"] == "Hirewell"

    reloaded = await get_version(client, workspace_id, version["id"])
    assert reloaded["document"] == proposal["document"], (
        "the stored application is the approved one"
    )
    assert reloaded["document"]["application"]["navigation"]["home"] == "dashboard"
    assert reloaded["data"]["candidates"][0]["name"] == "Amara Okafor"


async def test_the_application_endpoint_describes_screens_and_how_they_connect(
    client: httpx.AsyncClient, workspace_id: str
) -> None:
    missing = await client.get(f"{API}/workspaces/{workspace_id}/application")
    assert missing.status_code == 404

    await approve_application(client, workspace_id)
    response = await client.get(f"{API}/workspaces/{workspace_id}/application")

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["version_number"] == 1 and data["unreachable_screen_ids"] == []
    assert data["summary"]["component_count"] > 10
    edges = {(e["source"], e["target"], e["kind"]) for e in data["edges"]}
    assert ("candidates", "candidate_detail", "action") in edges
    assert ("dashboard", "jobs", "navigation") in edges


async def test_a_request_for_one_view_goes_through_the_single_view_pipeline(
    client: httpx.AsyncClient, llm: ScriptedLLMProvider, workspace_id: str
) -> None:
    llm.script(intent_json(), generation_json())

    started = await start_job(
        client, workspace_id, "Show revenue by region", theme_preset="emerald"
    )
    job = await finished_job(client, started.json()["data"]["id"])

    assert job["status"] == "ready", job
    proposal = job["proposal"]
    assert "application" not in proposal and "quality" not in proposal
    assert proposal["document"]["page"]["title"] == "Sales by Region"
    assert proposal["document"]["theme"]["preset"] == "emerald"
    assert not llm.stage_calls(GENERATOR), "no application screens were generated"
    messages = (await client.get(f"{API}/workspaces/{workspace_id}/messages")).json()["data"]
    assert [m["role"] for m in messages] == ["user", "assistant"], "the request is recorded once"


async def test_look_preferences_are_validated_before_any_work_starts(
    client: httpx.AsyncClient, workspace_id: str
) -> None:
    started = await start_job(client, workspace_id, "Build me a CRM", design_system="vaporwave")
    job = await finished_job(client, started.json()["data"]["id"])

    assert (job["status"], job["error"]["code"]) == ("failed", "VALIDATION_ERROR")
    assert "vaporwave" in job["error"]["message"]


# --- Failure, cancellation, concurrency ------------------------------------------------------


class _GatedLLM(ScriptedLLMProvider):
    """Answers only once ``gate`` is opened, so a job can be observed while it runs."""

    def __init__(self) -> None:
        super().__init__()
        self.gate = asyncio.Event()
        self.started = asyncio.Event()

    async def generate_structured(
        self, messages: Sequence[LLMMessage], options: Any = None
    ) -> LLMResponse:
        self.started.set()
        await self.gate.wait()
        return await super().generate_structured(messages, options)


async def test_one_generation_at_a_time_per_workspace_and_progress_is_visible(
    app: FastAPI, client: httpx.AsyncClient, workspace_id: str
) -> None:
    gated = _GatedLLM()
    app.dependency_overrides[get_llm_provider] = lambda: gated

    first = (await start_job(client, workspace_id, "Build me a recruitment platform")).json()[
        "data"
    ]
    await gated.started.wait()
    running = (await client.get(f"{JOBS}/{first['id']}")).json()["data"]
    second = await start_job(client, workspace_id, "Build me a CRM platform")

    assert (running["status"], running["stage"]) == ("running", "understanding")
    assert running["detail"] == "Understanding the product"
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "CONFLICT"

    gated.gate.set()
    assert (await finished_job(client, first["id"]))["status"] == "ready"
    third = await start_job(client, workspace_id, "Build me a CRM platform")
    assert third.status_code == 202, "a finished job no longer blocks the workspace"
    await finished_job(client, third.json()["data"]["id"])


async def test_a_cancelled_job_stops_and_stays_cancelled(
    app: FastAPI, client: httpx.AsyncClient, workspace_id: str, db_session: AsyncSession
) -> None:
    gated = _GatedLLM()
    app.dependency_overrides[get_llm_provider] = lambda: gated
    job = (await start_job(client, workspace_id, "Build me a recruitment platform")).json()["data"]
    await gated.started.wait()

    cancelled = await client.post(f"{JOBS}/{job['id']}/cancel")
    gated.gate.set()
    await asyncio.sleep(0.05)

    assert cancelled.json()["data"]["status"] == "cancelled"
    after = (await client.get(f"{JOBS}/{job['id']}")).json()["data"]
    assert (after["status"], after["proposal"]) == ("cancelled", None)
    assert (await db_session.scalars(select(UIVersion))).all() == []
    again = await client.post(f"{JOBS}/{job['id']}/cancel")
    assert again.json()["data"]["status"] == "cancelled", "cancelling twice is harmless"


async def test_a_failed_generation_reports_the_error_and_saves_nothing(
    client: httpx.AsyncClient, llm: ScriptedLLMProvider, workspace_id: str, db_session: AsyncSession
) -> None:
    llm.answer_stages = False
    llm.script(LLMProvidersExhaustedException(details=[{"provider": "groq", "kind": "timeout"}]))

    started = await start_job(client, workspace_id, "Build me a recruitment platform")
    job = await finished_job(client, started.json()["data"]["id"])

    assert (job["status"], job["stage"]) == ("failed", "failed")
    assert job["error"]["code"] == "LLM_ALL_PROVIDERS_FAILED"
    assert job["proposal"] is None and job["finished_at"] is not None
    assert (await db_session.scalars(select(UIVersion))).all() == []
    assert (await db_session.scalars(select(StoredAsset))).all() == []


async def test_jobs_left_running_by_a_dead_process_are_closed_on_startup(
    client: httpx.AsyncClient, workspace_id: str, db_engine: AsyncEngine, db_session: AsyncSession
) -> None:
    orphan = GenerationJob(
        workspace_id=uuid.UUID(workspace_id), kind="build", instruction="x", options={},
        status="running", stage="generating_screens", progress=55,
    )  # fmt: skip
    db_session.add(orphan)
    await db_session.commit()

    await fail_interrupted_jobs(Database(str(db_engine.url.render_as_string(hide_password=False))))

    job = (await client.get(f"{JOBS}/{orphan.id}")).json()["data"]
    assert (job["status"], job["error"]["code"]) == ("failed", "GENERATION_JOB_FAILED")
    assert "restarted" in job["error"]["message"]


# --- Images -----------------------------------------------------------------------------------


async def test_images_are_stored_once_and_served_without_a_token(
    client: httpx.AsyncClient, workspace_id: str
) -> None:
    version = await approve_application(client, workspace_id)
    [asset] = version["document"]["application"]["assets"]

    listed = (await client.get(f"{API}/workspaces/{workspace_id}/assets")).json()["data"]
    image = await client.get(asset["url"])

    assert [(a["url"], a["provider"], a["source"]) for a in listed] == [
        (asset["url"], "internal", "internal")
    ]
    assert listed[0]["prompt"].startswith("A candid photograph of three colleagues")
    assert image.status_code == 200 and image.headers["content-type"] == "image/svg+xml"
    assert image.content.startswith(b"<svg")
    assert "immutable" in image.headers["cache-control"]
    assert image.headers["content-security-policy"].startswith("default-src 'none'")
    assert (await client.get(f"{API}/assets/{uuid.uuid4()}/content")).status_code == 404


async def test_one_more_image_can_be_prepared_and_added_with_an_operation(
    client: httpx.AsyncClient, workspace_id: str
) -> None:
    version = await approve_application(client, workspace_id)

    created = await client.post(
        f"{API}/workspaces/{workspace_id}/assets",
        json={"id": "office_wide", "prompt": "A wide photograph of a calm open office at dusk",
              "alt": "An open office at dusk", "width": 1600, "height": 900},
    )  # fmt: skip

    assert created.status_code == 201, created.text
    asset = created.json()["data"]
    assert (asset["id"], asset["provider"], asset["width"]) == ("office_wide", "internal", 1600)
    saved = await save_version(
        client, workspace_id, base_version_id=version["id"],
        operations=[
            {"type": "ADD_ASSETS", "assets": [asset]},
            {"type": "UPDATE", "target": "dashboard_this_week", "props": {"image": "office_wide"}},
        ],
    )  # fmt: skip
    assert saved.status_code == 201, saved.text
    document = saved.json()["data"]["document"]
    assert len(document["application"]["assets"]) == 2
    assert saved.json()["data"]["description"].startswith("Add 1 image; Update image of")


# --- Using the application: actions on its data ---------------------------------------------


async def test_record_actions_change_the_applications_data_and_persist(
    client: httpx.AsyncClient, workspace_id: str, db_session: AsyncSession
) -> None:
    version = await approve_application(client, workspace_id)

    updated = await act(
        client, workspace_id, "record_update",
        entity="candidates", record_id="cand-003", values={"stage": "Interview"},
    )  # fmt: skip
    created = await act(
        client, workspace_id, "record_create",
        entity="jobs", values={"title": "QA Engineer", "openings": "2"}, navigate_to="/jobs",
    )  # fmt: skip
    deleted = await act(client, workspace_id, "record_delete", entity="jobs", record_id="job-105")

    assert updated.status_code == 200, updated.text
    result = updated.json()["data"]["result"]
    assert result["dataset"] == "candidates" and len(result["rows"]) == 8
    assert next(r for r in result["rows"] if r["id"] == "cand-003")["stage"] == "Interview"
    assert created.json()["data"]["result"]["navigate_to"] == "/jobs"
    assert created.json()["data"]["result"]["rows"][-1]["openings"] == 2
    assert "job-105" not in [r["id"] for r in deleted.json()["data"]["result"]["rows"]]

    reloaded = await get_version(client, workspace_id, version["id"])
    assert next(r for r in reloaded["data"]["candidates"] if r["id"] == "cand-003")["stage"] == (
        "Interview"
    ), "a reload shows the application as it was left"
    assert [r["title"] for r in reloaded["data"]["jobs"]][-1] == "QA Engineer"
    assert reloaded["document"] == version["document"], "the version itself never changes"
    assert len((await db_session.scalars(select(WorkspaceRecord))).all()) == 3


async def test_data_actions_work_on_application_entities(
    client: httpx.AsyncClient, workspace_id: str
) -> None:
    await approve_application(client, workspace_id)
    await act(client, workspace_id, "record_update", entity="candidates", record_id="cand-005",
              values={"stage": "Offer"})  # fmt: skip

    filtered = await act(
        client, workspace_id, "filter",
        dataset="candidates", field="stage", value="Offer", target="candidates_candidate_list",
    )  # fmt: skip

    rows = filtered.json()["data"]["result"]["rows"]
    assert sorted(row["id"] for row in rows) == ["cand-004", "cand-005"], "changes are included"


@pytest.mark.parametrize(
    ("action_type", "payload", "status", "code"),
    [
        ("record_update", {"entity": "invoices", "record_id": "x", "values": {"a": 1}}, 422,
         "ACTION_PAYLOAD_INVALID"),
        ("record_update", {"entity": "jobs", "record_id": "job-101", "values": {"salary": 1}}, 422,
         "ACTION_PAYLOAD_INVALID"),
        ("record_update", {"entity": "jobs", "record_id": "ghost", "values": {"status": "Open"}},
         404, "RESOURCE_NOT_FOUND"),
        ("record_create", {"entity": "jobs", "values": {}, "navigate_to": "https://evil.example"},
         422, "ACTION_PAYLOAD_INVALID"),
        ("record_delete", {"entity": "jobs"}, 422, "ACTION_PAYLOAD_INVALID"),
    ],
)  # fmt: skip
async def test_record_actions_outside_the_applications_shape_are_refused(
    client: httpx.AsyncClient, workspace_id: str, db_session: AsyncSession,
    action_type: str, payload: dict[str, Any], status: int, code: str,
) -> None:  # fmt: skip
    await approve_application(client, workspace_id)

    response = await act(client, workspace_id, action_type, **payload)

    assert (response.status_code, response.json()["error"]["code"]) == (status, code)
    assert (await db_session.scalars(select(WorkspaceRecord))).all() == []


async def test_record_actions_need_an_application(
    client: httpx.AsyncClient, workspace_id: str
) -> None:
    response = await act(client, workspace_id, "record_create", entity="jobs", values={"a": 1})

    assert response.status_code == 422
    assert "no application data" in response.json()["error"]["message"]


async def test_resetting_data_brings_the_sample_records_back(
    client: httpx.AsyncClient, workspace_id: str
) -> None:
    version = await approve_application(client, workspace_id)
    await act(client, workspace_id, "record_delete", entity="jobs", record_id="job-101")

    reset = await client.delete(f"{API}/workspaces/{workspace_id}/records")

    assert reset.status_code == 204
    data = (await get_version(client, workspace_id, version["id"]))["data"]
    assert data["jobs"][0]["id"] == "job-101"


# --- Editing at three levels, then going back -------------------------------------------------


async def test_redesign_restyle_and_restore_each_touch_only_their_level(
    client: httpx.AsyncClient, llm: ScriptedLLMProvider, workspace_id: str
) -> None:
    v1 = await approve_application(client, workspace_id)

    # Screen level: only the dashboard changes.
    redesign = await ask(client, workspace_id, v1["id"], "Redesign the dashboard",
                         active_screen_id="dashboard")  # fmt: skip
    assert redesign["kind"] == "mutate"
    assert [step["summary"] for step in redesign["steps"]] == ["Replace “Dashboard” with a screen"]
    assert redesign["affected_component_ids"] == ["dashboard"]
    v2 = await approve(client, workspace_id, v1["id"], redesign)
    before, after = _screens(v1["document"]), _screens(v2["document"])
    assert after["dashboard"] != before["dashboard"]
    assert {k: v for k, v in after.items() if k != "dashboard"} == {
        k: v for k, v in before.items() if k != "dashboard"
    }
    assert v2["document"]["theme"] == v1["document"]["theme"]

    # Application level: the design changes, no screen does.
    restyle = await ask(client, workspace_id, v2["id"], "Make the entire application more premium")
    assert [step["operation"]["type"] for step in restyle["steps"]] == [
        "SET_DESIGN_SYSTEM", "SET_THEME", "UPDATE_APPLICATION",
    ]  # fmt: skip
    assert "Visual style changed from premium_saas to luxury" in [
        change["summary"] for change in restyle["changes"]
    ]
    v3 = await approve(client, workspace_id, v2["id"], restyle)
    assert v3["document"]["design"]["design_system"] == "luxury"
    assert v3["document"]["page"] == v2["document"]["page"], "no screen was regenerated"
    assert len(llm.stage_calls(GENERATOR)) == 8, "seven screens, then one redesign; never more"

    # Component level, on another screen than the one on display.
    llm.script(plan_json("Compact it is.", {"type": "UPDATE", "target": "jobs_table",
                                           "props": {"page_size": 5}}))  # fmt: skip
    compact = await ask(client, workspace_id, v3["id"], "Make all tables more compact",
                        active_screen_id="dashboard")  # fmt: skip
    v4 = await approve(client, workspace_id, v3["id"], compact)
    assert _screens(v4["document"])["jobs"]["children"][2]["page_size"] == 5

    # Going back to the original creates a new version; nothing is deleted.
    llm.script(
        plan_json("Restoring the original.", {"type": "RESTORE_VERSION", "version_number": 1})
    )
    back = await ask(client, workspace_id, v4["id"], "Go back to the original version")
    assert (back["kind"], back["target_version"]["version_number"]) == ("restore", 1)
    restored = await client.post(
        f"{API}/workspaces/{workspace_id}/versions/{v1['id']}/restore",
        json={"base_version_id": v4["id"], "proposal_id": back["proposal_id"]},
    )
    assert restored.status_code == 201, restored.text
    v5 = restored.json()["data"]
    assert v5["version_number"] == 5 and v5["document"] == v1["document"]
    history = await list_versions(client, workspace_id)
    assert [v["version_number"] for v in history] == [5, 4, 3, 2, 1]
    assert [v["source"] for v in history] == [
        "restore", "ai_mutation", "ai_mutation", "ai_mutation", "ai_generation",
    ]  # fmt: skip


async def test_adding_a_screen_extends_data_and_navigation_in_one_version(
    client: httpx.AsyncClient, workspace_id: str
) -> None:
    v1 = await approve_application(client, workspace_id)

    proposal = await ask(client, workspace_id, v1["id"], "Add an offers section")
    v2 = await approve(client, workspace_id, v1["id"], proposal)

    assert proposal["application"]["screens"][-1]["title"] == "Offers"
    document = v2["document"]
    assert list(_screens(document))[-1] == "offers"
    assert document["application"]["navigation"]["items"][-1] == {
        "screen_id": "offers", "label": "Offers", "icon": "award",
    }  # fmt: skip
    assert len(v2["data"]["offers"]) == 3
    assert v2["description"].startswith("Update data: Offers; Add screen “Offers”")


async def test_an_edit_prepared_against_a_stale_version_is_rejected(
    client: httpx.AsyncClient, workspace_id: str
) -> None:
    v1 = await approve_application(client, workspace_id)
    slow = await ask(client, workspace_id, v1["id"], "Redesign the dashboard")
    fast = await ask(client, workspace_id, v1["id"], "Make the entire application more premium")
    v2 = await approve(client, workspace_id, v1["id"], fast)

    stale = await save_version(
        client, workspace_id, base_version_id=v1["id"], source="ai_mutation",
        operations=[step["operation"] for step in slow["steps"]],
    )  # fmt: skip
    asking = await client.post(
        f"{API}/ui/mutate",
        json={"workspace_id": workspace_id, "base_version_id": v1["id"], "instruction": "x"},
    )

    assert stale.status_code == 409 and asking.status_code == 409
    assert stale.json()["error"]["details"] == [
        {"current_version_id": v2["id"], "current_version_number": 2}
    ]
    assert len(await list_versions(client, workspace_id)) == 2


async def test_a_single_screen_can_be_generated_again_through_a_job(
    client: httpx.AsyncClient, workspace_id: str
) -> None:
    v1 = await approve_application(client, workspace_id)

    started = await start_job(
        client, workspace_id, "Rework it around the pipeline", kind="screen", screen_id="dashboard"
    )
    job = await finished_job(client, started.json()["data"]["id"])
    missing = await start_job(client, workspace_id, "Again", kind="screen")

    assert job["status"] == "ready", job
    assert job["base_version_id"] == v1["id"]
    assert [step["operation"]["type"] for step in job["proposal"]["steps"]] == ["REPLACE"]
    assert missing.status_code == 422


async def test_unknown_screen_in_an_edit_request_is_refused(
    client: httpx.AsyncClient, workspace_id: str
) -> None:
    v1 = await approve_application(client, workspace_id)

    response = await client.post(
        f"{API}/ui/mutate",
        json={"workspace_id": workspace_id, "base_version_id": v1["id"], "instruction": "x",
              "active_screen_id": "nowhere"},
    )  # fmt: skip

    assert response.status_code == 422
    assert "Screen 'nowhere' does not exist" in response.json()["error"]["message"]
