"""
Automatic door placement utilities.

This module provides functions for automatically placing doors in rooms
based on simple heuristics.
"""

from app.schemas.room import Room
from app.schemas.opening import Opening
from app.schemas.geometry import Point


def auto_place_door(room: Room) -> Opening:
    """
    Automatically place a door in a room.
    
    Places door on the bottom wall, centered horizontally, with a small
    margin from the bottom edge.
    
    Args:
        room: Room to place door in.
    
    Returns:
        Opening specification for the placed door.
    """
    door_width = 1.0
    margin = 0.3

    # Place on bottom side, centered
    x = room.origin.x + (room.width - door_width) / 2
    y = room.origin.y + margin

    return Opening(
        type="door",
        width=door_width,
        position=Point(x=x, y=y),
        orientation="horizontal",
    )
