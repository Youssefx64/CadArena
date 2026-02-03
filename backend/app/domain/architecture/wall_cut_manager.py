from app.domain.architecture.wall import WallSegment
from app.domain.architecture.opening import DoorPlacement
from app.schemas.geometry import Point


class WallCutManager:
    """
    Manages wall segments and cuts them for door openings.
    
    This ensures walls have proper gaps where doors are placed.
    """
    
    def __init__(self):
        self.wall_segments: list[WallSegment] = []
        self.door_placements: list[DoorPlacement] = []
    
    def add_wall_segments(self, segments: list[WallSegment]):
        """Add wall segments from a room."""
        self.wall_segments.extend(segments)
    
    def add_door_placement(self, placement: DoorPlacement):
        """Register a door placement for later cutting."""
        self.door_placements.append(placement)
    
    def process_cuts(self) -> list[WallSegment]:
        """
        Cut all walls where doors are placed.
        
        Returns:
            List of wall segments with gaps for doors
        """
        final_segments: list[WallSegment] = []

        # Group placements by wall segment id
        placements_by_wall: dict[int, list[DoorPlacement]] = {}
        for placement in self.door_placements:
            placements_by_wall.setdefault(id(placement.wall), []).append(placement)

        min_length = 0.1
        tol = 1e-6

        for segment in self.wall_segments:
            placements = placements_by_wall.get(id(segment))
            if not placements:
                final_segments.append(segment)
                continue

            length = segment.length()
            if length < 0.01:
                continue

            dx = segment.end.x - segment.start.x
            dy = segment.end.y - segment.start.y
            ux = dx / length
            uy = dy / length

            # Build cut intervals (start, end) along the wall
            intervals: list[tuple[float, float]] = []
            for placement in placements:
                start = placement.offset
                end = placement.offset + placement.door.width

                if start < 0 or end > length:
                    print(
                        f"Warning: Door doesn't fit on wall "
                        f"(offset={start}, width={placement.door.width}, length={length})"
                    )
                    continue

                intervals.append((start, end))

            if not intervals:
                final_segments.append(segment)
                continue

            intervals.sort(key=lambda item: item[0])

            # Merge overlapping intervals
            merged: list[list[float]] = []
            for start, end in intervals:
                if not merged:
                    merged.append([start, end])
                    continue
                last = merged[-1]
                if start <= last[1] + tol:
                    last[1] = max(last[1], end)
                else:
                    merged.append([start, end])

            cursor = 0.0
            for start, end in merged:
                if start - cursor > min_length:
                    seg_start = Point(
                        x=segment.start.x + ux * cursor,
                        y=segment.start.y + uy * cursor
                    )
                    seg_end = Point(
                        x=segment.start.x + ux * start,
                        y=segment.start.y + uy * start
                    )
                    final_segments.append(WallSegment(seg_start, seg_end))

                cursor = max(cursor, end)

            if length - cursor > min_length:
                seg_start = Point(
                    x=segment.start.x + ux * cursor,
                    y=segment.start.y + uy * cursor
                )
                seg_end = Point(
                    x=segment.start.x + ux * length,
                    y=segment.start.y + uy * length
                )
                final_segments.append(WallSegment(seg_start, seg_end))

        return final_segments
