"""Planning stage: user request -> intent -> UI plan."""

from collections.abc import Sequence
from dataclasses import dataclass

from pydantic import ValidationError

from app.ai.llm.base import GenerationOptions, LLMProvider
from app.ai.prompts.intent import INTENT_PROMPT, build_intent_messages
from app.core.logging import get_logger
from app.domains.data_sources.schemas import DatasetDescriptor
from app.domains.generative_ui.intent import IntentAnalysis, KeywordIntentClassifier
from app.domains.generative_ui.planner import ConversationTurn, PlanningContext, UIPlan, UIPlanner
from app.domains.generative_ui.schemas import ComponentType
from app.utils.json import parse_json_document

logger = get_logger(__name__)

INTENT_OPTIONS = GenerationOptions(temperature=0.0, max_tokens=300)


@dataclass(frozen=True, slots=True)
class PlanningRequest:
    user_request: str
    history: Sequence[ConversationTurn]
    datasets: Sequence[DatasetDescriptor]
    available_components: Sequence[ComponentType]


class RequestPlanner:
    """Asks the model what the user wants, then lets the domain planner decide the UI shape."""

    def __init__(
        self,
        llm: LLMProvider,
        ui_planner: UIPlanner,
        fallback_classifier: KeywordIntentClassifier,
    ) -> None:
        self._llm = llm
        self._ui_planner = ui_planner
        self._fallback_classifier = fallback_classifier

    async def plan(self, request: PlanningRequest) -> UIPlan:
        intent = await self._analyse_intent(request)
        return self._ui_planner.plan(
            PlanningContext(
                user_request=request.user_request,
                intent=intent,
                history=request.history,
                datasets=request.datasets,
                available_components=request.available_components,
            )
        )

    async def _analyse_intent(self, request: PlanningRequest) -> IntentAnalysis:
        messages = build_intent_messages(
            user_request=request.user_request, history=request.history, datasets=request.datasets
        )
        # Provider failures propagate; only unusable *output* falls back to keywords.
        response = await self._llm.generate_structured(messages, INTENT_OPTIONS)
        try:
            return IntentAnalysis.model_validate(parse_json_document(response.content))
        except (ValueError, ValidationError):
            logger.warning(
                "intent_analysis_invalid",
                extra={
                    "provider": response.provider,
                    "model": response.model,
                    "prompt_version": INTENT_PROMPT.version,
                    "fallback": "keyword_classifier",
                },
            )
            return self._fallback_classifier.classify(request.user_request, request.datasets)
