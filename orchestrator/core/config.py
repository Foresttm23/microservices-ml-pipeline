from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class OrchestratorSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    # Server
    PORT: int = 8081

    # Database
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    POSTGRES_DB: str = "ml_microservices"
    POSTGRES_USER: str = "ml_user"
    POSTGRES_PASSWORD: str = "change_me_in_local_dev"

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
