from fastapi import APIRouter
from app.pipeline.draw_pipeline import draw_rectangle_pipeline
from app.schemas.geometry import RectangleGeometry
from app.schemas.design_intent import DesignIntent
from app.pipeline.intent_to_agent import generate_dxf_from_intent

router = APIRouter()

@router.post("/draw/rectangle")
def draw_rectangle(rect: RectangleGeometry):
    file_path = draw_rectangle_pipeline(rect)

    return {
        "status": "dxf generated",
        "file": str(file_path)
    }

@router.post("/generate-dxf")
def generate_dxf(intent: DesignIntent):
    """
    Generate a DXF file from a structured design intent.
    """
    dxf_path = generate_dxf_from_intent(intent)

    return {
        "status": "success",
        "dxf_path": str(dxf_path)
    }