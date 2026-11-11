"""Depends() providers that build services. Controllers use these, never DAOs directly."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dao.area_dao import AreaDao
from app.dao.health_dao import HealthDao
from app.dao.homelessness_dao import HomelessnessDao
from app.dao.site_dao import SiteDao
from app.dao.tract_dao import TractDao
from app.services.health_service import HealthService
from app.services.homelessness_service import HomelessnessService
from app.services.site_service import SiteService
from app.services.stats_service import StatsService
from app.services.tract_service import TractService

DbSession = Annotated[Session, Depends(get_db)]


def get_health_service(db: DbSession) -> HealthService:
    return HealthService(HealthDao(db))


def get_homelessness_service(db: DbSession) -> HomelessnessService:
    return HomelessnessService(HomelessnessDao(db))


def get_stats_service(db: DbSession) -> StatsService:
    return StatsService(AreaDao(db), HomelessnessService(HomelessnessDao(db)))


def db_key(db: Session) -> str:
    """Identifies the database for process-wide caches (tests use housing_test)."""
    return str(db.get_bind().url)


def get_tract_service(db: DbSession) -> TractService:
    return TractService(TractDao(db), db_key(db))


def get_site_service(db: DbSession) -> SiteService:
    return SiteService(SiteDao(db))
