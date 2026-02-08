"""
Simple DXF rendering utilities.

This module provides basic functions for rendering simple shapes to DXF files.
"""

import ezdxf
from pathlib import Path
from app.schemas.geometry import Point


def draw_rectangle(points: list[Point], file_path: Path):
    """
    Draw a closed rectangle (polyline) to a DXF file.
    
    Args:
        points: List of 4 points defining the rectangle corners.
        file_path: Path where the DXF file will be saved.
    """
    doc = ezdxf.new("R2018")
    msp = doc.modelspace()

    msp.add_lwpolyline([(p.x, p.y) for p in points], close=True)

    doc.saveas(file_path)
