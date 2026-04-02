"""API v1 routes for DXF generation and file access."""

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, Query, Request, Response, UploadFile
from fastapi.responses import FileResponse

from app.core.file_utils import ensure_dxf_output_dir
from app.pipeline.intent_to_agent import generate_dxf_from_intent
from app.schemas.design_intent import DesignIntent
from app.services.dxf_exporter import (
    DxfExportDependencyError,
    DxfExportError,
    ExportFormat,
    export_dxf_file,
    get_media_type,
)
from app.services.file_token_registry import issue_session_file_token, resolve_request_file_token

router = APIRouter()
MAX_DXF_UPLOAD_BYTES = 20 * 1024 * 1024


def _safe_upload_stem(filename: str) -> str:
    stem = Path(filename).stem.strip()
    if not stem:
        return "upload"

    sanitized = "".join(char if (char.isalnum() or char in {"-", "_"}) else "_" for char in stem)
    sanitized = sanitized.strip("._-")
    if not sanitized:
        return "upload"
    return sanitized[:64]


def _normalize_attachment_filename(filename: str | None, fallback: str, required_suffix: str) -> str:
    if filename is None:
        return fallback

    normalized = Path(filename).name.strip()
    if not normalized:
        return fallback
    if not normalized.lower().endswith(required_suffix.lower()):
        normalized = f"{normalized}{required_suffix}"
    return normalized


@router.post("/generate-dxf")
def generate_dxf(intent: DesignIntent, request: Request, response: Response):
    """
    Generate a DXF file from a structured design intent.
    
    Processes a complete design intent (boundary, rooms, openings) and generates
    a DXF file with walls, doors, windows, and room labels.
    
    Args:
        intent: Complete design specification including boundary, rooms, and openings.

    Returns:
        Dictionary with status, session-scoped file token, and DXF filename.
    
    Raises:
        HTTPException: 400 if design intent is invalid or processing fails.
    """
    try:
        dxf_path = generate_dxf_from_intent(intent)
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    file_token = issue_session_file_token(request=request, response=response, absolute_path=dxf_path)

    return {
        "status": "success",
        "file_token": file_token,
        "dxf_name": Path(dxf_path).name,
    }


def _normalize_download_filename(filename: str | None, fallback: str) -> str:
    return _normalize_attachment_filename(filename, fallback, ".dxf")


@router.get("/dxf/download")
def download_dxf(
    request: Request,
    file_token: str = Query(..., min_length=1),
    filename: str | None = Query(default=None, min_length=1),
):
    """Download a generated DXF file by session-scoped token."""
    source_path = _resolve_dxf_source_path(request=request, file_token=file_token)
    if source_path.suffix.lower() != ".dxf":
        raise HTTPException(status_code=400, detail="Only .dxf files are supported")
    if not source_path.exists():
        raise HTTPException(status_code=404, detail=f"DXF file not found: {source_path.name}")

    attachment_name = _normalize_download_filename(filename, source_path.name)
    return FileResponse(
        source_path,
        media_type=get_media_type(ExportFormat.DXF),
        filename=attachment_name,
    )


@router.get("/dxf/preview")
def preview_dxf(request: Request, file_token: str = Query(..., min_length=1)):
    """Generate and return a PNG preview for a DXF file token."""
    source_path = _resolve_dxf_source_path(request=request, file_token=file_token)
    try:
        preview_path, preview_filename = export_dxf_file(
            dxf_path=source_path,
            export_format=ExportFormat.IMAGE,
        )
    except DxfExportDependencyError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except DxfExportError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return FileResponse(
        preview_path,
        media_type=get_media_type(ExportFormat.IMAGE),
        filename=preview_filename,
    )


@router.get("/dxf/export")
def export_dxf(
    request: Request,
    file_token: str = Query(..., min_length=1),
    format: ExportFormat = Query(default=ExportFormat.IMAGE),
    filename: str | None = Query(default=None, min_length=1),
):
    """Export a DXF file as PNG or PDF and return it as a downloadable file."""
    source_path = _resolve_dxf_source_path(request=request, file_token=file_token)
    if format == ExportFormat.DXF:
        return download_dxf(request=request, file_token=file_token, filename=filename)

    suffix = ".pdf" if format == ExportFormat.PDF else ".png"
    try:
        export_path, export_filename = export_dxf_file(
            dxf_path=source_path,
            export_format=format,
        )
    except DxfExportDependencyError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except DxfExportError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    attachment_name = _normalize_attachment_filename(filename, export_filename, suffix)
    return FileResponse(
        export_path,
        media_type=get_media_type(format),
        filename=attachment_name,
    )


@router.post("/dxf/upload")
async def upload_dxf(request: Request, response: Response, file: UploadFile = File(...)):
    """Upload a local DXF file into backend/output/dxf and return its file token."""
    original_filename = Path(file.filename or "").name
    if not original_filename:
        raise HTTPException(status_code=400, detail="Missing file name")
    if not original_filename.lower().endswith(".dxf"):
        raise HTTPException(status_code=400, detail="Only .dxf files are supported")

    try:
        payload = await file.read(MAX_DXF_UPLOAD_BYTES + 1)
    finally:
        await file.close()

    if not payload:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")
    if len(payload) > MAX_DXF_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File is too large. Maximum allowed size is 20 MB.")

    output_dir = ensure_dxf_output_dir()
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    suffix = uuid4().hex[:8]
    safe_stem = _safe_upload_stem(original_filename)
    stored_filename = f"{safe_stem}_{timestamp}_{suffix}.dxf"
    stored_path = output_dir / stored_filename
    stored_path.write_bytes(payload)
    file_token = issue_session_file_token(request=request, response=response, absolute_path=stored_path)

    return {
        "status": "success",
        "file_token": file_token,
        "stored_filename": stored_filename,
        "original_filename": original_filename,
    }


def _resolve_dxf_source_path(*, request: Request, file_token: str) -> Path:
    source_path = resolve_request_file_token(request=request, file_token=file_token)
    if source_path is None:
        raise HTTPException(status_code=404, detail="DXF file token not found")
    return source_path
