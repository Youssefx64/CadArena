"""
Door specification model.

This module defines the DoorSpec class for representing door properties
including width, hinge side, swing direction, and opening angle.
"""

from typing import Literal


class DoorSpec:
    """
    Specification for a door's physical properties.
    
    Attributes:
        width: Door width in meters. Defaults to 1.0.
        hinge: Hinge side ("left" or "right"). Defaults to "left".
        swing: Swing direction ("in" or "out"). Defaults to "in".
        angle: Door opening angle in degrees. Defaults to 90.
    """

    def __init__(
        self,
        width: float = 1.0,
        hinge: Literal["left", "right"] = "left",
        swing: Literal["in", "out"] = "in",
        angle: float = 90,
    ):
        """
        Initialize door specification.
        
        Args:
            width: Door width in meters.
            hinge: Hinge side ("left" or "right").
            swing: Swing direction ("in" or "out").
            angle: Door opening angle in degrees.
        """
        self.width = width
        self.hinge = hinge
        self.swing = swing
        self.angle = angle
