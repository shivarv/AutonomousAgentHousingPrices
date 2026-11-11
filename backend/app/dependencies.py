"""Depends() providers that build services. Controllers use these, never DAOs directly."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dao.health_dao import HealthDao
from app.services.health_service import HealthService

DbSession = Annotated[Session, Depends(get_db)]


def get_health_service(db: DbSession) -> HealthService:
    return HealthService(HealthDao(db))
