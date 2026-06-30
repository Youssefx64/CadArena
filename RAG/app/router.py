"""
RAG System - Integration-Ready API Router.

Mount this router with app.include_router(router) to expose /rag endpoints.
All paths are prefixed with /rag to avoid collisions with Project A routes.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request, UploadFile, status

from .document_loader import UnsupportedDocumentError
from .models import (
    AvailableModelsResponse,
    HealthResponse,
    IngestRequest,
    IngestResponse,
    OllamaModel,
    QueryRequest,
    QueryResponse,
    EngineeringResponse,
    VectorStoreResponse,
)

router = APIRouter(prefix="/rag", tags=["RAG"])


@router.get("/models", response_model=AvailableModelsResponse)
async def rag_list_models() -> AvailableModelsResponse:
    """Return all queryable LLM options (Ollama local + cloud providers)."""
    import httpx
    from .rag_engine import get_rag_engine

    settings = get_rag_engine().settings
    ollama_models: list[OllamaModel] = []
    ollama_url = (settings.RAG_OPENAI_API_URL.strip() or "http://localhost:11434").rstrip("/v1").rstrip("/")

    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            resp = await client.get(f"{ollama_url}/api/tags")
            resp.raise_for_status()
            for m in (resp.json() or {}).get("models", []):
                size_gb = round(m.get("size", 0) / 1e9, 1) if m.get("size") else None
                ollama_models.append(OllamaModel(name=m["name"], size_gb=size_gb))
    except Exception:
        pass  # Ollama not running — return empty list, cloud providers still available.

    cohere_available = bool(settings.RAG_COHERE_API_KEY.strip())
    return AvailableModelsResponse(
        ollama=ollama_models,
        cohere_available=cohere_available,
        default_provider=settings.RAG_LLM_PROVIDER,
        default_model=settings.RAG_LLM_MODEL,
    )


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
    """Query the RAG knowledge base with an optional LLM override."""
    from .rag_engine import get_rag_engine

    try:
        result = get_rag_engine().query(
            question=body.question,
            top_k=body.top_k,
            filters=body.filters,
            collection=body.collection,
            llm_provider=body.llm_provider,
            llm_model=body.llm_model,
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
    from .parsers import parse_document
    from .rag_engine import get_rag_engine
    from uuid import uuid4

    form = await request.form()
    collection = str(form.get("collection") or "default")
    source_value = form.get("source")
    source = str(source_value).strip() if source_value is not None else ""

    # Extract additional metadata fields
    document_ids = form.getlist("document_ids") or form.getlist("document_id")
    project_id = str(form.get("project_id") or form.get("thread_id") or "").strip()
    thread_id = str(form.get("thread_id") or "").strip()
    user_id = str(form.get("user_id") or "").strip()

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
    metadata: list[dict[str, Any]] = []
    failed = 0

    for idx, uploaded_file in enumerate(uploaded_files):
        filename = uploaded_file.filename or "uploaded-file"
        doc_id = document_ids[idx] if idx < len(document_ids) else str(uuid4())
        try:
            content = await uploaded_file.read()
            
            # Save a copy as an archive
            import os
            from datetime import datetime
            from pathlib import Path
            
            archive_dir = Path(__file__).parent.parent / "src" / "assets" / "files"
            archive_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate a safe, timestamped filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_filename = "".join(c for c in filename if c.isalnum() or c in "._- ")
            archive_path = archive_dir / f"{timestamp}_{safe_filename}"
            archive_path.write_bytes(content)
            
            parsed = parse_document(
                filename=filename,
                content=content,
                content_type=uploaded_file.content_type,
            )
            text = parsed.content.strip()
            meta = parsed.metadata
        except Exception as exc:
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
                "document_id": doc_id,
                "project_id": project_id,
                "thread_id": thread_id,
                "user_id": user_id,
                "source": source if source else filename,
                "filename": filename,
                "content_type": uploaded_file.content_type or "",
                "domain": meta.get("detected_domain", "civil-architecture"),
                "upload_type": "file",
                "page_count": meta.get("page_count", 1),
                "has_drawings": meta.get("has_drawings", False),
                "has_tables": meta.get("has_tables", False),
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


@router.post("/upload", response_model=IngestResponse)
async def rag_upload(request: Request) -> IngestResponse:
    """Upload and parse a document using ArchChat's customized parsers, then index it."""
    return await rag_ingest_files(request)


@router.post("/chat", response_model=EngineeringResponse)
async def rag_chat(body: QueryRequest) -> EngineeringResponse:
    """Chat with the multi-agent architectural & civil engineering pipeline."""
    from app.agents import AgentPipeline
    from app.config import get_rag_settings

    try:
        pipeline = AgentPipeline(get_rag_settings())
        result = pipeline.execute_chat(
            question=body.question,
            collection=body.collection or "default",
            filters=body.filters
        )
        return EngineeringResponse(**result)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.post("/analyze", response_model=EngineeringResponse)
async def rag_analyze(body: QueryRequest) -> EngineeringResponse:
    """Analyze drawings, specifications, or reports using specialized analysts."""
    from app.agents import AgentPipeline
    from app.config import get_rag_settings

    try:
        pipeline = AgentPipeline(get_rag_settings())
        result = pipeline.execute_chat(
            question=body.question,
            collection=body.collection or "default",
            filters=body.filters,
            override_intent="analyze"
        )
        return EngineeringResponse(**result)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.post("/compliance-check", response_model=EngineeringResponse)
