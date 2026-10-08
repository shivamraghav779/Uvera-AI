"""Proposals: generation and edits are returned for approval and never saved by themselves.

HTTP -> services -> orchestration -> PostgreSQL, with only the language model
replaced (scripted replies or a mocked HTTP transport).
"""

import json
import uuid
from typing import Any

import httpx
import pytest
from fastapi import FastAPI

from app.api.dependencies import get_http_client, get_llm_provider
from app.domains.generative_ui.design_registry import build_default_design_registry
from app.main import create_app
from tests.integration.api.flows import (
    API,
    approve_generation,
    create_workspace,
    list_versions,
    propose_edit,
    propose_generation,
)
from tests.support import (
    ScriptedLLMProvider,
    generation_json,
    intent_json,
    make_settings,
    plan_json,
    running_client,
    text_page,
)

DESIGN = build_default_design_registry()
GENERATE = f"{API}/ui/generate"
MUTATE = f"{API}/ui/mutate"
UNKNOWN_COMPONENT = generation_json(text_page({"type": "carousel", "id": "slides"}))
MOVE_TABLE_UP = {"type": "MOVE", "target": "regional_breakdown", "before": "regional_sales"}


@pytest.fixture
async def workspace_id(client: httpx.AsyncClient) -> str:
    return str((await create_workspace(client))["id"])


async def _messages(client: httpx.AsyncClient, workspace_id: str) -> list[dict[str, Any]]:
    return (await client.get(f"{API}/workspaces/{workspace_id}/messages")).json()["data"]  # type: ignore[no-any-return]


def _page_ids(document: dict[str, Any]) -> list[str]:
    return [component["id"] for component in document["page"]["components"]]


# --- Generate -------------------------------------------------------------------


async def test_generate_returns_a_validated_proposal_without_saving_it(
    client: httpx.AsyncClient, llm: ScriptedLLMProvider, workspace_id: str
) -> None:
    proposal = await propose_generation(client, llm, workspace_id)

    assert proposal["kind"] == "generate"
    assert proposal["base_version_id"] is None if "base_version_id" in proposal else True
    assert proposal["message"] == (
        "I drafted “Sales by Region” with 6 components in the Blue & White palette. "
        "Ask for another look any time."
    )
    assert proposal["validation"] == {"valid": True, "issues": []}
    assert proposal["metadata"] == {
        "provider": "scripted",
        "model": "scripted-model",
        "prompt_version": "2.2.0",
        "repair_attempts": 0,
        "intent": "comparison",
        "schema_version": "3.0",
    }

    document = proposal["document"]
    assert _page_ids(document) == ["kpis", "region_filter", "regional_sales", "regional_breakdown"]
    assert document["theme"]["preset"] == "blue_white"
    assert document["design"] == {"framework": "shadcn", "design_system": "modern_minimal"}
    chart = document["page"]["components"][2]
    assert chart["data_source"] == {"dataset": "sales_by_region"}
    assert chart["data"] == [], "the document holds bindings, not rows"
    assert {row["region"] for row in proposal["data"]["sales_by_region"]} == {
        "North", "South", "East", "West",
    }  # fmt: skip
    assert proposal["data"]["sales_summary"][0]["total_revenue"] > 0

    assert await list_versions(client, workspace_id) == [], "nothing is persisted"
    workspace = (await client.get(f"{API}/workspaces/{workspace_id}")).json()["data"]
    assert workspace["current_version_id"] is None


async def test_generate_records_the_conversation_with_the_proposal_reference(
    client: httpx.AsyncClient, llm: ScriptedLLMProvider, workspace_id: str
) -> None:
    proposal = await propose_generation(client, llm, workspace_id)

    user, assistant = await _messages(client, workspace_id)

    assert (user["role"], user["content"]) == ("user", "Create a sales dashboard")
    assert (assistant["role"], assistant["content"]) == ("assistant", proposal["message"])
    assert assistant["details"] == {"proposal_id": proposal["proposal_id"], "kind": "generate"}


async def test_a_new_ui_with_no_stated_look_gets_a_palette_picked_for_it(
    client: httpx.AsyncClient, llm: ScriptedLLMProvider, workspace_id: str
) -> None:
    llm.script(intent_json(), generation_json())

    response = await client.post(
        GENERATE, json={"workspace_id": workspace_id, "instruction": "Create a sales dashboard"}
    )

    assert response.status_code == 200, response.text
    proposal = response.json()["data"]
    palette = DESIGN.theme(proposal["document"]["theme"]["preset"])
    assert palette is not None
    assert proposal["document"]["theme"] == DESIGN.build_theme(
        palette.id, "modern_minimal"
    ).model_dump(mode="json", exclude_none=True)
    assert f"in the {palette.name} palette" in proposal["message"]


