"""Registered data sources are read for real: uploads, HTTPS APIs and SQL queries."""

import os
from collections.abc import Callable
from typing import Any

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_data_provider_factory
from app.domains.data_sources.providers.factory import DataProviderFactory, EnvSecretResolver
from tests.integration.api.flows import API, create_workspace, save_version
from tests.support import sample_document, text_page

SOURCES = f"{API}/data-sources"
CSV = "id,status,hours\n1,open,2.5\n2,closed,4\n3,open,\n"
TICKETS = {
    "name": "Support tickets",
    "type": "file_upload",
    "configuration": {"dataset": "tickets", "description": "Support tickets.", "content": CSV},
}
ORDERS_API = {
    "name": "Orders API",
    "type": "rest_api",
    "configuration": {
        "dataset": "orders",
        "url": "https://api.example.com/v1/orders",
        "records_path": "data.items",
        "credentials_ref": "ORDERS_API",
    },
}


def _tickets_chart() -> dict[str, Any]:
    return {
        "type": "chart",
        "id": "ticket_hours",
        "chart_type": "bar",
        "x_key": "status",
        "y_keys": ["hours"],
        "data_source": {"dataset": "tickets"},
    }


def _use_upstream(app: FastAPI, handler: Callable[[httpx.Request], httpx.Response]) -> None:
    """Route REST data sources to a fake upstream API."""
    upstream = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    app.dependency_overrides[get_data_provider_factory] = lambda: DataProviderFactory(
        http_client=upstream,
        secrets=EnvSecretResolver(),
        timeout_seconds=5,
        allow_private_hosts=True,
    )


async def _datasets(client: httpx.AsyncClient) -> dict[str, list[dict[str, str]]]:
    data = (await client.get(f"{SOURCES}/datasets")).json()["data"]
    return {dataset["name"]: dataset["fields"] for dataset in data}


# --- Uploads ---------------------------------------------------------------------


async def test_uploaded_csv_becomes_a_typed_dataset(client: httpx.AsyncClient) -> None:
    created = await client.post(SOURCES, json=TICKETS)

    assert created.status_code == 201, created.text
    source = created.json()["data"]
    assert (source["type"], source["datasets"]) == ("file_upload", ["tickets"])
    assert "configuration" not in source and "content" not in created.text
    assert (await _datasets(client))["tickets"] == [
        {"name": "id", "kind": "number"},
        {"name": "status", "kind": "string"},
        {"name": "hours", "kind": "number"},
    ]
    assert [s["id"] for s in (await client.get(SOURCES)).json()["data"]] == [source["id"]]


async def test_a_ui_bound_to_an_uploaded_dataset_validates_persists_and_gets_its_rows(
    client: httpx.AsyncClient,
) -> None:
    await client.post(SOURCES, json=TICKETS)
    workspace = await create_workspace(client)
    document = sample_document(text_page(_tickets_chart()))

    validated = await client.post(f"{API}/ui/validate", json={"document": document})
    saved = await save_version(client, workspace["id"], base_version_id=None, document=document)

    assert validated.json()["data"]["valid"] is True
    assert saved.status_code == 201, saved.text
    assert saved.json()["data"]["data"]["tickets"] == [
        {"id": 1, "status": "open", "hours": 2.5},
        {"id": 2, "status": "closed", "hours": 4},
        {"id": 3, "status": "open", "hours": None},
    ]


async def test_the_model_is_told_about_the_users_datasets(
    client: httpx.AsyncClient, llm: Any
) -> None:
    from tests.support import generation_json, intent_json

    await client.post(SOURCES, json=TICKETS)
    workspace = await create_workspace(client)
    llm.script(intent_json("breakdown", "tickets"), generation_json(text_page(_tickets_chart())))

    response = await client.post(
        f"{API}/ui/generate", json={"workspace_id": workspace["id"], "instruction": "Ticket hours"}
    )

    assert response.status_code == 200, response.text
    assert "- tickets: Support tickets." in llm.calls[0][1].content, "offered at the intent stage"
    assert 'dataset "tickets"' in llm.calls[1][1].content, "rows given at the generation stage"
    assert response.json()["data"]["data"]["tickets"][0]["status"] == "open"


async def test_json_uploads_are_supported(client: httpx.AsyncClient) -> None:
    body = {
        "name": "Plans",
        "type": "file_upload",
        "configuration": {
            "dataset": "plans",
            "format": "json",
            "content": '[{"plan": "pro", "seats": 5, "meta": {"tier": 2}}]',
        },
    }

    assert (await client.post(SOURCES, json=body)).status_code == 201
    assert (await _datasets(client))["plans"] == [
        {"name": "plan", "kind": "string"},
        {"name": "seats", "kind": "number"},
        {"name": "meta", "kind": "string"},
    ]


