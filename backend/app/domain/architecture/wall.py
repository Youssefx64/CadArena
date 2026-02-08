"""
Wall segment representation.

This module defines the WallSegment class for representing linear wall segments
in 2D space.
"""

from app.schemas.geometry import Point


class WallSegment:
    """
    Represents a linear wall segment between two points.
    
    Wall segments are used to represent both interior and boundary walls.
    They can be cut to create openings for doors and windows.
    """

    def __init__(self, start: Point, end: Point):
        """
        Initialize wall segment with start and end points.
        
        Args:
            start: Starting point of the wall segment.
            end: Ending point of the wall segment.
        """
        self.start = start
        self.end = end

    def length(self) -> float:
        """
        Calculate the length of the wall segment.
        
        Returns:
            Euclidean distance between start and end points.
        """
        return (
            (self.end.x - self.start.x) ** 2 + (self.end.y - self.start.y) ** 2
        ) ** 0.5
