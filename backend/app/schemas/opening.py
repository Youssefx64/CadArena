"""
Opening schema definition.

This module defines the Opening model for representing doors and windows
in a simplified format.
"""

from typing import Literal
from pydantic import BaseModel
from app.schemas.geometry import Point


class Opening(BaseModel):
    """
    Door or window opening specification.
    
    Attributes:
        type: Type of opening ("door" or "window").
        width: Opening width in meters.
        position: Position point of the opening.
        orientation: Opening orientation ("horizontal" or "vertical").
    """
    type: Literal["door", "window"]
    width: float
    position: Point
    orientation: Literal["horizontal", "vertical"]
