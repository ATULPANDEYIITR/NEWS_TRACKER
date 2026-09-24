from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central application configuration.

    Values are loaded from environment variables and the optional .env file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = Field(
        default="Global News Tracker",
        alias="APP_NAME",
    )

    app_env: str = Field(
        default="development",
        alias="APP_ENV",
    )

    debug: bool = Field(
        default=True,
        alias="DEBUG",
    )

    log_level: str = Field(
        default="INFO",
        alias="LOG_LEVEL",
    )

    api_host: str = Field(
        default="127.0.0.1",
        alias="API_HOST",
    )

    api_port: int = Field(
        default=8000,
        alias="API_PORT",
    )

    database_url: str = Field(
        default="postgresql+psycopg://news_tracker:NewsTracker2026!@localhost:5432/global_news",
        alias="DATABASE_URL",
    )

    app_timezone: str = Field(
        default="UTC",
        alias="APP_TIMEZONE",
    )

    news_collection_enabled: bool = Field(
        default=True,
        alias="NEWS_COLLECTION_ENABLED",
    )

    news_collection_interval_minutes: int = Field(
        default=30,
        alias="NEWS_COLLECTION_INTERVAL_MINUTES",
    )

    ai_enabled: bool = Field(
        default=False,
        alias="AI_ENABLED",
    )

    ai_provider: str = Field(
        default="",
        alias="AI_PROVIDER",
    )

    ai_api_key: str = Field(
        default="",
        alias="AI_API_KEY",
    )

    secret_key: str = Field(
        default="change_this_in_production",
        alias="SECRET_KEY",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()