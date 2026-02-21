from app.domain.constraints.overlap import OverlapConstraint
from app.domain.entities import Point2D, Room


def test_overlap_constraint_rejects_overlapping_rooms() -> None:
    constraint = OverlapConstraint()
    base = Room(
        name="Living",
        room_type="living",
        width=10.0,
        height=8.0,
        origin=Point2D(x=0.0, y=0.0),
    )
    candidate = Room(
        name="Bedroom",
        room_type="bedroom",
        width=5.0,
        height=5.0,
        origin=Point2D(x=5.0, y=3.0),
    )

    assert constraint.is_valid(candidate, [base]) is False


def test_overlap_constraint_accepts_non_overlapping_rooms() -> None:
    constraint = OverlapConstraint()
    base = Room(
        name="Living",
        room_type="living",
        width=10.0,
        height=8.0,
        origin=Point2D(x=0.0, y=0.0),
    )
    candidate = Room(
        name="Kitchen",
        room_type="kitchen",
        width=5.0,
        height=5.0,
        origin=Point2D(x=15.0, y=0.0),
    )

    assert constraint.is_valid(candidate, [base]) is True
