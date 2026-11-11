from sqlalchemy.exc import OperationalError

from app.services.health_service import HealthService


class _FailingDao:
    def ping(self) -> bool:
        raise OperationalError("SELECT 1", {}, Exception("down"))


class _OkDao:
    def ping(self) -> bool:
        return True


def test_health_degraded_when_database_unavailable() -> None:
    result = HealthService(_FailingDao()).check()  # type: ignore[arg-type]
    assert result.status == "degraded"
    assert result.database == "unavailable"


def test_health_ok() -> None:
    result = HealthService(_OkDao()).check()  # type: ignore[arg-type]
    assert result.status == "ok"
