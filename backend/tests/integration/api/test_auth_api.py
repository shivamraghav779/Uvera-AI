"""Authentication, per-user isolation and rate limiting with access control switched on."""

import uuid
from collections.abc import AsyncIterator
from typing import Any

import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.main import create_app
from tests.support import make_settings, running_client

API = "/api/v1"
PASSWORD = "correct-horse-battery"


@pytest.fixture
async def secured(database_url: str, db_engine: AsyncEngine) -> AsyncIterator[httpx.AsyncClient]:
    app = create_app(make_settings(database_url=database_url, auth_required=True))
    async with running_client(app) as client:
        yield client


async def _register(client: httpx.AsyncClient, email: str = "ana@example.com") -> dict[str, Any]:
    response = await client.post(
        f"{API}/auth/register", json={"email": email, "password": PASSWORD}
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]  # type: ignore[no-any-return]


def _bearer(session: dict[str, Any]) -> dict[str, str]:
    return {"Authorization": f"Bearer {session['access_token']}"}


async def test_register_returns_a_token_and_never_the_password(
    secured: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    response = await secured.post(
        f"{API}/auth/register", json={"email": "  Ana@Example.COM ", "password": PASSWORD}
    )

    session = response.json()["data"]
    assert response.status_code == 201
    assert session["token_type"] == "bearer"
    assert session["expires_in"] == 720 * 60
    assert session["user"]["email"] == "ana@example.com", "emails are normalised"
    assert PASSWORD not in response.text
    stored = await db_session.scalar(text("SELECT password_hash FROM users"))
    assert stored.startswith("scrypt$") and PASSWORD not in stored


async def test_login_and_me(secured: httpx.AsyncClient) -> None:
    registered = await _register(secured)

    login = await secured.post(
        f"{API}/auth/login", json={"email": "ANA@example.com", "password": PASSWORD}
    )
    me = await secured.get(f"{API}/auth/me", headers=_bearer(login.json()["data"]))

    assert login.status_code == 200
    assert me.json()["data"]["id"] == registered["user"]["id"]


async def test_wrong_password_and_unknown_email_are_indistinguishable(
    secured: httpx.AsyncClient,
) -> None:
    await _register(secured)

    wrong = await secured.post(
        f"{API}/auth/login", json={"email": "ana@example.com", "password": "wrong-password"}
    )
    unknown = await secured.post(
        f"{API}/auth/login", json={"email": "nobody@example.com", "password": PASSWORD}
    )

    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json()["error"]["code"] == unknown.json()["error"]["code"] == "INVALID_CREDENTIALS"
    assert wrong.json()["error"]["message"] == unknown.json()["error"]["message"]
    assert wrong.headers["www-authenticate"] == "Bearer"


async def test_an_email_can_only_be_registered_once(secured: httpx.AsyncClient) -> None:
    await _register(secured)

    again = await secured.post(
        f"{API}/auth/register", json={"email": "ANA@example.com", "password": PASSWORD}
    )

    assert again.status_code == 409
    assert again.json()["error"]["code"] == "EMAIL_ALREADY_REGISTERED"


@pytest.mark.parametrize(
    "body",
    [
        {"email": "not-an-email", "password": PASSWORD},
        {"email": "ana@example.com", "password": "short"},
        {"email": "ana@example.com"},
        {"email": "ana@example.com", "password": PASSWORD, "is_admin": True},
    ],
)
async def test_invalid_registrations_are_rejected(
    secured: httpx.AsyncClient, body: dict[str, Any]
) -> None:
    response = await secured.post(f"{API}/auth/register", json=body)

    assert response.status_code == 422
    assert PASSWORD not in response.text, "input is never echoed back"


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/workspaces"),
        ("POST", "/workspaces"),
        ("GET", f"/workspaces/{uuid.uuid4()}/versions"),
        ("GET", "/data-sources"),
        ("GET", "/data-sources/datasets"),
        ("POST", "/ui/generate"),
        ("POST", "/ui/mutate/stream"),
        ("POST", "/ui/validate"),
        ("POST", "/actions/execute"),
        ("GET", "/auth/me"),
    ],
)
async def test_protected_endpoints_require_a_token(
    secured: httpx.AsyncClient, method: str, path: str
) -> None:
    response = await secured.request(method, f"{API}{path}", json={})

    assert response.status_code == 401, response.text
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"


