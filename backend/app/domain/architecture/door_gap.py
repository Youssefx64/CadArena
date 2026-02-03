from app.domain.architecture.wall import WallSegment
from app.schemas.geometry import Point


def cut_wall_for_door(
    wall: WallSegment,
    offset: float,
    door_width: float
) -> tuple[WallSegment, WallSegment]:

    length = wall.length()
    if offset + door_width > length:
        raise ValueError("Door exceeds wall length")

    dx = wall.end.x - wall.start.x
    dy = wall.end.y - wall.start.y

    ux = dx / length
    uy = dy / length

    gap_start = Point(
        x=wall.start.x + ux * offset,
        y=wall.start.y + uy * offset
    )

    gap_end = Point(
        x=gap_start.x + ux * door_width,
        y=gap_start.y + uy * door_width
    )

    left = WallSegment(
        start=wall.start,
        end=gap_start,
        orientation=wall.orientation
    )

    right = WallSegment(
        start=gap_end,
        end=wall.end,
        orientation=wall.orientation
    )

    return left, right
