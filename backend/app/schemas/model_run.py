from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class ModelRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    kind: str
    created_at: datetime
    params: dict[str, Any]
    metrics: dict[str, Any]
    artifact_path: str | None
    notes: str | None


class ModelMetrics(BaseModel):
    home_value: ModelRunRead | None
    site_scoring: ModelRunRead | None
