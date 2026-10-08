import httpx

from tests.support import running_client, stateless_app


async def test_health_reports_database_up(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "data": {"status": "ok", "version": "0.1.0", "environment": "test", "database": "up"},
    }
    assert response.headers["x-request-id"]


async def test_health_reports_degraded_when_database_is_unreachable() -> None:
    async with running_client(stateless_app()) as client:
        response = await client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["data"] == {
        "status": "degraded",
        "version": "0.1.0",
        "environment": "test",
        "database": "down",
    }


async def test_openapi_documents_every_endpoint_under_its_tag() -> None:
    async with running_client(stateless_app()) as client:
        schema = (await client.get("/openapi.json")).json()
        docs = await client.get("/docs")

    operations = {
        (method.upper(), path): operation["tags"]
        for path, methods in schema["paths"].items()
        for method, operation in methods.items()
    }
    assert operations == {
        ("GET", "/api/v1/health"): ["Health"],
        ("GET", "/api/v1/auth/config"): ["Authentication"],
        ("POST", "/api/v1/auth/register"): ["Authentication"],
        ("POST", "/api/v1/auth/login"): ["Authentication"],
        ("GET", "/api/v1/auth/me"): ["Authentication"],
        ("GET", "/api/v1/workspaces"): ["Workspaces"],
        ("POST", "/api/v1/workspaces"): ["Workspaces"],
        ("GET", "/api/v1/workspaces/{workspace_id}"): ["Workspaces"],
        ("PATCH", "/api/v1/workspaces/{workspace_id}"): ["Workspaces"],
        ("DELETE", "/api/v1/workspaces/{workspace_id}"): ["Workspaces"],
        ("GET", "/api/v1/workspaces/{workspace_id}/versions"): ["Versions"],
        ("POST", "/api/v1/workspaces/{workspace_id}/versions"): ["Versions"],
        ("GET", "/api/v1/workspaces/{workspace_id}/versions/{version_id}"): ["Versions"],
        ("POST", "/api/v1/workspaces/{workspace_id}/versions/{version_id}/restore"): ["Versions"],
        ("GET", "/api/v1/workspaces/{workspace_id}/versions/{version_id}/compare"): ["Versions"],
        ("GET", "/api/v1/workspaces/{workspace_id}/messages"): ["Conversations"],
        ("POST", "/api/v1/workspaces/{workspace_id}/messages"): ["Conversations"],
        ("GET", "/api/v1/workspaces/{workspace_id}/submissions"): ["Actions"],
        ("DELETE", "/api/v1/workspaces/{workspace_id}/records"): ["Actions"],
        ("GET", "/api/v1/workspaces/{workspace_id}/application"): ["Workspaces"],
        ("GET", "/api/v1/workspaces/{workspace_id}/assets"): ["Assets"],
        ("POST", "/api/v1/workspaces/{workspace_id}/assets"): ["Assets"],
        ("GET", "/api/v1/assets/{asset_id}/content"): ["Assets"],
        ("GET", "/api/v1/references"): ["Reference components"],
        ("GET", "/api/v1/references/facets"): ["Reference components"],
        ("GET", "/api/v1/references/{reference_id}"): ["Reference components"],
        ("POST", "/api/v1/generation/jobs"): ["Generation"],
        ("GET", "/api/v1/generation/jobs"): ["Generation"],
        ("GET", "/api/v1/generation/jobs/{job_id}"): ["Generation"],
        ("POST", "/api/v1/generation/jobs/{job_id}/cancel"): ["Generation"],
        ("GET", "/api/v1/ui/patterns"): ["Generative UI"],
        ("POST", "/api/v1/ui/generate"): ["Generative UI"],
        ("POST", "/api/v1/ui/generate/stream"): ["Generative UI"],
        ("POST", "/api/v1/ui/mutate/stream"): ["Generative UI"],
        ("POST", "/api/v1/ui/mutate"): ["Generative UI"],
        ("POST", "/api/v1/ui/validate"): ["Generative UI"],
        ("GET", "/api/v1/ui/components"): ["Generative UI"],
        ("GET", "/api/v1/ui/frameworks"): ["Generative UI"],
        ("GET", "/api/v1/ui/themes"): ["Generative UI"],
        ("GET", "/api/v1/ui/capabilities"): ["Generative UI"],
        ("GET", "/api/v1/data-sources"): ["Data Sources"],
        ("POST", "/api/v1/data-sources"): ["Data Sources"],
        ("GET", "/api/v1/data-sources/datasets"): ["Data Sources"],
        ("DELETE", "/api/v1/data-sources/{data_source_id}"): ["Data Sources"],
        ("POST", "/api/v1/actions/execute"): ["Actions"],
    }
    assert docs.status_code == 200


async def test_cors_allows_configured_origin_only() -> None:
    async with running_client(stateless_app(cors_origins=["https://app.example.com"])) as client:
        allowed = await client.get(
            "/api/v1/ui/components", headers={"Origin": "https://app.example.com"}
        )
        denied = await client.get(
            "/api/v1/ui/components", headers={"Origin": "https://evil.example"}
        )

    assert allowed.headers["access-control-allow-origin"] == "https://app.example.com"
    assert "x-request-id" in allowed.headers["access-control-expose-headers"].lower()
    assert "access-control-allow-origin" not in denied.headers
