"""
Automatic window placement utilities.

This module provides functions for automatically placing windows in rooms
that are adjacent to the external boundary.
"""

from app.domain.entities import Room
from app.domain.entities import RectangleGeometry, Point
from app.domain.entities import Opening


def auto_place_windows(room: Room, boundary: RectangleGeometry) -> list[Opening]:
    """
    Place windows only if the room touches the external boundary.
    
    Checks each side of the room and places a window if that side
    aligns with the boundary edge. Windows are centered on the wall.
    
    Args:
        room: Room to place windows in.
        boundary: Building boundary to check alignment against.
    
    Returns:
        List of window openings (empty if room doesn't touch boundary).
    """
    windows: list[Opening] = []
    window_width = 1.2

    # Check left boundary alignment
    if room.origin.x == boundary.origin.x:
        windows.append(
            Opening(
                type="window",
                width=window_width,
                position=Point(x=room.origin.x, y=room.origin.y + room.height / 2),
                orientation="vertical",
            )
        )

    # Check right boundary alignment
    if room.origin.x + room.width == boundary.origin.x + boundary.width:
        windows.append(
            Opening(
                type="window",
                width=window_width,
                position=Point(
                    x=room.origin.x + room.width, y=room.origin.y + room.height / 2
                ),
                orientation="vertical",
            )
        )

    # Check bottom boundary alignment
    if room.origin.y == boundary.origin.y:
        windows.append(
            Opening(
                type="window",
                width=window_width,
                position=Point(x=room.origin.x + room.width / 2, y=room.origin.y),
                orientation="horizontal",
            )
        )

    # Check top boundary alignment
    if room.origin.y + room.height == boundary.origin.y + boundary.height:
        windows.append(
            Opening(
                type="window",
                width=window_width,
                position=Point(
                    x=room.origin.x + room.width / 2, y=room.origin.y + room.height
                ),
                orientation="horizontal",
            )
        )

    return windows
