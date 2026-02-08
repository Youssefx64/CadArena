"""
Door placement on wall segments.

This module provides functions for placing doors on wall segments,
either manually with specified offset or automatically on room walls.
Note: This is a duplicate/alternative implementation to door_wall_placement.py
in domain/architecture.
"""

from app.schemas.room import Room
from app.domain.architecture.wall import WallSegment
from app.domain.architecture.opening import DoorPlacement
from app.domain.architecture.door import DoorSpec


def place_door_on_wall(
    wall: WallSegment,
    offset: float | None = None,
    door_width: float = 1.0
) -> DoorPlacement:
    """
    Place a door on a specific wall segment.
    
    Creates a door placement with default specifications (left hinge, inward swing).
    If no offset is provided, the door is centered on the wall.
    
    Args:
        wall: Wall segment to place door on.
        offset: Distance from wall start to door opening start. None to center.
        door_width: Width of the door opening in meters. Defaults to 1.0.
    
    Returns:
        DoorPlacement with wall reference, offset, and door specification.
    
    Raises:
        ValueError: If door doesn't fit on wall (offset or width too large).
    """
    wall_length = wall.length()

    # Center door if no offset provided
    if offset is None:
        offset = (wall_length - door_width) / 2

    if offset < 0 or offset + door_width > wall_length:
        raise ValueError(
            f"Door (width={door_width}) does not fit on wall (length={wall_length})"
        )

    # Create door with default specifications
    door = DoorSpec(
        width=door_width,
        hinge="left",
        swing="in",
        angle=90
    )

    return DoorPlacement(
        wall=wall,
        offset=offset,
        door=door
    )


def auto_place_door_on_room(
    room: Room,
    wall_segments: list[WallSegment]
) -> DoorPlacement:
    """
    Automatically place one door on the bottom wall of the room.
    
    Uses the first wall segment (bottom wall) and centers the door.
    
    Args:
        room: Room to place door in.
        wall_segments: List of 4 wall segments in order [bottom, right, top, left].
    
    Returns:
        DoorPlacement on the bottom wall, centered.
    """
    bottom_wall = wall_segments[0]

    return place_door_on_wall(
        wall=bottom_wall,
        offset=None,     # centered
        door_width=1.0
    )
