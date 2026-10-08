from collections.abc import AsyncIterator

import httpx
import pytest

from app.ai.llm.cohere import CohereProvider
from app.ai.llm.factory import LLMFactory
from app.ai.llm.fallback import FallbackLLMProvider
from app.ai.llm.groq import GroqProvider
from app.core.exceptions import ProviderNotConfiguredException
from tests.support import make_settings


@pytest.fixture
async def http_client() -> AsyncIterator[httpx.AsyncClient]:
    async with httpx.AsyncClient() as client:
        yield client


def test_creates_groq_provider_from_configuration(http_client: httpx.AsyncClient) -> None:
    settings = make_settings(groq_api_key="groq-key", groq_model="llama-test")

    provider = LLMFactory(settings, http_client).create("groq")

    assert isinstance(provider, GroqProvider)
    assert (provider.name, provider.model) == ("groq", "llama-test")


def test_creates_cohere_provider_from_configuration(http_client: httpx.AsyncClient) -> None:
    settings = make_settings(cohere_api_key="cohere-key", cohere_model="command-test")

    provider = LLMFactory(settings, http_client).create("cohere")

    assert isinstance(provider, CohereProvider)
    assert (provider.name, provider.model) == ("cohere", "command-test")


def test_provider_without_api_key_is_not_configured(http_client: httpx.AsyncClient) -> None:
    factory = LLMFactory(make_settings(), http_client)

    assert not factory.is_configured("groq")
    with pytest.raises(ProviderNotConfiguredException, match="groq"):
        factory.create("groq")


def test_unknown_provider_is_rejected(http_client: httpx.AsyncClient) -> None:
    factory = LLMFactory(make_settings(groq_api_key="k"), http_client)

    with pytest.raises(ProviderNotConfiguredException, match="Supported providers: groq, cohere"):
        factory.create("openai")


def test_default_provider_follows_configuration(http_client: httpx.AsyncClient) -> None:
    settings = make_settings(
        default_llm_provider="cohere", cohere_api_key="cohere-key", groq_api_key="groq-key"
    )

    provider = LLMFactory(settings, http_client).create_default()

    assert provider.name == "cohere"


def test_default_chain_includes_configured_fallbacks_in_order(
    http_client: httpx.AsyncClient,
) -> None:
    settings = make_settings(
        groq_api_key="groq-key", cohere_api_key="cohere-key", llm_fallback_providers="cohere,groq"
    )

    provider = LLMFactory(settings, http_client).create_default()

    assert isinstance(provider, FallbackLLMProvider)
    assert [member.name for member in provider._providers] == ["groq", "cohere"]


def test_unconfigured_fallback_is_skipped(http_client: httpx.AsyncClient) -> None:
    settings = make_settings(groq_api_key="groq-key", llm_fallback_providers=["cohere"])

    provider = LLMFactory(settings, http_client).create_default()

    assert isinstance(provider, FallbackLLMProvider)
    assert [member.name for member in provider._providers] == ["groq"]


def test_default_provider_must_be_configured(http_client: httpx.AsyncClient) -> None:
    settings = make_settings(cohere_api_key="cohere-key", llm_fallback_providers=["cohere"])

    with pytest.raises(ProviderNotConfiguredException):
        LLMFactory(settings, http_client).create_default()
