"""
Door placement model.

This module defines the DoorPlacement class for representing a door's
position on a wall segment.
"""

from app.domain.architecture.wall import WallSegment
from app.domain.architecture.door import DoorSpec


class DoorPlacement:
    """
    Represents a door placed on a wall segment.
    
    Combines a wall segment, offset position, and door specification
    to define where and how a door is placed.
    
    Attributes:
        wall: Wall segment where the door is placed.
        offset: Distance from wall start point to door opening start.
        door: Door specification (width, hinge, swing, angle).
    """

    def __init__(self, wall: WallSegment, offset: float, door: DoorSpec):
        """
        Initialize door placement.
        
        Args:
            wall: Wall segment where door is placed.
            offset: Distance from wall start to door opening start.
            door: Door specification.
        """
        self.wall = wall
        self.offset = offset
        self.door = door
