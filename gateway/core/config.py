from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class GatewaySettings(BaseSettings):
    """Gateway service settings."""

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    # Service URLs
    ORCHESTRATOR_URL: str = "http://orchestrator:8001"

    # HTTPX Client settings
    HTTPX_TIMEOUT_SECONDS: int = 60
    HTTPX_MAX_CONNECTIONS: int = 100
    HTTPX_MAX_KEEPALIVE_CONNECTIONS: int = 20

    # JWT settings
    JWT_ENABLED: bool = True
    JWT_SECRET_KEY: str = "dev-secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_ISSUER: str | None = None
    JWT_AUDIENCE: str | None = None
    JWT_USER_ID_CLAIM: str = "sub"
    JWT_LEEWAY_SECONDS: int = 0
    JWT_PUBLIC_PATHS: list[str] = ["/", "/health", "/docs", "/openapi.json"]


@lru_cache
def get_settings() -> GatewaySettings:
    """Get cached gateway settings."""
    return GatewaySettings()
