from app.schemas.room import Room
from app.schemas.geometry import RectangleGeometry, Point
from app.schemas.opening import Opening


def auto_place_windows(room: Room, boundary: RectangleGeometry) -> list[Opening]:
    """
    Place windows only if the room touches the external boundary.
    """

    windows: list[Opening] = []
    window_width = 1.2

    # Left boundary
    if room.origin.x == boundary.origin.x:
        windows.append(
            Opening(
                type="window",
                width=window_width,
                position=Point(
                    x=room.origin.x,
                    y=room.origin.y + room.height / 2
                ),
                orientation="vertical"
            )
        )

    # Right boundary
    if room.origin.x + room.width == boundary.origin.x + boundary.width:
        windows.append(
            Opening(
                type="window",
                width=window_width,
                position=Point(
                    x=room.origin.x + room.width,
                    y=room.origin.y + room.height / 2
                ),
                orientation="vertical"
            )
        )

    # Bottom boundary
    if room.origin.y == boundary.origin.y:
        windows.append(
            Opening(
                type="window",
                width=window_width,
                position=Point(
                    x=room.origin.x + room.width / 2,
                    y=room.origin.y
                ),
                orientation="horizontal"
            )
        )

    # Top boundary
    if room.origin.y + room.height == boundary.origin.y + boundary.height:
        windows.append(
            Opening(
                type="window",
                width=window_width,
                position=Point(
                    x=room.origin.x + room.width / 2,
                    y=room.origin.y + room.height
                ),
                orientation="horizontal"
            )
        )

    return windows
