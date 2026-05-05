from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

# HTTP Header constants
CORRELATION_ID_HEADER = "X-Correlation-ID"
USER_ID_HEADER = "X-User-ID"


class SharedSettings(BaseSettings):
    """Shared settings across all services (Redis, logging, etc.)."""

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str | None = None

    DEBUG: bool = True

    @property
    def REDIS_URL(self) -> str:
        """Construct the Redis connection URL."""
        password_part = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{password_part}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


@lru_cache
def get_shared_settings() -> SharedSettings:
    """Get cached shared settings."""
    return SharedSettings()
