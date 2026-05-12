from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class AuthSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    # Server
    PORT: int = 8003

    # Database
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    POSTGRES_DB: str = "auth_db"
    POSTGRES_USER: str = "ml_user"
    POSTGRES_PASSWORD: str = "change_me_in_local_dev"

    # JWT
    JWT_SECRET_KEY: str = "dev-secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_ISSUER: str | None = None
    JWT_AUDIENCE: str | None = None
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 14
    JWT_LEEWAY_SECONDS: int = 0

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.POSTGRES_DB}"
        )


@lru_cache
def get_settings() -> AuthSettings:
    return AuthSettings()

