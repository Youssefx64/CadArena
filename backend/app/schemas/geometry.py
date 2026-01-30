from pydantic import BaseModel
from typing import List, Literal


class Point(BaseModel):
    x: float
    y: float


class RectangleGeometry(BaseModel):
    type: Literal["rectangle"]
    width: float
    height: float
    origin: Point


class GeometryPlan(BaseModel):
    shape: RectangleGeometry
    layer: str
