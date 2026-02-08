"""
Door geometry computation.

This module provides functions to calculate the geometric elements
needed to render a door in a DXF drawing, including hinge point,
door leaf, and swing arc.
"""

from app.domain.architecture.opening import DoorPlacement
from app.schemas.geometry import Point
import math


class DoorGeometry:
    """
    Represents the geometric elements needed to draw a door.
    
    Contains all coordinates and angles required to render a door
    with its swing arc in a DXF drawing.
    
    Attributes:
        hinge_point: Point where door is hinged (on wall).
        leaf_end_point: End point of door leaf when open.
        swing_center: Center point for swing arc (same as hinge_point).
        swing_radius: Radius of swing arc (door width).
        swing_start_angle: Starting angle of swing arc in degrees.
        swing_end_angle: Ending angle of swing arc in degrees.
    """
    def __init__(
        self,
        hinge_point: Point,
        leaf_end_point: Point,
        swing_center: Point,
        swing_radius: float,
        swing_start_angle: float,
        swing_end_angle: float
    ):
        """
        Initialize door geometry.
        
        Args:
            hinge_point: Hinge point on wall.
            leaf_end_point: Door leaf end point.
            swing_center: Swing arc center.
            swing_radius: Swing arc radius.
            swing_start_angle: Swing start angle in degrees.
            swing_end_angle: Swing end angle in degrees.
        """
        self.hinge_point = hinge_point
        self.leaf_end_point = leaf_end_point
        self.swing_center = swing_center
        self.swing_radius = swing_radius
        self.swing_start_angle = swing_start_angle
        self.swing_end_angle = swing_end_angle


def compute_door_geometry(placement: DoorPlacement) -> DoorGeometry:
    """
    Calculate the exact geometry for rendering a door.
    
    Computes hinge point, door leaf end point, and swing arc parameters
    based on wall orientation, door placement, and door specifications
    (hinge side, swing direction, opening angle).
    
    Args:
        placement: DoorPlacement containing wall and door specification.
    
    Returns:
        DoorGeometry with all rendering coordinates and angles.
    
    Raises:
        ValueError: If wall segment is too short for door placement.
    """
    wall = placement.wall
    door = placement.door
    offset = placement.offset
    
    wall_length = wall.length()
    if wall_length < 0.001:
        raise ValueError("Wall segment too short for door placement")

    # Calculate unit vector along wall direction
    dx = wall.end.x - wall.start.x
    dy = wall.end.y - wall.start.y

    ux = dx / wall_length
    uy = dy / wall_length

    # Determine hinge position based on hinge side
    if door.hinge == "right":
        hinge_offset = offset + door.width
        closed_dir_x = -ux
        closed_dir_y = -uy
    else:
        hinge_offset = offset
        closed_dir_x = ux
        closed_dir_y = uy

    hinge_point = Point(
        x=wall.start.x + ux * hinge_offset,
        y=wall.start.y + uy * hinge_offset
    )

    # Calculate interior normal (perpendicular pointing into room)
    interior_nx = -uy
    interior_ny = ux

    # Calculate two possible swing directions (CCW and CW)
    swing_rad = math.radians(door.angle)
    cos_a = math.cos(swing_rad)
    sin_a = math.sin(swing_rad)

    open_ccw_x = closed_dir_x * cos_a - closed_dir_y * sin_a
    open_ccw_y = closed_dir_x * sin_a + closed_dir_y * cos_a

    open_cw_x = closed_dir_x * cos_a + closed_dir_y * sin_a
    open_cw_y = -closed_dir_x * sin_a + closed_dir_y * cos_a

    # Choose swing direction based on interior normal and swing preference
    dot_ccw = open_ccw_x * interior_nx + open_ccw_y * interior_ny
    dot_cw = open_cw_x * interior_nx + open_cw_y * interior_ny

    if door.swing == "in":
        use_ccw = dot_ccw >= dot_cw
    else:
        use_ccw = dot_ccw < dot_cw

    if use_ccw:
        open_dir_x, open_dir_y = open_ccw_x, open_ccw_y
    else:
        open_dir_x, open_dir_y = open_cw_x, open_cw_y

    # Calculate door leaf end point
    leaf_end_point = Point(
        x=hinge_point.x + open_dir_x * door.width,
        y=hinge_point.y + open_dir_y * door.width
    )

    def _normalize_angle(deg: float) -> float:
        """Normalize angle to 0-360 range."""
        normalized = deg % 360
        if normalized < 0:
            normalized += 360
        return normalized

    # Calculate swing arc angles
    closed_angle = _normalize_angle(math.degrees(math.atan2(closed_dir_y, closed_dir_x)))
    open_angle = _normalize_angle(math.degrees(math.atan2(open_dir_y, open_dir_x)))

    if use_ccw:
        swing_start_angle = closed_angle
        swing_end_angle = open_angle
    else:
        swing_start_angle = open_angle
        swing_end_angle = closed_angle

    return DoorGeometry(
        hinge_point=hinge_point,
        leaf_end_point=leaf_end_point,
        swing_center=hinge_point,
        swing_radius=door.width,
        swing_start_angle=swing_start_angle,
        swing_end_angle=swing_end_angle
    )
