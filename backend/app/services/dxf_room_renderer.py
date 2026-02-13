import ezdxf
from pathlib import Path
from app.schemas.geometry import Point
from app.core.file_utils import generate_dxf_filename
from app.domain.architecture.door_geometry import DoorGeometry


class DXFRoomRenderer:
    """
    Professional CAD renderer with standard architectural door representation.
    
    This class provides methods to render complete floor plans including:
    - Boundary walls
    - Interior walls with thickness
    - Doors with swing arcs
    - Windows
    - Room labels and dimensions
    - Stair representations
    """

    def __init__(self):
        """
        Initialize DXF document and create standard layers.
        
        Creates a new DXF document (R2018 format) and sets up layers
        for different architectural elements with appropriate colors.
        """
        self.doc = ezdxf.new("R2018")
        self.msp = self.doc.modelspace()
        # Create standard layers with colors
        self._ensure_layer("BOUNDARY", color=7)
        self._ensure_layer("WALLS", color=7)
        self._ensure_layer("DOORS", color=1)
        self._ensure_layer("WINDOWS", color=5)
        self._ensure_layer("ROOM_TEXT", color=2)
        self._ensure_layer("DIMENSIONS", color=3)
        self._ensure_layer("STAIRS", color=4)

    def draw_boundary(self, points: list[Point]):
        if len(points) < 2:
            return
        self.msp.add_lwpolyline(
            [(p.x, p.y) for p in points],
            close=True,
            dxfattribs={"layer": "BOUNDARY"},
        )

    def draw_wall_segments(self, segments: list[tuple[Point, Point]]):
        self.draw_line_segments(segments, layer="WALLS")

    def draw_boundary_segments(self, segments: list[tuple[Point, Point]]):
        self.draw_line_segments(segments, layer="BOUNDARY")

    def draw_line_segments(
        self,
        segments: list[tuple[Point, Point]],
        layer: str,
        lineweight: int | None = None,
    ):
        for start, end in segments:
            dxfattribs = {"layer": layer}
            if lineweight is not None:
                dxfattribs["lineweight"] = lineweight
            self.msp.add_line(
                (start.x, start.y),
                (end.x, end.y),
                dxfattribs=dxfattribs,
            )

    def draw_door_geometry(self, door_geom: DoorGeometry):
        """
        Draw door leaf line and swing arc.
        
        Args:
            door_geom: Door geometry containing all rendering coordinates.
        """
        # Draw door leaf (line from hinge to end)
        self.msp.add_line(
            (door_geom.hinge_point.x, door_geom.hinge_point.y),
            (door_geom.leaf_end_point.x, door_geom.leaf_end_point.y),
            dxfattribs={
                "layer": "DOORS",
                "lineweight": 35
            }
        )

        # Draw swing arc (door opening path)
        self.msp.add_arc(
            center=(door_geom.swing_center.x, door_geom.swing_center.y),
            radius=door_geom.swing_radius,
            start_angle=door_geom.swing_start_angle,
            end_angle=door_geom.swing_end_angle,
            dxfattribs={"layer": "DOORS"}
        )

    def draw_window_segment(self, start: Point, end: Point):
        self.msp.add_line(
            (start.x, start.y),
            (end.x, end.y),
            dxfattribs={
                "layer": "WINDOWS",
                "lineweight": 25
            }
        )

    def draw_room_label(self, text: str, position: Point):
        self.msp.add_mtext(
            text,
            dxfattribs={
                "layer": "ROOM_TEXT",
                "char_height": 0.5,
                "insert": (position.x, position.y),
                "attachment_point": 5
            }
        )

    def draw_room_dimensions(self, text: str, position: Point):
        self.msp.add_mtext(
            text,
            dxfattribs={
                "layer": "DIMENSIONS",
                "char_height": 0.35,
                "insert": (position.x, position.y),
                "attachment_point": 5
            }
        )

    def draw_stair_lines(self, segments: list[tuple[Point, Point]]):
        self.draw_line_segments(segments, layer="STAIRS")

    def save(self) -> Path:
        """
        Save DXF file with generated filename.
        
        Returns:
            Path to the saved DXF file.
        """
        file_path = generate_dxf_filename(prefix="layout")
        self.doc.saveas(file_path)
        return file_path

    def _ensure_layer(self, name: str, color: int | None = None):
        """
        Create DXF layer if it doesn't exist.
        
        Args:
            name: Layer name.
            color: Optional layer color (DXF color index).
        """
        if name not in self.doc.layers:
            layer = self.doc.layers.new(name)
            if color is not None:
                layer.color = color
