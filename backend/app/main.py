"""
Main FastAPI application entry point.

This module initializes the FastAPI application and registers API routes.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from app.api.v1.routes import router as dxf_router
from app.core.settings import get_settings
from app.routers.design_parser import router as design_parser_router
from app.services.design_parser_service import (
    shutdown_design_parser_service,
    startup_design_parser_service,
)

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    await startup_design_parser_service()
    try:
        yield
    finally:
        await shutdown_design_parser_service()


# Initialize FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.api_version,
    docs_url=None if not settings.docs_enabled else "/docs",
    redoc_url=None if not settings.docs_enabled else "/redoc",
    lifespan=lifespan,
)

# Register API v1 routes with prefix
app.include_router(dxf_router, prefix="/api/v1")
app.include_router(design_parser_router, prefix="/api/v1")
