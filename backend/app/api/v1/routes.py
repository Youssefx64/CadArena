from fastapi import APIRouter
from app.pipeline.draw_pipeline import draw_rectangle_pipeline
from app.schemas.geometry import RectangleGeometry

router = APIRouter()

@router.post("/draw/rectangle")
def draw_rectangle(rect: RectangleGeometry):
    draw_rectangle_pipeline(rect)
    return {"status": "dxf generated"}
