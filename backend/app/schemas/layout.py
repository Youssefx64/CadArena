"""
Layout schema definition.

This module defines the Layout model for representing a complete floor plan
with boundary and rooms.
"""

from pydantic import BaseModel
from app.schemas.geometry import RectangleGeometry


class Layout(BaseModel):
    """
    Complete layout specification.
    
    Attributes:
        boundary: Outer boundary rectangle.
        rooms: List of rooms in the layout.
    """
    boundary: RectangleGeometry
    rooms: list