async def test_a_look_named_by_the_user_wins_over_the_automatic_palette(
    client: httpx.AsyncClient, llm: ScriptedLLMProvider, workspace_id: str
) -> None:
    llm.script(intent_json(), generation_json(theme_preset="emerald"))

    response = await client.post(
        GENERATE, json={"workspace_id": workspace_id, "instruction": "A green sales dashboard"}
    )

    assert response.status_code == 200, response.text
    proposal = response.json()["data"]
    assert proposal["document"]["theme"]["preset"] == "emerald"
    assert "Emerald palette" in proposal["message"]


async def test_generate_honours_look_preferences_for_a_new_workspace(
    client: httpx.AsyncClient, llm: ScriptedLLMProvider, workspace_id: str
) -> None:
    proposal = await propose_generation(
        client,
        llm,
        workspace_id,
        theme_preset="slate_dark",
        design_system="soft",
        framework="material",
    )

    theme = proposal["document"]["theme"]
    assert (theme["preset"], theme["mode"], theme["radius"]) == ("slate_dark", "dark", "lg")
    assert proposal["document"]["design"] == {"framework": "material", "design_system": "soft"}


@pytest.mark.parametrize(
    "preferences",
    [
        {"framework": "mui"},
        {"framework": "jquery"},
        {"design_system": "neon"},
        {"theme_preset": "x"},
    ],
)
async def test_generate_rejects_unknown_look_preferences_before_calling_the_model(
    client: httpx.AsyncClient,
    llm: ScriptedLLMProvider,
    workspace_id: str,
    preferences: dict[str, str],
) -> None:
    response = await client.post(
        GENERATE, json={"workspace_id": workspace_id, "instruction": "x", **preferences}
    )

    assert response.status_code == 422
    assert llm.calls == []


async def test_invalid_model_output_is_repaired_before_reaching_the_client(
    client: httpx.AsyncClient, llm: ScriptedLLMProvider, workspace_id: str
) -> None:
    llm.script(intent_json(), UNKNOWN_COMPONENT, generation_json())

    response = await client.post(GENERATE, json={"workspace_id": workspace_id, "instruction": "x"})

    assert response.status_code == 200
    assert response.json()["data"]["metadata"]["repair_attempts"] == 1
    assert "carousel" not in response.text


@pytest.mark.parametrize(
    "bad_output",
    [
        UNKNOWN_COMPONENT,
        "Sure! Here is some React: <div onClick={steal}/>",
        generation_json(
            text_page(
                {
                    "type": "button",
                    "id": "run",
                    "label": "Run",
                    "action": {"type": "run_shell", "payload": {"cmd": "rm -rf /"}},
                }
            )
        ),
        generation_json(
            text_page({"type": "text", "id": "t", "content": "x", "style": {"css": "x"}})
        ),
    ],
    ids=["unknown-component", "not-json", "unknown-action", "css"],
)
async def test_persistently_invalid_output_is_rejected(
    client: httpx.AsyncClient, llm: ScriptedLLMProvider, workspace_id: str, bad_output: str
) -> None:
    llm.script(intent_json(), bad_output, bad_output)

    response = await client.post(
        GENERATE, json={"workspace_id": workspace_id, "instruction": "Show sales"}
    )

    assert response.status_code == 502
    body = response.json()
    assert body["error"]["code"] == "UI_SCHEMA_INVALID"
    assert body["error"]["message"] == "Generated UI schema is invalid."
    assert body["error"]["details"], "the validator's findings are reported"
    assert "document" not in response.text
    stored = await _messages(client, workspace_id)
    assert [(m["role"], m["content"]) for m in stored] == [("user", "Show sales")], "request kept"


async def test_generate_requires_an_existing_workspace(
    client: httpx.AsyncClient, llm: ScriptedLLMProvider
) -> None:
    response = await client.post(
        GENERATE, json={"workspace_id": str(uuid.uuid4()), "instruction": "x"}
    )

    assert response.status_code == 404
    assert llm.calls == [], "no model call is made for an unknown workspace"


async def test_generate_without_configured_provider_fails_clearly(
    app: FastAPI, client: httpx.AsyncClient, workspace_id: str
) -> None:
    del app.dependency_overrides[get_llm_provider]

    response = await client.post(GENERATE, json={"workspace_id": workspace_id, "instruction": "x"})

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "PROVIDER_NOT_CONFIGURED"


# --- Mutate ---------------------------------------------------------------------