@pytest.mark.parametrize(
    ("configuration", "status"),
    [
        ({"dataset": "tickets", "content": "id,status\n"}, 422),
        ({"dataset": "tickets", "format": "json", "content": "{not json"}, 422),
        ({"dataset": "tickets", "format": "json", "content": '{"a": 1}'}, 422),
        ({"dataset": "Bad Name", "content": CSV}, 422),
        ({"dataset": "tickets"}, 422),
        ({"dataset": "tickets", "content": CSV, "api_key": "sk-live-123"}, 422),
        ({"dataset": "sales_by_region", "content": CSV}, 409),
    ],
    ids=["no-rows", "bad-json", "json-not-list", "bad-name", "no-content", "secret", "name-taken"],
)
async def test_invalid_uploads_are_rejected_and_not_stored(
    client: httpx.AsyncClient, configuration: dict[str, Any], status: int
) -> None:
    response = await client.post(
        SOURCES, json={"name": "X", "type": "file_upload", "configuration": configuration}
    )

    assert response.status_code == status, response.text
    assert "sk-live-123" not in response.text
    assert (await client.get(SOURCES)).json()["data"] == []


async def test_dataset_names_are_unique_and_freed_by_deleting_the_source(
    client: httpx.AsyncClient,
) -> None:
    first = (await client.post(SOURCES, json=TICKETS)).json()["data"]

    duplicate = await client.post(SOURCES, json=TICKETS)
    deleted = await client.delete(f"{SOURCES}/{first['id']}")
    again = await client.post(SOURCES, json=TICKETS)

    assert (duplicate.status_code, duplicate.json()["error"]["code"]) == (409, "CONFLICT")
    assert deleted.status_code == 204
    assert again.status_code == 201
    assert (await client.delete(f"{SOURCES}/{first['id']}")).status_code == 404


async def test_a_ui_still_loads_after_its_data_source_is_removed(client: httpx.AsyncClient) -> None:
    source = (await client.post(SOURCES, json=TICKETS)).json()["data"]
    workspace = await create_workspace(client)
    document = sample_document(text_page(_tickets_chart()))
    version = (
        await save_version(client, workspace["id"], base_version_id=None, document=document)
    ).json()["data"]

    await client.delete(f"{SOURCES}/{source['id']}")
    reloaded = await client.get(f"{API}/workspaces/{workspace['id']}/versions/{version['id']}")

    assert reloaded.status_code == 200
    assert reloaded.json()["data"]["data"] == {"tickets": []}, "the chart shows its empty state"


# --- REST APIs ---------------------------------------------------------------------


