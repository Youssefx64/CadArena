"""
RAG System - Standalone FastAPI application.

Run independently with: python -m uvicorn app.main:app --port 8001
Future integration should either call this service over HTTP or include the
router from RAG.app.router in a separately approved Project A change.
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_rag_settings
from .router import router


def create_rag_app() -> FastAPI:
    """Create the standalone RAG FastAPI application."""
    settings = get_rag_settings()
    app = FastAPI(
        title="CadArena RAG System",
        description="Integration-ready Retrieval-Augmented Generation API",
        version="1.0.0",
        docs_url=f"{settings.RAG_PREFIX}/docs",
        redoc_url=f"{settings.RAG_PREFIX}/redoc",
        openapi_url=f"{settings.RAG_PREFIX}/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)

    @app.get(f"{settings.RAG_PREFIX}/ping", tags=["RAG"])
    async def ping() -> dict[str, str]:
        """Return a minimal liveness response."""
        return {"status": "RAG system online"}

    return app


app = create_rag_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_rag_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.RAG_HOST,
        port=settings.RAG_PORT,
        reload=True,
    )
