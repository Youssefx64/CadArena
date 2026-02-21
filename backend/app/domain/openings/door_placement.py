"""
Door placement strategies.

This module provides various strategies for placing doors in rooms,
including inside placement and user preference-based placement.
"""

from app.domain.entities import Room
from app.domain.entities import RectangleGeometry, Point
from app.domain.entities import Opening


def place_door_inside_room(room: Room) -> Opening:
    """
    Place door slightly inside the room for guaranteed visibility.
    
    Places door near the bottom-left corner with a small offset from edges.
    This ensures the door is always visible even if wall rendering is imprecise.
    
    Args:
        room: Room to place door in.
    
    Returns:
        Opening specification for the placed door.
    """
    door_width = 1.0
    offset = 0.3  # push inside room

    x = room.origin.x + offset
    y = room.origin.y + offset

    return Opening(
        type="door",
        width=door_width,
        position=Point(x=x, y=y),
        orientation="horizontal",
    )


def place_door_with_user_preference(room: Room, intent) -> Opening:
    """
    Place door based on user preferences from design intent.
    
    Uses intent specifications for wall side, offset, and width.
    Falls back to inside placement if wall preference is not recognized.
    
    Args:
        room: Room to place door in.
        intent: Opening intent with user preferences.
    
    Returns:
        Opening specification for the placed door.
    """
    door_width = intent.width
    offset = intent.offset or (room.width / 2)

    if intent.wall == "left":
        return Opening(
            type="door",
            width=door_width,
            position=Point(x=room.origin.x, y=room.origin.y + offset),
            orientation="vertical",
        )

    if intent.wall == "bottom":
        return Opening(
            type="door",
            width=door_width,
            position=Point(x=room.origin.x + offset, y=room.origin.y),
            orientation="horizontal",
        )

    # fallback to inside placement
    return place_door_inside_room(room)
