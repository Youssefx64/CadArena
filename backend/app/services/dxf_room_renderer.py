import ezdxf
from pathlib import Path
from app.schemas.room import Room
from app.schemas.geometry import RectangleGeometry, Point
from app.core.file_utils import generate_dxf_filename
from app.domain.architecture.wall import WallSegment
from app.domain.architecture.door_geometry import DoorGeometry


class DXFRoomRenderer:
    """
    Professional CAD renderer with standard architectural door representation.
    """

    def __init__(self):
        self.doc = ezdxf.new("R2018")
        self.msp = self.doc.modelspace()
        self.wall_thickness = 0.15
        
        self._ensure_layer("BOUNDARY", color=7)
        self._ensure_layer("WALLS", color=7)
        self._ensure_layer("DOORS", color=1)
        self._ensure_layer("WINDOWS", color=5)
        self._ensure_layer("ROOM_TEXT", color=2)
        self._ensure_layer("DIMENSIONS", color=3)
        self._ensure_layer("STAIRS", color=4)

    def draw_boundary(self, boundary: RectangleGeometry):
        """Draw outer boundary."""
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

    def draw_wall_segment(self, segment: WallSegment):
        """Draw wall as two parallel lines."""
        self._draw_thick_segment(segment, layer="WALLS", thickness=self.wall_thickness)

    def draw_wall_segments(self, segments: list[WallSegment]):
        """Draw all wall segments."""
        for segment in segments:
            self.draw_wall_segment(segment)

    def draw_boundary_segments(self, segments: list[WallSegment]):
        """Draw boundary segments as two parallel lines."""
        for segment in segments:
            self._draw_thick_segment(segment, layer="BOUNDARY", thickness=self.wall_thickness)

    def _draw_thick_segment(self, segment: WallSegment, layer: str, thickness: float):
        length = segment.length()
        if length < 0.01:
            return

        dx = segment.end.x - segment.start.x
        dy = segment.end.y - segment.start.y

        ux = dx / length
        uy = dy / length

        px = -uy
        py = ux

        offset_x = px * thickness / 2
        offset_y = py * thickness / 2

        self.msp.add_line(
            (
                segment.start.x + offset_x,
                segment.start.y + offset_y
            ),
            (
                segment.end.x + offset_x,
                segment.end.y + offset_y
            ),
            dxfattribs={"layer": layer}
        )

        self.msp.add_line(
            (
                segment.start.x - offset_x,
                segment.start.y - offset_y
            ),
            (
                segment.end.x - offset_x,
                segment.end.y - offset_y
            ),
            dxfattribs={"layer": layer}
        )

    def draw_door_geometry(self, door_geom: DoorGeometry):
        """Draw door leaf line and swing arc."""
        self.msp.add_line(
            (door_geom.hinge_point.x, door_geom.hinge_point.y),
            (door_geom.leaf_end_point.x, door_geom.leaf_end_point.y),
            dxfattribs={
                "layer": "DOORS",
                "lineweight": 35
            }
        )

        self.msp.add_arc(
            center=(door_geom.swing_center.x, door_geom.swing_center.y),
            radius=door_geom.swing_radius,
            start_angle=door_geom.swing_start_angle,
            end_angle=door_geom.swing_end_angle,
            dxfattribs={"layer": "DOORS"}
        )

    def draw_window_segment(self, start: Point, end: Point):
        """Draw a simple window line within a wall opening."""
        self.msp.add_line(
            (start.x, start.y),
            (end.x, end.y),
            dxfattribs={
                "layer": "WINDOWS",
                "lineweight": 25
            }
        )

    def draw_room_label(self, room: Room):
        """Draw room name."""
        if room.origin is None:
            return
            
        cx = room.origin.x + room.width / 2
        cy = room.origin.y + room.height / 2

        self.msp.add_mtext(
            room.name,
            dxfattribs={
                "layer": "ROOM_TEXT",
                "char_height": 0.5,
                "insert": (cx, cy + 0.3),
                "attachment_point": 5
            }
        )

    def draw_room_dimensions(self, room: Room):
        """Draw room dimensions."""
        if room.origin is None:
            return
            
        cx = room.origin.x + room.width / 2
        cy = room.origin.y + room.height / 2

        text = f"{room.width}m x {room.height}m"

        self.msp.add_mtext(
            text,
            dxfattribs={
                "layer": "DIMENSIONS",
                "char_height": 0.35,
                "insert": (cx, cy - 0.3),
                "attachment_point": 5
            }
        )

    def draw_stairs(self, origin: Point, width: float, height: float, steps: int = 8):
        """Draw simple stair treads inside a rectangle."""
        if steps < 2:
            steps = 2

        if height >= width:
            step_depth = height / steps
            for i in range(1, steps):
                y = origin.y + i * step_depth
                self.msp.add_line(
                    (origin.x, y),
                    (origin.x + width, y),
                    dxfattribs={"layer": "STAIRS"}
                )
        else:
            step_width = width / steps
            for i in range(1, steps):
                x = origin.x + i * step_width
                self.msp.add_line(
                    (x, origin.y),
                    (x, origin.y + height),
                    dxfattribs={"layer": "STAIRS"}
                )

    def save(self) -> Path:
        """Save DXF file."""
        file_path = generate_dxf_filename(prefix="layout")
        self.doc.saveas(file_path)
        return file_path

    def _ensure_layer(self, name: str, color: int | None = None):
        """Create layer if doesn't exist."""
        if name not in self.doc.layers:
            layer = self.doc.layers.new(name)
            if color is not None:
                layer.color = color
