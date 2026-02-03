from app.schemas.room import Room
from app.schemas.geometry import Point
from app.domain.architecture.wall import WallSegment

WALL_THICKNESS = 0.2

def build_room_walls(room: Room) -> dict[str, WallSegment]:
    x = room.origin.x
    y = room.origin.y
    w = room.width
    h = room.height

    return {
        "bottom": WallSegment(
            start=Point(x=x, y=y),
            end=Point(x=x + w, y=y),
            thickness=WALL_THICKNESS
        ),
        "top": WallSegment(
            start=Point(x=x, y=y + h),
            end=Point(x=x + w, y=y + h),
            thickness=WALL_THICKNESS
        ),
        "left": WallSegment(
            start=Point(x=x, y=y),
            end=Point(x=x, y=y + h),
            thickness=WALL_THICKNESS
        ),
        "right": WallSegment(
            start=Point(x=x + w, y=y),
            end=Point(x=x + w, y=y + h),
            thickness=WALL_THICKNESS
        ),
    }
