"""FastAPI application factory."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from app.controllers import (
    area_controller,
    geocode_controller,
    health_controller,
    reference_controller,
    site_controller,
    stats_controller,
    tract_controller,
)
from app.core.config import get_settings
from app.core.exceptions import DomainError


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version="0.1.0")
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(DomainError)
    async def domain_error_handler(_: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

    app.include_router(health_controller.router)
    app.include_router(stats_controller.router)
    app.include_router(tract_controller.router)
    app.include_router(site_controller.router)
    app.include_router(area_controller.router)
    app.include_router(reference_controller.router)
    app.include_router(geocode_controller.router)
    return app


app = create_app()