@pytest.mark.parametrize("path", ["/health", "/auth/config", "/ui/components", "/ui/themes"])
async def test_public_endpoints_need_no_token(secured: httpx.AsyncClient, path: str) -> None:
    assert (await secured.get(f"{API}{path}")).status_code == 200


async def test_forged_and_orphaned_tokens_are_rejected(
    secured: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    session = await _register(secured)
    forged = await secured.get(f"{API}/workspaces", headers={"Authorization": "Bearer abc.def.ghi"})

    await db_session.execute(text("DELETE FROM users"))
    await db_session.commit()
    orphaned = await secured.get(f"{API}/workspaces", headers=_bearer(session))

    assert (forged.status_code, forged.json()["error"]["code"]) == (401, "INVALID_TOKEN")
    assert (orphaned.status_code, orphaned.json()["error"]["code"]) == (401, "INVALID_TOKEN")


async def test_users_only_see_and_touch_their_own_workspaces(secured: httpx.AsyncClient) -> None:
    ana, ben = (
        _bearer(await _register(secured)),
        _bearer(await _register(secured, "ben@example.com")),
    )
    workspace = (
        await secured.post(f"{API}/workspaces", json={"title": "Ana's"}, headers=ana)
    ).json()["data"]
    url = f"{API}/workspaces/{workspace['id']}"

    assert [
        w["id"] for w in (await secured.get(f"{API}/workspaces", headers=ana)).json()["data"]
    ] == [workspace["id"]]
    assert (await secured.get(f"{API}/workspaces", headers=ben)).json()["data"] == []
    for response in (
        await secured.get(url, headers=ben),
        await secured.patch(url, json={"title": "Mine now"}, headers=ben),
        await secured.delete(url, headers=ben),
        await secured.get(f"{url}/versions", headers=ben),
        await secured.get(f"{url}/messages", headers=ben),
        await secured.get(f"{url}/submissions", headers=ben),
    ):
        assert response.status_code == 404, "another user's workspace does not exist for you"
    assert (await secured.get(url, headers=ana)).json()["data"]["title"] == "Ana's"


async def test_credential_endpoints_are_rate_limited(
    database_url: str, db_engine: AsyncEngine
) -> None:
    app = create_app(
        make_settings(database_url=database_url, auth_required=True, auth_rate_limit_per_minute=3)
    )
    async with running_client(app) as client:
        attempts = [
            await client.post(f"{API}/auth/login", json={"email": "a@b.co", "password": "guess"})
            for _ in range(4)
        ]

    assert [r.status_code for r in attempts] == [401, 401, 401, 429]
    blocked = attempts[-1]
    assert blocked.json()["error"]["code"] == "RATE_LIMIT_EXCEEDED"
    assert 1 <= int(blocked.headers["retry-after"]) <= 60


async def test_general_budget_is_per_caller(database_url: str, db_engine: AsyncEngine) -> None:
    app = create_app(
        make_settings(database_url=database_url, auth_required=True, rate_limit_per_minute=2)
    )
    async with running_client(app) as client:
        ana = _bearer(await _register(client))
        ben = _bearer(await _register(client, "ben@example.com"))
        ana_calls = [await client.get(f"{API}/workspaces", headers=ana) for _ in range(3)]
        ben_call = await client.get(f"{API}/workspaces", headers=ben)

    assert [r.status_code for r in ana_calls] == [200, 200, 429]
    assert ben_call.status_code == 200, "one caller's traffic does not use another's budget"


async def test_anonymous_mode_reports_itself_and_lets_requests_through(
    client: httpx.AsyncClient,
) -> None:
    config = await client.get(f"{API}/auth/config")

    assert config.json()["data"]["auth_required"] is False
    assert (await client.get(f"{API}/workspaces")).status_code == 200
