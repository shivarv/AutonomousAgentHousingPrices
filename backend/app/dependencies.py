"""Depends() providers that build services. Controllers use these, never DAOs directly."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dao.area_dao import AreaDao
from app.dao.health_dao import HealthDao
from app.dao.homelessness_dao import HomelessnessDao
from app.services.health_service import HealthService
from app.services.homelessness_service import HomelessnessService
from app.services.stats_service import StatsService

DbSession = Annotated[Session, Depends(get_db)]


def get_health_service(db: DbSession) -> HealthService:
    return HealthService(HealthDao(db))


def get_homelessness_service(db: DbSession) -> HomelessnessService:
    return HomelessnessService(HomelessnessDao(db))


def get_stats_service(db: DbSession) -> StatsService:
    return StatsService(AreaDao(db), HomelessnessService(HomelessnessDao(db)))
