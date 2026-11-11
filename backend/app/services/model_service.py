from app.dao.model_run_dao import ModelRunDao
from app.schemas.model_run import ModelMetrics, ModelRunRead


class ModelService:
    def __init__(self, dao: ModelRunDao) -> None:
        self.dao = dao

    def _latest(self, kind: str) -> ModelRunRead | None:
        run = self.dao.latest(kind)
        return ModelRunRead.model_validate(run) if run else None

    def metrics(self) -> ModelMetrics:
        return ModelMetrics(
            home_value=self._latest("home_value"), site_scoring=self._latest("site_scoring")
        )
