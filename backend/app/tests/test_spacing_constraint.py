from app.schemas.room import Room
from app.schemas.geometry import Point
from app.domain.constraints.spacing import SpacingConstraint
from app.core.logging import get_logger

logger = get_logger("spacing-test")

def main():
    spacing = SpacingConstraint(min_spacing=0.5)

    room_a = Room(
        name="Living",
        room_type="living",
        width=10,
        height=8,
        origin=Point(x=0, y=0)
    )

    room_b = Room(
        name="Bedroom",
        room_type="bedroom",
        width=5,
        height=5,
        origin=Point(x=10.6, y=0)  # spacing OK
    )

    room_c = Room(
        name="Kitchen",
        room_type="kitchen",
        width=5,
        height=5,
        origin=Point(x=10.1, y=0)  # spacing too small
    )

    logger.info("A vs B spacing: %s", spacing.is_valid(room_b, [room_a]))
    logger.info("A vs C spacing: %s", spacing.is_valid(room_c, [room_a]))

if __name__ == "__main__":
    main()
