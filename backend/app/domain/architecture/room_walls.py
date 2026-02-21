from app.domain.entities import Room
from app.domain.architecture.wall import WallSegment
from app.domain.architecture.wall_generator import generate_wall_segments


def build_room_walls(room: Room) -> dict[str, WallSegment]:
    segments = generate_wall_segments(room)
    return {
        "bottom": segments[0],
        "right": segments[1],
        "top": segments[2],
        "left": segments[3],
    }
