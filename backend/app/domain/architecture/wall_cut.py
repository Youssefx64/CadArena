"""
Wall cutting utilities for door openings.

This module provides functions to cut wall segments to create openings
for doors and windows.
"""

from app.domain.architecture.wall import WallSegment
from app.domain.architecture.opening import DoorPlacement
from app.domain.architecture.wall_cut_manager import WallCutManager
from app.domain.architecture.opening_geometry import opening_points_from_placement


def cut_wall(wall: WallSegment, placement: DoorPlacement):
    manager = WallCutManager()
    manager.add_wall_segments([wall])
    cut_start, cut_end = opening_points_from_placement(placement)
    manager.add_cut_segment(cut_start, cut_end, wall=wall, allow_shared=False)
    segments = manager.process_cuts()
    if len(segments) != 2:
        raise ValueError("Unexpected wall cut result")
    return segments[0], segments[1]
