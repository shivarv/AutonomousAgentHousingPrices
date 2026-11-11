"""Engine, session factory and the get_db dependency."""

from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import get_settings, normalise_database_url


@lru_cache
def get_engine(url: str | None = None) -> Engine:
    settings = get_settings()
    target = normalise_database_url(url) if url else settings.database_url
    if settings.db_null_pool:
        return create_engine(target, poolclass=NullPool)
    return create_engine(target, pool_pre_ping=True)


@lru_cache
def get_session_factory(url: str | None = None) -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(url), autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()
