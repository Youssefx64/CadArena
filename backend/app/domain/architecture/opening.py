from app.schemas.geometry import Point
from app.domain.architecture.wall import WallSegment
from app.domain.architecture.door import DoorSpec


class DoorPlacement:
    def __init__(self, wall: WallSegment, offset: float, door: DoorSpec):
        self.wall = wall
        self.offset = offset
        self.door = door
