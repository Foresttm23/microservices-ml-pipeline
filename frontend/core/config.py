from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    GATEWAY_CLIENT_URL: str = (
        "http://localhost:8080"  # Default local, from browser perspective
    )
    GATEWAY_CLIENT_WS_URL: str = "ws://localhost:8080"
    PORT: int = 8004

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


def get_settings() -> Settings:
    return Settings()
