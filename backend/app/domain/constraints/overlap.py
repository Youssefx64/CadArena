"""
Overlap constraint validator.

This module provides a constraint that prevents rooms from overlapping
with each other.
"""

from app.domain.constraints.base import Constraint
from app.schemas.room import Room


class OverlapConstraint(Constraint):
    """
    Constraint preventing room overlaps.
    
    Ensures that a room does not overlap with any previously placed rooms.
    Rooms can share walls (touch) but cannot have overlapping interiors.
    """

    def is_valid(self, room: Room, other_rooms: list[Room]) -> bool:
        """
        Check if room overlaps with any other rooms.
        
        Args:
            room: Room to validate.
            other_rooms: List of already placed rooms to check against.
        
        Returns:
            True if no overlaps, False if room overlaps with any other room.
            Also returns False if room has no origin (not placed).
        """
        if room.origin is None:
            return False

        for other in other_rooms:
            if other.origin is None:
                continue

            if self._overlaps(room, other):
                return False

        return True

    def _overlaps(self, a: Room, b: Room) -> bool:
        """
        Check if two rooms overlap.
        
        Uses axis-aligned bounding box (AABB) collision detection.
        Rooms that only touch (share edges) are not considered overlapping.
        
        Args:
            a: First room.
            b: Second room.
        
        Returns:
            True if rooms overlap, False if they are separate or only touch.
        """
        # Check if rectangles are separated (no overlap)
        return not (
            a.origin.x + a.width <= b.origin.x
            or a.origin.x >= b.origin.x + b.width
            or a.origin.y + a.height <= b.origin.y
            or a.origin.y >= b.origin.y + b.height
        )
