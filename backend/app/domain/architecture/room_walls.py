"""
Room wall builder with thickness.

This module provides functions to build room walls with thickness information.
Note: This appears to be an alternative implementation to wall_generator.py.
"""

from app.schemas.room import Room
from app.schemas.geometry import Point
from app.domain.architecture.wall import WallSegment

# Standard wall thickness in meters
WALL_THICKNESS = 0.2

def build_room_walls(room: Room) -> dict[str, WallSegment]:
    """
    Build room walls as a dictionary with named sides.
    
    Creates wall segments for all four sides of a room with thickness
    information. Returns a dictionary keyed by wall side name.
    
    Args:
        room: Room to build walls for.
    
    Returns:
        Dictionary mapping wall side names ("bottom", "top", "left", "right")
        to WallSegment objects.
    """
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
