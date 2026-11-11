from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import ModelRun


class ModelRunDao:
    def __init__(self, session: Session) -> None:
        self.session = session

    def replace_kind(self, kind: str, **fields: Any) -> ModelRun:
        """Delete earlier runs of ``kind`` (nothing else references them) and add this one."""
        self.session.execute(delete(ModelRun).where(ModelRun.kind == kind))
        run = ModelRun(kind=kind, **fields)
        self.session.add(run)
        self.session.flush()
        return run

    def latest(self, kind: str) -> ModelRun | None:
        return self.session.scalar(
            select(ModelRun).where(ModelRun.kind == kind).order_by(ModelRun.id.desc()).limit(1)
        )
