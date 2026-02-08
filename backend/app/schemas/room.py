"""
Room schema definition.

This module defines the Room model used for internal room representation
after placement by the planner agent.
"""

from typing import Literal
from pydantic import BaseModel
from app.schemas.geometry import Point


class Room(BaseModel):
    """
    Room model with placement information.
    
    Attributes:
        name: Unique identifier for the room.
        room_type: Type of room (bedroom, living, kitchen, bathroom, corridor, stairs).
        width: Room width in meters.
        height: Room height in meters.
        origin: Bottom-left corner point. None if room hasn't been placed yet.
    
    Properties:
        layer: DXF layer name derived from room type (e.g., "ROOM_BEDROOM").
    """
    name: str
    room_type: Literal[
        "bedroom", "living", "kitchen", "bathroom", "corridor", "stairs"
    ]
    width: float
    height: float
    origin: Point | None = None

    @property
    def layer(self) -> str:
        """
        Get the DXF layer name for this room type.
        
        Returns:
            Layer name in format "ROOM_{ROOM_TYPE_UPPERCASE}".
        """
        return f"ROOM_{self.room_type.upper()}"
