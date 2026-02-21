from app.domain.architecture.opening import DoorPlacement
from app.domain.architecture.wall import WallSegment
from app.domain.entities import Point


def opening_points_from_placement(placement: DoorPlacement) -> tuple[Point, Point]:
    wall = placement.wall
    length = wall.length()
    if length < 0.001:
        raise ValueError("Wall segment too short for opening placement")

    dx = wall.end.x - wall.start.x
    dy = wall.end.y - wall.start.y
    ux = dx / length
    uy = dy / length

    cut_start = Point(
        x=wall.start.x + ux * placement.offset,
        y=wall.start.y + uy * placement.offset
    )
    cut_end = Point(
        x=cut_start.x + ux * placement.door.width,
        y=cut_start.y + uy * placement.door.width
    )
    return cut_start, cut_end


def point_on_axis_segment(segment: WallSegment, point: Point, tol: float = 1e-6) -> bool:
    if abs(segment.start.x - segment.end.x) < tol:
        if abs(point.x - segment.start.x) > tol:
            return False
        return (
            min(segment.start.y, segment.end.y) - tol
            <= point.y
            <= max(segment.start.y, segment.end.y) + tol
        )
    if abs(segment.start.y - segment.end.y) < tol:
        if abs(point.y - segment.start.y) > tol:
            return False
        return (
            min(segment.start.x, segment.end.x) - tol
            <= point.x
            <= max(segment.start.x, segment.end.x) + tol
        )
    return False


def opening_segment_key(cut_start: Point, cut_end: Point) -> tuple[float, float, float, float]:
    p1 = (round(cut_start.x, 4), round(cut_start.y, 4))
    p2 = (round(cut_end.x, 4), round(cut_end.y, 4))
    if p2 < p1:
        p1, p2 = p2, p1
    return (p1[0], p1[1], p2[0], p2[1])


def project_point_on_segment(segment: WallSegment, point: Point) -> float:
    length = segment.length()
    if length < 1e-6:
        return 0.0
    dx = segment.end.x - segment.start.x
    dy = segment.end.y - segment.start.y
    ux = dx / length
    uy = dy / length
    return (point.x - segment.start.x) * ux + (point.y - segment.start.y) * uy


def opening_interval_on_wall(
    segment: WallSegment,
    cut_start: Point,
    cut_end: Point,
) -> tuple[float, float]:
    start = project_point_on_segment(segment, cut_start)
    end = project_point_on_segment(segment, cut_end)
    if end < start:
        start, end = end, start
    length = segment.length()
    start = max(0.0, min(start, length))
    end = max(0.0, min(end, length))
    return start, end
