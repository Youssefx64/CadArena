"""
Geometric shape schema definitions.

This module defines Pydantic models for basic geometric entities used
throughout the application.
"""

from pydantic import BaseModel
from typing import Literal


class Point(BaseModel):
    """
    2D point in Cartesian coordinates.
    
    Attributes:
        x: X coordinate.
        y: Y coordinate.
    """
    x: float
    y: float


class RectangleGeometry(BaseModel):
    """
    Rectangle shape specification.
    
    Attributes:
        type: Shape type (currently only "rectangle" supported).
        width: Rectangle width in meters.
        height: Rectangle height in meters.
        origin: Bottom-left corner point of the rectangle.
    """
    type: Literal["rectangle"]
    width: float
    height: float
    origin: Point


class GeometryPlan(BaseModel):
    """
    Geometry with layer assignment for DXF rendering.
    
    Attributes:
        shape: Rectangle geometry to render.
        layer: DXF layer name for this geometry.
    """
    shape: RectangleGeometry
    layer: str
