"""
Boundary constraint validator.

This module provides a constraint that ensures rooms are placed entirely
within the building boundary.
"""

from app.domain.constraints.base import Constraint
from app.schemas.room import Room
from app.schemas.geometry import RectangleGeometry


class BoundaryConstraint(Constraint):
    """
    Constraint ensuring rooms are within the building boundary.
    
    Validates that a room's bounding box is completely contained within
    the boundary rectangle.
    """

    def is_valid(self, room: Room, boundary: RectangleGeometry) -> bool:
        """
        Check if room is entirely within the boundary.
        
        Args:
            room: Room to validate.
            boundary: Building boundary rectangle.
        
        Returns:
            True if room is within boundary, False otherwise.
            Also returns False if room has no origin (not placed).
        """
        if room.origin is None:
            return False

        # Calculate room bounding box
        room_left = room.origin.x
        room_bottom = room.origin.y
        room_right = room_left + room.width
        room_top = room_bottom + room.height

        # Calculate boundary bounding box
        boundary_left = boundary.origin.x
        boundary_bottom = boundary.origin.y
        boundary_right = boundary_left + boundary.width
        boundary_top = boundary_bottom + boundary.height

        # Check all corners are within boundary
        return (
            room_left >= boundary_left
            and room_bottom >= boundary_bottom
            and room_right <= boundary_right
            and room_top <= boundary_top
        )
