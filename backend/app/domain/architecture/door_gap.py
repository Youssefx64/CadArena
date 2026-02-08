"""
Wall cutting for door gaps.

This module provides functions to cut walls to create gaps for doors.
Note: This appears to be an alternative implementation to wall_cut.py.
"""

from app.domain.architecture.wall import WallSegment
from app.schemas.geometry import Point


def cut_wall_for_door(
    wall: WallSegment,
    offset: float,
    door_width: float
) -> tuple[WallSegment, WallSegment]:
    """
    Cut a wall segment to create a gap for a door.
    
    Args:
        wall: Wall segment to cut.
        offset: Distance from wall start to gap start.
        door_width: Width of the door gap.
    
    Returns:
        Tuple of (left_segment, right_segment) with gap between them.
    
    Raises:
        ValueError: If door exceeds wall length.
    """
    length = wall.length()
    if offset + door_width > length:
        raise ValueError("Door exceeds wall length")

    # Calculate unit vector along wall
    dx = wall.end.x - wall.start.x
    dy = wall.end.y - wall.start.y

    ux = dx / length
    uy = dy / length

    # Calculate gap start and end points
    gap_start = Point(
        x=wall.start.x + ux * offset,
        y=wall.start.y + uy * offset
    )

    gap_end = Point(
        x=gap_start.x + ux * door_width,
        y=gap_start.y + uy * door_width
    )

    # Create segments with gap
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
