"""
Design intent schema definitions.

This module defines Pydantic models for representing user design specifications,
including boundaries, rooms, and openings (doors/windows).
"""

from typing import List, Literal
from pydantic import BaseModel
from app.schemas.geometry import Point


class BoundaryIntent(BaseModel):
    """
    Specification for the overall building boundary.
    
    Attributes:
        width: Boundary width in meters.
        height: Boundary height in meters.
        unit: Measurement unit (currently only "meter" supported).
    """
    width: float
    height: float
    unit: Literal["meter"] = "meter"


class RoomIntent(BaseModel):
    """
    Specification for a single room in the design.
    
    Attributes:
        name: Unique identifier for the room.
        room_type: Type of room (living, bedroom, kitchen, bathroom, corridor, stairs).
        width: Room width in meters.
        height: Room height in meters.
        origin: Optional origin point. If None, room will be auto-placed by planner.
    """
    name: str
    room_type: Literal["living", "bedroom", "kitchen", "bathroom", "corridor", "stairs"]
    width: float
    height: float
    origin: Point | None = None


class OpeningIntent(BaseModel):
    """
    Specification for a door or window opening.
    
    Attributes:
        type: Type of opening ("door" or "window").
        width: Opening width in meters. Defaults to 1.0.
        room_name: Name of the room this opening belongs to.
        wall: Wall side ("left", "right", "top", "bottom") relative to room.
        offset: Distance from wall start point. If None, opening is centered.
        cut_start: Alternative to offset - explicit start point of opening.
        cut_end: Alternative to offset - explicit end point of opening.
        hinge: Door hinge side ("left" or "right"). Only applies to doors.
        swing: Door swing direction ("in" or "out"). Only applies to doors.
    
    Note:
        Either use (offset) OR (cut_start, cut_end), not both.
    """
    type: Literal["door", "window"]
    width: float = 1.0
    room_name: str | None = None
    wall: Literal["left", "right", "top", "bottom"] | None = None
    offset: float | None = None
    cut_start: Point | None = None
    cut_end: Point | None = None
    hinge: Literal["left", "right"] | None = None
    swing: Literal["in", "out"] | None = None


class DesignIntent(BaseModel):
    """
    Complete design specification containing boundary, rooms, and openings.
    
    Attributes:
        boundary: Overall building boundary specification.
        rooms: List of room specifications.
        openings: List of door/window opening specifications. Defaults to empty list.
    """
    boundary: BoundaryIntent
    rooms: List[RoomIntent]
    openings: List[OpeningIntent] = []
