"""
Main FastAPI application entry point.

This module initializes the FastAPI application and registers API routes.
"""

from fastapi import FastAPI
from app.api.v1.routes import router

# Initialize FastAPI application
app = FastAPI()

# Register API v1 routes with prefix
app.include_router(router, prefix="/api/v1")
