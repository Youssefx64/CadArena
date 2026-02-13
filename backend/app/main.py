"""
Main FastAPI application entry point.

This module initializes the FastAPI application and registers API routes.
"""

from fastapi import FastAPI
from app.api.v1.routes import router
from app.core.settings import get_settings

settings = get_settings()

# Initialize FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.api_version,
    docs_url=None if not settings.docs_enabled else "/docs",
    redoc_url=None if not settings.docs_enabled else "/redoc",
)

# Register API v1 routes with prefix
app.include_router(router, prefix="/api/v1")
