"""Application settings, read only from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    app_name: str = "Massachusetts Housing Need & Site Finder"
    database_url: str = "postgresql+psycopg://postgres@localhost:5544/housing"
    test_database_url: str = "postgresql+psycopg://postgres@localhost:5544/housing_test"
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
