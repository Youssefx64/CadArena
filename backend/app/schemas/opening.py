from typing import Literal
from pydantic import BaseModel
from app.schemas.geometry import Point


class Opening(BaseModel):
    type: Literal["door", "window"]
    width: float
    position: Point
    orientation: Literal["horizontal", "vertical"]
