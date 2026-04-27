from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    GEMINI_API_KEY: str | None = Field(default=None)
    GEMINI_MODEL: str = Field(default="gemini-2.0-flash")
    GEMINI_API_BASE: str = Field(
        default="https://generativelanguage.googleapis.com/v1beta",
    )
    GEMINI_TIMEOUT_SECONDS: float = Field(default=30.0)
    ML_WORKER_DRY_RUN: bool = Field(default=False)

    @field_validator("GEMINI_API_BASE", mode="before")
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
def get_settings() -> Settings:
    return Settings()
