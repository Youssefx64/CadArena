from app.schemas.room import Room
from app.schemas.opening import Opening
from app.schemas.geometry import Point


def auto_place_door(room: Room) -> Opening:
    door_width = 1.0
    margin = 0.3

    # Try bottom side
    x = room.origin.x + (room.width - door_width) / 2
    y = room.origin.y + margin

    return Opening(
        type="door",
        width=door_width,
        position=Point(x=x, y=y),
        orientation="horizontal"
    )
