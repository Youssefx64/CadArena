"""
Door rotation computation.

This module provides functions to calculate door rotation angles
based on wall orientation and door specifications.
"""

from app.domain.architecture.wall import WallSegment
from app.domain.architecture.door import DoorSpec


def compute_door_rotation(wall: WallSegment, door: DoorSpec) -> float:
    """
    Compute door rotation angle based on wall orientation and door properties.
    
    Calculates base rotation from wall orientation (horizontal/vertical),
    then adjusts for hinge side and swing direction.
    
    Args:
        wall: Wall segment where door is placed.
        door: Door specification.
    
    Returns:
        Rotation angle in degrees (0-360).
    """
    # Determine base rotation from wall orientation
    if abs(wall.start.y - wall.end.y) < abs(wall.start.x - wall.end.x):
        base = 0    # horizontal wall
    else:
        base = 90   # vertical wall

    # Adjust for hinge side
    if door.hinge == "right":
        base += 180

    # Adjust for swing direction
    if door.swing == "out":
        base += 180

    return base % 360