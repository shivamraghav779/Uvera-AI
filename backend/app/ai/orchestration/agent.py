"""Coordinates the generation pipeline. Each stage lives in its own class.

    request -> plan (intent + UI plan) -> retrieve data -> generate + validate

The agent only sequences stages and passes typed results between them; it holds
no prompt text, validation logic or provider knowledge. Edits to an existing UI
take the shorter path in ``mutation.py``.
"""

from collections.abc import Sequence

from app.ai.orchestration.executor import GenerationTask, UIGenerationExecutor
from app.ai.orchestration.planner import PlanningRequest, RequestPlanner
from app.domains.data_sources.providers.base import DataProvider
from app.domains.data_sources.schemas import DatasetDescriptor, DatasetSnapshot
from app.domains.generative_ui.contracts import (
    ProgressStage,
    UIGenerationInput,
    UIGenerationOutput,
    report,
)
from app.domains.generative_ui.planner import UIPlan
from app.domains.generative_ui.registry import ComponentRegistry
from app.domains.generative_ui.validator import ValidationContext

# Rows of each planned dataset shown to the model.
PROMPT_ROW_LIMIT = 40


class GenerativeUIAgent:
    """Implements the domain's ``UIGenerator`` port."""

    def __init__(
        self,
        *,
        planner: RequestPlanner,
        executor: UIGenerationExecutor,
        data_provider: DataProvider,
        registry: ComponentRegistry,
    ) -> None:
        self._planner = planner
        self._executor = executor
        self._data_provider = data_provider
        self._registry = registry

    async def generate(self, request: UIGenerationInput) -> UIGenerationOutput:
        await report(request.progress, ProgressStage.UNDERSTANDING)
        datasets = await self._data_provider.list_datasets()
        plan = await self._planner.plan(
            PlanningRequest(
                user_request=request.user_request,
                history=request.history,
                datasets=datasets,
                available_components=self._registry.types(),
            )
        )
        await report(request.progress, ProgressStage.PLANNING)
        generated = await self._executor.execute(
            GenerationTask(
                user_request=request.user_request,
                plan=plan,
                history=request.history,
                datasets=await self._retrieve(plan),
                validation_context=_validation_context(datasets),
                base_theme=request.base_theme,
                design=request.design,
                progress=request.progress,
            )
        )
        return UIGenerationOutput(
            document=generated.document,
            intent=plan.intent,
            provider=generated.provider,
            model=generated.model,
            prompt_version=generated.prompt_version,
            repair_attempts=generated.repair_attempts,
        )

    async def _retrieve(self, plan: UIPlan) -> list[DatasetSnapshot]:
        return [
            await self._data_provider.fetch(name, limit=PROMPT_ROW_LIMIT)
            for name in plan.required_data
        ]


def _validation_context(datasets: Sequence[DatasetDescriptor]) -> ValidationContext:
    return ValidationContext(datasets={dataset.name: dataset for dataset in datasets})
