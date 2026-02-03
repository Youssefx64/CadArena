from app.domain.constraints.base import Constraint
from app.schemas.room import Room


class OverlapConstraint(Constraint):

    def is_valid(self, room: Room, other_rooms: list[Room]) -> bool:
        if room.origin is None:
            return False

        for other in other_rooms:
            if other.origin is None:
                continue

            if self._overlaps(room, other):
                return False

        return True

    def _overlaps(self, a: Room, b: Room) -> bool:
        return not (
            a.origin.x + a.width <= b.origin.x
            or a.origin.x >= b.origin.x + b.width
            or a.origin.y + a.height <= b.origin.y
            or a.origin.y >= b.origin.y + b.height
        )