async def test_rest_source_is_fetched_with_the_server_side_secret(
    app: FastAPI, client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: list[httpx.Request] = []

    def upstream(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        items = [{"order": 1, "total": 120.5}, {"order": 2, "total": 80}]
        return httpx.Response(200, json={"data": {"items": items}})

    _use_upstream(app, upstream)
    monkeypatch.setenv("DATASOURCE_SECRET_ORDERS_API", "upstream-token-123")

    created = await client.post(SOURCES, json=ORDERS_API)

    assert created.status_code == 201, created.text
    assert seen[0].headers["authorization"] == "Bearer upstream-token-123"
    assert str(seen[0].url) == "https://api.example.com/v1/orders"
    assert "upstream-token-123" not in created.text
    assert (await _datasets(client))["orders"] == [
        {"name": "order", "kind": "number"},
        {"name": "total", "kind": "number"},
    ]


@pytest.mark.parametrize(
    ("reply", "message"),
    [
        (httpx.Response(500, json={"error": "boom"}), "HTTP 500"),
        (httpx.Response(302, headers={"location": "http://169.254.169.254/"}), "HTTP 302"),
        (httpx.Response(200, text="<html>"), "did not return JSON"),
        (httpx.Response(200, json={"data": {}}), "no 'data.items'"),
        (httpx.Response(200, json={"data": {"items": "nope"}}), "list of records"),
    ],
    ids=["server-error", "redirect", "not-json", "missing-path", "not-a-list"],
)
async def test_an_unreadable_rest_source_is_refused_with_a_reason(
    app: FastAPI,
    client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    reply: httpx.Response,
    message: str,
) -> None:
    _use_upstream(app, lambda request: reply)
    monkeypatch.setenv("DATASOURCE_SECRET_ORDERS_API", "t")

    response = await client.post(SOURCES, json=ORDERS_API)

    assert response.status_code == 502
    assert response.json()["error"]["code"] == "DATA_SOURCE_ERROR"
    assert message in response.json()["error"]["message"]
    assert (await client.get(SOURCES)).json()["data"] == []


async def test_a_missing_secret_is_reported_by_name_only(client: httpx.AsyncClient) -> None:
    os.environ.pop("DATASOURCE_SECRET_ORDERS_API", None)

    response = await client.post(SOURCES, json=ORDERS_API)

    assert response.status_code == 502
    assert "DATASOURCE_SECRET_ORDERS_API" in response.json()["error"]["message"]


@pytest.mark.parametrize(
    "url", ["https://localhost/admin", "https://127.0.0.1/", "https://10.0.0.5/internal"]
)
async def test_rest_sources_cannot_reach_private_addresses(
    client: httpx.AsyncClient, url: str
) -> None:
    body = {"name": "Internal", "type": "rest_api", "configuration": {"dataset": "x", "url": url}}

    response = await client.post(SOURCES, json=body)

    assert response.status_code == 502
    assert "public internet addresses" in response.json()["error"]["message"]


async def test_rest_sources_must_use_https(client: httpx.AsyncClient) -> None:
    body = {
        "name": "Plain",
        "type": "rest_api",
        "configuration": {"dataset": "x", "url": "http://api.example.com/x"},
    }

    assert (await client.post(SOURCES, json=body)).status_code == 422


# --- PostgreSQL ----------------------------------------------------------------------


@pytest.fixture
def warehouse(database_url: str, monkeypatch: pytest.MonkeyPatch) -> str:
    """Uses the test database itself as the "external" warehouse."""
    dsn = make_url(database_url).set(drivername="postgresql").render_as_string(hide_password=False)
    monkeypatch.setenv("DATASOURCE_SECRET_WAREHOUSE", dsn)
    return dsn


def _sql_source(query: str, name: str = "workspace_counts") -> dict[str, Any]:
    return {
        "name": "Warehouse",
        "type": "postgresql",
        "configuration": {
            "credentials_ref": "WAREHOUSE",
            "datasets": [{"name": name, "query": query}],
        },
    }


@pytest.mark.usefixtures("warehouse")
async def test_sql_source_runs_its_query_and_exposes_the_result(client: httpx.AsyncClient) -> None:
    await create_workspace(client, "One")
    await create_workspace(client, "Two")
    query = "SELECT title, length(title) AS title_length FROM workspaces ORDER BY title"

    created = await client.post(SOURCES, json=_sql_source(query))

    assert created.status_code == 201, created.text
    assert "postgresql://" not in created.text, "the connection string is never returned"
    assert (await _datasets(client))["workspace_counts"] == [
        {"name": "title", "kind": "string"},
        {"name": "title_length", "kind": "number"},
    ]


@pytest.mark.usefixtures("warehouse")
@pytest.mark.parametrize(
    ("query", "status"),
    [
        ("DELETE FROM workspaces", 422),
        ("SELECT 1; DROP TABLE workspaces", 422),
        ("UPDATE workspaces SET title = 'x'", 422),
        # Looks like a SELECT, tries to write: the READ ONLY transaction refuses it.
        ("WITH gone AS (DELETE FROM workspaces RETURNING id) SELECT * FROM gone", 502),
        ("SELECT * FROM table_that_does_not_exist", 502),
    ],
    ids=["delete", "two-statements", "update", "writing-cte", "bad-table"],
)
async def test_sql_sources_are_read_only(
    client: httpx.AsyncClient, db_session: AsyncSession, query: str, status: int
) -> None:
    await create_workspace(client, "Keep me")

    response = await client.post(SOURCES, json=_sql_source(query))

    assert response.status_code == status, response.text
    assert await db_session.scalar(text("SELECT count(*) FROM workspaces")) == 1
    assert "workspaces" not in response.json()["error"]["message"] or status == 422
    assert (await client.get(SOURCES)).json()["data"] == []


async def test_sql_source_with_unreachable_database_fails_cleanly(
    client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DATASOURCE_SECRET_WAREHOUSE", "postgresql://u:secret-pw@127.0.0.1:1/none")

    response = await client.post(SOURCES, json=_sql_source("SELECT 1 AS one"))

    assert response.status_code == 502
    assert "secret-pw" not in response.text
