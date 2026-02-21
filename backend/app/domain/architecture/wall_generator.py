"""
Wall segment generation utilities.

This module provides functions to generate wall segments from rooms
and boundary rectangles.
"""

from app.domain.entities import Room
from app.domain.architecture.wall import WallSegment
from app.domain.entities import Point, RectangleGeometry


def generate_wall_segments(room: Room) -> list[WallSegment]:
    """
    Convert a room into 4 wall segments.
    
    Creates wall segments for all four sides of a room in order:
    bottom, right, top, left (counter-clockwise from bottom-left corner).
    
    Args:
        room: Room to generate walls for.
    
    Returns:
        List of 4 wall segments.
    
    Raises:
        ValueError: If room has no origin (not placed).
    """
    if room.origin is None:
        raise ValueError(f"Room {room.name} has no origin")
    
    x = room.origin.x
    y = room.origin.y
    w = room.width
    h = room.height
    
    # Create 4 wall segments in counter-clockwise order
    segments = [
        WallSegment(Point(x=x, y=y), Point(x=x + w, y=y)),           # Bottom
        WallSegment(Point(x=x + w, y=y), Point(x=x + w, y=y + h)),   # Right
        WallSegment(Point(x=x + w, y=y + h), Point(x=x, y=y + h)),   # Top
        WallSegment(Point(x=x, y=y + h), Point(x=x, y=y)),           # Left
    ]
    
    return segments


def generate_boundary_segments(boundary: RectangleGeometry) -> list[WallSegment]:
    """
    Convert a rectangle boundary into 4 wall segments.
    
    Creates wall segments for all four sides of the boundary in order:
    bottom, right, top, left (counter-clockwise from bottom-left corner).
    
    Args:
        boundary: Boundary rectangle to generate walls for.
    
    Returns:
        List of 4 wall segments.
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
