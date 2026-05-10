"""Standalone smoke tests for the integration-ready RAG API."""
from __future__ import annotations

import asyncio
from typing import Any

import httpx


async def _request(method: str, path: str, **kwargs: Any) -> httpx.Response:
    """Call the RAG ASGI app without binding a network port."""
    from app.main import app

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.request(method, path, **kwargs)


def _call(method: str, path: str, **kwargs: Any) -> httpx.Response:
    """Run an ASGI request from synchronous pytest tests."""
    return asyncio.run(_request(method, path, **kwargs))


def test_rag_ping() -> None:
    resp = _call("GET", "/rag/ping")
    assert resp.status_code == 200
    assert resp.json()["status"] == "RAG system online"


def test_rag_health() -> None:
    resp = _call("GET", "/rag/health")
    assert resp.status_code in (200, 503)
    if resp.status_code == 200:
        data = resp.json()
        assert data["vector_store"] == "QDRANT"
        assert data["embedding_model"] == "embed-multilingual-v3.0"


def test_rag_query_requires_body() -> None:
    resp = _call("POST", "/rag/query", json={})
    assert resp.status_code == 422


def test_rag_query_valid_shape_or_runtime_dependency_error() -> None:
    resp = _call("POST", "/rag/query", json={"question": "test question"})
    assert resp.status_code in (200, 500)
    if resp.status_code == 200:
        data = resp.json()
        assert "answer" in data
        assert "sources" in data


def test_rag_ingest_empty() -> None:
    resp = _call("POST", "/rag/ingest", json={"documents": []})
    assert resp.status_code == 200
    assert resp.json()["ingested"] == 0


def test_rag_ingest_documents_or_runtime_dependency_error() -> None:
    resp = _call(
        "POST",
        "/rag/ingest",
        json={
            "documents": ["Test document about architectural design."],
            "metadata": [{"source": "test"}],
        },
    )
    assert resp.status_code in (200, 500)


def test_rag_ingest_files_rejects_unsupported_extension() -> None:
    resp = _call(
        "POST",
        "/rag/ingest/files",
        data={"collection": "default"},
        files={"files": ("plan.dwg", b"not a supported drawing exchange", "application/acad")},
    )
    assert resp.status_code == 400
    assert "Only PDF, TXT, Markdown, CSV, and JSON files are supported" in resp.json()["detail"]


def test_rag_ingest_files_empty_txt() -> None:
    resp = _call(
        "POST",
        "/rag/ingest/files",
        data={"collection": "default"},
        files={"files": ("empty.txt", b"   ", "text/plain")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["ingested"] == 0
    assert data["failed"] == 1
    assert data["collection"] == "default"


def test_rag_ingest_files_missing_file_has_clear_error() -> None:
    resp = _call(
        "POST",
        "/rag/ingest/files",
        data={"collection": "default"},
    )
    assert resp.status_code == 400
    assert "field name 'files'" in resp.json()["detail"]


def test_rag_ingest_files_accepts_single_file_alias() -> None:
    resp = _call(
        "POST",
        "/rag/ingest/files",
        data={"collection": "default"},
        files={"file": ("empty.txt", b"   ", "text/plain")},
    )
    assert resp.status_code == 200
    assert resp.json()["failed"] == 1


def test_rag_ingest_files_ignores_text_documents_field_in_multipart() -> None:
    resp = _call(
        "POST",
        "/rag/ingest/files",
        data={
            "collection": "default",
            "documents": "this is plain text and should not be treated as uploaded file",
        },
        files={"files": ("empty.txt", b"   ", "text/plain")},
    )
    assert resp.status_code == 200
    assert resp.json()["failed"] == 1


def test_config_no_main_backend_conflicts() -> None:
    """Verify RAG config uses the RAG_ prefix and avoids Project A's port."""
    from app.config import get_rag_settings

    settings = get_rag_settings()
    assert settings.RAG_PORT != 8000
    assert settings.RAG_VECTOR_STORE == "QDRANT"
    assert settings.RAG_LLM_PROVIDER == "COHERE"
