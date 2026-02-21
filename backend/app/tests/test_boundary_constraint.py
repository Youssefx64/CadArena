from app.domain.constraints.boundary import BoundaryConstraint
from app.domain.entities import Point2D, RectangleBoundary, Room


def test_boundary_constraint_accepts_room_inside_boundary() -> None:
    boundary = RectangleBoundary(width=30.0, height=50.0, origin=Point2D(x=0.0, y=0.0))
    room = Room(
        name="Living",
        room_type="living",
        width=10.0,
        height=8.0,
        origin=Point2D(x=5.0, y=5.0),
    )

    assert BoundaryConstraint().is_valid(room, boundary) is True


def test_boundary_constraint_rejects_room_outside_boundary() -> None:
    boundary = RectangleBoundary(width=30.0, height=50.0, origin=Point2D(x=0.0, y=0.0))
    room = Room(
        name="Bedroom",
        room_type="bedroom",
        width=10.0,
        height=8.0,
        origin=Point2D(x=25.0, y=45.0),
    )

    assert BoundaryConstraint().is_valid(room, boundary) is False
