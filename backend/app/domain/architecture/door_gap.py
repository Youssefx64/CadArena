"""
Wall cutting for door gaps.

This module provides functions to cut walls to create gaps for doors.
Note: This appears to be an alternative implementation to wall_cut.py.
"""

from app.domain.architecture.wall import WallSegment
from app.domain.architecture.wall_cut_manager import WallCutManager
from app.domain.architecture.door_wall_placement import place_door_on_wall
from app.domain.architecture.opening_geometry import opening_points_from_placement


def cut_wall_for_door(
    wall: WallSegment,
    offset: float,
    door_width: float
) -> tuple[WallSegment, WallSegment]:
    placement = place_door_on_wall(wall=wall, offset=offset, door_width=door_width)
    manager = WallCutManager()
    manager.add_wall_segments([wall])
    cut_start, cut_end = opening_points_from_placement(placement)
    manager.add_cut_segment(cut_start, cut_end, wall=wall, allow_shared=False)
    segments = manager.process_cuts()
    if len(segments) != 2:
        raise ValueError("Unexpected wall cut result")
    return segments[0], segments[1]
