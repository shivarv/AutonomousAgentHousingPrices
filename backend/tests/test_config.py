"""Settings: database URL normalisation for hosted Postgres providers."""

import pytest

from app.core.config import Settings, normalise_database_url


@pytest.mark.parametrize(
    ("given", "expected"),
    [
        ("postgres://u:p@host/db?sslmode=require", "postgresql+psycopg://u:p@host/db?sslmode=require"),
        ("postgresql://u@host:5432/db", "postgresql+psycopg://u@host:5432/db"),
        ("postgresql+psycopg://u@host/db", "postgresql+psycopg://u@host/db"),
    ],
)
def test_normalise_database_url(given: str, expected: str) -> None:
    assert normalise_database_url(given) == expected


def test_settings_normalise_env_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgres://u@host/db")
    monkeypatch.setenv("DB_NULL_POOL", "true")
    settings = Settings()
    assert settings.database_url == "postgresql+psycopg://u@host/db"
    assert settings.db_null_pool is True
