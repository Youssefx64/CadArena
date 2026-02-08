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
        self.wall_thickness = 0.15
        
        # Create standard layers with colors
        self._ensure_layer("BOUNDARY", color=7)
        self._ensure_layer("WALLS", color=7)
        self._ensure_layer("DOORS", color=1)
        self._ensure_layer("WINDOWS", color=5)
        self._ensure_layer("ROOM_TEXT", color=2)
        self._ensure_layer("DIMENSIONS", color=3)
        self._ensure_layer("STAIRS", color=4)

    def draw_boundary(self, boundary: RectangleGeometry):
        """
        Draw outer boundary as a closed polyline.
        
        Args:
            boundary: Rectangle geometry defining the building boundary.
        """
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
        """
        Draw a single wall segment as two parallel lines.
        
        Args:
            segment: Wall segment to draw.
        """
        self._draw_thick_segment(segment, layer="WALLS", thickness=self.wall_thickness)

    def draw_wall_segments(self, segments: list[WallSegment]):
        """
        Draw multiple wall segments.
        
        Args:
            segments: List of wall segments to draw.
        """
        for segment in segments:
            self.draw_wall_segment(segment)

    def draw_boundary_segments(self, segments: list[WallSegment]):
        """
        Draw boundary wall segments as two parallel lines.
        
        Args:
            segments: List of boundary wall segments to draw.
        """
        for segment in segments:
            self._draw_thick_segment(segment, layer="BOUNDARY", thickness=self.wall_thickness)

    def _draw_thick_segment(self, segment: WallSegment, layer: str, thickness: float):
        """
        Draw a wall segment as two parallel lines representing wall thickness.
        
        Calculates perpendicular offset to create two parallel lines
        representing the wall edges.
        
        Args:
            segment: Wall segment to draw.
            layer: DXF layer name.
            thickness: Wall thickness in meters.
        """
        length = segment.length()
        if length < 0.01:
            return

        # Calculate unit vector along wall direction
        dx = segment.end.x - segment.start.x
        dy = segment.end.y - segment.start.y

        ux = dx / length
        uy = dy / length

        # Calculate perpendicular vector (90-degree rotation)
        px = -uy
        py = ux

        # Calculate offset for parallel lines
        offset_x = px * thickness / 2
        offset_y = py * thickness / 2

        # Draw first parallel line (one side of wall)
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

        # Draw second parallel line (other side of wall)
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
        """
        Draw a simple window line within a wall opening.
        
        Args:
            start: Window start point.
            end: Window end point.
        """
        self.msp.add_line(
            (start.x, start.y),
            (end.x, end.y),
            dxfattribs={
                "layer": "WINDOWS",
                "lineweight": 25
            }
        )

    def draw_room_label(self, room: Room):
        """
        Draw room name label at room center.
        
        Args:
            room: Room to label.
        """
        if room.origin is None:
            return
            
        # Calculate room center
        cx = room.origin.x + room.width / 2
        cy = room.origin.y + room.height / 2

        self.msp.add_mtext(
            room.name,
            dxfattribs={
                "layer": "ROOM_TEXT",
                "char_height": 0.5,
                "insert": (cx, cy + 0.3),
                "attachment_point": 5  # Center alignment
            }
        )

    def draw_room_dimensions(self, room: Room):
        """
        Draw room dimensions text below room label.
        
        Args:
            room: Room to dimension.
        """
        if room.origin is None:
            return
            
        # Calculate room center
        cx = room.origin.x + room.width / 2
        cy = room.origin.y + room.height / 2

        text = f"{room.width}m x {room.height}m"

        self.msp.add_mtext(
            text,
            dxfattribs={
                "layer": "DIMENSIONS",
                "char_height": 0.35,
                "insert": (cx, cy - 0.3),
                "attachment_point": 5  # Center alignment
            }
        )

    def draw_stairs(self, origin: Point, width: float, height: float, steps: int = 8):
        """
        Draw simple stair treads inside a rectangle.
        
        Draws parallel lines representing stair treads. Orientation
        (horizontal or vertical) depends on room dimensions.
        
        Args:
            origin: Bottom-left corner of stairs rectangle.
            width: Stairs width in meters.
            height: Stairs height in meters.
            steps: Number of steps to draw. Defaults to 8.
        """
        if steps < 2:
            steps = 2

        # Vertical stairs (taller than wide)
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
            # Horizontal stairs (wider than tall)
            step_width = width / steps
            for i in range(1, steps):
                x = origin.x + i * step_width
                self.msp.add_line(
                    (x, origin.y),
                    (x, origin.y + height),
                    dxfattribs={"layer": "STAIRS"}
                )

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
