from sqlalchemy.exc import SQLAlchemyError

from app.core.config import get_settings
from app.dao.health_dao import HealthDao
from app.schemas.health import HealthRead


class HealthService:
    def __init__(self, dao: HealthDao) -> None:
        self.dao = dao

    def check(self) -> HealthRead:
        try:
            db_ok = self.dao.ping()
        except SQLAlchemyError:
            db_ok = False
        return HealthRead(
            status="ok" if db_ok else "degraded",
            database="ok" if db_ok else "unavailable",
            app=get_settings().app_name,
        )
