"""Reference data: official homelessness counts, shelters, model metrics, data sources."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies import (
    get_data_source_service,
    get_homelessness_service,
    get_model_service,
    get_shelter_service,
)
from app.schemas.data_source import DataSourceRead
from app.schemas.homelessness import CocHomelessness, HomelessnessOverview
from app.schemas.model_run import ModelMetrics
from app.schemas.shelter import ShelterList
from app.services.data_source_service import DataSourceService
from app.services.homelessness_service import HomelessnessService
from app.services.model_service import ModelService
from app.services.shelter_service import ShelterService

router = APIRouter(prefix="/api", tags=["reference"])


@router.get("/homelessness", response_model=HomelessnessOverview)
def homelessness(
    service: Annotated[HomelessnessService, Depends(get_homelessness_service)],
) -> HomelessnessOverview:
    """Official HUD PIT counts and HIC beds per CoC by year (CoC level only)."""
    return service.overview()


@router.get("/homelessness/{coc_number}", response_model=CocHomelessness)
def homelessness_coc(
    coc_number: str,
    service: Annotated[HomelessnessService, Depends(get_homelessness_service)],
) -> CocHomelessness:
    return service.coc(coc_number)


@router.get("/shelters", response_model=ShelterList)
def shelters(
    service: Annotated[ShelterService, Depends(get_shelter_service)],
    coc: str | None = None,
) -> ShelterList:
    return service.list(coc)


@router.get("/model/metrics", response_model=ModelMetrics)
def model_metrics(service: Annotated[ModelService, Depends(get_model_service)]) -> ModelMetrics:
    return service.metrics()


@router.get("/sources", response_model=list[DataSourceRead])
def sources(
    service: Annotated[DataSourceService, Depends(get_data_source_service)],
) -> list[DataSourceRead]:
    return service.list_sources()
