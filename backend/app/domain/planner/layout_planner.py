from app.schemas.room import Room
from app.schemas.geometry import Point


class LayoutPlanner:

    def __init__(self, boundary_width: float, boundary_height: float):
        self.boundary_width = boundary_width
        self.boundary_height = boundary_height
        self.cursor_x = 0
        self.cursor_y = 0

    def place_room(self, room: Room) -> Room:
        if self.cursor_x + room.width > self.boundary_width:
            self.cursor_x = 0
            self.cursor_y += room.height

        room.origin = Point(x=self.cursor_x, y=self.cursor_y)

        self.cursor_x += room.width
        return room
