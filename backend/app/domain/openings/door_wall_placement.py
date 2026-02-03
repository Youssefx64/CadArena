from app.schemas.room import Room
from app.domain.architecture.wall import WallSegment
from app.domain.architecture.opening import DoorPlacement
from app.domain.architecture.door import DoorSpec


def place_door_on_wall(
    wall: WallSegment,
    offset: float | None = None,
    door_width: float = 1.0
) -> DoorPlacement:
    """
    Place a door on a specific wall segment.
    """
    wall_length = wall.length()

    # Center door if no offset provided
    if offset is None:
        offset = (wall_length - door_width) / 2

    if offset < 0 or offset + door_width > wall_length:
        raise ValueError(
            f"Door (width={door_width}) does not fit on wall (length={wall_length})"
        )

    door = DoorSpec(
        width=door_width,
        hinge="left",
        swing="in",
        angle=90
    )

    return DoorPlacement(
        wall=wall,
        offset=offset,
        door=door
    )


def auto_place_door_on_room(
    room: Room,
    wall_segments: list[WallSegment]
) -> DoorPlacement:
    """
    Auto place ONE door on the bottom wall of the room.
    wall_segments order:
    [bottom, right, top, left]
    """
    bottom_wall = wall_segments[0]

    return place_door_on_wall(
        wall=bottom_wall,
        offset=None,     # centered
        door_width=1.0
    )
