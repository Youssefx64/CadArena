from typing import Literal
from pydantic import BaseModel
from app.schemas.geometry import Point


class Room(BaseModel):
    name: str
    room_type: Literal[
        "bedroom", "living", "kitchen", "bathroom"
    ]
    width: float
    height: float
    origin: Point | None = None

    @property
    def layer(self) -> str:
        return f"ROOM_{self.room_type.upper()}"
