"""
Lenient design intent schema for default resolution.
"""

from typing import List, Literal
from pydantic import BaseModel
from app.schemas.geometry import Point


class BoundaryDraft(BaseModel):
    """
    Lenient boundary specification.
    """
    width: float | None = None
    height: float | None = None
    unit: Literal["meter"] | None = "meter"


class RoomDraft(BaseModel):
    """
    Lenient room specification.
    """
    name: str | None = None
    room_type: Literal[
        "living", "bedroom", "kitchen", "bathroom", "corridor", "stairs"
    ] | None = None
    width: float | None = None
    height: float | None = None
    origin: Point | None = None


class OpeningDraft(BaseModel):
    """
    Lenient opening specification.
    """
    type: Literal["door", "window"] | None = None
    width: float | None = None
    room_name: str | None = None
    wall: Literal["left", "right", "top", "bottom"] | None = None
    offset: float | None = None
    cut_start: Point | None = None
    cut_end: Point | None = None
    hinge: Literal["left", "right"] | None = None
    swing: Literal["in", "out"] | None = None


class DesignIntentDraft(BaseModel):
    """
    Lenient design intent payload allowing missing or ambiguous fields.
    """
    boundary: BoundaryDraft | None = None
    rooms: List[RoomDraft] | None = None
    openings: List[OpeningDraft] | None = None
    planning: dict | None = None

    class Config:
        extra = "allow"
