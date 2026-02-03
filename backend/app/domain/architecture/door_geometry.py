from app.domain.architecture.opening import DoorPlacement
from app.schemas.geometry import Point
import math


class DoorGeometry:
    """
    Represents the geometric elements needed to draw a door.
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
        self.hinge_point = hinge_point
        self.leaf_end_point = leaf_end_point
        self.swing_center = swing_center
        self.swing_radius = swing_radius
        self.swing_start_angle = swing_start_angle
        self.swing_end_angle = swing_end_angle


def compute_door_geometry(placement: DoorPlacement) -> DoorGeometry:
    """
    Calculate the exact geometry for rendering a door.
    
    Args:
        placement: DoorPlacement containing wall and door spec
    
    Returns:
        DoorGeometry with all rendering coordinates
    """
    wall = placement.wall
    door = placement.door
    offset = placement.offset
    
    wall_length = wall.length()
    if wall_length < 0.001:
        raise ValueError("Wall segment too short for door placement")

    dx = wall.end.x - wall.start.x
    dy = wall.end.y - wall.start.y

    # Unit vector along wall
    ux = dx / wall_length
    uy = dy / wall_length

    # Hinge placement along the wall opening
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

    # Swing direction: rotate closed direction by door angle
    swing_sign = 1 if door.swing == "in" else -1
    swing_rad = math.radians(door.angle) * swing_sign

    cos_a = math.cos(swing_rad)
    sin_a = math.sin(swing_rad)

    open_dir_x = closed_dir_x * cos_a - closed_dir_y * sin_a
    open_dir_y = closed_dir_x * sin_a + closed_dir_y * cos_a

    leaf_end_point = Point(
        x=hinge_point.x + open_dir_x * door.width,
        y=hinge_point.y + open_dir_y * door.width
    )

    def _normalize_angle(deg: float) -> float:
        normalized = deg % 360
        if normalized < 0:
            normalized += 360
        return normalized

    closed_angle = _normalize_angle(math.degrees(math.atan2(closed_dir_y, closed_dir_x)))
    open_angle = _normalize_angle(math.degrees(math.atan2(open_dir_y, open_dir_x)))

    if swing_sign > 0:
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
