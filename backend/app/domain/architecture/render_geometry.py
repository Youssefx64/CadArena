from app.domain.architecture.wall import WallSegment
from app.domain.entities import Point
from app.domain.entities import Room


RENDER_WALL_THICKNESS = 0.15


def build_thick_wall_lines(
    segments: list[WallSegment],
    thickness: float = RENDER_WALL_THICKNESS,
) -> list[tuple[Point, Point]]:
    lines: list[tuple[Point, Point]] = []
    for segment in segments:
        length = segment.length()
        if length < 0.01:
            continue

        dx = segment.end.x - segment.start.x
        dy = segment.end.y - segment.start.y
        ux = dx / length
        uy = dy / length

        px = -uy
        py = ux

        offset_x = px * thickness / 2
        offset_y = py * thickness / 2

        lines.append(
            (
                Point(
                    x=segment.start.x + offset_x,
                    y=segment.start.y + offset_y,
                ),
                Point(
                    x=segment.end.x + offset_x,
                    y=segment.end.y + offset_y,
                ),
            )
        )
        lines.append(
            (
                Point(
                    x=segment.start.x - offset_x,
                    y=segment.start.y - offset_y,
                ),
                Point(
                    x=segment.end.x - offset_x,
                    y=segment.end.y - offset_y,
                ),
            )
        )
    return lines


def build_room_labels(rooms: list[Room]) -> list[tuple[str, str, Point]]:
    labels: list[tuple[str, str, Point]] = []
    for room in rooms:
        if room.origin is None:
            continue
        cx = room.origin.x + room.width / 2
        cy = room.origin.y + room.height / 2
        labels.append((room.name, room.room_type, Point(x=cx, y=cy + 0.3)))
    return labels


def build_room_dimensions(rooms: list[Room]) -> list[tuple[str, Point]]:
    labels: list[tuple[str, Point]] = []
    for room in rooms:
        if room.origin is None:
            continue
        cx = room.origin.x + room.width / 2
        cy = room.origin.y + room.height / 2
        text = f"{_fmt_dimension(room.width)}m x {_fmt_dimension(room.height)}m"
        labels.append((text, Point(x=cx, y=cy - 0.3)))
    return labels


def _fmt_dimension(value: float) -> str:
    text = f"{value:.2f}".rstrip("0").rstrip(".")
    return text if text else "0"


def build_stair_lines(origin: Point, width: float, height: float, steps: int = 8) -> list[tuple[Point, Point]]:
    lines: list[tuple[Point, Point]] = []
    if steps < 2:
        steps = 2

    if height >= width:
        step_depth = height / steps
        for i in range(1, steps):
            y = origin.y + i * step_depth
            lines.append((Point(x=origin.x, y=y), Point(x=origin.x + width, y=y)))
    else:
        step_width = width / steps
        for i in range(1, steps):
            x = origin.x + i * step_width
            lines.append((Point(x=x, y=origin.y), Point(x=x, y=origin.y + height)))

    return lines
