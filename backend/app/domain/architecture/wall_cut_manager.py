from app.domain.architecture.wall import WallSegment
from app.domain.architecture.opening import DoorPlacement
from app.domain.entities import Point
from app.domain.architecture.opening_geometry import (
    opening_interval_on_wall,
    opening_points_from_placement,
    point_on_axis_segment,
)


class WallCutManager:
    """
    Manages wall segments and cuts them for door openings.
    
    This ensures walls have proper gaps where doors are placed.
    """
    
    def __init__(self):
        self.wall_segments: list[WallSegment] = []
        self.cut_segments: list[tuple[Point, Point, WallSegment | None, bool]] = []
    
    def add_wall_segments(self, segments: list[WallSegment]):
        """
        Add wall segments from a room.
        
        Args:
            segments: List of wall segments to add.
        """
        self.wall_segments.extend(segments)
    
    def add_door_placement(self, placement: DoorPlacement):
        """
        Register a door placement for later cutting.
        
        Args:
            placement: Door placement to register.
        """
        cut_start, cut_end = opening_points_from_placement(placement)
        self.add_cut_segment(cut_start, cut_end, wall=placement.wall, allow_shared=True)

    def add_cut_segment(
        self,
        cut_start: Point,
        cut_end: Point,
        wall: WallSegment | None = None,
        allow_shared: bool = False,
    ):
        self.cut_segments.append((cut_start, cut_end, wall, allow_shared))
    
    def process_cuts(self) -> list[WallSegment]:
        """
        Cut all walls where doors are placed.
        
        Returns:
            List of wall segments with gaps for doors
        """
        final_segments: list[WallSegment] = []

        min_length = 0.1  # Minimum segment length to keep
        tol = 1e-6  # Tolerance for interval merging

        for segment in self.wall_segments:
            length = segment.length()
            if length < 0.01:
                # Skip very short segments
                continue

            # Build cut intervals (start, end) along the wall
            intervals: list[tuple[float, float]] = []
            for cut_start, cut_end, primary_wall, allow_shared in self.cut_segments:
                if primary_wall is not None and id(primary_wall) == id(segment):
                    if not (
                        point_on_axis_segment(segment, cut_start)
                        and point_on_axis_segment(segment, cut_end)
                    ):
                        continue
                elif not allow_shared:
                    continue
                elif not (
                    point_on_axis_segment(segment, cut_start)
                    and point_on_axis_segment(segment, cut_end)
                ):
                    continue
                start, end = opening_interval_on_wall(segment, cut_start, cut_end)
                if start < 0 or end > length:
                    continue
                if end - start <= 0:
                    continue
                intervals.append((start, end))

            if not intervals:
                # No valid intervals - keep segment as-is
                final_segments.append(segment)
                continue

            # Sort intervals by start position
            intervals.sort(key=lambda item: item[0])

            # Merge overlapping intervals
            merged: list[list[float]] = []
            for start, end in intervals:
                if not merged:
                    merged.append([start, end])
                    continue
                last = merged[-1]
                # Merge if intervals overlap or are very close
                if start <= last[1] + tol:
                    last[1] = max(last[1], end)
                else:
                    merged.append([start, end])

            # Create wall segments between cuts
            cursor = 0.0
            for start, end in merged:
                # Add segment before cut if it's long enough
                if start - cursor > min_length:
                    seg_start = Point(
                        x=segment.start.x + (segment.end.x - segment.start.x) * (cursor / length),
                        y=segment.start.y + (segment.end.y - segment.start.y) * (cursor / length)
                    )
                    seg_end = Point(
                        x=segment.start.x + (segment.end.x - segment.start.x) * (start / length),
                        y=segment.start.y + (segment.end.y - segment.start.y) * (start / length)
                    )
                    final_segments.append(WallSegment(seg_start, seg_end))

                cursor = max(cursor, end)

            # Add final segment after last cut if it's long enough
            if length - cursor > min_length:
                seg_start = Point(
                    x=segment.start.x + (segment.end.x - segment.start.x) * (cursor / length),
                    y=segment.start.y + (segment.end.y - segment.start.y) * (cursor / length)
                )
                seg_end = Point(
                    x=segment.start.x + (segment.end.x - segment.start.x) * (length / length),
                    y=segment.start.y + (segment.end.y - segment.start.y) * (length / length)
                )
                final_segments.append(WallSegment(seg_start, seg_end))

        return final_segments
