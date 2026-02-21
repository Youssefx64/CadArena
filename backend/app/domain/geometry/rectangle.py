"""
Rectangle geometry utilities.

This module provides functions for converting rectangle geometries
to point lists for rendering.
"""

from app.domain.entities import Point, RectangleGeometry


def rectangle_to_points(rect: RectangleGeometry):
    """
    Convert a rectangle to a list of 4 corner points.
    
    Points are returned in counter-clockwise order starting from bottom-left:
    bottom-left, bottom-right, top-right, top-left.
    
    Args:
        rect: Rectangle geometry to convert.
    
    Returns:
        List of 4 Point objects representing rectangle corners.
    """
    x = rect.origin.x
    y = rect.origin.y
    w = rect.width
    h = rect.height

    return [
        Point(x=x, y=y),                    # Bottom-left
        Point(x=x + w, y=y),                 # Bottom-right
        Point(x=x + w, y=y + h),            # Top-right
        Point(x=x, y=y + h),                # Top-left
    ]
