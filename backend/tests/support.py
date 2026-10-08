"""Test doubles and sample documents shared across the suite."""

import json
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from typing import Any

import httpx
from fastapi import FastAPI

from app.ai.llm.base import GenerationOptions, LLMChunk, LLMMessage, LLMProvider, LLMResponse
from app.core.config import Environment, LLMProviderName, LogFormat, Settings
from app.domains.generative_ui.design_registry import build_default_design_registry
from app.domains.generative_ui.document import UIDocument, dump_document
from app.main import create_app
from scripts import sample_app
from scripts.sample_build import build_sample_application

STREAM_CHUNK_SIZE = 64
UNREACHABLE_DATABASE_URL = "postgresql+asyncpg://nobody:nothing@127.0.0.1:1/none"


def make_settings(**overrides: Any) -> Settings:
    """Settings that ignore the developer's .env and shell environment."""
    values: dict[str, Any] = {
        "app_env": Environment.TEST,
        "database_url": UNREACHABLE_DATABASE_URL,
        "default_llm_provider": LLMProviderName.GROQ,
        "llm_fallback_providers": [],
        "llm_max_repair_attempts": 1,
        "groq_api_key": None,
        "cohere_api_key": None,
        "google_api_key": None,
        "twentyfirst_api_key": None,
        "google_search_engine_id": None,
        "cors_origins": ["http://localhost:3000"],
        "log_level": "INFO",
        "log_format": LogFormat.JSON,
        "log_prompts": False,
        "enable_mock_data": True,
        # Most tests exercise behaviour, not access control: anonymous mode, no budgets.
        "auth_required": False,
        "secret_key": None,
        "rate_limit_per_minute": 0,
        "ai_rate_limit_per_minute": 0,
        "auth_rate_limit_per_minute": 0,
        "llm_max_retries": 0,
        "llm_retry_backoff_seconds": 0,
        "data_source_allow_private_hosts": False,
        # No network for images, no waiting, no optional extra passes.
        "image_generation_provider": "none",
        "image_search_provider": "none",
        "unsplash_access_key": None,
        "llm_rate_limit_retries": 0,
        "llm_rate_limit_wait_seconds": 0,
        "app_refinement_passes": 0,
        "app_screen_concurrency": 1,
    }
    return Settings(_env_file=None, **(values | overrides))


class ScriptedLLMProvider(LLMProvider):
    """Returns queued responses in order and records every call."""

    def __init__(self, name: str = "scripted", model: str = "scripted-model") -> None:
        self._name = name
        self._model = model
        self._responses: list[str | Exception] = []
        self.calls: list[list[LLMMessage]] = []
        self.answer_stages = True

    def stage_calls(self, opening: str) -> list[list[LLMMessage]]:
        """Calls whose system prompt starts with ``opening``."""
        return [call for call in self.calls if call[0].content.startswith(opening)]

    def script(self, *responses: str | Exception) -> None:
        self._responses.extend(responses)

    @property
    def name(self) -> str:
        return self._name

    @property
    def model(self) -> str:
        return self._model

    async def generate_text(
        self, messages: Sequence[LLMMessage], options: GenerationOptions | None = None
    ) -> LLMResponse:
        return self._next(messages)

    async def generate_structured(
        self, messages: Sequence[LLMMessage], options: GenerationOptions | None = None
    ) -> LLMResponse:
        return self._next(messages)

    async def stream_text(
        self,
        messages: Sequence[LLMMessage],
        options: GenerationOptions | None = None,
        *,
        json_mode: bool = False,
    ) -> AsyncIterator[LLMChunk]:
        """Streams the next scripted response in small pieces."""
        content = self._next(messages).content
        for start in range(0, len(content), STREAM_CHUNK_SIZE):
            yield LLMChunk(content[start : start + STREAM_CHUNK_SIZE], self._name, self._model)

    def _next(self, messages: Sequence[LLMMessage]) -> LLMResponse:
        self.calls.append(list(messages))
        # Application-generation stages are answered by the scripted sample application,
        # whatever order they arrive in; everything else comes from the queue.
        staged = sample_app.reply(messages[0].content, messages[1].content)
        if staged is not None and self.answer_stages:
            return LLMResponse(content=staged, provider=self._name, model=self._model)
        if not self._responses:
            raise AssertionError("ScriptedLLMProvider was called more often than scripted.")
        response = self._responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return LLMResponse(content=response, provider=self._name, model=self._model)


def intent_json(intent: str = "comparison", *required_data: str) -> str:
    return json.dumps(
        {
            "intent": intent,
            "title": "Sales by region",
            "required_data": list(required_data or ("sales_by_region",)),
        }
    )


