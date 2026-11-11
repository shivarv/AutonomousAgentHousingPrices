"""Application settings, read only from environment variables."""

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def normalise_database_url(url: str) -> str:
    """Use the psycopg 3 driver for plain postgres:// URLs (as hosted providers hand them out)."""
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix) :]
    return url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    app_name: str = "Massachusetts Housing Need & Site Finder"
    database_url: str = "postgresql+psycopg://postgres@localhost:5544/housing"
    test_database_url: str = "postgresql+psycopg://postgres@localhost:5544/housing_test"
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    # Serverless hosts (Vercel) freeze idle instances, so pooled connections go stale; set
    # DB_NULL_POOL=true there to open one connection per request (use the provider's pooler URL).
    db_null_pool: bool = False

    @field_validator("database_url", "test_database_url")
    @classmethod
    def _normalise_url(cls, value: str) -> str:
        return normalise_database_url(value)


@lru_cache
def get_settings() -> Settings:
    return Settings()
