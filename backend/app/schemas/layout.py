from pydantic import BaseModel
from app.schemas.geometry import RectangleGeometry


class Layout(BaseModel):
    boundary: RectangleGeometry
    rooms: list
