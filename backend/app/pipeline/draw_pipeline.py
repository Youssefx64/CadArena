from app.domain.geometry.rectangle import rectangle_to_points
from app.domain.geometry.rules import validate_rectangle
from app.services.dxf_renderer import draw_rectangle
from app.schemas.geometry import RectangleGeometry

def draw_rectangle_pipeline(rect: RectangleGeometry):
    validate_rectangle(rect.width, rect.height)
    points = rectangle_to_points(rect)
    draw_rectangle(points, "output.dxf")
