from typing import List, Literal
from pydantic import BaseModel
from app.schemas.geometry import Point


class BoundaryIntent(BaseModel):
    width: float
    height: float
    unit: Literal["meter"] = "meter"


class RoomIntent(BaseModel):
    name: str
    room_type: Literal["living", "bedroom", "kitchen", "bathroom"]
    width: float
    height: float
    origin: Point | None = None


class OpeningIntent(BaseModel):
    type: Literal["door", "window"]
    width: float

    wall: Literal["left", "right", "top", "bottom"]
    offset: float | None = None


class DesignIntent(BaseModel):
    boundary: BoundaryIntent
    rooms: List[RoomIntent]
    openings: List[OpeningIntent] = []
