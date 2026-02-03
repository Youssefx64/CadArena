from app.domain.architecture.wall import WallSegment
from app.domain.architecture.door import DoorSpec


def compute_door_rotation(wall: WallSegment, door: DoorSpec) -> float:
    if abs(wall.start.y - wall.end.y) < abs(wall.start.x - wall.end.x):
        base = 0    # horizontal
    else:
        base = 90   # vertical

    if door.hinge == "right":
        base += 180

    if door.swing == "out":
        base += 180

    return base % 360