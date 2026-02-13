"""
Strict validation layer for design intents.
"""

from app.core.logging import get_logger
from app.schemas.design_intent import DesignIntent, OpeningIntent, RoomIntent
from app.schemas.geometry import Point


class IntentValidationError(RuntimeError):
    """
    Raised when intent validation fails.
    """


class DesignIntentValidator:
    """
    Validate design intents before planning.
    """

    def __init__(self):
        self.logger = get_logger("IntentValidator")

    def validate(self, intent: DesignIntent) -> None:
        self._validate_boundary(intent)
        self._validate_rooms(intent.rooms, intent.boundary.width, intent.boundary.height)
        self._validate_openings(intent.openings, intent.rooms)

    def _validate_boundary(self, intent: DesignIntent) -> None:
        if intent.boundary.width <= 0 or intent.boundary.height <= 0:
            raise IntentValidationError("Boundary dimensions must be > 0")

    def _validate_rooms(
        self,
        rooms: list[RoomIntent],
        boundary_width: float,
        boundary_height: float,
    ) -> None:
        if not rooms:
            self.logger.info("No rooms provided; skipping room validation")
            return

        names: set[str] = set()
        for room in rooms:
            if room.name in names:
                raise IntentValidationError(f"Duplicate room name: {room.name}")
            names.add(room.name)

            if room.width <= 0 or room.height <= 0:
                raise IntentValidationError(f"Room {room.name} has invalid size")

            if room.width > boundary_width or room.height > boundary_height:
                raise IntentValidationError(f"Room {room.name} exceeds boundary size")

            if room.origin is not None:
                if room.origin.x < 0 or room.origin.y < 0:
                    raise IntentValidationError(f"Room {room.name} origin must be >= 0")
                if room.origin.x + room.width > boundary_width:
                    raise IntentValidationError(f"Room {room.name} is out of boundary")
                if room.origin.y + room.height > boundary_height:
                    raise IntentValidationError(f"Room {room.name} is out of boundary")

        self._validate_fixed_room_overlap(rooms)

    def _validate_fixed_room_overlap(self, rooms: list[RoomIntent]) -> None:
        fixed = [r for r in rooms if r.origin is not None]
        for i, room in enumerate(fixed):
            for other in fixed[i + 1 :]:
                if self._rooms_overlap(room, other):
                    raise IntentValidationError(
                        f"Rooms {room.name} and {other.name} overlap"
                    )

    def _rooms_overlap(self, a: RoomIntent, b: RoomIntent) -> bool:
        return not (
            a.origin.x + a.width <= b.origin.x
            or a.origin.x >= b.origin.x + b.width
            or a.origin.y + a.height <= b.origin.y
            or a.origin.y >= b.origin.y + b.height
        )

    def _validate_openings(
        self,
        openings: list[OpeningIntent],
        rooms: list[RoomIntent],
    ) -> None:
        if not openings:
            return

        room_map = {room.name: room for room in rooms}
        segments_by_wall: dict[tuple[str, str], list[tuple[float, float]]] = {}

        for opening in openings:
            self._validate_opening(opening, room_map)
            room = room_map[opening.room_name]
            wall = opening.wall
            segment = self._opening_segment(opening, room)
            key = (opening.room_name, wall)
            segments = segments_by_wall.setdefault(key, [])
            for existing in segments:
                if self._segments_overlap(segment, existing):
                    raise IntentValidationError(
                        f"Overlapping openings on {opening.room_name} {wall} wall"
                    )
            segments.append(segment)

    def _validate_opening(
        self,
        opening: OpeningIntent,
        room_map: dict[str, RoomIntent],
    ) -> None:
        if opening.width <= 0:
            raise IntentValidationError("Opening.width must be > 0")
        if opening.room_name is None:
            raise IntentValidationError("Opening.room_name is required")
        if opening.wall is None:
            raise IntentValidationError("Opening.wall is required")
        if opening.room_name not in room_map:
            raise IntentValidationError(f"Opening room not found: {opening.room_name}")
        if opening.offset is not None and opening.offset < 0:
            raise IntentValidationError("Opening.offset must be >= 0")
        if (opening.cut_start is None) != (opening.cut_end is None):
            raise IntentValidationError("Opening.cut_start and Opening.cut_end must be provided together")
        if opening.cut_start is not None and opening.offset is not None:
            raise IntentValidationError("Use either cut_start/cut_end or offset, not both")

        room = room_map[opening.room_name]
        wall_length = self._wall_length(room, opening.wall)
        if opening.width > wall_length:
            raise IntentValidationError("Opening.width exceeds wall length")

        if opening.cut_start is not None and opening.cut_end is not None:
            if room.origin is None:
                raise IntentValidationError(
                    "Opening cut points require explicit room origin"
                )
            self._validate_cut_points(opening, room)
        else:
            offset = opening.offset if opening.offset is not None else (wall_length - opening.width) / 2
            if offset < 0 or offset + opening.width > wall_length:
                raise IntentValidationError("Opening does not fit on wall")

    def _wall_length(self, room: RoomIntent, wall: str) -> float:
        if wall in ("top", "bottom"):
            return room.width
        return room.height

    def _validate_cut_points(self, opening: OpeningIntent, room: RoomIntent) -> None:
        cut_start = opening.cut_start
        cut_end = opening.cut_end
        if cut_start is None or cut_end is None:
            return

        tol = 1e-6
        x0 = room.origin.x
        y0 = room.origin.y
        x1 = x0 + room.width
        y1 = y0 + room.height

        if opening.wall == "bottom":
            self._ensure_horizontal(cut_start, cut_end, y0, x0, x1, tol)
        elif opening.wall == "top":
            self._ensure_horizontal(cut_start, cut_end, y1, x0, x1, tol)
        elif opening.wall == "left":
            self._ensure_vertical(cut_start, cut_end, x0, y0, y1, tol)
        elif opening.wall == "right":
            self._ensure_vertical(cut_start, cut_end, x1, y0, y1, tol)

        segment = self._opening_segment(opening, room)
        if segment[1] - segment[0] <= 0:
            raise IntentValidationError("Opening width too small")

    def _ensure_horizontal(
        self,
        a: Point,
        b: Point,
        y: float,
        min_x: float,
        max_x: float,
        tol: float,
    ) -> None:
        if abs(a.y - y) > tol or abs(b.y - y) > tol:
            raise IntentValidationError("Opening cut points not on wall")
        if not (min_x - tol <= a.x <= max_x + tol and min_x - tol <= b.x <= max_x + tol):
            raise IntentValidationError("Opening cut points out of wall bounds")

    def _ensure_vertical(
        self,
        a: Point,
        b: Point,
        x: float,
        min_y: float,
        max_y: float,
        tol: float,
    ) -> None:
        if abs(a.x - x) > tol or abs(b.x - x) > tol:
            raise IntentValidationError("Opening cut points not on wall")
        if not (min_y - tol <= a.y <= max_y + tol and min_y - tol <= b.y <= max_y + tol):
            raise IntentValidationError("Opening cut points out of wall bounds")

    def _opening_segment(self, opening: OpeningIntent, room: RoomIntent) -> tuple[float, float]:
        wall = opening.wall
        wall_length = self._wall_length(room, wall)
        if opening.cut_start is not None and opening.cut_end is not None and room.origin is not None:
            if wall in ("top", "bottom"):
                start = min(opening.cut_start.x, opening.cut_end.x) - room.origin.x
                end = max(opening.cut_start.x, opening.cut_end.x) - room.origin.x
            else:
                start = min(opening.cut_start.y, opening.cut_end.y) - room.origin.y
                end = max(opening.cut_start.y, opening.cut_end.y) - room.origin.y
            return (max(0.0, start), min(wall_length, end))

        offset = opening.offset if opening.offset is not None else (wall_length - opening.width) / 2
        return (offset, offset + opening.width)

    def _segments_overlap(self, a: tuple[float, float], b: tuple[float, float]) -> bool:
        tol = 1e-6
        return not (a[1] <= b[0] + tol or b[1] <= a[0] + tol)
