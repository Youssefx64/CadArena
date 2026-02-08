"""
Simple rectangle drawing pipeline.

This module provides a pipeline for generating DXF files containing
a single rectangle shape.
"""

from app.domain.geometry.rectangle import rectangle_to_points
from app.domain.geometry.rules import validate_rectangle
from app.services.dxf_renderer import draw_rectangle
from app.schemas.geometry import RectangleGeometry
from app.core.file_utils import generate_dxf_filename


def draw_rectangle_pipeline(rect: RectangleGeometry):
    """
    Generate a DXF file containing a single rectangle.
    
    Validates the rectangle dimensions, converts to points, generates
    a unique filename, and renders the rectangle to DXF.
    
    Args:
        rect: Rectangle geometry specification.
    
    Returns:
        Path to the generated DXF file.
    
    Raises:
        ValueError: If rectangle dimensions are invalid (too small or negative).
    """
    validate_rectangle(rect.width, rect.height)

    points = rectangle_to_points(rect)

    file_path = generate_dxf_filename(
        prefix=f"rectangle_{int(rect.width)}x{int(rect.height)}"
    )

    draw_rectangle(points, file_path)

    return file_path