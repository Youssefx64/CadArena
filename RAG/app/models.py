"""
Pydantic request and response models for the integration-ready RAG API.

The models are intentionally small and stable so Project A can call the RAG
service over HTTP without depending on the legacy RAG internals.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator


class QueryRequest(BaseModel):
    """Query the RAG system with a natural-language question."""

    question: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=50)
    filters: dict[str, Any] = Field(default_factory=dict)
    collection: str | None = None


class QueryResponse(BaseModel):
    """RAG response with a generated answer and retrieved source documents."""

    answer: str
    sources: list[dict[str, Any]] = Field(default_factory=list)
    confidence: float | None = None


class IngestRequest(BaseModel):
    """Ingest raw text documents into a RAG collection."""

    documents: list[str] = Field(default_factory=list)
    metadata: list[dict[str, Any]] = Field(default_factory=list)
    collection: str = "default"

    @field_validator("documents")
    @classmethod
    def _strip_empty_documents(cls, value: list[str]) -> list[str]:
        """Normalize documents and discard empty entries."""
        return [doc.strip() for doc in value if doc and doc.strip()]


class IngestResponse(BaseModel):
    """Result of document ingestion."""

    ingested: int
    failed: int = 0
    collection: str


class HealthResponse(BaseModel):
    """RAG system health status."""

    status: str
    vector_store: str
    embedding_model: str
    document_count: int | None = None

