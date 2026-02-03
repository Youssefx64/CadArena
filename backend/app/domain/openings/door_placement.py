from app.schemas.room import Room
from app.schemas.geometry import RectangleGeometry, Point
from app.schemas.opening import Opening


def place_door_inside_room(room: Room) -> Opening:
    """
    Guaranteed visible door:
    placed slightly inside the room.
    """

    door_width = 1.0
    offset = 0.3  # push inside room

    x = room.origin.x + offset
    y = room.origin.y + offset

    return Opening(
        type="door",
        width=door_width,
        position=Point(x=x, y=y),
        orientation="horizontal",
    )


def place_door_with_user_preference(room: Room, intent) -> Opening:
    door_width = intent.width
    offset = intent.offset or (room.width / 2)

    if intent.wall == "left":
        return Opening(
            type="door",
            width=door_width,
            position=Point(x=room.origin.x, y=room.origin.y + offset),
            orientation="vertical",
        )

    if intent.wall == "bottom":
        return Opening(
            type="door",
            width=door_width,
            position=Point(x=room.origin.x + offset, y=room.origin.y),
            orientation="horizontal",
        )

    # fallback
    return place_door_inside_room(room)
