from app.schemas.room import Room
from app.domain.architecture.wall import WallSegment
from app.schemas.geometry import Point, RectangleGeometry


def generate_wall_segments(room: Room) -> list[WallSegment]:
    """
    Convert a room into 4 wall segments (bottom, right, top, left).
    """
    if room.origin is None:
        raise ValueError(f"Room {room.name} has no origin")
    
    x = room.origin.x
    y = room.origin.y
    w = room.width
    h = room.height
    
    # Create 4 wall segments - 2 ARGUMENTS ONLY (no thickness)
    segments = [
        WallSegment(Point(x=x, y=y), Point(x=x + w, y=y)),           # Bottom
        WallSegment(Point(x=x + w, y=y), Point(x=x + w, y=y + h)),   # Right
        WallSegment(Point(x=x + w, y=y + h), Point(x=x, y=y + h)),   # Top
        WallSegment(Point(x=x, y=y + h), Point(x=x, y=y)),           # Left
    ]
    
    return segments


def generate_boundary_segments(boundary: RectangleGeometry) -> list[WallSegment]:
    """
    Convert a rectangle boundary into 4 wall segments (bottom, right, top, left).
    """
    x = boundary.origin.x
    y = boundary.origin.y
    w = boundary.width
    h = boundary.height

    return [
        WallSegment(Point(x=x, y=y), Point(x=x + w, y=y)),           # Bottom
        WallSegment(Point(x=x + w, y=y), Point(x=x + w, y=y + h)),   # Right
        WallSegment(Point(x=x + w, y=y + h), Point(x=x, y=y + h)),   # Top
        WallSegment(Point(x=x, y=y + h), Point(x=x, y=y)),           # Left
    ]
