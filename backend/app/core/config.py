"""Environment-driven application configuration."""

from enum import StrEnum
from functools import lru_cache
from typing import Annotated, Self

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Environment(StrEnum):
    DEVELOPMENT = "development"
    TEST = "test"
    STAGING = "staging"
    PRODUCTION = "production"


class LLMProviderName(StrEnum):
    GROQ = "groq"
    COHERE = "cohere"


class ImageGenerationProvider(StrEnum):
    POLLINATIONS = "pollinations"
    NONE = "none"


class ImageSearchProvider(StrEnum):
    AUTO = "auto"
    UNSPLASH = "unsplash"
    OPENVERSE = "openverse"
    NONE = "none"


class LogFormat(StrEnum):
    JSON = "json"
    CONSOLE = "console"


MIN_SECRET_KEY_LENGTH = 32
# Not a secret: only ever used outside production, where SECRET_KEY is mandatory.
DEVELOPMENT_SECRET_KEY = "development-only-signing-key-do-not-use-in-production"


def _split_csv(value: object) -> object:
    """Allow list settings to be written as ``a,b,c`` in the environment."""
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return value


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
    )

    app_name: str = "Generative UI Platform"
    app_version: str = "0.1.0"
    app_env: Environment = Environment.DEVELOPMENT

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/generative_ui"
    database_pool_size: int = Field(default=5, ge=1)
    database_max_overflow: int = Field(default=10, ge=0)

    default_llm_provider: LLMProviderName = LLMProviderName.GROQ
    llm_fallback_providers: Annotated[list[LLMProviderName], NoDecode] = Field(default_factory=list)
    llm_timeout_seconds: float = Field(default=30.0, gt=0)
    llm_temperature: float = Field(default=0.2, ge=0, le=1)
    llm_max_output_tokens: int = Field(default=4096, ge=256)
    llm_max_repair_attempts: int = Field(default=2, ge=0, le=3)
    # Extra attempts per provider for transient failures (timeouts, 429, 5xx).
    llm_max_retries: int = Field(default=1, ge=0, le=5)
    llm_retry_backoff_seconds: float = Field(default=0.5, ge=0)

    groq_api_key: SecretStr | None = None
    groq_model: str = "openai/gpt-oss-120b"
    groq_base_url: str = "https://api.groq.com/openai/v1"

    cohere_api_key: SecretStr | None = None
    cohere_model: str = "command-a-03-2025"
    cohere_base_url: str = "https://api.cohere.com/v2"

    google_api_key: SecretStr | None = None
    google_search_engine_id: str | None = None

    # --- Application generation ---
    # Upper bound on the screens of one generated application.
    app_max_screens: int = Field(default=10, ge=1, le=20)
    app_records_per_entity: int = Field(default=10, ge=2, le=40)
    # Screens designed at the same time. Lower it on rate-limited model plans.
    app_screen_concurrency: int = Field(default=2, ge=1, le=8)
    # Design review passes that may regenerate weak screens (0 disables refinement).
    app_refinement_passes: int = Field(default=1, ge=0, le=2)
    app_generation_max_output_tokens: int = Field(default=6000, ge=1024)
    # Request timeout for generation stages, which produce long answers.
    app_generation_timeout_seconds: float = Field(default=120.0, gt=0)
    # A pipeline of many calls will meet provider rate limits and slow answers: wait
    # (at least this long, longer if the provider says so) and try again.
    llm_rate_limit_retries: int = Field(default=5, ge=0, le=10)
    llm_rate_limit_wait_seconds: float = Field(default=10.0, ge=0)

    # --- Images ---
    # Images of one generated application (0 disables imagery altogether).
    app_max_assets: int = Field(default=8, ge=0, le=40)
    # Text-to-image provider. Prompts derived from the user's idea are sent to it.
    image_generation_provider: ImageGenerationProvider = ImageGenerationProvider.POLLINATIONS
    # Photograph search. "auto" uses Unsplash when a key is set, otherwise Openverse.
    image_search_provider: ImageSearchProvider = ImageSearchProvider.AUTO
    unsplash_access_key: SecretStr | None = None

    # Reference component library (scripts.import_references). Optional: only the
    # 21st.dev source needs a key; the open-source registries need none.
    twentyfirst_api_key: SecretStr | None = None
    asset_timeout_seconds: float = Field(default=45.0, gt=0)

    # --- Identity and access ---
    # When false (local development only) requests without a token act as one shared
    # anonymous user.
    auth_required: bool = True
    secret_key: SecretStr | None = None
    access_token_ttl_minutes: int = Field(default=720, ge=5)

    # Requests per minute per caller; 0 disables a limit. Counted per process.
    rate_limit_per_minute: int = Field(default=240, ge=0)
    ai_rate_limit_per_minute: int = Field(default=20, ge=0)
    auth_rate_limit_per_minute: int = Field(default=10, ge=0)

    # --- Data sources ---
    # Allow REST data sources to call private/loopback addresses (development only).
    data_source_allow_private_hosts: bool = False
    data_source_timeout_seconds: float = Field(default=10.0, gt=0)

    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:5173"]
    )

    log_level: str = "INFO"
    log_format: LogFormat = LogFormat.JSON
    # Logs full prompts and model output at DEBUG level. Never allowed in production.
    log_prompts: bool = False

    # Development-only demo dataset. Unset means "on unless production".
    enable_mock_data: bool | None = None

    @field_validator("cors_origins", "llm_fallback_providers", mode="before")
    @classmethod
    def _parse_csv(cls, value: object) -> object:
        return _split_csv(value)

    @field_validator("log_level")
    @classmethod
    def _normalise_log_level(cls, value: str) -> str:
        return value.upper()

    @model_validator(mode="after")
    def _guard_production(self) -> Self:
        if not self.is_production:
            return self
        if self.log_prompts:
            raise ValueError("LOG_PROMPTS must not be enabled in production.")
        if self.enable_mock_data:
            raise ValueError("ENABLE_MOCK_DATA must not be enabled in production.")
        if not self.auth_required:
            raise ValueError("AUTH_REQUIRED must not be disabled in production.")
        if (
            self.secret_key is None
            or len(self.secret_key.get_secret_value()) < MIN_SECRET_KEY_LENGTH
        ):
            raise ValueError(
                f"SECRET_KEY needs at least {MIN_SECRET_KEY_LENGTH} characters in production."
            )
        if self.data_source_allow_private_hosts:
            raise ValueError("DATA_SOURCE_ALLOW_PRIVATE_HOSTS must not be enabled in production.")
        return self

    @property
    def token_signing_key(self) -> str:
        """Key used to sign access tokens. Outside production a fixed development key
        is used when SECRET_KEY is unset, so tokens survive restarts while developing."""
        if self.secret_key is not None:
            return self.secret_key.get_secret_value()
        return DEVELOPMENT_SECRET_KEY

    @property
    def is_production(self) -> bool:
        return self.app_env is Environment.PRODUCTION

    @property
    def mock_data_enabled(self) -> bool:
        if self.enable_mock_data is None:
            return not self.is_production
        return self.enable_mock_data


@lru_cache
def get_settings() -> Settings:
    return Settings()
