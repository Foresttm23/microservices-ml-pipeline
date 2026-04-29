from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# HTTP Header constants
CORRELATION_ID_HEADER = "X-Correlation-ID"
USER_ID_HEADER = "X-User-ID"


class GatewaySettings(BaseSettings):
    """Gateway service settings."""

    model_config = SettingsConfigDict(env_prefix="GATEWAY_", extra="ignore")

    # Service URLs
    ORCHESTRATOR_URL: str = Field(
        default="http://orchestrator:8000",
        description="Orchestrator service URL",
    )

    # HTTPX Client settings
    HTTPX_TIMEOUT_SECONDS: float = Field(
        default=60.0,
        description="Timeout for HTTPX requests",
    )
    HTTPX_MAX_CONNECTIONS: int = Field(
        default=100,
        description="Max concurrent connections",
    )
    HTTPX_MAX_KEEPALIVE_CONNECTIONS: int = Field(
        default=20,
        description="Max keepalive connections",
    )

    # Redis
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL",
    )


@lru_cache
def get_settings() -> GatewaySettings:
    """Get cached gateway settings."""
    return GatewaySettings()