async def test_edit_proposal_contains_operations_result_and_changes_but_saves_nothing(
    client: httpx.AsyncClient, llm: ScriptedLLMProvider, workspace_id: str
) -> None:
    v1 = await approve_generation(client, llm, workspace_id)
    calls_before = len(llm.calls)

    proposal = await propose_edit(
        client,
        llm,
        workspace_id,
        v1["id"],
        "Put the table above the chart and make the chart half width",
        MOVE_TABLE_UP,
        {"type": "RESIZE", "target": "regional_sales", "span": 6},
    )

    assert len(llm.calls) == calls_before + 1, "an edit is one model call, not a regeneration"
    assert proposal["kind"] == "mutate"
    assert proposal["base_version_id"] == v1["id"]
    assert [(step["operation"]["type"], step["summary"]) for step in proposal["steps"]] == [
        ("MOVE", "Move “Breakdown” before “regional_sales”"),
        ("RESIZE", "Resize “regional_sales” to 6 of 12 columns wide"),
    ]
    assert proposal["affected_component_ids"] == ["regional_breakdown", "regional_sales"]
    assert [change["kind"] for change in proposal["changes"]] == ["resized", "moved"]
    assert _page_ids(proposal["document"])[2:] == ["regional_breakdown", "regional_sales"]
    assert proposal["metadata"]["prompt_version"] == "1.1.0"

    [only_version] = await list_versions(client, workspace_id)
    assert only_version["id"] == v1["id"], "the proposal did not create a version"


async def test_selected_component_is_given_to_the_model(
    client: httpx.AsyncClient, llm: ScriptedLLMProvider, workspace_id: str
) -> None:
    v1 = await approve_generation(client, llm, workspace_id)

    await propose_edit(
        client,
        llm,
        workspace_id,
        v1["id"],
        "Make this a line chart",
        {"type": "UPDATE", "target": "regional_sales", "props": {"chart_type": "line"}},
        selected_component_id="regional_sales",
    )

    assert "Selected component\nregional_sales" in llm.calls[-1][1].content


async def test_selected_component_must_exist(
    client: httpx.AsyncClient, llm: ScriptedLLMProvider, workspace_id: str
) -> None:
    v1 = await approve_generation(client, llm, workspace_id)
    calls_before = len(llm.calls)

    response = await client.post(
        MUTATE,
        json={
            "workspace_id": workspace_id,
            "base_version_id": v1["id"],
            "instruction": "Delete this",
            "selected_component_id": "ghost",
        },
    )

    assert response.status_code == 422
    assert len(llm.calls) == calls_before


@pytest.mark.parametrize(
    "operation",
    [
        {"type": "DELETE", "target": "does_not_exist"},
        {"type": "RUN_SCRIPT", "code": "alert(1)"},
        {"type": "CREATE", "component": {"type": "iframe", "id": "frame", "src": "//evil"}},
        {"type": "SET_THEME", "tokens": {"colors": {"primary": "red; background: url(x)"}}},
    ],
    ids=["unknown-target", "unknown-operation", "unknown-component", "css-injection"],
)
async def test_invalid_operations_from_the_model_are_rejected(
    client: httpx.AsyncClient,
    llm: ScriptedLLMProvider,
    workspace_id: str,
    operation: dict[str, Any],
) -> None:
    v1 = await approve_generation(client, llm, workspace_id)
    llm.script(plan_json("x", operation), plan_json("x", operation))

    response = await client.post(
        MUTATE,
        json={"workspace_id": workspace_id, "base_version_id": v1["id"], "instruction": "Do it"},
    )

    assert response.status_code == 502
    assert response.json()["error"]["message"] == "Generated operations are invalid."
    assert len(await list_versions(client, workspace_id)) == 1


async def test_client_operations_are_checked_without_calling_the_model(
    client: httpx.AsyncClient, llm: ScriptedLLMProvider, workspace_id: str
) -> None:
    v1 = await approve_generation(client, llm, workspace_id)
    calls_before = len(llm.calls)

    async def check(*operations: dict[str, Any]) -> dict[str, Any]:
        body = {"workspace_id": workspace_id, "base_version_id": v1["id"], "operations": operations}
        response = await client.post(MUTATE, json=body)
        assert response.status_code == 200, response.text
        return response.json()["data"]  # type: ignore[no-any-return]

    valid = await check(MOVE_TABLE_UP)
    invalid = await check({"type": "DELETE", "target": "regional_sales"})

    assert len(llm.calls) == calls_before
    assert valid["validation"]["valid"] is True
    assert _page_ids(valid["document"])[2] == "regional_breakdown"
    assert invalid["validation"]["valid"] is False
    assert "document" not in invalid
    assert invalid["validation"]["issues"][0]["stage"] == "semantic", "filter now targets nothing"
    assert len(await _messages(client, workspace_id)) == 2, (
        "checks are not part of the conversation"
    )


