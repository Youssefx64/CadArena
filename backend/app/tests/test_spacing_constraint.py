from app.domain.constraints.spacing import SpacingConstraint
from app.domain.entities import Point2D, Room


def test_spacing_constraint_accepts_sufficient_gap() -> None:
    spacing = SpacingConstraint(min_spacing=0.5)
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
        origin=Point2D(x=10.6, y=0.0),
    )

    assert spacing.is_valid(candidate, [base]) is True


def test_spacing_constraint_rejects_insufficient_gap() -> None:
    spacing = SpacingConstraint(min_spacing=0.5)
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
        origin=Point2D(x=10.1, y=0.0),
    )

    assert spacing.is_valid(candidate, [base]) is False
