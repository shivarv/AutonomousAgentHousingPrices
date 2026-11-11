"""Shared fixtures: API tests run against the housing_test database."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db, get_session_factory
from app.main import create_app


@pytest.fixture(scope="session")
def test_session_factory():
    return get_session_factory(get_settings().test_database_url)


@pytest.fixture
def db_session(test_session_factory) -> Iterator[Session]:
    session = test_session_factory()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def client(db_session: Session) -> Iterator[TestClient]:
    app = create_app()
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as c:
        yield c


@pytest.fixture
def seeded(db_session: Session) -> Session:
    """Skip API tests that need data when housing_test is empty (scripts/seed_test_db.sh)."""
    from sqlalchemy import func, select

    from app.models import Tract

    if not db_session.scalar(select(func.count()).select_from(Tract)):
        pytest.skip("housing_test is empty: run scripts/seed_test_db.sh")
    return db_session