def sample_ui() -> dict[str, Any]:
    """A valid page over the mock sales data: metrics, filter, chart and table."""
    return {
        "type": "page",
        "title": "Sales by Region",
        "components": [
            {
                "type": "section",
                "id": "kpis",
                "children": [
                    {
                        "type": "metric",
                        "id": "revenue_metric",
                        "title": "Revenue",
                        "data_source": {"dataset": "sales_summary", "field": "total_revenue"},
                        "layout": {"span": 6},
                    },
                    {
                        "type": "metric",
                        "id": "orders_metric",
                        "title": "Orders",
                        "value": 1234,
                        "layout": {"span": 6},
                    },
                ],
            },
            {
                "type": "select",
                "id": "region_filter",
                "name": "region",
                "label": "Region",
                "options": [{"label": "North", "value": "North"}],
                "on_change": {
                    "type": "filter",
                    "payload": {
                        "dataset": "sales_by_region",
                        "field": "region",
                        "target": "regional_sales",
                    },
                },
            },
            {
                "type": "chart",
                "id": "regional_sales",
                "chart_type": "bar",
                "x_key": "region",
                "y_keys": ["revenue"],
                "data_source": {"dataset": "sales_by_region"},
            },
            {
                "type": "table",
                "id": "regional_breakdown",
                "title": "Breakdown",
                "columns": [
                    {"key": "region", "label": "Region"},
                    {"key": "revenue", "label": "Revenue", "format": "currency"},
                ],
                "data_source": {"dataset": "sales_by_region"},
            },
        ],
    }


def text_page(*components: dict[str, Any]) -> dict[str, Any]:
    """A minimal page wrapping ``components`` (or a single text component)."""
    default = {"type": "text", "id": "note", "content": "Hello"}
    return {"type": "page", "title": "Test", "components": list(components) or [default]}


def default_theme() -> dict[str, Any]:
    theme = build_default_design_registry().default_theme()
    return theme.model_dump(mode="json", exclude_none=True)


def sample_document(page: dict[str, Any] | None = None, **overrides: Any) -> dict[str, Any]:
    """A complete UI document around ``page`` (default: ``sample_ui``)."""
    document = {
        "schema_version": "3.0",
        "page": page or sample_ui(),
        "theme": default_theme(),
        "design": {"framework": "shadcn", "design_system": "modern_minimal"},
    }
    return document | overrides


def parsed_document(page: dict[str, Any] | None = None, **overrides: Any) -> UIDocument:
    return UIDocument.model_validate(sample_document(page, **overrides))


def canonical_document(page: dict[str, Any] | None = None, **overrides: Any) -> dict[str, Any]:
    """The JSON form the backend stores and serves: defaults filled in, no nulls."""
    return dump_document(parsed_document(page, **overrides))


def generation_json(page: dict[str, Any] | None = None, theme_preset: str | None = None) -> str:
    """What the model returns for a generation request."""
    return json.dumps({"theme_preset": theme_preset, "page": page or sample_ui()})


def plan_json(message: str, *operations: dict[str, Any]) -> str:
    """What the model returns for an edit request."""
    return json.dumps({"message": message, "operations": list(operations)})


EXAMPLE_ASSET_IDS = ("hero_image", "project_mirador", "studio_interior", "pipeline_preview")


_SAMPLE_APPLICATION: list[str] = []


async def sample_application() -> dict[str, Any]:
    """The sample recruitment application in canonical JSON form (a fresh copy).

    The pipeline is deterministic on scripted answers, so it is built once per run.
    """
    if not _SAMPLE_APPLICATION:
        _SAMPLE_APPLICATION.append(json.dumps(dump_document(await build_sample_application())))
    return json.loads(_SAMPLE_APPLICATION[0])  # type: ignore[no-any-return]


async def sample_application_document() -> UIDocument:
    return UIDocument.model_validate(await sample_application())


async def application_with(*components: dict[str, Any]) -> dict[str, Any]:
    """The sample application with ``components`` added to its candidate screen.

    That screen has a route parameter, so record-bound components validate, and
    the images the catalogue examples mention are registered as assets.
    """
    document = await sample_application()
    screen = next(s for s in document["page"]["components"] if s["id"] == "candidate_detail")
    # Catalogue examples reuse ids the application already has.
    screen["children"] += [{**c, "id": f"example_{c['id']}"} for c in components]
    template = document["application"]["assets"][0]
    document["application"]["assets"] += [
        {**template, "id": asset_id} for asset_id in EXAMPLE_ASSET_IDS
    ]
    return document


@asynccontextmanager
async def running_client(app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    """Run the app's lifespan and yield an HTTP client bound to it."""
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            yield client


def stateless_app(**settings_overrides: Any) -> FastAPI:
    """An app whose database is never reached; for routes that need no storage."""
    return create_app(make_settings(**settings_overrides))
