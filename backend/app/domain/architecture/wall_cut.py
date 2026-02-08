"""
Wall cutting utilities for door openings.

This module provides functions to cut wall segments to create openings
for doors and windows.
"""

from app.domain.architecture.wall import WallSegment
from app.domain.architecture.opening import DoorPlacement
from app.schemas.geometry import Point


def cut_wall(wall: WallSegment, placement: DoorPlacement):
    """
    Cut a wall segment to create a door opening.
    
    Splits a wall segment into two segments with a gap between them
    where the door opening is located.
    
    Args:
        wall: Wall segment to cut.
        placement: Door placement specifying offset and width.
    
    Returns:
        Tuple of (left_segment, right_segment) with gap for door.
    
    Raises:
        ValueError: If door exceeds wall length.
    """
    door = placement.door
    offset = placement.offset

    length = wall.length()
    if offset + door.width > length:
        raise ValueError("Door exceeds wall length")

    # Calculate unit vector along wall direction
    dx = wall.end.x - wall.start.x
    dy = wall.end.y - wall.start.y

    ux = dx / length
    uy = dy / length

    # Cut start point (where door opening begins)
    cut_start = Point(
        x=wall.start.x + ux * offset,
        y=wall.start.y + uy * offset
    )

    # Cut end point (where door opening ends)
    cut_end = Point(
        x=cut_start.x + ux * door.width,
        y=cut_start.y + uy * door.width
    )

    # Create left and right wall segments (gap between them)
    left = WallSegment(wall.start, cut_start)
    right = WallSegment(cut_end, wall.end)

    return left, right