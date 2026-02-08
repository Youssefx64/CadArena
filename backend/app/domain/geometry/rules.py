"""
Geometry validation rules.

This module provides validation functions for geometric entities
and defines standard architectural constants.
"""

# Standard wall thickness in meters
WALL_THICKNESS = 0.2  # meters


def validate_rectangle(width: float, height: float):
    """
    Validate rectangle dimensions.
    
    Ensures dimensions are positive and meet minimum size requirements
    for room placement.
    
    Args:
        width: Rectangle width in meters.
        height: Rectangle height in meters.
    
    Raises:
        ValueError: If dimensions are invalid (non-positive or too small).
    """
    if width <= 0 or height <= 0:
        raise ValueError("Invalid rectangle dimensions")

    if width < 2 or height < 2:
        raise ValueError("Room too small")
