from app.domain.constraints.base import Constraint
from app.schemas.room import Room
from app.schemas.geometry import RectangleGeometry


class BoundaryConstraint(Constraint):

    def is_valid(self, room: Room, boundary: RectangleGeometry) -> bool:
        if room.origin is None:
            return False

        room_left = room.origin.x
        room_bottom = room.origin.y
        room_right = room_left + room.width
        room_top = room_bottom + room.height

        boundary_left = boundary.origin.x
        boundary_bottom = boundary.origin.y
        boundary_right = boundary_left + boundary.width
        boundary_top = boundary_bottom + boundary.height

        return (
            room_left >= boundary_left
            and room_bottom >= boundary_bottom
            and room_right <= boundary_right
            and room_top <= boundary_top
        )
