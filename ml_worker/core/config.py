from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class GeminiSettings(BaseSettings):
    """
    Settings for ML Worker using generic provider-agnostic keys.
    Fulfills ModelSettingsProtocol structurally.
    """

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    API_KEY: str | None = None
    MODEL: str = "gemini-2.0-flash"
    API_BASE: str = "https://generativelanguage.googleapis.com/v1beta"
    TIMEOUT_SECONDS: float = 30.0
    MAX_RETRIES: int = 3
    ML_WORKER_DRY_RUN: bool = False

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    @field_validator("API_BASE", mode="before")
    @classmethod
    def _normalize_api_base(cls, value: object) -> object:
        if isinstance(value, str):
            return value.rstrip("/")
        return value

    @field_validator("ML_WORKER_DRY_RUN", mode="before")
    @classmethod
    def _parse_dry_run(cls, value: object) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on"}
        if value is None:
            return False
        return bool(value)


@lru_cache
def get_gemini_settings() -> GeminiSettings:
    return GeminiSettings()
