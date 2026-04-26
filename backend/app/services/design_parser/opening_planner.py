"""Deterministic door and window generation for architectural layouts."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from itertools import product
import logging
from typing import Any, Literal

from app.services.design_parser.rule_violation import RuleViolationError


logger = logging.getLogger(__name__)

_EPSILON = 1e-6
_DOOR_END_CLEARANCE = 0.25
_MIN_DOOR_END_CLEARANCE = 0.10
_OPENING_CLEARANCE = 0.20
_COLUMN_CLEARANCE = 0.22
_DEFAULT_WINDOW_HEIGHT = 1.2
_LIVING_WINDOW_RATIO_MIN = 0.05
_MIN_STANDARD_DOOR_WIDTH = 0.75
_MIN_BATHROOM_DOOR_WIDTH = 0.65
MIN_DOOR_CORNER_CLEARANCE = 0.4


@dataclass(frozen=True)
class _RoomBox:
    name: str
    room_type: str
    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def width(self) -> float:
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        return self.y1 - self.y0

    @property
    def area(self) -> float:
        return self.width * self.height


@dataclass(frozen=True)
class _SharedBoundary:
    room_a: str
    room_b: str
    axis: Literal["vertical", "horizontal"]
    coordinate: float
    start: float
    end: float

    @property
    def length(self) -> float:
        return self.end - self.start


@dataclass(frozen=True)
class _PlacedCut:
    start: float
    end: float


class DeterministicOpeningPlanner:
    """Creates deterministic door/window openings from planned room geometry."""

    def plan(
        self,
        *,
        extracted_payload: dict[str, Any],
        layout_payload: dict[str, Any],
    ) -> dict[str, Any]:
        boundary = layout_payload.get("boundary")
        rooms_raw = layout_payload.get("rooms")
        if not isinstance(boundary, dict) or not isinstance(rooms_raw, list):
            raise RuleViolationError(
                code="OPENING_INPUT_INVALID",
                reason="layout payload must include boundary and rooms",
                violated_rule="opening-input",
            )

        boundary_width = float(boundary.get("width", 0.0))
        boundary_height = float(boundary.get("height", 0.0))
        if boundary_width <= 0 or boundary_height <= 0:
            raise RuleViolationError(
                code="OPENING_INPUT_INVALID",
                reason="boundary dimensions must be positive",
                violated_rule="opening-input",
            )

        rooms = self._to_rooms(rooms_raw)
        by_name = {room.name: room for room in rooms}
        shared_boundaries = self._build_shared_boundaries(rooms)
        neighbors = self._build_neighbors(shared_boundaries)
        corridor = self._find_main_corridor(rooms)
        columns = self._build_column_grid(width=boundary_width, height=boundary_height)

        openings: list[dict[str, Any]] = []
        occupied: dict[tuple[str, str], list[_PlacedCut]] = {}
        door_pairs_done: set[tuple[str, str]] = set()
        corridor_targets = self._corridor_targets(rooms=rooms, main_corridor=corridor.name)

        for room in rooms:
            if self._is_bedroom(room):
                target = self._pick_adjacent_target(
                    source=room.name,
                    candidates=corridor_targets,
                    neighbors=neighbors,
                )
                if target is None:
                    target = self._pick_adjacent_target(
                        source=room.name,
                        candidates=self._sorted_room_names(rooms, predicate=self._is_bathroom),
                        neighbors=neighbors,
                    )
                if target is None:
                    raise RuleViolationError(
                        code="DOOR_CONNECTIVITY_FAILED",
                        reason="bedroom must connect to corridor spine or bathroom",
                        violated_rule="bedroom-door-policy",
                        room=room.name,
                    )
                self._add_door_between(
                    room_a=room.name,
                    room_b=target,
                    by_name=by_name,
                    shared_boundaries=shared_boundaries,
                    columns=columns,
                    occupied=occupied,
                    openings=openings,
                    door_pairs_done=door_pairs_done,
                    reason_rule="bedroom-door-policy",
                )

        for room in rooms:
            if self._is_living_main(room):
                target = self._pick_adjacent_target(
                    source=room.name,
                    candidates=corridor_targets,
                    neighbors=neighbors,
                )
                if target is None:
                    raise RuleViolationError(
                        code="DOOR_CONNECTIVITY_FAILED",
                        reason="living room must connect to circulation spine",
                        violated_rule="living-door-to-corridor",
                        room=room.name,
                    )
                self._add_door_between(
                    room_a=room.name,
                    room_b=target,
                    by_name=by_name,
                    shared_boundaries=shared_boundaries,
                    columns=columns,
                    occupied=occupied,
                    openings=openings,
                    door_pairs_done=door_pairs_done,
                    reason_rule="living-door-to-corridor",
                )

        for room in rooms:
            if self._is_dining(room):
                target = self._pick_adjacent_target(
                    source=room.name,
                    candidates=self._sorted_room_names(
                        rooms,
                        predicate=lambda current: self._is_kitchen(current) or self._is_living_space(current),
                    )
                    + [corridor.name],
                    neighbors=neighbors,
                )
                if target is None:
                    raise RuleViolationError(
                        code="DOOR_CONNECTIVITY_FAILED",
                        reason="dining room must connect to kitchen, living, or corridor",
                        violated_rule="dining-door-connectivity",
                        room=room.name,
                    )
                self._add_door_between(
                    room_a=room.name,
                    room_b=target,
                    by_name=by_name,
                    shared_boundaries=shared_boundaries,
                    columns=columns,
                    occupied=occupied,
                    openings=openings,
                    door_pairs_done=door_pairs_done,
                    reason_rule="dining-door-connectivity",
                )

        for room in rooms:
            if self._is_kitchen(room):
                kitchen_targets = self._sorted_room_names(rooms, predicate=self._is_dining)
                if not kitchen_targets:
                    kitchen_targets = corridor_targets + self._sorted_room_names(rooms, predicate=self._is_living_space)
                else:
                    kitchen_targets = kitchen_targets + corridor_targets
                added_kitchen_door = False
                kitchen_door_error: RuleViolationError | None = None
                adjacent_targets = [
                    candidate
                    for candidate in kitchen_targets
                    if candidate != room.name and candidate in neighbors.get(room.name, set())
                ]
                for target in adjacent_targets:
                    try:
                        self._add_door_between(
                            room_a=room.name,
                            room_b=target,
                            by_name=by_name,
                            shared_boundaries=shared_boundaries,
                            columns=columns,
                            occupied=occupied,
                            openings=openings,
                            door_pairs_done=door_pairs_done,
                            reason_rule="kitchen-door-connectivity",
                        )
                    except RuleViolationError as exc:
                        kitchen_door_error = exc
                        continue
                    added_kitchen_door = True
                    break
                if not added_kitchen_door and kitchen_door_error is not None:
                    raise kitchen_door_error
                if not added_kitchen_door:
                    raise RuleViolationError(
                        code="DOOR_CONNECTIVITY_FAILED",
                        reason="kitchen must connect to dining, living, or corridor",
                        violated_rule="kitchen-door-connectivity",
                        room=room.name,
                    )

        master_candidates = self._sorted_room_names(
            rooms,
            predicate=lambda current: self._is_bedroom(current) and "master" in current.name.lower(),
        )
        master_name = master_candidates[0] if master_candidates else None
        for room in rooms:
            if not self._is_bathroom(room):
                continue
            lowered_name = room.name.lower()
            if self._is_laundry(room):
                laundry_targets = list(
                    dict.fromkeys(
                        corridor_targets
                        + self._sorted_room_names(
                            rooms,
                            predicate=lambda current: self._is_kitchen(current)
                            or self._is_dining(current)
                            or self._is_storage(current),
                        )
                    )
                )
                laundry_door_error: RuleViolationError | None = None
                added_laundry_door = False
                adjacent_targets = [
                    candidate
                    for candidate in laundry_targets
                    if candidate != room.name and candidate in neighbors.get(room.name, set())
                ]
                for target in adjacent_targets:
                    try:
                        self._add_door_between(
                            room_a=room.name,
                            room_b=target,
                            by_name=by_name,
                            shared_boundaries=shared_boundaries,
                            columns=columns,
                            occupied=occupied,
                            openings=openings,
                            door_pairs_done=door_pairs_done,
                            reason_rule="service-door-to-corridor",
                        )
                    except RuleViolationError as exc:
                        laundry_door_error = exc
                        continue
                    added_laundry_door = True
                    break
                if not added_laundry_door and laundry_door_error is not None:
                    raise laundry_door_error
                if not added_laundry_door:
                    raise RuleViolationError(
                        code="DOOR_CONNECTIVITY_FAILED",
                        reason="laundry must connect to corridor or service cluster",
                        violated_rule="service-door-to-corridor",
                        room=room.name,
                    )
                continue

            use_master = (
                master_name is not None
                and ("ensuite" in lowered_name or "master" in lowered_name or "private" in lowered_name)
                and master_name in neighbors.get(room.name, set())
            )
            bathroom_targets = list(corridor_targets)
            if use_master and master_name is not None:
                bathroom_targets = [master_name] + bathroom_targets
            bathroom_targets.extend(
                self._sorted_room_names(
                    rooms,
                    predicate=lambda current: self._is_living_space(current) or self._is_bedroom(current),
                )
            )
            bathroom_targets = list(dict.fromkeys(bathroom_targets))
            bathroom_door_error: RuleViolationError | None = None
            added_bathroom_door = False
            adjacent_targets = [
                candidate
                for candidate in bathroom_targets
                if candidate != room.name and candidate in neighbors.get(room.name, set())
            ]
            for target in adjacent_targets:
                try:
                    self._add_door_between(
                        room_a=room.name,
                        room_b=target,
                        by_name=by_name,
                        shared_boundaries=shared_boundaries,
                        columns=columns,
                        occupied=occupied,
                        openings=openings,
                        door_pairs_done=door_pairs_done,
                        reason_rule="bathroom-door-policy",
                    )
                except RuleViolationError as exc:
                    bathroom_door_error = exc
                    continue
                added_bathroom_door = True
                break
            if not added_bathroom_door and bathroom_door_error is not None:
                raise bathroom_door_error
            if not added_bathroom_door:
                raise RuleViolationError(
                    code="DOOR_CONNECTIVITY_FAILED",
                    reason="bathroom must connect to corridor, living room, or bedroom",
                    violated_rule="bathroom-door-policy",
                    room=room.name,
                )

        for room in rooms:
            if self._is_storage(room) and room.room_type != "corridor":
                target = self._pick_adjacent_target(
                    source=room.name,
                    candidates=corridor_targets,
                    neighbors=neighbors,
                )
                if target is None:
                    raise RuleViolationError(
                        code="DOOR_CONNECTIVITY_FAILED",
                        reason="service spaces must connect to corridor",
                        violated_rule="service-door-to-corridor",
                        room=room.name,
                    )
                self._add_door_between(
                    room_a=room.name,
                    room_b=target,
                    by_name=by_name,
                    shared_boundaries=shared_boundaries,
                    columns=columns,
                    occupied=occupied,
                    openings=openings,
                    door_pairs_done=door_pairs_done,
                    reason_rule="service-door-to-corridor",
                )

        for room in rooms:
            if room.room_type != "corridor" or room.name == corridor.name:
                continue
            target = self._pick_adjacent_target(
                source=room.name,
                candidates=[corridor.name]
                + self._sorted_room_names(
                    rooms,
                    predicate=lambda current: current.room_type != "bedroom" and current.name != room.name,
                ),
                neighbors=neighbors,
            )
            if target is None:
                raise RuleViolationError(
                    code="DOOR_CONNECTIVITY_FAILED",
                    reason="auxiliary corridor/service spaces must connect to circulation graph",
                    violated_rule="aux-corridor-connectivity",
                    room=room.name,
                )
            self._add_door_between(
                room_a=room.name,
                room_b=target,
                by_name=by_name,
                shared_boundaries=shared_boundaries,
                columns=columns,
                occupied=occupied,
                openings=openings,
                door_pairs_done=door_pairs_done,
                reason_rule="aux-corridor-connectivity",
            )

        openings = self._ensure_room_connectivity(
            rooms=rooms,
            openings=openings,
            boundary_width=boundary_width,
            boundary_height=boundary_height,
        )
        occupied = self._occupied_from_openings(openings)

        orientation_map = self._resolve_orientation_map(extracted_payload)
        mechanical_allowed = self._mechanical_ventilation_allowed(extracted_payload)
        for room in rooms:
            required_width = self._required_window_width(room)
            if required_width <= 0:
                continue
            exterior_sides = self._exterior_sides(room, boundary_width=boundary_width, boundary_height=boundary_height)
            if not exterior_sides:
                if self._window_optional_with_mechanical(room, mechanical_allowed):
                    continue
                raise RuleViolationError(
                    code="WINDOW_REQUIREMENT_FAILED",
                    reason="room has no exterior wall for required window",
                    violated_rule="window-exterior-wall-required",
                    room=room.name,
                )

            preferred_order = self._window_preference_order(room, exterior_sides, orientation_map)
            remaining = required_width
            windows_for_room = 0
            for side in preferred_order:
                if remaining <= _EPSILON:
                    break
                while remaining > _EPSILON:
                    min_chunk = 1.0 if self._is_bedroom(room) and windows_for_room == 0 else 0.6
                    placed = self._place_window_on_side(
                        room=room,
                        side=side,
                        required_width=remaining,
                        min_chunk=min_chunk,
                        boundary_width=boundary_width,
                        boundary_height=boundary_height,
                        columns=columns,
                        occupied=occupied,
                        openings=openings,
                    )
                    if placed <= 0:
                        break
                    remaining -= placed
                    windows_for_room += 1

            if remaining > _EPSILON and not self._window_optional_with_mechanical(room, mechanical_allowed):
                raise RuleViolationError(
                    code="WINDOW_REQUIREMENT_FAILED",
                    reason="insufficient exterior window length for daylight/ventilation rule",
                    violated_rule="window-size-or-ventilation",
                    room=room.name,
                )

        output = dict(layout_payload)
        output["openings"] = openings
        return output

    @staticmethod
    def _to_rooms(rooms_raw: list[Any]) -> list[_RoomBox]:
        rooms: list[_RoomBox] = []
        for raw in rooms_raw:
            if not isinstance(raw, dict):
                continue
            origin = raw.get("origin")
            if not isinstance(origin, dict):
                continue
            name = str(raw.get("name", "")).strip()
            room_type = str(raw.get("room_type", "")).strip().lower()
            width = float(raw.get("width", 0.0))
            height = float(raw.get("height", 0.0))
            x0 = float(origin.get("x", 0.0))
            y0 = float(origin.get("y", 0.0))
            if not name or width <= 0 or height <= 0:
                continue
            rooms.append(
                _RoomBox(
                    name=name,
                    room_type=room_type,
                    x0=x0,
                    y0=y0,
                    x1=x0 + width,
                    y1=y0 + height,
                )
            )
        if not rooms:
            raise RuleViolationError(
                code="OPENING_INPUT_INVALID",
                reason="no valid rooms found for opening placement",
                violated_rule="opening-input",
            )
        return rooms

    @staticmethod
    def _build_shared_boundaries(rooms: list[_RoomBox]) -> dict[tuple[str, str], _SharedBoundary]:
        shared: dict[tuple[str, str], _SharedBoundary] = {}
        touch_tolerance = 0.1
        for idx, room_a in enumerate(rooms):
            for room_b in rooms[idx + 1 :]:
                overlap_x = max(0.0, min(room_a.x1, room_b.x1) - max(room_a.x0, room_b.x0))
                overlap_y = max(0.0, min(room_a.y1, room_b.y1) - max(room_a.y0, room_b.y0))

                vertical_touch = (
                    min(abs(room_a.x1 - room_b.x0), abs(room_b.x1 - room_a.x0)) <= touch_tolerance + _EPSILON
                    and overlap_y > 0.6
                )
                horizontal_touch = (
                    min(abs(room_a.y1 - room_b.y0), abs(room_b.y1 - room_a.y0)) <= touch_tolerance + _EPSILON
                    and overlap_x > 0.6
                )

                if vertical_touch:
                    coordinate = room_a.x1 if abs(room_a.x1 - room_b.x0) <= abs(room_b.x1 - room_a.x0) else room_b.x1
                    key = tuple(sorted((room_a.name, room_b.name)))
                    shared[key] = _SharedBoundary(
                        room_a=room_a.name,
                        room_b=room_b.name,
                        axis="vertical",
                        coordinate=coordinate,
                        start=max(room_a.y0, room_b.y0),
                        end=min(room_a.y1, room_b.y1),
                    )
                    continue
                if horizontal_touch:
                    coordinate = room_a.y1 if abs(room_a.y1 - room_b.y0) <= abs(room_b.y1 - room_a.y0) else room_b.y1
                    key = tuple(sorted((room_a.name, room_b.name)))
                    shared[key] = _SharedBoundary(
                        room_a=room_a.name,
                        room_b=room_b.name,
                        axis="horizontal",
                        coordinate=coordinate,
                        start=max(room_a.x0, room_b.x0),
                        end=min(room_a.x1, room_b.x1),
                    )
        return shared

    @staticmethod
    def _build_neighbors(shared: dict[tuple[str, str], _SharedBoundary]) -> dict[str, set[str]]:
        neighbors: dict[str, set[str]] = {}
        for room_a, room_b in shared.keys():
            neighbors.setdefault(room_a, set()).add(room_b)
            neighbors.setdefault(room_b, set()).add(room_a)
        return neighbors

    @staticmethod
    def _find_main_corridor(rooms: list[_RoomBox]) -> _RoomBox:
        named_main = [room for room in rooms if room.name.lower() == "main corridor"]
        if named_main:
            return named_main[0]
        corridors = [room for room in rooms if room.room_type == "corridor" or "corridor" in room.name.lower()]
        if not corridors:
            raise RuleViolationError(
                code="DOOR_CONNECTIVITY_FAILED",
                reason="corridor spine is required for deterministic circulation",
                violated_rule="corridor-spine-required",
            )
        return max(corridors, key=lambda current: current.area)

    @staticmethod
    def _sorted_room_names(rooms: list[_RoomBox], predicate) -> list[str]:
        return [current.name for current in sorted(rooms, key=lambda current: current.name) if predicate(current)]

    @staticmethod
    def _pick_adjacent_target(
        *,
        source: str,
        candidates: list[str],
        neighbors: dict[str, set[str]],
    ) -> str | None:
        adjacent = neighbors.get(source, set())
        for candidate in candidates:
            if candidate != source and candidate in adjacent:
                return candidate
        return None

    @staticmethod
    def _corridor_targets(*, rooms: list[_RoomBox], main_corridor: str) -> list[str]:
        others = sorted(
            (
                room.name
                for room in rooms
                if room.room_type == "corridor" and room.name != main_corridor
            )
        )
        return [main_corridor] + others

    def _ensure_room_connectivity(
        self,
        *,
        rooms: list[_RoomBox],
        openings: list[dict[str, Any]],
        boundary_width: float,
        boundary_height: float,
    ) -> list[dict[str, Any]]:
        if not rooms:
            return openings

        by_name = {room.name: room for room in rooms}
        room_names = sorted(by_name)
        shared_boundaries = self._build_connectivity_shared_boundaries(rooms)
        neighbor_graph = self._build_neighbors(shared_boundaries)
        columns = self._build_column_grid(width=boundary_width, height=boundary_height)
        augmented_openings = list(openings)
        occupied = self._occupied_from_openings(augmented_openings)
        door_pairs_done = self._door_pairs_from_openings(
            openings=augmented_openings,
            by_name=by_name,
            shared_boundaries=shared_boundaries,
        )
        door_graph = self._door_adjacency(room_names=room_names, door_pairs_done=door_pairs_done)
        hub_name = self._select_connectivity_hub(rooms=rooms, door_adjacency=door_graph)
        all_rooms = set(room_names)
        reachable = self._bfs(start=hub_name, adjacency=door_graph)

        while reachable != all_rooms:
            progress = False
            for room_name in sorted(all_rooms - reachable):
                candidates = self._rank_reachable_connectivity_candidates(
                    room_name=room_name,
                    hub_name=hub_name,
                    reachable=reachable,
                    by_name=by_name,
                    shared_boundaries=shared_boundaries,
                    neighbor_graph=neighbor_graph,
                    occupied=occupied,
                    columns=columns,
                )
                if not candidates:
                    continue

                for _, target_name in candidates:
                    try:
                        self._add_door_between(
                            room_a=room_name,
                            room_b=target_name,
                            by_name=by_name,
                            shared_boundaries=shared_boundaries,
                            columns=columns,
                            occupied=occupied,
                            openings=augmented_openings,
                            door_pairs_done=door_pairs_done,
                            reason_rule="graph-connected",
                        )
                    except RuleViolationError:
                        continue

                    door_graph.setdefault(room_name, set()).add(target_name)
                    door_graph.setdefault(target_name, set()).add(room_name)
                    reachable = self._bfs(start=hub_name, adjacency=door_graph)
                    progress = True
                    break

            if not progress:
                break

        final_pairs = self._door_pairs_from_openings(
            openings=augmented_openings,
            by_name=by_name,
            shared_boundaries=shared_boundaries,
        )
        final_graph = self._door_adjacency(room_names=room_names, door_pairs_done=final_pairs)
        final_reachable = self._bfs(start=hub_name, adjacency=final_graph)
        unreachable = sorted(all_rooms - final_reachable)
        if unreachable:
            logger.warning(
                "[OpeningPlanner] unreachable rooms remain after connectivity pass: hub=%s rooms=%s",
                hub_name,
                unreachable,
            )

        door_counts = self._door_counts_by_room(augmented_openings)
        isolated = sorted(name for name in room_names if door_counts.get(name, 0) <= 0)
        if isolated:
            logger.warning(
                "[OpeningPlanner] rooms still lack door openings after connectivity pass: %s",
                isolated,
            )

        return augmented_openings

    @staticmethod
    def _build_connectivity_shared_boundaries(
        rooms: list[_RoomBox],
    ) -> dict[tuple[str, str], _SharedBoundary]:
        shared: dict[tuple[str, str], _SharedBoundary] = {}
        for idx, room_a in enumerate(rooms):
            for room_b in rooms[idx + 1 :]:
                overlap_x = max(0.0, min(room_a.x1, room_b.x1) - max(room_a.x0, room_b.x0))
                overlap_y = max(0.0, min(room_a.y1, room_b.y1) - max(room_a.y0, room_b.y0))

                right_to_left = abs(room_a.x1 - room_b.x0) <= 0.1 + _EPSILON
                left_to_right = abs(room_a.x0 - room_b.x1) <= 0.1 + _EPSILON
                vertical_touch = (right_to_left or left_to_right) and overlap_y >= 1.0 - _EPSILON

                top_to_bottom = abs(room_a.y1 - room_b.y0) <= 0.1 + _EPSILON
                bottom_to_top = abs(room_a.y0 - room_b.y1) <= 0.1 + _EPSILON
                horizontal_touch = (top_to_bottom or bottom_to_top) and overlap_x >= 1.0 - _EPSILON

                if vertical_touch:
                    coordinate = room_a.x1 if right_to_left else room_b.x1
                    key = tuple(sorted((room_a.name, room_b.name)))
                    shared[key] = _SharedBoundary(
                        room_a=room_a.name,
                        room_b=room_b.name,
                        axis="vertical",
                        coordinate=coordinate,
                        start=max(room_a.y0, room_b.y0),
                        end=min(room_a.y1, room_b.y1),
                    )
                    continue
                if horizontal_touch:
                    coordinate = room_a.y1 if top_to_bottom else room_b.y1
                    key = tuple(sorted((room_a.name, room_b.name)))
                    shared[key] = _SharedBoundary(
                        room_a=room_a.name,
                        room_b=room_b.name,
                        axis="horizontal",
                        coordinate=coordinate,
                        start=max(room_a.x0, room_b.x0),
                        end=min(room_a.x1, room_b.x1),
                    )
        return shared

    def _rank_reachable_connectivity_candidates(
        self,
        *,
        room_name: str,
        hub_name: str,
        reachable: set[str],
        by_name: dict[str, _RoomBox],
        shared_boundaries: dict[tuple[str, str], _SharedBoundary],
        neighbor_graph: dict[str, set[str]],
        occupied: dict[tuple[str, str], list[_PlacedCut]],
        columns: list[tuple[float, float]],
    ) -> list[tuple[tuple[int, float, float, str], str]]:
        room = by_name[room_name]
        candidates: list[tuple[tuple[int, float, float, str], str]] = []
        for neighbor_name in sorted(neighbor_graph.get(room_name, set())):
            if neighbor_name not in reachable:
                continue
            pair = tuple(sorted((room_name, neighbor_name)))
            boundary = shared_boundaries.get(pair)
            if boundary is None:
                continue

            usable_length = self._largest_clear_span(
                room_a=room_name,
                room_b=neighbor_name,
                boundary=boundary,
                by_name=by_name,
                occupied=occupied,
                columns=columns,
            )
            if usable_length <= 0:
                continue

            priority = (
                0 if neighbor_name == hub_name else 1,
                -usable_length,
                self._room_center_distance(room, by_name[neighbor_name]),
                neighbor_name,
            )
            candidates.append((priority, neighbor_name))

        candidates.sort(key=lambda item: item[0])
        return candidates

    def _largest_clear_span(
        self,
        *,
        room_a: str,
        room_b: str,
        boundary: _SharedBoundary,
        by_name: dict[str, _RoomBox],
        occupied: dict[tuple[str, str], list[_PlacedCut]],
        columns: list[tuple[float, float]],
    ) -> float:
        side_a = self._wall_side(by_name[room_a], boundary)
        side_b = self._wall_side(by_name[room_b], boundary)
        blocked = self._collect_blocked_intervals(
            room_name=room_a,
            wall=side_a,
            boundary=boundary,
            occupied=occupied,
            columns=columns,
        ) + self._collect_blocked_intervals(
            room_name=room_b,
            wall=side_b,
            boundary=boundary,
            occupied=occupied,
            columns=columns,
        )
        if not blocked:
            return boundary.length

        merged: list[tuple[float, float]] = []
        for item in sorted(blocked, key=lambda current: (current.start, current.end)):
            start = max(boundary.start, item.start - _OPENING_CLEARANCE)
            end = min(boundary.end, item.end + _OPENING_CLEARANCE)
            if end <= start + _EPSILON:
                continue
            if merged and start <= merged[-1][1] + _EPSILON:
                merged[-1] = (merged[-1][0], max(merged[-1][1], end))
            else:
                merged.append((start, end))

        best = 0.0
        cursor = boundary.start
        for start, end in merged:
            best = max(best, start - cursor)
            cursor = max(cursor, end)
        best = max(best, boundary.end - cursor)
        return best

    @staticmethod
    def _room_center_distance(first: _RoomBox, second: _RoomBox) -> float:
        first_x = first.x0 + (first.width / 2.0)
        first_y = first.y0 + (first.height / 2.0)
        second_x = second.x0 + (second.width / 2.0)
        second_y = second.y0 + (second.height / 2.0)
        return abs(first_x - second_x) + abs(first_y - second_y)

    @staticmethod
    def _select_connectivity_hub(
        *,
        rooms: list[_RoomBox],
        door_adjacency: dict[str, set[str]],
    ) -> str:
        for room in rooms:
            if room.name.lower() == "main corridor":
                return room.name

        corridors = [room for room in rooms if room.room_type == "corridor" or "corridor" in room.name.lower()]
        if corridors:
            return sorted(corridors, key=lambda current: (-current.area, current.name))[0].name

        for room in rooms:
            if room.name.lower() == "living room":
                return room.name

        living_rooms = [room for room in rooms if DeterministicOpeningPlanner._is_living_space(room)]
        if living_rooms:
            return sorted(living_rooms, key=lambda current: (-current.area, current.name))[0].name

        return sorted(
            rooms,
            key=lambda current: (
                -len(door_adjacency.get(current.name, set())),
                -current.area,
                current.name,
            ),
        )[0].name

    @staticmethod
    def _occupied_from_openings(
        openings: list[dict[str, Any]],
    ) -> dict[tuple[str, str], list[_PlacedCut]]:
        occupied: dict[tuple[str, str], list[_PlacedCut]] = {}
        for opening in openings:
            room_name = str(opening.get("room_name", "")).strip()
            wall = str(opening.get("wall", "")).strip()
            cut = DeterministicOpeningPlanner._cut_from_opening(opening)
            if not room_name or not wall or cut is None:
                continue
            occupied.setdefault((room_name, wall), []).append(cut)
        return occupied

    def _door_pairs_from_openings(
        self,
        *,
        openings: list[dict[str, Any]],
        by_name: dict[str, _RoomBox],
        shared_boundaries: dict[tuple[str, str], _SharedBoundary],
    ) -> set[tuple[str, str]]:
        lookup: dict[tuple[str, str], set[tuple[str, float, float, float]]] = {}
        for opening in openings:
            if str(opening.get("type", "")).strip().lower() != "door":
                continue
            room_name = str(opening.get("room_name", "")).strip()
            wall = str(opening.get("wall", "")).strip()
            signature = self._opening_signature(opening)
            if not room_name or not wall or signature is None:
                continue
            lookup.setdefault((room_name, wall), set()).add(signature)

        pairs: set[tuple[str, str]] = set()
        for pair, boundary in shared_boundaries.items():
            room_a, room_b = pair
            first = by_name.get(room_a)
            second = by_name.get(room_b)
            if first is None or second is None:
                continue
            side_a = self._wall_side(first, boundary)
            side_b = self._wall_side(second, boundary)
            if lookup.get((room_a, side_a), set()).intersection(lookup.get((room_b, side_b), set())):
                pairs.add(pair)
        return pairs

    @staticmethod
    def _opening_signature(
        opening: dict[str, Any],
    ) -> tuple[str, float, float, float] | None:
        cut_start = opening.get("cut_start")
        cut_end = opening.get("cut_end")
        if not isinstance(cut_start, dict) or not isinstance(cut_end, dict):
            return None
        try:
            sx = float(cut_start.get("x"))
            sy = float(cut_start.get("y"))
            ex = float(cut_end.get("x"))
            ey = float(cut_end.get("y"))
        except (TypeError, ValueError):
            return None

        if abs(sx - ex) <= _EPSILON:
            return ("vertical", round(sx, 6), round(min(sy, ey), 6), round(max(sy, ey), 6))
        if abs(sy - ey) <= _EPSILON:
            return ("horizontal", round(sy, 6), round(min(sx, ex), 6), round(max(sx, ex), 6))
        return None

    @staticmethod
    def _cut_from_opening(opening: dict[str, Any]) -> _PlacedCut | None:
        signature = DeterministicOpeningPlanner._opening_signature(opening)
        if signature is None:
            return None
        _, _, start, end = signature
        return _PlacedCut(start=start, end=end)

    @staticmethod
    def _door_counts_by_room(openings: list[dict[str, Any]]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for opening in openings:
            if str(opening.get("type", "")).strip().lower() != "door":
                continue
            room_name = str(opening.get("room_name", "")).strip()
            if not room_name:
                continue
            counts[room_name] = counts.get(room_name, 0) + 1
        return counts

    @staticmethod
    def _door_adjacency(
        *,
        room_names: list[str],
        door_pairs_done: set[tuple[str, str]],
    ) -> dict[str, set[str]]:
        adjacency: dict[str, set[str]] = {name: set() for name in room_names}
        for room_a, room_b in door_pairs_done:
            adjacency.setdefault(room_a, set()).add(room_b)
            adjacency.setdefault(room_b, set()).add(room_a)
        return adjacency

    @staticmethod
    def _bfs(*, start: str, adjacency: dict[str, set[str]]) -> set[str]:
        visited: set[str] = set()
        queue = deque([start])
        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)
            for nxt in adjacency.get(current, set()):
                if nxt not in visited:
                    queue.append(nxt)
        return visited

    def _add_door_between(
        self,
        *,
        room_a: str,
        room_b: str,
        by_name: dict[str, _RoomBox],
        shared_boundaries: dict[tuple[str, str], _SharedBoundary],
        columns: list[tuple[float, float]],
        occupied: dict[tuple[str, str], list[_PlacedCut]],
        openings: list[dict[str, Any]],
        door_pairs_done: set[tuple[str, str]],
        reason_rule: str,
    ) -> None:
        if room_a == room_b:
            return
        pair = tuple(sorted((room_a, room_b)))
        if pair in door_pairs_done:
            return
        boundary = shared_boundaries.get(pair)
        if boundary is None:
            raise RuleViolationError(
                code="DOOR_CONNECTIVITY_FAILED",
                reason="required door connection rooms are not adjacent",
                violated_rule=reason_rule,
                room=room_a,
            )

        first = by_name[room_a]
        second = by_name[room_b]
        self._validate_forbidden_door_pair(first=first, second=second)
        bathroom_pair = self._is_bathroom(first) or self._is_bathroom(second)
        preferred_door_width = 0.8 if bathroom_pair else 0.9
        min_door_width = _MIN_BATHROOM_DOOR_WIDTH if bathroom_pair else _MIN_STANDARD_DOOR_WIDTH

        end_clearance = _DOOR_END_CLEARANCE
        available_span = boundary.length - (2.0 * end_clearance)
        if available_span + _EPSILON < preferred_door_width:
            end_clearance = min(
                _DOOR_END_CLEARANCE,
                max(_MIN_DOOR_END_CLEARANCE, (boundary.length - min_door_width) / 2.0),
            )
            available_span = boundary.length - (2.0 * end_clearance)

        door_width = min(preferred_door_width, available_span)
        if door_width + _EPSILON < min_door_width:
            raise RuleViolationError(
                code="DOOR_GEOMETRY_FAILED",
                reason="wall span too short for minimum compliant door width",
                violated_rule="door-on-wall-span",
                room=room_a,
            )

        side_a = self._wall_side(first, boundary)
        side_b = self._wall_side(second, boundary)
        cut = self._allocate_cut(
            boundary=boundary,
            requested_width=door_width,
            blocked=self._collect_blocked_intervals(
                room_name=room_a,
                wall=side_a,
                boundary=boundary,
                occupied=occupied,
                columns=columns,
            )
            + self._collect_blocked_intervals(
                room_name=room_b,
                wall=side_b,
                boundary=boundary,
                occupied=occupied,
                columns=columns,
            ),
            end_clearance=end_clearance,
            corner_clearance=MIN_DOOR_CORNER_CLEARANCE,
        )

        opening_a = self._build_opening_payload(
            room=first,
            wall=side_a,
            boundary=boundary,
            cut=cut,
            opening_type="door",
            is_exterior_wall=False,
            connected_room_type=second.room_type,
        )
        opening_b = self._build_opening_payload(
            room=second,
            wall=side_b,
            boundary=boundary,
            cut=cut,
            opening_type="door",
            is_exterior_wall=False,
            connected_room_type=first.room_type,
        )

        openings.append(opening_a)
        openings.append(opening_b)
        occupied.setdefault((room_a, side_a), []).append(cut)
        occupied.setdefault((room_b, side_b), []).append(cut)
        door_pairs_done.add(pair)

    @staticmethod
    def _validate_forbidden_door_pair(*, first: _RoomBox, second: _RoomBox) -> None:
        names = {first.name.lower(), second.name.lower()}
        first_bath = first.room_type == "bathroom" and "laundry" not in first.name.lower()
        second_bath = second.room_type == "bathroom" and "laundry" not in second.name.lower()
        if first_bath or second_bath:
            if any("kitchen" in value for value in names):
                raise RuleViolationError(
                    code="DOOR_POLICY_FAILED",
                    reason="bathroom doors cannot connect directly to kitchen",
                    violated_rule="bathroom-door-forbidden-kitchen",
                )
            if any("dining" in value for value in names):
                raise RuleViolationError(
                    code="DOOR_POLICY_FAILED",
                    reason="bathroom doors cannot connect directly to dining",
                    violated_rule="bathroom-door-forbidden-dining",
                )

        if first.room_type == "bedroom" or second.room_type == "bedroom":
            if first.room_type == "bedroom" and second.room_type == "bedroom":
                raise RuleViolationError(
                    code="DOOR_POLICY_FAILED",
                    reason="bedroom doors cannot connect directly to other bedrooms",
                    violated_rule="bedroom-door-forbidden-bedroom",
                )
            if first.room_type == "kitchen" or second.room_type == "kitchen":
                raise RuleViolationError(
                    code="DOOR_POLICY_FAILED",
                    reason="bedroom doors cannot connect directly to kitchen",
                    violated_rule="bedroom-door-forbidden-kitchen",
                )

    def _collect_blocked_intervals(
        self,
        *,
        room_name: str,
        wall: str,
        boundary: _SharedBoundary,
        occupied: dict[tuple[str, str], list[_PlacedCut]],
        columns: list[tuple[float, float]],
    ) -> list[_PlacedCut]:
        blocked = list(occupied.get((room_name, wall), []))
        blocked.extend(self._column_blocked_intervals(boundary=boundary, columns=columns))
        return blocked

    @staticmethod
    def _column_blocked_intervals(
        *,
        boundary: _SharedBoundary,
        columns: list[tuple[float, float]],
    ) -> list[_PlacedCut]:
        blocked: list[_PlacedCut] = []
        for column_x, column_y in columns:
            if boundary.axis == "vertical":
                if abs(column_x - boundary.coordinate) <= _EPSILON and boundary.start <= column_y <= boundary.end:
                    blocked.append(_PlacedCut(start=column_y - _COLUMN_CLEARANCE, end=column_y + _COLUMN_CLEARANCE))
            else:
                if abs(column_y - boundary.coordinate) <= _EPSILON and boundary.start <= column_x <= boundary.end:
                    blocked.append(_PlacedCut(start=column_x - _COLUMN_CLEARANCE, end=column_x + _COLUMN_CLEARANCE))
        return blocked

    def _allocate_cut(
        self,
        *,
        boundary: _SharedBoundary,
        requested_width: float,
        blocked: list[_PlacedCut],
        end_clearance: float,
        corner_clearance: float | None = None,
    ) -> _PlacedCut:
        candidate_segments: list[tuple[float, float]] = []
        if corner_clearance is not None:
            preferred_start = boundary.start + corner_clearance
            preferred_end = boundary.end - corner_clearance
            if (preferred_end - preferred_start) + _EPSILON >= requested_width:
                candidate_segments.append((preferred_start, preferred_end))

        fallback_start = boundary.start + end_clearance
        fallback_end = boundary.end - end_clearance
        if (fallback_end - fallback_start) + _EPSILON < requested_width:
            raise RuleViolationError(
                code="DOOR_GEOMETRY_FAILED",
                reason="wall span too short for deterministic opening",
                violated_rule="door-on-wall-span",
            )
        if all(
            abs(fallback_start - start) > _EPSILON or abs(fallback_end - end) > _EPSILON
            for start, end in candidate_segments
        ):
            candidate_segments.append((fallback_start, fallback_end))

        for segment_start, segment_end in candidate_segments:
            for start in self._candidate_starts(
                segment_start=segment_start,
                segment_end=segment_end,
                width=requested_width,
            ):
                cut = _PlacedCut(start=start, end=start + requested_width)
                if self._interval_conflicts(cut=cut, blocked=blocked):
                    continue
                return cut

        raise RuleViolationError(
            code="DOOR_GEOMETRY_FAILED",
            reason="unable to place opening without collisions",
            violated_rule="door-clearance",
        )

    @staticmethod
    def _candidate_starts(
        *,
        segment_start: float,
        segment_end: float,
        width: float,
    ) -> list[float]:
        available = segment_end - segment_start - width
        if available < 0:
            return []
        if available <= _EPSILON:
            return [segment_start]

        raw = [segment_start + available * (step / 24.0) for step in range(25)]
        center = segment_start + available / 2.0
        ordered = sorted(raw, key=lambda value: (abs(value - center), value))
        deduped: list[float] = []
        for value in ordered:
            if all(abs(value - existing) > 1e-6 for existing in deduped):
                deduped.append(value)
        return deduped

    @staticmethod
    def _interval_conflicts(*, cut: _PlacedCut, blocked: list[_PlacedCut]) -> bool:
        for item in blocked:
            if cut.start < item.end + _OPENING_CLEARANCE and cut.end > item.start - _OPENING_CLEARANCE:
                return True
        return False

    @staticmethod
    def _wall_side(room: _RoomBox, boundary: _SharedBoundary) -> str:
        if boundary.axis == "vertical":
            if abs(room.x1 - boundary.coordinate) <= _EPSILON:
                return "right"
            return "left"
        if abs(room.y1 - boundary.coordinate) <= _EPSILON:
            return "top"
        return "bottom"

    @staticmethod
    def _build_opening_payload(
        *,
        room: _RoomBox,
        wall: str,
        boundary: _SharedBoundary,
        cut: _PlacedCut,
        opening_type: Literal["door", "window"],
        is_exterior_wall: bool = False,
        connected_room_type: str | None = None,
    ) -> dict[str, Any]:
        if boundary.axis == "vertical":
            cut_start = {"x": boundary.coordinate, "y": cut.start}
            cut_end = {"x": boundary.coordinate, "y": cut.end}
        else:
            cut_start = {"x": cut.start, "y": boundary.coordinate}
            cut_end = {"x": cut.end, "y": boundary.coordinate}

        payload: dict[str, Any] = {
            "type": opening_type,
            "room_name": room.name,
            "wall": wall,
            "cut_start": cut_start,
            "cut_end": cut_end,
        }
        if opening_type == "door":
            hinge, swing = DeterministicOpeningPlanner._determine_door_swing(
                room_type=room.room_type,
                wall_side=wall,
                is_exterior_wall=is_exterior_wall,
                connected_room_type=connected_room_type,
            )
            payload["hinge"] = hinge
            payload["swing"] = swing
        return payload

    @staticmethod
    def _determine_door_swing(
        *,
        room_type: str,
        wall_side: str,
        is_exterior_wall: bool,
        connected_room_type: str | None,
    ) -> tuple[str, str]:
        """
        Determine door hinge side and swing direction for a room-facing door payload.

        All current planner-generated doors are interior, but the helper keeps the
        exterior-wall flag and connected-room type so future call sites can reuse it.
        """

        del is_exterior_wall
        del connected_room_type

        swing = "in"
        hinge = "left"

        if room_type == "bathroom":
            if wall_side in ("bottom", "top"):
                hinge = "right"
            else:
                hinge = "left"

        if room_type == "corridor":
            swing = "out"

        return hinge, swing

    def _place_window_on_side(
        self,
        *,
        room: _RoomBox,
        side: str,
        required_width: float,
        min_chunk: float,
        boundary_width: float,
        boundary_height: float,
        columns: list[tuple[float, float]],
        occupied: dict[tuple[str, str], list[_PlacedCut]],
        openings: list[dict[str, Any]],
    ) -> float:
        boundary = self._boundary_for_room_side(room=room, side=side)
        blocked = list(occupied.get((room.name, side), []))
        blocked.extend(self._column_blocked_intervals(boundary=boundary, columns=columns))

        segment_start = boundary.start + 0.15
        segment_end = boundary.end - 0.15
        max_possible = segment_end - segment_start
        if max_possible < min_chunk - _EPSILON:
            return 0.0

        target = min(required_width, max_possible, 2.8)
        target = max(target, min_chunk)
        if target > max_possible + _EPSILON:
            return 0.0

        span = max(0.0, target - min_chunk)
        steps = int(span / 0.1)
        candidate_widths: list[float] = [target]
        for step in range(1, steps + 1):
            value = target - (step * 0.1)
            if value > min_chunk + _EPSILON:
                candidate_widths.append(value)
        candidate_widths.append(min_chunk)

        cut: _PlacedCut | None = None
        for requested_width in candidate_widths:
            try:
                cut = self._allocate_cut(
                    boundary=boundary,
                    requested_width=requested_width,
                    blocked=blocked,
                    end_clearance=0.15,
                )
                break
            except RuleViolationError:
                continue
        if cut is None:
            return 0.0

        opening = self._build_opening_payload(
            room=room,
            wall=side,
            boundary=boundary,
            cut=cut,
            opening_type="window",
        )
        openings.append(opening)
        occupied.setdefault((room.name, side), []).append(cut)
        return cut.end - cut.start

    @staticmethod
    def _boundary_for_room_side(*, room: _RoomBox, side: str) -> _SharedBoundary:
        if side == "left":
            return _SharedBoundary(
                room_a=room.name,
                room_b="__exterior__",
                axis="vertical",
                coordinate=room.x0,
                start=room.y0,
                end=room.y1,
            )
        if side == "right":
            return _SharedBoundary(
                room_a=room.name,
                room_b="__exterior__",
                axis="vertical",
                coordinate=room.x1,
                start=room.y0,
                end=room.y1,
            )
        if side == "bottom":
            return _SharedBoundary(
                room_a=room.name,
                room_b="__exterior__",
                axis="horizontal",
                coordinate=room.y0,
                start=room.x0,
                end=room.x1,
            )
        return _SharedBoundary(
            room_a=room.name,
            room_b="__exterior__",
            axis="horizontal",
            coordinate=room.y1,
            start=room.x0,
            end=room.x1,
        )

    @staticmethod
    def _required_window_width(room: _RoomBox) -> float:
        name = room.name.lower()
        if room.room_type == "bedroom":
            return 1.0
        if room.room_type == "living" and "living" in name:
            return max(1.0, (room.area * _LIVING_WINDOW_RATIO_MIN) / _DEFAULT_WINDOW_HEIGHT)
        if room.room_type == "kitchen":
            return 1.0
        if room.room_type == "bathroom" and "laundry" not in name:
            return 0.6
        return 0.0

    @staticmethod
    def _window_optional_with_mechanical(room: _RoomBox, mechanical_allowed: bool) -> bool:
        if not mechanical_allowed:
            return False
        if room.room_type == "kitchen":
            return True
        if room.room_type == "bathroom" and "laundry" not in room.name.lower():
            return True
        return False

    @staticmethod
    def _mechanical_ventilation_allowed(extracted_payload: dict[str, Any]) -> bool:
        constraints = extracted_payload.get("constraints")
        if not isinstance(constraints, dict):
            return False
        notes = constraints.get("notes")
        if not isinstance(notes, list):
            return False
        joined = " ".join(str(note).lower() for note in notes)
        return "mechanical ventilation" in joined or "mech ventilation" in joined

    @staticmethod
    def _exterior_sides(
        room: _RoomBox,
        *,
        boundary_width: float,
        boundary_height: float,
    ) -> list[str]:
        sides: list[str] = []
        if abs(room.x0 - 0.0) <= _EPSILON:
            sides.append("left")
        if abs(room.x1 - boundary_width) <= _EPSILON:
            sides.append("right")
        if abs(room.y0 - 0.0) <= _EPSILON:
            sides.append("bottom")
        if abs(room.y1 - boundary_height) <= _EPSILON:
            sides.append("top")
        return sides

    def _window_preference_order(
        self,
        room: _RoomBox,
        exterior_sides: list[str],
        orientation_map: dict[str, str],
    ) -> list[str]:
        side_priority: list[str]
        name = room.name.lower()
        if room.room_type == "living" and ("living" in name or "dining" in name):
            side_priority = self._sides_by_compass_priority(
                compass_priority=["south", "east", "north", "west"],
                orientation_map=orientation_map,
            )
        elif room.room_type == "bedroom":
            side_priority = self._sides_by_compass_priority(
                compass_priority=["east", "north", "south", "west"],
                orientation_map=orientation_map,
            )
        elif room.room_type == "kitchen":
            side_priority = self._sides_by_compass_priority(
                compass_priority=["west", "north", "east", "south"],
                orientation_map=orientation_map,
            )
        else:
            side_priority = self._sides_by_compass_priority(
                compass_priority=["north", "east", "south", "west"],
                orientation_map=orientation_map,
            )

        ordered = [side for side in side_priority if side in exterior_sides]
        for side in exterior_sides:
            if side not in ordered:
                ordered.append(side)
        return ordered

    @staticmethod
    def _sides_by_compass_priority(
        *,
        compass_priority: list[str],
        orientation_map: dict[str, str],
    ) -> list[str]:
        side_for_compass = {compass: side for side, compass in orientation_map.items()}
        ordered: list[str] = []
        for compass in compass_priority:
            side = side_for_compass.get(compass)
            if side is not None:
                ordered.append(side)
        return ordered

    @staticmethod
    def _resolve_orientation_map(extracted_payload: dict[str, Any]) -> dict[str, str]:
        constraints = extracted_payload.get("constraints")
        notes = constraints.get("notes") if isinstance(constraints, dict) else []
        joined = " ".join(str(note).lower() for note in notes) if isinstance(notes, list) else ""
        directions = ("north", "east", "south", "west")
        top_direction = "north"
        for direction in directions:
            if f"top boundary {direction}" in joined or f"top is {direction}" in joined:
                top_direction = direction
                break
            if f"{direction}-facing top" in joined:
                top_direction = direction
                break

        compass_ring = ["north", "east", "south", "west"]
        top_index = compass_ring.index(top_direction)
        return {
            "top": compass_ring[top_index],
            "right": compass_ring[(top_index + 1) % 4],
            "bottom": compass_ring[(top_index + 2) % 4],
            "left": compass_ring[(top_index + 3) % 4],
        }

    @staticmethod
    def _build_column_grid(*, width: float, height: float) -> list[tuple[float, float]]:
        x_lines = DeterministicOpeningPlanner._axis_grid(width)
        y_lines = DeterministicOpeningPlanner._axis_grid(height)
        return [(x, y) for x, y in product(x_lines, y_lines)]

    @staticmethod
    def _axis_grid(length: float) -> list[float]:
        candidates: list[tuple[int, float]] = []
        max_segments = max(1, int(length // 3))
        for segments in range(1, max_segments + 1):
            span = length / segments
            if 3.0 - _EPSILON <= span <= 6.0 + _EPSILON:
                candidates.append((segments, span))

        if candidates:
            selected_segments, _ = min(candidates, key=lambda item: abs(item[1] - 4.0))
        else:
            selected_segments = max(1, round(length / 4.0))
        step = length / selected_segments
        return [round(step * idx, 6) for idx in range(selected_segments + 1)]

    @staticmethod
    def _is_bedroom(room: _RoomBox) -> bool:
        return room.room_type == "bedroom"

    @staticmethod
    def _is_bathroom(room: _RoomBox) -> bool:
        return room.room_type == "bathroom"

    @staticmethod
    def _is_laundry(room: _RoomBox) -> bool:
        return room.room_type == "bathroom" and "laundry" in room.name.lower()

    @staticmethod
    def _is_storage(room: _RoomBox) -> bool:
        return "storage" in room.name.lower()

    @staticmethod
    def _is_kitchen(room: _RoomBox) -> bool:
        return room.room_type == "kitchen"

    @staticmethod
    def _is_dining(room: _RoomBox) -> bool:
        return room.room_type == "living" and "dining" in room.name.lower()

    @staticmethod
    def _is_living_space(room: _RoomBox) -> bool:
        return room.room_type == "living" and "dining" not in room.name.lower()

    @staticmethod
    def _is_living_main(room: _RoomBox) -> bool:
        return room.room_type == "living" and "living" in room.name.lower()
