import ezdxf
from pathlib import Path
from app.schemas.room import Room
from app.schemas.geometry import RectangleGeometry
from app.core.file_utils import generate_dxf_filename
import math

class DXFRoomRenderer:
    """
    Fast DXF renderer for rooms and boundary.
    """

    def __init__(self):
        self.doc = ezdxf.new("R2018")
        self.msp = self.doc.modelspace()
        
        self._ensure_layer("WALLS", color=7)        # white
        self._ensure_layer("DOORS", color=1)        # red
        self._ensure_layer("WINDOWS", color=4)      # cyan
        self._ensure_layer("ROOM_TEXT", color=2)    # yellow
        self._ensure_layer("DIMENSIONS", color=3)   # green


    def draw_boundary(self, boundary: RectangleGeometry):
        self._ensure_layer("BOUNDARY")

        self.msp.add_lwpolyline(
            [
                (boundary.origin.x, boundary.origin.y),
                (boundary.origin.x + boundary.width, boundary.origin.y),
                (boundary.origin.x + boundary.width, boundary.origin.y + boundary.height),
                (boundary.origin.x, boundary.origin.y + boundary.height),
            ],
            close=True,
            dxfattribs={"layer": "BOUNDARY"}
        )

    def draw_room(self, room: Room):
        self._ensure_layer(room.layer)

        x = room.origin.x
        y = room.origin.y

        self.msp.add_lwpolyline(
            [
                (x, y),
                (x + room.width, y),
                (x + room.width, y + room.height),
                (x, y + room.height),
            ],
            close=True,
            dxfattribs={"layer": room.layer}
        )

    def save(self) -> Path:
        file_path = generate_dxf_filename(prefix="layout")
        self.doc.saveas(file_path)
        return file_path

    def _ensure_layer(self, name: str, color: int | None = None):
        if name not in self.doc.layers:
            layer = self.doc.layers.new(name)
            if color is not None:
                layer.color = color

    def draw_room_label(self, room: Room):
        self._ensure_layer("ROOM_TEXT")

        cx = room.origin.x + room.width / 2
        cy = room.origin.y + room.height / 2

        self.msp.add_mtext(
            room.name,
            dxfattribs={
                "layer": "ROOM_TEXT",
                "char_height": 0.7,          # bigger
                "insert": (cx, cy + 0.4),    # push UP a bit
                "attachment_point": 5        # middle center
            }
        )

    def draw_room_dimensions(self, room: Room):
        self._ensure_layer("DIMENSIONS")

        cx = room.origin.x + room.width / 2
        cy = room.origin.y + room.height / 2

        text = f"{room.width}m x {room.height}m"

        self.msp.add_mtext(
            text,
            dxfattribs={
                "layer": "DIMENSIONS",
                "char_height": 0.45,         # smaller
                "insert": (cx, cy - 0.4),    # push DOWN a bit
                "attachment_point": 5        # middle center
            }
        )
        
    def draw_door(self, opening):
        self._ensure_layer("DOORS")

        x = opening.position.x
        y = opening.position.y
        w = opening.width

        # Door leaf (line)
        if opening.orientation == "horizontal":
            self.msp.add_line(
                (x, y),
                (x + w, y),
                dxfattribs={"layer": "DOORS"}
            )

            # Swing arc
            self.msp.add_arc(
                center=(x, y),
                radius=w,
                start_angle=0,
                end_angle=90,
                dxfattribs={"layer": "DOORS"}
            )

        else:  # vertical
            self.msp.add_line(
                (x, y),
                (x, y + w),
                dxfattribs={"layer": "DOORS"}
            )

            self.msp.add_arc(
                center=(x, y),
                radius=w,
                start_angle=90,
                end_angle=180,
                dxfattribs={"layer": "DOORS"}
            )
        
    def draw_window(self, opening):
        self._ensure_layer("WINDOWS")

        x = opening.position.x
        y = opening.position.y
        w = opening.width
        offset = 0.1

        self.msp.add_line(
            (x - w / 2, y - offset),
            (x + w / 2, y - offset),
            dxfattribs={"layer": "WINDOWS", "color": 5}
        )

    def draw_room_walls(self, room):
        self._ensure_layer("WALLS")

        t = 0.2  # wall thickness
        x = room.origin.x
        y = room.origin.y
        w = room.width
        h = room.height

        # Outer wall
        self.msp.add_lwpolyline(
            [
                (x, y),
                (x + w, y),
                (x + w, y + h),
                (x, y + h),
            ],
            close=True,
            dxfattribs={"layer": "WALLS"}
        )

        # Inner wall (offset inward)
        self.msp.add_lwpolyline(
            [
                (x + t, y + t),
                (x + w - t, y + t),
                (x + w - t, y + h - t),
                (x + t, y + h - t),
            ],
            close=True,
            dxfattribs={"layer": "WALLS"}
        )
