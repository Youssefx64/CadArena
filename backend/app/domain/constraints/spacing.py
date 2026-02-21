"""
Spacing constraint validator.

This module provides a constraint that ensures minimum spacing between rooms,
while allowing rooms to share walls or touch at corners.
"""

from app.domain.constraints.base import Constraint
from app.domain.entities import Room
from app.domain.planner.config import MIN_SPACING


class SpacingConstraint(Constraint):
    """
    Constraint ensuring minimum spacing between rooms.
    
    Allows rooms to share walls or touch at corners, but requires minimum
    spacing on at least one axis (horizontal or vertical) if rooms are separated.
    """

    def __init__(self, min_spacing: float = MIN_SPACING):
        """
        Initialize spacing constraint.
        
        Args:
            min_spacing: Minimum required spacing in meters. Defaults to PlannerConfig.MIN_SPACING.
        """
        self.min_spacing = min_spacing

    def is_valid(self, room: Room, other_rooms: list[Room]) -> bool:
        """
        Check if room has minimum spacing from all other rooms.
        
        Args:
            room: Room to validate.
            other_rooms: List of already placed rooms to check against.
        
        Returns:
            True if spacing requirements are met, False otherwise.
            Also returns False if room has no origin (not placed).
        """
        if room.origin is None:
            return False

        for other in other_rooms:
            if other.origin is None:
                continue

            if not self._has_min_spacing(room, other):
                return False

        return True

    def _has_min_spacing(self, a: Room, b: Room) -> bool:
        """
        Check if two rooms have minimum spacing.
        
        Calculates horizontal and vertical gaps. If rooms share walls or touch
        (both gaps are 0), spacing is satisfied. Otherwise, at least one axis
        must have the minimum spacing.
        
        Args:
            a: First room.
            b: Second room.
        
        Returns:
            True if spacing requirement is met, False otherwise.
        """
        # Calculate bounding boxes
        a_left = a.origin.x
        a_right = a_left + a.width
        a_bottom = a.origin.y
        a_top = a_bottom + a.height

        b_left = b.origin.x
        b_right = b_left + b.width
        b_bottom = b.origin.y
        b_top = b_bottom + b.height

        # Calculate gaps (0 if overlapping or touching)
        horizontal_gap = max(b_left - a_right, a_left - b_right, 0)

        vertical_gap = max(b_bottom - a_top, a_bottom - b_top, 0)

        # Allow shared walls or touching corners; overlap is handled separately
        if horizontal_gap == 0 and vertical_gap == 0:
            return True

        # At least one axis must satisfy spacing
        return horizontal_gap >= self.min_spacing or vertical_gap >= self.min_spacing
