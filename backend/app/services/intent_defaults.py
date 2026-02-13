"""
Default resolution layer for incomplete or ambiguous design intents.
"""

from app.core.defaults import (
    DEFAULT_BOUNDARY_HEIGHT,
    DEFAULT_BOUNDARY_WIDTH,
    DEFAULT_OPENING_WALL,
    DEFAULT_OPENING_WIDTH,
    DEFAULT_ROOM_SIZES,
    DEFAULT_ROOM_TYPE,
)
from app.core.logging import get_logger
from app.schemas.design_intent import BoundaryIntent, DesignIntent, OpeningIntent, RoomIntent
from app.schemas.intent_draft import DesignIntentDraft, OpeningDraft, RoomDraft
from app.schemas.geometry import Point
from app.services.planning_context_builder import PlanningContextBuilder
from app.domain.planner.planning_context import PlanningContext


class IntentDefaultsResolver:
    """
    Resolve missing or ambiguous fields with deterministic defaults.
    """

    def __init__(self):
        self.logger = get_logger("IntentDefaults")
        self._planning_builder = PlanningContextBuilder()

    def resolve(
        self,
        payload: DesignIntentDraft | dict,
    ) -> tuple[DesignIntent, PlanningContext]:
        draft = payload
        if isinstance(payload, dict):
            draft = DesignIntentDraft.parse_obj(payload)

        boundary = self._resolve_boundary(draft.boundary)
        rooms = self._resolve_rooms(draft.rooms, boundary)
        openings = self._resolve_openings(draft.openings, rooms)
        planning_context = self._planning_builder.build(rooms, draft.planning)

        intent = DesignIntent(boundary=boundary, rooms=rooms, openings=openings)
        return intent, planning_context

    def _resolve_boundary(self, boundary) -> BoundaryIntent:
        width = boundary.width if boundary and boundary.width is not None else DEFAULT_BOUNDARY_WIDTH
        height = boundary.height if boundary and boundary.height is not None else DEFAULT_BOUNDARY_HEIGHT

        if boundary is None or boundary.width is None:
            self.logger.info("Defaulted boundary.width to %s", width)
        if boundary is None or boundary.height is None:
            self.logger.info("Defaulted boundary.height to %s", height)

        unit = boundary.unit if boundary and boundary.unit is not None else "meter"
        return BoundaryIntent(width=width, height=height, unit=unit)

    def _resolve_rooms(
        self,
        rooms: list[RoomDraft] | None,
        boundary: BoundaryIntent,
    ) -> list[RoomIntent]:
        resolved: list[RoomIntent] = []

        if not rooms:
            self.logger.info("No rooms provided; defaulting to a single room")
            rooms = [RoomDraft()]

        existing_names: set[str] = set()

        for idx, draft in enumerate(rooms, start=1):
            name_from_input = bool(draft.name and draft.name.strip())
            name = (draft.name or f"Room {idx}").strip()
            if not name_from_input:
                self.logger.info("Defaulted room.name to %s", name)

            if name in existing_names and not name_from_input:
                suffix = 2
                unique = f"{name} {suffix}"
                while unique in existing_names:
                    suffix += 1
                    unique = f"{name} {suffix}"
                self.logger.info("Adjusted duplicate room.name to %s", unique)
                name = unique

            existing_names.add(name)

            room_type = draft.room_type or DEFAULT_ROOM_TYPE
            if draft.room_type is None:
                self.logger.info("Defaulted room_type for %s to %s", name, room_type)

            default_width, default_height = DEFAULT_ROOM_SIZES.get(
                room_type, DEFAULT_ROOM_SIZES[DEFAULT_ROOM_TYPE]
            )

            width = draft.width if draft.width is not None else min(default_width, boundary.width)
            height = draft.height if draft.height is not None else min(default_height, boundary.height)

            if draft.width is None:
                self.logger.info("Defaulted width for %s to %s", name, width)
            if draft.height is None:
                self.logger.info("Defaulted height for %s to %s", name, height)

            origin = draft.origin if isinstance(draft.origin, Point) else draft.origin

            resolved.append(
                RoomIntent(
                    name=name,
                    room_type=room_type,
                    width=width,
                    height=height,
                    origin=origin,
                )
            )

        return resolved

    def _resolve_openings(
        self,
        openings: list[OpeningDraft] | None,
        rooms: list[RoomIntent],
    ) -> list[OpeningIntent]:
        resolved: list[OpeningIntent] = []

        if not openings:
            self.logger.info("No openings provided; defaulting to auto doors per room")
            return resolved

        room_names = [room.name for room in rooms]
        room_map = {room.name: room for room in rooms}

        for draft in openings:
            o_type = draft.type or "door"
            if draft.type is None:
                self.logger.info("Defaulted opening.type to %s", o_type)

            width = draft.width if draft.width is not None else DEFAULT_OPENING_WIDTH
            if draft.width is None:
                self.logger.info("Defaulted opening.width to %s", width)

            room_name = draft.room_name
            if not room_name:
                room_name = room_names[0] if room_names else None
                self.logger.info("Defaulted opening.room_name to %s", room_name)

            wall = draft.wall
            if wall is None:
                inferred = None
                if room_name and draft.cut_start and draft.cut_end:
                    inferred = self._infer_wall_from_cut_points(room_map.get(room_name), draft)
                wall = inferred or DEFAULT_OPENING_WALL
                self.logger.info("Defaulted opening.wall to %s", wall)

            if draft.offset is None and draft.cut_start is None and draft.cut_end is None:
                self.logger.info("Defaulted opening.offset to centered on %s wall", wall)

            resolved.append(
                OpeningIntent(
                    type=o_type,
                    width=width,
                    room_name=room_name,
                    wall=wall,
                    offset=draft.offset,
                    cut_start=draft.cut_start,
                    cut_end=draft.cut_end,
                    hinge=draft.hinge,
                    swing=draft.swing,
                )
            )

        return resolved

    def _infer_wall_from_cut_points(
        self,
        room: RoomIntent | None,
        opening: OpeningDraft,
    ) -> str | None:
        if room is None or room.origin is None or opening.cut_start is None or opening.cut_end is None:
            return None

        tol = 1e-6
        x0 = room.origin.x
        y0 = room.origin.y
        x1 = x0 + room.width
        y1 = y0 + room.height

        if abs(opening.cut_start.y - y0) < tol and abs(opening.cut_end.y - y0) < tol:
            return "bottom"
        if abs(opening.cut_start.y - y1) < tol and abs(opening.cut_end.y - y1) < tol:
            return "top"
        if abs(opening.cut_start.x - x0) < tol and abs(opening.cut_end.x - x0) < tol:
            return "left"
        if abs(opening.cut_start.x - x1) < tol and abs(opening.cut_end.x - x1) < tol:
            return "right"

        return None