async def rag_compliance_check(body: QueryRequest) -> EngineeringResponse:
    """Run EBC 2023 or standard code compliance checks on architectural models."""
    from app.agents import AgentPipeline
    from app.config import get_rag_settings

    try:
        pipeline = AgentPipeline(get_rag_settings())
        result = pipeline.execute_chat(
            question=body.question,
            collection=body.collection or "default",
            filters=body.filters,
            override_intent="compliance-check"
        )
        return EngineeringResponse(**result)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.post("/compare", response_model=EngineeringResponse)
async def rag_compare(body: QueryRequest) -> EngineeringResponse:
    """Compare specifications, designs, or drawings."""
    from app.agents import AgentPipeline
    from app.config import get_rag_settings

    try:
        pipeline = AgentPipeline(get_rag_settings())
        result = pipeline.execute_chat(
            question=body.question,
            collection=body.collection or "default",
            filters=body.filters,
            override_intent="compare"
        )
        return EngineeringResponse(**result)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.post("/extract", response_model=EngineeringResponse)
async def rag_extract(body: QueryRequest) -> EngineeringResponse:
    """Extract structural parameters, tables, or design annotations."""
    from app.agents import AgentPipeline
    from app.config import get_rag_settings

    try:
        pipeline = AgentPipeline(get_rag_settings())
        result = pipeline.execute_chat(
            question=body.question,
            collection=body.collection or "default",
            filters=body.filters,
            override_intent="extract"
        )
        return EngineeringResponse(**result)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.post("/summarize", response_model=EngineeringResponse)
async def rag_summarize(body: QueryRequest) -> EngineeringResponse:
    """Summarize long specifications or reports."""
    from app.agents import AgentPipeline
    from app.config import get_rag_settings

    try:
        pipeline = AgentPipeline(get_rag_settings())
        result = pipeline.execute_chat(
            question=body.question,
            collection=body.collection or "default",
            filters=body.filters,
            override_intent="summarize"
        )
        return EngineeringResponse(**result)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.post("/calculate-area", response_model=EngineeringResponse)
async def rag_calculate_area(body: QueryRequest) -> EngineeringResponse:
    """Calculate boundaries and areas from CAD data."""
    from app.agents import AgentPipeline
    from app.config import get_rag_settings

    try:
        pipeline = AgentPipeline(get_rag_settings())
        result = pipeline.execute_chat(
            question=body.question,
            collection=body.collection or "default",
            filters=body.filters,
            override_intent="calculate-area"
        )
        return EngineeringResponse(**result)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.post("/calculate-boq", response_model=EngineeringResponse)
async def rag_calculate_boq(body: QueryRequest) -> EngineeringResponse:
    """Calculate quantity takeoffs and BOQ tables."""
    from app.agents import AgentPipeline
    from app.config import get_rag_settings

    try:
        pipeline = AgentPipeline(get_rag_settings())
        result = pipeline.execute_chat(
            question=body.question,
            collection=body.collection or "default",
            filters=body.filters,
            override_intent="calculate-boq"
        )
        return EngineeringResponse(**result)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.post("/check-dxf", response_model=EngineeringResponse)
async def rag_check_dxf(body: QueryRequest) -> EngineeringResponse:
    """Inspect DXF files for layer compliance and standards."""
    from app.agents import AgentPipeline
    from app.config import get_rag_settings

    try:
        pipeline = AgentPipeline(get_rag_settings())
        result = pipeline.execute_chat(
            question=body.question,
            collection=body.collection or "default",
            filters=body.filters,
            override_intent="check-dxf"
        )
        return EngineeringResponse(**result)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.get("/vector-store", response_model=VectorStoreResponse)
async def rag_vector_store() -> VectorStoreResponse:
    """Retrieve statistics about vector store collections."""
    from .rag_engine import get_rag_engine

    collections = [
        "ebc_2023",
        "architectural_standards",
        "structural_engineering",
        "construction_docs",
        "building_materials",
        "mep_standards",
        "bim_knowledge",
        "cad_entities",
        "user_uploads",
        "conversation_memory"
    ]

    engine = get_rag_engine()
    stats = {}
    for col in collections:
        try:
            count = engine.count_documents(col)
            stats[col] = count if count is not None else 0
        except Exception:
            stats[col] = 0

    return VectorStoreResponse(collections=stats)


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


@router.delete("/collection/{collection_name}/document/{document_id}")
async def rag_delete_document(collection_name: str, document_id: str) -> dict[str, Any]:
    """Delete a document and all its indexed chunks from a collection using document_id."""
    import logging
    from pathlib import Path

    from .rag_engine import get_rag_engine

    logger = logging.getLogger(__name__)

    try:
        # Delete from Qdrant, returning the filename if found
        filename = get_rag_engine().delete_document(collection_name, document_id)

        # Delete archived files matching *_{filename} in RAG/src/assets/files
        deleted_files: list[str] = []
        if filename:
            archive_dir = Path(__file__).resolve().parent.parent / "src" / "assets" / "files"
            if archive_dir.exists():
                for file_path in archive_dir.iterdir():
                    if file_path.is_file() and file_path.name.endswith(f"_{filename}"):
                        try:
                            file_path.unlink()
                            deleted_files.append(file_path.name)
                        except Exception as e:
                            logger.error(f"Failed to delete archived file {file_path.name}: {e}")

        return {
            "status": "deleted",
            "collection": collection_name,
            "document_id": document_id,
            "filename": filename or "unknown",
            "archived_deleted": deleted_files,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
