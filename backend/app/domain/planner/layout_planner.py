"""
Simple layout planner using cursor-based placement.

This module provides a basic layout planner that places rooms sequentially
in a grid pattern, wrapping to the next row when the current row is full.
"""

from app.schemas.room import Room
from app.schemas.geometry import Point


class LayoutPlanner:
    """
    Simple cursor-based layout planner.
    
    Places rooms sequentially from left to right, top to bottom,
    wrapping to the next row when the boundary width is exceeded.
    """

    def __init__(self, boundary_width: float, boundary_height: float):
        """
        Initialize layout planner with boundary dimensions.
        
        Args:
            boundary_width: Maximum width of the layout area.
            boundary_height: Maximum height of the layout area.
        """
        self.boundary_width = boundary_width
        self.boundary_height = boundary_height
        self.cursor_x = 0
        self.cursor_y = 0

    def place_room(self, room: Room) -> Room:
        """
        Place a room at the current cursor position.
        
        Automatically wraps to the next row if room doesn't fit in current row.
        
        Args:
            room: Room to place.
        
        Returns:
            Room with origin set to cursor position.
        """
        # Wrap to next row if room doesn't fit
        if self.cursor_x + room.width > self.boundary_width:
            self.cursor_x = 0
            self.cursor_y += room.height

        room.origin = Point(x=self.cursor_x, y=self.cursor_y)

        # Advance cursor for next room
        self.cursor_x += room.width
        return room
