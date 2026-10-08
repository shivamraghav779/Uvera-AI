"""Builds LLM providers from configuration."""

from collections.abc import Callable

import httpx

from app.ai.llm.base import LLMProvider
from app.ai.llm.cohere import CohereProvider
from app.ai.llm.fallback import FallbackLLMProvider
from app.ai.llm.groq import GroqProvider
from app.core.config import LLMProviderName, Settings
from app.core.exceptions import ProviderNotConfiguredException
from app.core.logging import get_logger

logger = get_logger(__name__)

ProviderBuilder = Callable[[], LLMProvider | None]


class LLMFactory:
    """Creates providers by name, or the configured default with its fallbacks.

    To add a vendor: implement ``LLMProvider``, add a ``LLMProviderName`` member
    and one entry in ``_builders``. Nothing else in the application changes.
    """

    def __init__(self, settings: Settings, http_client: httpx.AsyncClient) -> None:
        self._settings = settings
        self._http_client = http_client
        self._builders: dict[LLMProviderName, ProviderBuilder] = {
            LLMProviderName.GROQ: self._build_groq,
            LLMProviderName.COHERE: self._build_cohere,
        }

    def is_configured(self, name: LLMProviderName | str) -> bool:
        return self._build(name) is not None

    def create(self, name: LLMProviderName | str) -> LLMProvider:
        provider = self._build(name)
        if provider is None:
            raise ProviderNotConfiguredException(
                f"LLM provider '{name}' is not configured: its API key is missing."
            )
        return provider

    def create_default(self) -> LLMProvider:
        """The default provider, followed by every configured fallback."""
        settings = self._settings
        chain = [self.create(settings.default_llm_provider)]
        for name in settings.llm_fallback_providers:
            if name is settings.default_llm_provider:
                continue
            fallback = self._build(name)
            if fallback is None:
                logger.warning("llm_fallback_not_configured", extra={"provider": name.value})
                continue
            chain.append(fallback)
        # Always wrapped, so failures are logged and reported the same way with or
        # without fallbacks.
        return FallbackLLMProvider(chain)

    def _build(self, name: LLMProviderName | str) -> LLMProvider | None:
        try:
            builder = self._builders[LLMProviderName(name)]
        except (ValueError, KeyError):
            supported = ", ".join(provider.value for provider in self._builders)
            raise ProviderNotConfiguredException(
                f"Unknown LLM provider '{name}'. Supported providers: {supported}."
            ) from None
        return builder()

    def _build_groq(self) -> LLMProvider | None:
        settings = self._settings
        if settings.groq_api_key is None:
            return None
        return GroqProvider(
            api_key=settings.groq_api_key,
            model=settings.groq_model,
            base_url=settings.groq_base_url,
            client=self._http_client,
            timeout_seconds=settings.llm_timeout_seconds,
            max_retries=settings.llm_max_retries,
            retry_backoff_seconds=settings.llm_retry_backoff_seconds,
        )

    def _build_cohere(self) -> LLMProvider | None:
        settings = self._settings
        if settings.cohere_api_key is None:
            return None
        return CohereProvider(
            api_key=settings.cohere_api_key,
            model=settings.cohere_model,
            base_url=settings.cohere_base_url,
            client=self._http_client,
            timeout_seconds=settings.llm_timeout_seconds,
            max_retries=settings.llm_max_retries,
            retry_backoff_seconds=settings.llm_retry_backoff_seconds,
        )
