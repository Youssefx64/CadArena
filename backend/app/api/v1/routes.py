"""
API v1 routes for DXF generation and file operations.

This module defines REST API endpoints for:
- Drawing simple rectangles
- Generating DXF files from design intents
- Downloading DXF files in various formats (DXF, PDF, PNG)
"""

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import FileResponse

from app.pipeline.draw_pipeline import draw_rectangle_pipeline
from app.schemas.geometry import RectangleGeometry
from app.schemas.design_intent import DesignIntent
from app.schemas.export import DxfDownloadRequest
from app.pipeline.intent_to_agent import generate_dxf_from_intent
from app.services.dxf_exporter import (
    DxfExportDependencyError,
    DxfExportError,
    ExportFormat,
    export_dxf_file,
    get_media_type,
)

router = APIRouter()


def _download_file_response(dxf_path: str, export_format: ExportFormat) -> FileResponse:
    """
    Internal helper to generate a file download response.
    
    Args:
        dxf_path: Path to the DXF file to export/download.
        export_format: Target export format (DXF, PDF, or IMAGE).
    
    Returns:
        FileResponse configured for the requested format.
    
    Raises:
        HTTPException: 500 if export dependencies are missing, 400 if export fails.
    """
    try:
        export_path, filename = export_dxf_file(dxf_path, export_format)
    except DxfExportDependencyError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except DxfExportError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return FileResponse(
        path=export_path,
        media_type=get_media_type(export_format),
        filename=filename,
    )


def _build_download_links(request: Request, dxf_path: str) -> dict[str, str]:
    """
    Build download URLs for all supported export formats.
    
    Args:
        request: FastAPI request object for URL generation.
        dxf_path: Path to the DXF file.
    
    Returns:
        Dictionary mapping format names to download URLs.
    """
    file_name = Path(dxf_path).name
    base_url = request.url_for("download_dxf_by_name", dxf_filename=file_name)
    return {
        export_format.value: f"{base_url}?format={export_format.value}"
        for export_format in ExportFormat
    }


@router.post("/draw/rectangle")
def draw_rectangle(rect: RectangleGeometry):
    """
    Generate a DXF file containing a single rectangle.
    
    Args:
        rect: Rectangle geometry specification (width, height, origin).
    
    Returns:
        Dictionary with status and generated file path.
    """
    file_path = draw_rectangle_pipeline(rect)

    return {
        "status": "dxf generated",
        "file": str(file_path)
    }

@router.post("/generate-dxf")
def generate_dxf(intent: DesignIntent, request: Request):
    """
    Generate a DXF file from a structured design intent.
    
    Processes a complete design intent (boundary, rooms, openings) and generates
    a DXF file with walls, doors, windows, and room labels.
    
    Args:
        intent: Complete design specification including boundary, rooms, and openings.
        request: FastAPI request object for URL generation.
    
    Returns:
        Dictionary with status, DXF file path, and download URLs for all formats.
    
    Raises:
        HTTPException: 400 if design intent is invalid or processing fails.
    """
    try:
        dxf_path = generate_dxf_from_intent(intent)
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "status": "success",
        "dxf_path": str(dxf_path),
        "download_urls": _build_download_links(request, str(dxf_path)),
    }


@router.post("/download-dxf")
def download_dxf(
    request: DxfDownloadRequest,
    export_format: ExportFormat = Query(default=ExportFormat.DXF, alias="format"),
):
    """
    Download a DXF file in the specified format.
    
    Args:
        request: Request containing the DXF file path.
        export_format: Export format (DXF, PDF, or IMAGE). Defaults to DXF.
    
    Returns:
        FileResponse with the requested file.
    
    Raises:
        HTTPException: 400 if file not found or export fails, 500 if dependencies missing.
    """
    return _download_file_response(request.dxf_path, export_format)


@router.get("/download/{dxf_filename}", name="download_dxf_by_name")
def download_dxf_by_name(
    dxf_filename: str,
    export_format: ExportFormat = Query(default=ExportFormat.DXF, alias="format"),
):
    """
    Download a DXF file by filename in the specified format.
    
    Args:
        dxf_filename: Name of the DXF file (with or without .dxf extension).
        export_format: Export format (DXF, PDF, or IMAGE). Defaults to DXF.
    
    Returns:
        FileResponse with the requested file.
    
    Raises:
        HTTPException: 400 if filename is invalid or file not found, 500 if dependencies missing.
    """
    # Security: prevent directory traversal by ensuring no path separators
    if Path(dxf_filename).name != dxf_filename:
        raise HTTPException(status_code=400, detail="Invalid dxf filename")

    normalized_name = dxf_filename
    # Auto-append .dxf extension if missing
    if not normalized_name.lower().endswith(".dxf"):
        normalized_name = f"{normalized_name}.dxf"

    return _download_file_response(normalized_name, export_format)


@router.post("/generate-dxf/download")
def generate_and_download_dxf(
    intent: DesignIntent,
    export_format: ExportFormat = Query(default=ExportFormat.DXF, alias="format"),
):
    """
    Generate a DXF file from design intent and immediately download it.
    
    Convenience endpoint that combines generation and download in one request.
    
    Args:
        intent: Complete design specification including boundary, rooms, and openings.
        export_format: Export format (DXF, PDF, or IMAGE). Defaults to DXF.
    
    Returns:
        FileResponse with the generated file in the requested format.
    
    Raises:
        HTTPException: 400 if design intent is invalid or processing fails, 500 if dependencies missing.
    """
    try:
        dxf_path = generate_dxf_from_intent(intent)
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return _download_file_response(str(dxf_path), export_format)
