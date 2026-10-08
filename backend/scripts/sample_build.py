"""Builds the sample application by running the real pipeline on scripted answers.

Nothing here talks to a model, a database or the network: the model is
``scripts.sample_app``, images are drawn by the internal provider and kept in
memory. The result is exactly what the product would produce for those
answers, validated by the same validator.
"""

import uuid
from collections.abc import AsyncIterator, Sequence
from typing import Any

from app.ai.llm.base import GenerationOptions, LLMChunk, LLMMessage, LLMProvider, LLMResponse
from app.api.dependencies import ApplicationStack, build_application_stack
from app.core.config import Environment, Settings
from app.domains.actions.handlers import build_default_action_registry
from app.domains.actions.schemas import ActionType
from app.domains.assets.models import StoredAsset
from app.domains.assets.providers import InternalImageProvider
from app.domains.assets.service import AssetEngine
from app.domains.data_sources.providers.base import DataProvider, EmptyDataProvider
from app.domains.generative_ui.contracts import ApplicationBuildInput
from app.domains.generative_ui.design_registry import build_default_design_registry
from app.domains.generative_ui.document import UIDocument
from app.domains.generative_ui.mutator import DocumentMutator
from app.domains.generative_ui.pattern_registry import build_default_pattern_registry
from app.domains.generative_ui.registry import build_default_registry
from app.domains.generative_ui.validator import UISchemaValidator
from app.utils.datetime import utc_now
from scripts import sample_app

SAMPLE_WORKSPACE_ID = uuid.UUID("00000000-0000-4000-8000-000000000001")
SAMPLE_IDEA = "Build me a modern AI recruitment SaaS."


class ScriptedStageLLM(LLMProvider):
    """Answers generation-stage prompts from ``scripts.sample_app``."""

    def __init__(self) -> None:
        self.stages: list[str] = []

    @property
    def name(self) -> str:
        return "scripted"

    @property
    def model(self) -> str:
        return "scripted-model"

    async def generate_text(
        self, messages: Sequence[LLMMessage], options: GenerationOptions | None = None
    ) -> LLMResponse:
        return self._answer(messages)

    async def generate_structured(
        self, messages: Sequence[LLMMessage], options: GenerationOptions | None = None
    ) -> LLMResponse:
        return self._answer(messages)

    async def stream_text(
        self,
        messages: Sequence[LLMMessage],
        options: GenerationOptions | None = None,
        *,
        json_mode: bool = False,
    ) -> AsyncIterator[LLMChunk]:
        yield LLMChunk(self._answer(messages).content, self.name, self.model)

    def _answer(self, messages: Sequence[LLMMessage]) -> LLMResponse:
        system, prompt = messages[0].content, messages[1].content
        content = sample_app.reply(system, prompt)
        if content is None:
            raise AssertionError(f"No scripted answer for prompt starting: {system[:60]!r}")
        self.stages.append(system.split(".")[0])
        return LLMResponse(content=content, provider=self.name, model=self.model)


class MemoryAssetRepository:
    """Keeps stored assets in a list. Stands in for ``AssetRepository``."""

    def __init__(self) -> None:
        self.assets: list[StoredAsset] = []

    async def add(self, asset: StoredAsset) -> StoredAsset:
        # Stable ids and timestamps keep the exported fixture reproducible.
        asset.id = uuid.UUID(int=len(self.assets) + 1, version=4)
        asset.created_at = utc_now().replace(year=2026, month=1, day=1, hour=0, minute=0, second=0)
        self.assets.append(asset)
        return asset


class _NoTransaction:
    async def commit(self) -> None:
        return None

    async def rollback(self) -> None:
        return None


def offline_settings(**overrides: Any) -> Settings:
    values: dict[str, Any] = {
        "app_env": Environment.TEST,
        "image_generation_provider": "none",
        "image_search_provider": "none",
        "llm_rate_limit_retries": 0,
        "app_refinement_passes": 0,
        "app_screen_concurrency": 1,
        "llm_max_repair_attempts": 0,
    }
    return Settings(_env_file=None, **(values | overrides))  # type: ignore[call-arg]


def build_stack(
    llm: LLMProvider,
    *,
    data_provider: DataProvider | None = None,
    settings: Settings | None = None,
    assets: MemoryAssetRepository | None = None,
) -> ApplicationStack:
    """The application builder and editor wired without FastAPI or a database."""
    registry, design = build_default_registry(), build_default_design_registry()
    validator = UISchemaValidator(registry, frozenset(ActionType), design)
    engine = AssetEngine(
        repository=assets or MemoryAssetRepository(),  # type: ignore[arg-type]
        internal=InternalImageProvider(),
        generator=None,
        searcher=None,
        uow=_NoTransaction(),
    )
    return build_application_stack(
        settings=settings or offline_settings(),
        llm=llm,
        validator=validator,
        mutator=DocumentMutator(validator, design),
        registry=registry,
        design=design,
        patterns=build_default_pattern_registry(),
        actions=build_default_action_registry(data_provider or EmptyDataProvider(), None),
        assets=engine,
    )


async def build_sample_application() -> UIDocument:
    """The Hirewell application as the pipeline assembles and validates it."""
    stack = build_stack(ScriptedStageLLM())
    output = await stack.builder.build(
        ApplicationBuildInput(
            user_request=SAMPLE_IDEA,
            workspace_id=SAMPLE_WORKSPACE_ID,
            history=(),
            datasets=(),
            framework="shadcn",
            design_system=None,
            theme_preset=None,
        )
    )
    assert output.document is not None, "the sample idea must be understood as an application"
    assert not output.failed_screen_ids, output.failed_screen_ids
    return output.document
