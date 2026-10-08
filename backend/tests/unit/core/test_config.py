import pytest
from pydantic import ValidationError

from app.core.config import LLMProviderName, Settings
from tests.support import make_settings


def test_settings_are_read_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "staging")
    monkeypatch.setenv("DEFAULT_LLM_PROVIDER", "cohere")
    monkeypatch.setenv("LLM_FALLBACK_PROVIDERS", "groq")
    monkeypatch.setenv("COHERE_API_KEY", "cohere-secret")
    monkeypatch.setenv("CORS_ORIGINS", "https://app.example.com, https://admin.example.com")
    monkeypatch.setenv("LOG_LEVEL", "debug")

    settings = Settings(_env_file=None)

    assert settings.app_env == "staging"
    assert settings.default_llm_provider is LLMProviderName.COHERE
    assert settings.llm_fallback_providers == [LLMProviderName.GROQ]
    assert settings.cors_origins == ["https://app.example.com", "https://admin.example.com"]
    assert settings.log_level == "DEBUG"


def test_secrets_are_masked_when_settings_are_printed() -> None:
    settings = make_settings(groq_api_key="groq-secret", google_api_key="google-secret")

    rendered = f"{settings!r} {settings.model_dump()}"

    assert "groq-secret" not in rendered
    assert "google-secret" not in rendered
    assert settings.groq_api_key is not None
    assert settings.groq_api_key.get_secret_value() == "groq-secret"


def test_blank_api_keys_count_as_not_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "")

    assert Settings(_env_file=None).groq_api_key is None


def test_unknown_provider_name_is_rejected() -> None:
    with pytest.raises(ValidationError):
        make_settings(default_llm_provider="skynet")


PRODUCTION = {
    "app_env": "production",
    "enable_mock_data": None,
    "auth_required": True,
    "secret_key": "k" * 40,
}


def test_mock_data_defaults_to_development_only() -> None:
    assert make_settings(enable_mock_data=None, app_env="development").mock_data_enabled
    assert not make_settings(**PRODUCTION).mock_data_enabled


def test_safe_production_settings_are_accepted() -> None:
    assert make_settings(**PRODUCTION).is_production


@pytest.mark.parametrize(
    "unsafe",
    [
        {"enable_mock_data": True},
        {"log_prompts": True},
        {"auth_required": False},
        {"secret_key": None},
        {"secret_key": "too-short"},
        {"data_source_allow_private_hosts": True},
    ],
)
def test_unsafe_settings_are_refused_in_production(unsafe: dict[str, object]) -> None:
    with pytest.raises(ValidationError, match="production"):
        make_settings(**(PRODUCTION | unsafe))


def test_development_falls_back_to_a_fixed_signing_key_but_production_never_does() -> None:
    assert make_settings().token_signing_key.startswith("development-only")
    assert make_settings(**PRODUCTION).token_signing_key == "k" * 40
