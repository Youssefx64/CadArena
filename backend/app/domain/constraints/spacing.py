from app.domain.constraints.base import Constraint
from app.schemas.room import Room
from app.core.config import PlannerConfig


class SpacingConstraint(Constraint):

    def __init__(self, min_spacing: float = PlannerConfig.MIN_SPACING):
        self.min_spacing = min_spacing

    def is_valid(self, room: Room, other_rooms: list[Room]) -> bool:
        if room.origin is None:
            return False

        for other in other_rooms:
            if other.origin is None:
                continue

            if not self._has_min_spacing(room, other):
                return False

        return True

    def _has_min_spacing(self, a: Room, b: Room) -> bool:
        a_left = a.origin.x
        a_right = a_left + a.width
        a_bottom = a.origin.y
        a_top = a_bottom + a.height

        b_left = b.origin.x
        b_right = b_left + b.width
        b_bottom = b.origin.y
        b_top = b_bottom + b.height

        # Calculate gaps
        horizontal_gap = max(
            b_left - a_right,
            a_left - b_right,
            0
        )

        vertical_gap = max(
            b_bottom - a_top,
            a_bottom - b_top,
            0
        )

        # If overlapping in both axes → invalid
        if horizontal_gap == 0 and vertical_gap == 0:
            return False

        # At least one axis must satisfy spacing
        return (
            horizontal_gap >= self.min_spacing or
            vertical_gap >= self.min_spacing
        )

