"""
Main FastAPI application entry point.

This module initializes the FastAPI application and registers API routes.
"""

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, FastAPI
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from app.core.env_loader import load_backend_env
from app.core.logging import get_logger

load_backend_env()

# Guard DXF router import so missing CAD deps disable only DXF endpoints, not the whole app.
try:
    from app.api.v1.routes import router as dxf_router
except ImportError as exc:
    if exc.name != "ezdxf":
        raise
    dxf_router: Optional[APIRouter] = None
    _DXF_ROUTER_IMPORT_ERROR: ImportError | None = exc
else:
    _DXF_ROUTER_IMPORT_ERROR = None

from app.core.settings import get_settings
from app.routers.design_parser import router as design_parser_router
from app.routers.community import router as community_router
from app.routers.contact import router as contact_router
from app.routers.auth import router as auth_router
from app.routers.profile import router as profile_router
from app.routers.workspace import router as workspace_router
from app.routers.workspace_auth import router as workspace_auth_router
from app.services.auth_storage import init_auth_db
from app.services.community_storage import init_community_db
from app.services.design_parser_service import (
    shutdown_design_parser_service,
    startup_design_parser_service,
)
from app.services.output_cleanup import run_cleanup_loop
from app.services.workspace_storage import init_workspace_db

logger = get_logger(__name__)
settings = get_settings()
PROJECT_ROOT_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIR = PROJECT_ROOT_DIR / "frontend"
FRONTEND_BUILD_DIR = FRONTEND_DIR / "build"
FRONTEND_PUBLIC_DIR = FRONTEND_DIR / "public"
HOME_PAGE_PATH = FRONTEND_DIR / "landing.html"
BLOG_PAGE_PATH = FRONTEND_DIR / "blog.html"
CONTACT_PAGE_PATH = FRONTEND_DIR / "contact.html"
REACT_INDEX_PATH = FRONTEND_BUILD_DIR / "index.html"
BUILD_FAVICON_PATH = FRONTEND_BUILD_DIR / "assets" / "cadarena-mark.svg"
PUBLIC_FAVICON_PATH = FRONTEND_PUBLIC_DIR / "assets" / "cadarena-mark.svg"


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_workspace_db()
    init_auth_db()
    init_community_db()
    await startup_design_parser_service()
    cleanup_task = asyncio.create_task(
        run_cleanup_loop(interval_hours=6)
    )
    try:
        yield
    finally:
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass
        await shutdown_design_parser_service()


# Initialize FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.api_version,
    docs_url=None if not settings.docs_enabled else "/docs",
    redoc_url=None if not settings.docs_enabled else "/redoc",
    lifespan=lifespan,
)

# Register API v1 routes with prefix.
if dxf_router is not None:
    app.include_router(dxf_router, prefix="/api/v1")
else:
    logger.warning(
        "DXF routes disabled because CAD dependencies are unavailable: %s",
        _DXF_ROUTER_IMPORT_ERROR,
    )
app.include_router(design_parser_router, prefix="/api/v1")
app.include_router(contact_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(profile_router, prefix="/api/v1")
app.include_router(workspace_router, prefix="/api/v1")
app.include_router(community_router, prefix="/api/v1")
app.include_router(workspace_auth_router, prefix="/api/v1")

if FRONTEND_BUILD_DIR.exists():
    build_static_dir = FRONTEND_BUILD_DIR / "static"
    build_assets_dir = FRONTEND_BUILD_DIR / "assets"
    build_studio_dir = FRONTEND_BUILD_DIR / "studio-app"
    if build_static_dir.exists():
        app.mount("/static", StaticFiles(directory=build_static_dir), name="frontend_static")
    if build_assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=build_assets_dir), name="frontend_assets")
    if build_studio_dir.exists():
        app.mount("/studio-app", StaticFiles(directory=build_studio_dir, html=True), name="studio_app")
elif (FRONTEND_PUBLIC_DIR / "assets").exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_PUBLIC_DIR / "assets"), name="frontend_assets")
    studio_public_dir = FRONTEND_PUBLIC_DIR / "studio-app"
    if studio_public_dir.exists():
        app.mount("/studio-app", StaticFiles(directory=studio_public_dir, html=True), name="studio_app")


def _react_index_response():
    if REACT_INDEX_PATH.exists():
        return FileResponse(REACT_INDEX_PATH)
    return None


@app.get("/", include_in_schema=False)
def root():
    react_response = _react_index_response()
    if react_response is not None:
        return react_response
    if HOME_PAGE_PATH.exists():
        return FileResponse(HOME_PAGE_PATH)
    return {"status": "ok", "message": "CadArena API is running"}


@app.get("/studio", include_in_schema=False)
@app.get("/community", include_in_schema=False)
@app.get("/generate", include_in_schema=False)
@app.get("/models", include_in_schema=False)
@app.get("/metrics", include_in_schema=False)
@app.get("/about", include_in_schema=False)
@app.get("/developers", include_in_schema=False)
def react_app_route():
    react_response = _react_index_response()
    if react_response is not None:
        return react_response
    return RedirectResponse(url="/")


@app.get("/blog", include_in_schema=False)
@app.get("/blog/", include_in_schema=False)
def blog_page():
    if BLOG_PAGE_PATH.exists():
        return FileResponse(BLOG_PAGE_PATH)
    return RedirectResponse(url="/")


@app.get("/contact", include_in_schema=False)
@app.get("/contact/", include_in_schema=False)
def contact_page():
    if CONTACT_PAGE_PATH.exists():
        return FileResponse(CONTACT_PAGE_PATH)
    return RedirectResponse(url="/")


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    if BUILD_FAVICON_PATH.exists():
        return FileResponse(BUILD_FAVICON_PATH, media_type="image/svg+xml")
    if PUBLIC_FAVICON_PATH.exists():
        return FileResponse(PUBLIC_FAVICON_PATH, media_type="image/svg+xml")
    return RedirectResponse(url="/")
