from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class OrchestratorSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    # Server
    PORT: int = 8001

    # Database
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    POSTGRES_DB: str = "orchestrator_db"
    POSTGRES_USER: str = "ml_user"
    POSTGRES_PASSWORD: str = "change_me_in_local_dev"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_URL: str = "redis://localhost:6379/0"

    # CORS
    CORS_ALLOW_ORIGINS: list[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list[str] = ["*"]
    CORS_ALLOW_HEADERS: list[str] = ["*"]

    # Pagination
    DEFAULT_PAGINATION_LIMIT: int = 20
    MAX_PAGINATION_LIMIT: int = 100

    @property
    def DATABASE_URL(self) -> str:
        """Construct the PostgreSQL connection URL."""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.POSTGRES_DB}"
        )


@lru_cache
def get_settings() -> OrchestratorSettings:
    return OrchestratorSettings()