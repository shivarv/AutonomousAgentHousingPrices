from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies import get_health_service
from app.schemas.health import HealthRead
from app.services.health_service import HealthService

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health", response_model=HealthRead)
def health(service: Annotated[HealthService, Depends(get_health_service)]) -> HealthRead:
    return service.check()
