"""
RAG System - Integration-Ready API Router.

Mount this router with app.include_router(router) to expose /rag endpoints.
All paths are prefixed with /rag to avoid collisions with Project A routes.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, UploadFile, status

from .document_loader import UnsupportedDocumentError, extract_uploaded_document_text
from .models import (
    HealthResponse,
    IngestRequest,
    IngestResponse,
    QueryRequest,
    QueryResponse,
)

router = APIRouter(prefix="/rag", tags=["RAG"])


@router.get("/health", response_model=HealthResponse)
async def rag_health() -> HealthResponse:
    """Check RAG health without touching Project A state."""
    from .rag_engine import get_rag_engine

    try:
        engine = get_rag_engine()
        return HealthResponse(
            status="healthy",
            vector_store=engine.vector_store_type,
            embedding_model=engine.embedding_model_name,
            document_count=engine.count_documents(),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"RAG system unhealthy: {exc}",
        ) from exc


@router.post("/query", response_model=QueryResponse)
async def rag_query(body: QueryRequest) -> QueryResponse:
    """Query the RAG knowledge base."""
    from .rag_engine import get_rag_engine

    try:
        result = get_rag_engine().query(
            question=body.question,
            top_k=body.top_k,
            filters=body.filters,
            collection=body.collection,
        )
        return QueryResponse(**result)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.post("/ingest", response_model=IngestResponse)
async def rag_ingest(body: IngestRequest) -> IngestResponse:
    """Add raw text documents to the RAG knowledge base."""
    from .rag_engine import get_rag_engine

    try:
        result = get_rag_engine().ingest(
            documents=body.documents,
            metadata=body.metadata,
            collection=body.collection,
        )
        return IngestResponse(**result)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.post("/ingest/files", response_model=IngestResponse)
async def rag_ingest_files(
    request: Request,
) -> IngestResponse:
    """Extract and ingest uploaded engineering reference documents."""
    from .rag_engine import get_rag_engine

    form = await request.form()
    collection = str(form.get("collection") or "default")
    source_value = form.get("source")
    source = str(source_value).strip() if source_value is not None else ""

    uploaded_files: list[UploadFile] = []
    for field_name in ("files", "documents", "file"):
        for value in form.getlist(field_name):
            if hasattr(value, "filename") and hasattr(value, "read"):
                uploaded_files.append(value)  # type: ignore[arg-type]

    if not uploaded_files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "No files were uploaded. Send multipart/form-data with the "
                "field name 'files'."
            ),
        )

    documents: list[str] = []
    metadata: list[dict[str, str]] = []
    failed = 0

    for uploaded_file in uploaded_files:
        filename = uploaded_file.filename or "uploaded-file"
        try:
            content = await uploaded_file.read()
            text = extract_uploaded_document_text(
                filename=filename,
                content=content,
                content_type=uploaded_file.content_type,
            ).strip()
        except UnsupportedDocumentError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{filename}: {exc}",
            ) from exc
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{filename}: {exc}",
            ) from exc
        finally:
            await uploaded_file.close()

        if not text:
            failed += 1
            continue

        documents.append(text)
        metadata.append(
            {
                "source": source if source else filename,
                "filename": filename,
                "content_type": uploaded_file.content_type or "",
                "domain": "civil-architecture",
                "upload_type": "file",
            }
        )

    if not documents:
        return IngestResponse(ingested=0, failed=failed or len(uploaded_files), collection=collection)

    try:
        result = get_rag_engine().ingest(
            documents=documents,
            metadata=metadata,
            collection=collection,
        )
        return IngestResponse(
            ingested=result["ingested"],
            failed=result.get("failed", 0) + failed,
            collection=result["collection"],
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.delete("/collection/{collection_name}")
async def rag_clear_collection(collection_name: str) -> dict[str, str]:
    """Clear all documents from a RAG collection."""
    from .rag_engine import get_rag_engine

    try:
        get_rag_engine().clear_collection(collection_name)
        return {"status": "cleared", "collection": collection_name}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
