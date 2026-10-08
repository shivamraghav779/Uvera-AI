"""Intent vocabulary and a deterministic classifier.

The classifier is the fallback used when the model's intent analysis is
unusable; it needs no network and always returns a valid result.
"""

from collections.abc import Sequence
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from app.domains.data_sources.schemas import DatasetDescriptor
from app.utils.helpers import tokenize, truncate

MAX_TITLE_LENGTH = 80
MAX_FALLBACK_DATASETS = 2


class UIIntent(StrEnum):
    OVERVIEW = "overview"
    COMPARISON = "comparison"
    TREND = "trend"
    BREAKDOWN = "breakdown"
    DETAIL = "detail"
    DATA_ENTRY = "data_entry"
    STATUS = "status"
    GENERAL = "general"


class IntentAnalysis(BaseModel):
    """What the user wants, in the platform's vocabulary."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    intent: UIIntent
    title: str = Field(min_length=1, max_length=MAX_TITLE_LENGTH)
    required_data: list[str] = Field(default_factory=list, max_length=10)


# First match wins, so more specific intents come first.
_INTENT_KEYWORDS: tuple[tuple[UIIntent, frozenset[str]], ...] = (
    (UIIntent.DATA_ENTRY, frozenset({"form", "submit", "enter", "register", "signup", "feedback"})),
    (
        UIIntent.COMPARISON,
        frozenset({"compare", "comparison", "versus", "vs", "across", "against"}),
    ),
    (UIIntent.TREND, frozenset({"trend", "trends", "over", "monthly", "growth", "timeline"})),
    (UIIntent.BREAKDOWN, frozenset({"breakdown", "by", "share", "distribution", "split", "per"})),
    (UIIntent.STATUS, frozenset({"status", "progress", "health", "track", "tracking"})),
    (UIIntent.DETAIL, frozenset({"list", "details", "detail", "records", "table", "all"})),
    (UIIntent.OVERVIEW, frozenset({"overview", "summary", "dashboard", "performance", "report"})),
)
_SINGULAR_SUFFIX = "s"


def _stem(word: str) -> str:
    return word.removesuffix(_SINGULAR_SUFFIX)


def _dataset_terms(dataset: DatasetDescriptor) -> set[str]:
    terms = tokenize(dataset.name.replace("_", " "))
    for field in dataset.fields:
        terms |= tokenize(field.name.replace("_", " "))
    return {_stem(term) for term in terms}


class KeywordIntentClassifier:
    def classify(self, user_request: str, datasets: Sequence[DatasetDescriptor]) -> IntentAnalysis:
        words = tokenize(user_request)
        return IntentAnalysis(
            intent=self._intent(words),
            title=truncate(user_request.strip().rstrip(".?!"), MAX_TITLE_LENGTH) or "Untitled",
            required_data=self._relevant_datasets(words, datasets),
        )

    @staticmethod
    def _intent(words: set[str]) -> UIIntent:
        for intent, keywords in _INTENT_KEYWORDS:
            if words & keywords:
                return intent
        return UIIntent.GENERAL

    @staticmethod
    def _relevant_datasets(words: set[str], datasets: Sequence[DatasetDescriptor]) -> list[str]:
        stems = {_stem(word) for word in words}
        scored = [(len(stems & _dataset_terms(dataset)), dataset.name) for dataset in datasets]
        ranked = sorted((item for item in scored if item[0] > 0), key=lambda item: -item[0])
        return [name for _, name in ranked[:MAX_FALLBACK_DATASETS]]
