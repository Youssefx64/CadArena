"""API v1 routes for DXF generation."""

from fastapi import APIRouter, HTTPException

from app.pipeline.intent_to_agent import generate_dxf_from_intent
from app.schemas.design_intent import DesignIntent

router = APIRouter()

@router.post("/generate-dxf")
def generate_dxf(intent: DesignIntent):
    """
    Generate a DXF file from a structured design intent.
    
    Processes a complete design intent (boundary, rooms, openings) and generates
    a DXF file with walls, doors, windows, and room labels.
    
    Args:
        intent: Complete design specification including boundary, rooms, and openings.

    Returns:
        Dictionary with status and generated DXF path.
    
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
    }