async def test_edit_based_on_a_stale_version_is_refused(
    client: httpx.AsyncClient, llm: ScriptedLLMProvider, workspace_id: str
) -> None:
    await approve_generation(client, llm, workspace_id)
    calls_before = len(llm.calls)

    response = await client.post(
        MUTATE,
        json={
            "workspace_id": workspace_id,
            "base_version_id": str(uuid.uuid4()),
            "instruction": "Make it dark",
        },
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "VERSION_CONFLICT"
    assert len(llm.calls) == calls_before


async def test_edit_requires_an_existing_ui(client: httpx.AsyncClient, workspace_id: str) -> None:
    response = await client.post(
        MUTATE,
        json={
            "workspace_id": workspace_id,
            "base_version_id": str(uuid.uuid4()),
            "instruction": "x",
        },
    )

    assert response.status_code == 409, "a workspace without versions has no such base"


async def test_request_must_carry_exactly_one_of_instruction_and_operations(
    client: httpx.AsyncClient, workspace_id: str
) -> None:
    base = {"workspace_id": workspace_id, "base_version_id": str(uuid.uuid4())}

    neither = await client.post(MUTATE, json=base)
    both = await client.post(
        MUTATE, json={**base, "instruction": "x", "operations": [MOVE_TABLE_UP]}
    )

    assert (neither.status_code, both.status_code) == (422, 422)


# --- Real provider classes over a mocked transport --------------------------------


def _groq_reply(content: str) -> httpx.Response:
    return httpx.Response(200, json={"choices": [{"message": {"content": content}}]})


def _cohere_reply(content: str) -> httpx.Response:
    return httpx.Response(200, json={"message": {"content": [{"type": "text", "text": content}]}})


def _is_intent_call(request: httpx.Request) -> bool:
    return "You analyse a user's request" in json.loads(request.content)["messages"][0]["content"]


async def _generate_with_transport(
    database_url: str, handler: httpx.MockTransport, **settings: Any
) -> httpx.Response:
    app = create_app(
        make_settings(
            database_url=database_url,
            groq_api_key="groq-secret",
            groq_base_url="https://groq.test",
            **settings,
        )
    )
    async with httpx.AsyncClient(transport=handler) as upstream, running_client(app) as client:
        app.dependency_overrides[get_http_client] = lambda: upstream
        workspace = await create_workspace(client)
        return await client.post(
            GENERATE, json={"workspace_id": workspace["id"], "instruction": "Show sales"}
        )


@pytest.mark.usefixtures("db_engine")
async def test_groq_is_used_end_to_end_through_the_provider_factory(database_url: str) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.host == "groq.test"
        assert request.headers["authorization"] == "Bearer groq-secret"
        return _groq_reply(intent_json() if _is_intent_call(request) else generation_json())

    response = await _generate_with_transport(database_url, httpx.MockTransport(handler))

    assert response.status_code == 200, response.text
    metadata = response.json()["data"]["metadata"]
    assert (metadata["provider"], metadata["model"]) == ("groq", "openai/gpt-oss-120b")
    assert "groq-secret" not in response.text


@pytest.mark.usefixtures("db_engine")
async def test_cohere_answers_when_groq_fails(database_url: str) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "groq.test":
            return httpx.Response(503, json={"error": "overloaded"})
        return _cohere_reply(intent_json() if _is_intent_call(request) else generation_json())

    response = await _generate_with_transport(
        database_url,
        httpx.MockTransport(handler),
        cohere_api_key="cohere-secret",
        cohere_base_url="https://cohere.test",
        llm_fallback_providers=["cohere"],
    )

    assert response.status_code == 200, response.text
    assert response.json()["data"]["metadata"]["provider"] == "cohere"


@pytest.mark.usefixtures("db_engine")
async def test_controlled_error_when_every_provider_fails(database_url: str) -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(500, json={"error": "secret-detail"})
    )

    response = await _generate_with_transport(
        database_url,
        transport,
        cohere_api_key="cohere-secret",
        cohere_base_url="https://cohere.test",
        llm_fallback_providers=["cohere"],
    )

    assert response.status_code == 502
    error = response.json()["error"]
    assert error["code"] == "LLM_ALL_PROVIDERS_FAILED"
    assert [(d["provider"], d["reason"]) for d in error["details"]] == [
        ("groq", "HTTP 500"),
        ("cohere", "HTTP 500"),
    ]
    assert "secret" not in response.text
