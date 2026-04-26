"""Deterministic semantic validation for architectural layouts."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from itertools import product
from typing import Any

from app.services.design_parser.rule_violation import RuleViolationError


_EPSILON = 1e-6
_WINDOW_HEIGHT_FACTOR = 1.2
_LIVING_WINDOW_RATIO_MIN = 0.05
_CORRIDOR_MIN_SPAN = 1.1
_CORRIDOR_MAX_SPAN = 2.0
_CORRIDOR_MAX_RATIO = 0.18
_CORRIDOR_VS_LARGEST_RATIO = 0.85
_EFFICIENCY_MIN_ACCEPT = 0.75
_OVERALL_SCORE_THRESHOLD = 0.72
_MAX_ROOM_AREA_RATIO = 0.35
_MAX_LIVING_AREA_RATIO = 0.28
_MAX_STRUCTURAL_SPAN = 7.0
_EXTERIOR_CONTINUITY_TOLERANCE = 0.22

_W_AREA_BALANCE = 0.18
_W_ZONING = 0.16
_W_CIRCULATION = 0.14
_W_DAYLIGHT = 0.12
_W_STRUCTURAL = 0.10
_W_FURNITURE = 0.14
_W_EFFICIENCY = 0.16


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

    @property
    def cx(self) -> float:
        return (self.x0 + self.x1) / 2.0

    @property
    def cy(self) -> float:
        return (self.y0 + self.y1) / 2.0


@dataclass(frozen=True)
class _OpeningCut:
    type: str
    room_name: str
    wall: str
    start_x: float
    start_y: float
    end_x: float
    end_y: float
    hinge: str | None
    swing: str | None

    @property
    def length(self) -> float:
        if abs(self.start_x - self.end_x) <= _EPSILON:
            return abs(self.end_y - self.start_y)
        return abs(self.end_x - self.start_x)

    @property
    def center(self) -> tuple[float, float]:
        return ((self.start_x + self.end_x) / 2.0, (self.start_y + self.end_y) / 2.0)


@dataclass(frozen=True)
class LayoutValidationMetrics:
    area_balance: float
    zoning: float
    circulation: float
    daylight: float
    structural: float
    furniture: float
    efficiency: float
    total_score: float
    selected_topology: str


class LayoutValidator:
    """Validates architectural quality, circulation, daylight, and structural logic."""

    def validate(
        self,
        *,
        extracted_payload: dict[str, Any],
        planned_payload: dict[str, Any],
        selected_topology: str = "unknown",
    ) -> LayoutValidationMetrics:
        boundary = planned_payload.get("boundary")
        rooms_raw = planned_payload.get("rooms")
        openings_raw = planned_payload.get("openings", [])
        walls_raw = planned_payload.get("walls", [])
        if not isinstance(boundary, dict) or not isinstance(rooms_raw, list):
            self._violate(
                code="LAYOUT_VALIDATION_FAILED",
                reason="planned payload must include boundary and rooms",
                rule="layout-input",
            )

        boundary_width = float(boundary.get("width", 0.0))
        boundary_height = float(boundary.get("height", 0.0))
        if boundary_width <= 0 or boundary_height <= 0:
            self._violate(
                code="LAYOUT_VALIDATION_FAILED",
                reason="boundary dimensions must be positive",
                rule="layout-input",
            )

        rooms = self._to_rooms(rooms_raw)
        room_by_name = {room.name: room for room in rooms}
        openings = self._to_openings(openings_raw)
        wall_adjacency = self._build_wall_adjacency(rooms)
        door_edges, door_neighbors = self._build_door_graph(openings, wall_adjacency)
        orientation_map = self._resolve_orientation_map(extracted_payload)
        mechanical_allowed = self._mechanical_ventilation_allowed(extracted_payload)
        boundary_area = boundary_width * boundary_height

        self._check_program_completeness(extracted_payload, rooms)
        corridor_rooms, corridor_area = self._check_corridor_limits(rooms=rooms, boundary_area=boundary_area)
        self._check_hard_layout_limits(
            rooms=rooms,
            boundary_area=boundary_area,
            corridor_area=corridor_area,
        )
        self._check_room_proportion_rules(rooms, wall_adjacency)
        self._check_door_logic(rooms, door_neighbors)
        self._check_window_logic(
            rooms=rooms,
            openings=openings,
            boundary_width=boundary_width,
            boundary_height=boundary_height,
            mechanical_allowed=mechanical_allowed,
        )
        self._check_sunlight_rules(
            rooms=rooms,
            openings=openings,
            boundary_width=boundary_width,
            boundary_height=boundary_height,
            orientation_map=orientation_map,
        )
        zoning_score = self._check_zoning_rules(
            rooms=rooms,
            door_neighbors=door_neighbors,
            wall_adjacency=wall_adjacency,
        )
        circulation_depth = self._check_circulation_graph(
            rooms=rooms,
            door_neighbors=door_neighbors,
            corridor=self._find_main_corridor(rooms),
        )
        structural_score = self._check_structural_wall_continuity(
            walls_raw=walls_raw,
            boundary_width=boundary_width,
            boundary_height=boundary_height,
        )
        self._check_column_grid_compatibility(
            boundary_width=boundary_width,
            boundary_height=boundary_height,
            openings=openings,
        )
        furniture_fit_score = self._check_furniture_clearance(rooms)

        # Door edges must map to valid rooms only.
        for room_a, room_b in door_edges:
            if room_a not in room_by_name or room_b not in room_by_name:
                self._violate(
                    code="DOOR_GRAPH_INVALID",
                    reason="door graph references unknown room",
                    rule="door-graph-room-reference",
                )

        efficiency_ratio = self._efficiency_ratio(
            boundary_area=boundary_area,
            rooms=rooms,
            corridor_area=corridor_area,
        )
        self._check_efficiency_rules(efficiency_ratio=efficiency_ratio)
        area_balance_score = self._area_balance_score(rooms=rooms, boundary_area=boundary_area)
        circulation_quality = self._circulation_quality_score(circulation_depth)
        daylight_score = self._daylight_score(
            rooms=rooms,
            openings=openings,
        )
        overall_score = (
            (_W_AREA_BALANCE * area_balance_score)
            + (_W_ZONING * zoning_score)
            + (_W_CIRCULATION * circulation_quality)
            + (_W_DAYLIGHT * daylight_score)
            + (_W_STRUCTURAL * structural_score)
            + (_W_FURNITURE * furniture_fit_score)
            + (_W_EFFICIENCY * efficiency_ratio)
        )
        if overall_score + _EPSILON < _OVERALL_SCORE_THRESHOLD:
            self._violate(
                code="LAYOUT_SCORE_TOO_LOW",
                reason=(
                    f"layout overall score {overall_score:.3f} is below "
                    f"threshold {_OVERALL_SCORE_THRESHOLD:.3f}"
                ),
                rule="multi-objective-score-threshold",
            )

        _ = corridor_rooms  # explicit to keep corridor checks in signature for future use.
        return LayoutValidationMetrics(
            area_balance=round(area_balance_score, 4),
            zoning=round(zoning_score, 4),
            circulation=round(circulation_quality, 4),
            daylight=round(daylight_score, 4),
            structural=round(structural_score, 4),
            furniture=round(furniture_fit_score, 4),
            efficiency=round(efficiency_ratio, 4),
            total_score=round(overall_score, 4),
            selected_topology=selected_topology,
        )

    def _check_corridor_limits(
        self,
        *,
        rooms: list[_RoomBox],
        boundary_area: float,
    ) -> tuple[list[_RoomBox], float]:
        corridors = [room for room in rooms if room.room_type == "corridor" or "corridor" in room.name.lower()]
        corridors = [room for room in corridors if "storage" not in room.name.lower()]
        if not corridors:
            self._violate(
                code="CORRIDOR_RULE_FAILED",
                reason="central corridor spine is required",
                rule="corridor-required",
            )

        corridor_area = sum(room.area for room in corridors)
        non_corridor = [room for room in rooms if room not in corridors]
        if not non_corridor:
            self._violate(
                code="CORRIDOR_RULE_FAILED",
                reason="layout must include usable non-corridor rooms",
                rule="corridor-usable-space",
            )

        largest_non_corridor = max(room.area for room in non_corridor)
        for corridor in corridors:
            span = min(corridor.width, corridor.height)
            if span < _CORRIDOR_MIN_SPAN - _EPSILON or span > _CORRIDOR_MAX_SPAN + _EPSILON:
                self._violate(
                    code="CORRIDOR_RULE_FAILED",
                    reason="corridor width must stay between 1.1m and 2.0m",
                    rule="corridor-width-range",
                    room=corridor.name,
                )
            if corridor.area >= largest_non_corridor - _EPSILON:
                self._violate(
                    code="CORRIDOR_RULE_FAILED",
                    reason="corridor cannot be the largest room",
                    rule="corridor-not-largest",
                    room=corridor.name,
                )
            if corridor.area > (largest_non_corridor * _CORRIDOR_VS_LARGEST_RATIO) + _EPSILON:
                self._violate(
                    code="CORRIDOR_RULE_FAILED",
                    reason="corridor area cannot exceed 85% of largest room area",
                    rule="corridor-vs-largest-room",
                    room=corridor.name,
                )

        if corridor_area > (_CORRIDOR_MAX_RATIO * boundary_area) + _EPSILON:
            self._violate(
                code="CORRIDOR_RULE_FAILED",
                reason="total corridor area cannot exceed 18% of boundary area",
                rule="corridor-area-ratio",
            )
        return corridors, corridor_area

    def _check_hard_layout_limits(
        self,
        *,
        rooms: list[_RoomBox],
        boundary_area: float,
        corridor_area: float,
    ) -> None:
        for room in rooms:
            if room.area - (boundary_area * _MAX_ROOM_AREA_RATIO) > _EPSILON:
                self._violate(
                    code="HARD_CONSTRAINT_FAILED",
                    reason="a room exceeds 35% of boundary area",
                    rule="room-max-area-ratio",
                    room=room.name,
                )
            if room.room_type == "living" and "living" in room.name.lower():
                if room.area - (boundary_area * _MAX_LIVING_AREA_RATIO) > _EPSILON:
                    self._violate(
                        code="HARD_CONSTRAINT_FAILED",
                        reason="living room exceeds 28% of boundary area",
                        rule="living-max-area-ratio",
                        room=room.name,
                    )

            if room.room_type in {"bedroom", "stairs"} and min(room.width, room.height) - _MAX_STRUCTURAL_SPAN > _EPSILON:
                self._violate(
                    code="HARD_CONSTRAINT_FAILED",
                    reason=f"structural span exceeds {int(_MAX_STRUCTURAL_SPAN)}m without deterministic support segmentation",
                    rule="structural-max-span",
                    room=room.name,
                )

        if corridor_area - (_CORRIDOR_MAX_RATIO * boundary_area) > _EPSILON:
            self._violate(
                code="HARD_CONSTRAINT_FAILED",
                reason="corridor area exceeds 18% of boundary area",
                rule="corridor-max-area-ratio",
            )

    @staticmethod
    def _efficiency_ratio(*, boundary_area: float, rooms: list[_RoomBox], corridor_area: float) -> float:
        if boundary_area <= _EPSILON:
            return 0.0
        usable = sum(room.area for room in rooms) - corridor_area
        return max(0.0, min(1.0, usable / boundary_area))

    def _check_efficiency_rules(self, *, efficiency_ratio: float) -> None:
        if efficiency_ratio + _EPSILON < _EFFICIENCY_MIN_ACCEPT:
            self._violate(
                code="LAYOUT_EFFICIENCY_FAILED",
                reason=(
                    f"layout efficiency ratio {efficiency_ratio:.3f} is below 0.75"
                ),
                rule="layout-efficiency-minimum",
            )

    def _area_balance_score(self, *, rooms: list[_RoomBox], boundary_area: float) -> float:
        public_area = 0.0
        private_area = 0.0
        service_area = 0.0
        hierarchy_areas: list[float] = []
        for room in rooms:
            lowered = room.name.lower()
            if room.room_type == "corridor":
                continue

            if room.room_type == "bedroom" or (room.room_type == "bathroom" and "guest" not in lowered and "laundry" not in lowered):
                private_area += room.area
            elif room.room_type == "kitchen" or "laundry" in lowered or "storage" in lowered:
                service_area += room.area
            else:
                public_area += room.area

            if "storage" not in lowered:
                hierarchy_areas.append(room.area)

        def in_band_score(ratio: float, low: float, high: float) -> float:
            if low <= ratio <= high:
                return 1.0
            if ratio < low:
                return max(0.0, 1.0 - ((low - ratio) / max(low, _EPSILON)))
            return max(0.0, 1.0 - ((ratio - high) / max(1.0 - high, _EPSILON)))

        public_ratio = public_area / max(boundary_area, _EPSILON)
        private_ratio = private_area / max(boundary_area, _EPSILON)
        service_ratio = service_area / max(boundary_area, _EPSILON)
        zone_score = (
            in_band_score(public_ratio, 0.30, 0.45)
            + in_band_score(private_ratio, 0.30, 0.45)
            + in_band_score(service_ratio, 0.15, 0.25)
        ) / 3.0

        hierarchy_score = 1.0
        if len(hierarchy_areas) >= 2:
            largest = max(hierarchy_areas)
            smallest = max(min(hierarchy_areas), _EPSILON)
            ratio = largest / smallest
            if ratio > 2.5:
                hierarchy_score = max(0.0, 1.0 - ((ratio - 2.5) / 2.5))

        return max(0.0, min(1.0, (0.75 * zone_score) + (0.25 * hierarchy_score)))

    @staticmethod
    def _circulation_quality_score(circulation_depth: int) -> float:
        if circulation_depth <= 1:
            return 1.0
        if circulation_depth == 2:
            return 0.9
        if circulation_depth == 3:
            return 0.7
        return 0.5

    def _daylight_score(self, *, rooms: list[_RoomBox], openings: list[_OpeningCut]) -> float:
        windows_by_room: dict[str, list[_OpeningCut]] = defaultdict(list)
        for opening in openings:
            if opening.type == "window":
                windows_by_room[opening.room_name].append(opening)

        measured: list[float] = []
        for room in rooms:
            lowered = room.name.lower()
            if room.room_type == "living" and "living" in lowered:
                window_area = sum(window.length * _WINDOW_HEIGHT_FACTOR for window in windows_by_room.get(room.name, []))
                ratio = window_area / max(room.area, _EPSILON)
                measured.append(min(1.0, ratio / _LIVING_WINDOW_RATIO_MIN))
            elif room.room_type == "bedroom":
                has_window = 1.0 if windows_by_room.get(room.name) else 0.0
                measured.append(has_window)
            elif room.room_type == "kitchen":
                has_window = 1.0 if windows_by_room.get(room.name) else 0.7
                measured.append(has_window)
            elif room.room_type == "bathroom" and "laundry" not in lowered:
                has_window = 1.0 if windows_by_room.get(room.name) else 0.6
                measured.append(has_window)

        if not measured:
            return 1.0
        return max(0.0, min(1.0, sum(measured) / len(measured)))

    def _check_program_completeness(self, extracted_payload: dict[str, Any], rooms: list[_RoomBox]) -> None:
        room_program = extracted_payload.get("room_program")
        if not isinstance(room_program, list):
            self._violate(
                code="PROGRAM_COMPLETENESS_FAILED",
                reason="extracted payload missing room_program",
                rule="program-completeness",
            )

        expected_names: list[str] = []
        for raw in room_program:
            if not isinstance(raw, dict):
                continue
            name = str(raw.get("name", "")).strip()
            count = int(raw.get("count", 1))
            if not name:
                continue
            if count <= 1:
                expected_names.append(name)
            else:
                expected_names.extend(f"{name} {idx + 1}" for idx in range(count))

        actual_names = {room.name for room in rooms}
        missing = [name for name in expected_names if name not in actual_names]
        if missing:
            self._violate(
                code="PROGRAM_COMPLETENESS_FAILED",
                reason=f"missing rooms: {missing}",
                rule="program-completeness",
            )

    def _check_room_proportion_rules(
        self,
        rooms: list[_RoomBox],
        wall_adjacency: dict[str, set[str]],
    ) -> None:
        living_public_areas: list[float] = []
        master_area: float | None = None
        children_areas: list[float] = []
        room_by_name = {room.name: room for room in rooms}

        for room in rooms:
            if room.room_type != "corridor" and min(room.width, room.height) < 1.0 - _EPSILON:
                self._violate(
                    code="SPACE_WASTE_DETECTED",
                    reason="sliver space detected with width below 1.0m",
                    rule="sliver-space-width",
                    room=room.name,
                )
            ratio = max(room.width, room.height) / max(min(room.width, room.height), _EPSILON)
            if room.room_type not in {"corridor", "bathroom"} and ratio > 4.0:
                self._violate(
                    code="ROOM_PROPORTION_INVALID",
                    reason="room aspect ratio is irrational for residential layout",
                    rule="room-proportion",
                    room=room.name,
                )

            lowered = room.name.lower()
            if room.room_type == "bedroom":
                if "master" in lowered:
                    if room.area < 12.0 - _EPSILON:
                        self._violate(
                            code="ROOM_PROPORTION_INVALID",
                            reason="master bedroom area must be at least 12 sqm",
                            rule="master-bedroom-area",
                            room=room.name,
                        )
                    master_area = room.area
                elif "child" in lowered or "kid" in lowered:
                    if room.area < 9.0 - _EPSILON:
                        self._violate(
                            code="ROOM_PROPORTION_INVALID",
                            reason="children bedroom area must be at least 9 sqm",
                            rule="children-bedroom-area",
                            room=room.name,
                        )
                    children_areas.append(room.area)
                else:
                    if room.area < 9.0 - _EPSILON:
                        self._violate(
                            code="ROOM_PROPORTION_INVALID",
                            reason="bedroom area must be at least 9 sqm",
                            rule="bedroom-area",
                            room=room.name,
                        )

            if room.room_type == "living":
                if "living" in lowered:
                    if room.area < 12.0 - _EPSILON:
                        self._violate(
                            code="ROOM_PROPORTION_INVALID",
                            reason="living room area must be at least 12 sqm",
                            rule="living-room-area",
                            room=room.name,
                        )
                    living_public_areas.append(room.area)
                elif "dining" in lowered:
                    if room.area < 10.0 - _EPSILON or room.area > 20.0 + _EPSILON:
                        self._violate(
                            code="ROOM_PROPORTION_INVALID",
                            reason="dining area must be between 10 and 20 sqm",
                            rule="dining-area",
                            room=room.name,
                        )
                    living_public_areas.append(room.area)

            if room.room_type == "kitchen":
                if room.area < 6.0 - _EPSILON:
                    self._violate(
                        code="ROOM_PROPORTION_INVALID",
                        reason="kitchen area must be at least 6 sqm",
                        rule="kitchen-area",
                        room=room.name,
                    )
                if min(room.width, room.height) < 2.2 - _EPSILON:
                    self._violate(
                        code="ROOM_PROPORTION_INVALID",
                        reason="kitchen minimum clear width must be >= 2.2m",
                        rule="kitchen-min-width",
                        room=room.name,
                    )

            if room.room_type == "bathroom":
                if "laundry" in lowered:
                    if room.area < 3.5 - _EPSILON:
                        self._violate(
                            code="ROOM_PROPORTION_INVALID",
                            reason="laundry must be at least 3.5 sqm",
                            rule="laundry-area",
                            room=room.name,
                        )
                else:
                    if room.area < 3.5 - _EPSILON:
                        self._violate(
                            code="ROOM_PROPORTION_INVALID",
                            reason="bathroom area must be at least 3.5 sqm",
                            rule="bathroom-area",
                            room=room.name,
                        )
                    if min(room.width, room.height) < 1.5 - _EPSILON:
                        self._violate(
                            code="ROOM_PROPORTION_INVALID",
                            reason="bathroom minimum width must be >= 1.5m",
                            rule="bathroom-min-width",
                            room=room.name,
                        )
                    neighbor_bedrooms = [
                        room_by_name[name]
                        for name in wall_adjacency.get(room.name, set())
                        if room_by_name[name].room_type == "bedroom"
                    ]
                    if neighbor_bedrooms:
                        max_neighbor_bedroom = max(neighbor.area for neighbor in neighbor_bedrooms)
                        if room.area > max_neighbor_bedroom + _EPSILON:
                            self._violate(
                                code="ROOM_PROPORTION_INVALID",
                                reason="bathroom area cannot exceed adjacent bedroom area",
                                rule="bathroom-vs-bedroom-area",
                                room=room.name,
                            )

            if "storage" in lowered:
                if room.area < 2.0 - _EPSILON or room.area > 6.0 + _EPSILON:
                    self._violate(
                        code="ROOM_PROPORTION_INVALID",
                        reason="storage area must be between 2 and 6 sqm",
                        rule="storage-area",
                        room=room.name,
                    )

        if master_area is not None and children_areas:
            if any((child - master_area) > 0.05 for child in children_areas):
                self._violate(
                    code="ROOM_PROPORTION_INVALID",
                    reason="master bedroom cannot be smaller than any children bedroom",
                    rule="master-larger-than-children",
                )

        public_living = [room.area for room in rooms if room.room_type == "living" and "living" in room.name.lower()]
        if public_living and living_public_areas:
            if max(public_living) + _EPSILON < max(living_public_areas):
                self._violate(
                    code="ROOM_PROPORTION_INVALID",
                    reason="living room must be the largest public space",
                    rule="living-largest-public-space",
                )

    def _check_door_logic(self, rooms: list[_RoomBox], door_neighbors: dict[str, set[str]]) -> None:
        _ = self._find_main_corridor(rooms)
        room_by_name = {room.name: room for room in rooms}
        corridor_names = {room.name for room in rooms if room.room_type == "corridor"}

        for room in rooms:
            neighbors = door_neighbors.get(room.name, set())
            lowered = room.name.lower()

            if room.room_type == "bedroom":
                has_corridor_door = any(name in corridor_names for name in neighbors)
                has_bathroom_door = any(room_by_name[name].room_type == "bathroom" for name in neighbors)
                if not has_corridor_door and not has_bathroom_door:
                    self._violate(
                        code="DOOR_POLICY_FAILED",
                        reason="bedroom must have at least one door to corridor or bathroom",
                        rule="bedroom-door-policy",
                        room=room.name,
                    )
                for neighbor_name in neighbors:
                    neighbor = room_by_name[neighbor_name]
                    if neighbor.room_type == "kitchen" or neighbor.room_type == "bedroom":
                        self._violate(
                            code="DOOR_POLICY_FAILED",
                            reason="bedroom doors cannot open into kitchen or another bedroom",
                            rule="bedroom-door-forbidden-target",
                            room=room.name,
                        )

            if room.room_type == "bathroom" and "laundry" not in lowered:
                for neighbor_name in neighbors:
                    neighbor = room_by_name[neighbor_name]
                    n_name = neighbor.name.lower()
                    if neighbor.room_type == "kitchen" or "dining" in n_name:
                        self._violate(
                            code="DOOR_POLICY_FAILED",
                            reason="bathroom doors cannot open directly into kitchen or dining",
                            rule="bathroom-door-forbidden-target",
                            room=room.name,
                        )
                has_corridor_door = any(name in corridor_names for name in neighbors)
                has_bedroom_door = any(
                    room_by_name[name].room_type == "bedroom"
                    for name in neighbors
                )
                has_living_door = any(
                    room_by_name[name].room_type == "living" and "dining" not in room_by_name[name].name.lower()
                    for name in neighbors
                )
                if not has_corridor_door and not has_bedroom_door and not has_living_door:
                    self._violate(
                        code="DOOR_POLICY_FAILED",
                        reason="bathroom must open to corridor, living room, or bedroom",
                        rule="bathroom-door-target",
                        room=room.name,
                    )

            if room.room_type == "kitchen":
                has_dining = any("dining" in room_by_name[name].name.lower() for name in neighbors)
                has_corridor = any(name in corridor_names for name in neighbors)
                has_living = any(room_by_name[name].room_type == "living" for name in neighbors)
                if not has_dining and not has_corridor and not has_living:
                    self._violate(
                        code="DOOR_POLICY_FAILED",
                        reason="kitchen must connect to dining, living, or corridor",
                        rule="kitchen-door-connectivity",
                        room=room.name,
                    )

            if room.room_type == "living" and "living" in lowered:
                if not any(name in corridor_names for name in neighbors):
                    self._violate(
                        code="DOOR_POLICY_FAILED",
                        reason="living room must connect to circulation spine",
                        rule="living-door-corridor",
                        room=room.name,
                    )

    def _check_window_logic(
        self,
        *,
        rooms: list[_RoomBox],
        openings: list[_OpeningCut],
        boundary_width: float,
        boundary_height: float,
        mechanical_allowed: bool,
    ) -> None:
        windows_by_room: dict[str, list[_OpeningCut]] = defaultdict(list)
        doors_by_room_wall: dict[tuple[str, str], list[_OpeningCut]] = defaultdict(list)
        for opening in openings:
            if opening.type == "window":
                windows_by_room[opening.room_name].append(opening)
            elif opening.type == "door":
                doors_by_room_wall[(opening.room_name, opening.wall)].append(opening)

        for room in rooms:
            room_windows = windows_by_room.get(room.name, [])
            exterior_sides = self._exterior_sides(room, boundary_width=boundary_width, boundary_height=boundary_height)

            for window in room_windows:
                if window.wall not in exterior_sides:
                    self._violate(
                        code="WINDOW_POLICY_FAILED",
                        reason="window must be placed on exterior wall",
                        rule="window-exterior-wall-only",
                        room=room.name,
                    )
                for door in doors_by_room_wall.get((room.name, window.wall), []):
                    if self._segments_overlap(window, door):
                        self._violate(
                            code="WINDOW_POLICY_FAILED",
                            reason="window cannot overlap door opening",
                            rule="window-door-overlap",
                            room=room.name,
                        )

            lowered = room.name.lower()
            if room.room_type == "bedroom":
                if not room_windows:
                    self._violate(
                        code="WINDOW_POLICY_FAILED",
                        reason="bedroom must have at least one exterior window",
                        rule="bedroom-window-required",
                        room=room.name,
                    )
                if not any(window.length >= 1.0 - _EPSILON for window in room_windows):
                    self._violate(
                        code="WINDOW_POLICY_FAILED",
                        reason="bedroom window width must be at least 1.0m",
                        rule="bedroom-window-min-width",
                        room=room.name,
                    )

            if room.room_type == "living" and "living" in lowered:
                total_window_area = sum(window.length * _WINDOW_HEIGHT_FACTOR for window in room_windows)
                if total_window_area + _EPSILON < room.area * _LIVING_WINDOW_RATIO_MIN:
                    self._violate(
                        code="WINDOW_POLICY_FAILED",
                        reason="living room must satisfy minimum window-to-floor ratio",
                        rule="living-daylight-ratio",
                        room=room.name,
                    )

            if room.room_type == "bathroom" and "laundry" not in lowered:
                if not room_windows and not mechanical_allowed:
                    self._violate(
                        code="WINDOW_POLICY_FAILED",
                        reason="bathroom requires exterior window or mechanical ventilation flag",
                        rule="bathroom-ventilation",
                        room=room.name,
                    )

            if room.room_type == "kitchen":
                if not room_windows and not mechanical_allowed:
                    self._violate(
                        code="WINDOW_POLICY_FAILED",
                        reason="kitchen requires exterior window or mechanical ventilation flag",
                        rule="kitchen-ventilation",
                        room=room.name,
                    )

    def _check_sunlight_rules(
        self,
        *,
        rooms: list[_RoomBox],
        openings: list[_OpeningCut],
        boundary_width: float,
        boundary_height: float,
        orientation_map: dict[str, str],
    ) -> None:
        windows_by_room: dict[str, list[_OpeningCut]] = defaultdict(list)
        for opening in openings:
            if opening.type == "window":
                windows_by_room[opening.room_name].append(opening)

        bedroom_west_only = 0
        bedroom_total = 0
        for room in rooms:
            room_windows = windows_by_room.get(room.name, [])
            room_compass = {orientation_map[window.wall] for window in room_windows}
            lowered = room.name.lower()

            if room.room_type == "living" and "living" in lowered:
                preferred = {"south", "east"}
                exterior = {
                    orientation_map[side]
                    for side in self._exterior_sides(room, boundary_width=boundary_width, boundary_height=boundary_height)
                }
                if exterior.intersection(preferred) and not room_compass.intersection(preferred):
                    self._violate(
                        code="SUNLIGHT_RULE_FAILED",
                        reason="public spaces should prioritize south/east exposure when available",
                        rule="public-exposure-preference",
                        room=room.name,
                    )
            if room.room_type == "living" and "dining" in lowered and room_windows:
                preferred = {"south", "east"}
                exterior = {
                    orientation_map[side]
                    for side in self._exterior_sides(room, boundary_width=boundary_width, boundary_height=boundary_height)
                }
                if exterior.intersection(preferred) and not room_compass.intersection(preferred):
                    self._violate(
                        code="SUNLIGHT_RULE_FAILED",
                        reason="dining space should prioritize south/east exposure when available",
                        rule="dining-exposure-preference",
                        room=room.name,
                    )

            if room.room_type == "bedroom":
                bedroom_total += 1
                if room_compass and room_compass.issubset({"west"}):
                    bedroom_west_only += 1
                preferred = {"east", "north"}
                exterior = {
                    orientation_map[side]
                    for side in self._exterior_sides(room, boundary_width=boundary_width, boundary_height=boundary_height)
                }
                if exterior.intersection(preferred) and not room_compass.intersection(preferred):
                    self._violate(
                        code="SUNLIGHT_RULE_FAILED",
                        reason="bedrooms should prefer east or north exposure when available",
                        rule="bedroom-exposure-preference",
                        room=room.name,
                    )

        if bedroom_total > 0 and bedroom_west_only == bedroom_total:
            self._violate(
                code="SUNLIGHT_RULE_FAILED",
                reason="all bedrooms cannot face only west",
                rule="bedroom-west-only-forbidden",
            )

    def _check_zoning_rules(
        self,
        *,
        rooms: list[_RoomBox],
        door_neighbors: dict[str, set[str]],
        wall_adjacency: dict[str, set[str]],
    ) -> float:
        corridor = self._find_main_corridor(rooms)
        orientation = "horizontal" if corridor.width >= corridor.height else "vertical"
        room_by_name = {room.name: room for room in rooms}

        def room_side(room: _RoomBox) -> int:
            if orientation == "horizontal":
                return 1 if room.cy >= corridor.cy else -1
            return 1 if room.cx >= corridor.cx else -1

        public_votes: list[int] = []
        private_votes: list[int] = []
        guest_bathrooms: list[_RoomBox] = []
        service_spaces: list[_RoomBox] = []

        for room in rooms:
            if room.name == corridor.name:
                continue
            lowered = room.name.lower()
            side = room_side(room)
            if room.room_type == "bedroom" or (room.room_type == "bathroom" and "guest" not in lowered and "laundry" not in lowered):
                private_votes.append(side)
            elif room.room_type == "living" or (room.room_type == "bathroom" and "guest" in lowered):
                public_votes.append(side)
                if room.room_type == "bathroom" and "guest" in lowered:
                    guest_bathrooms.append(room)
            elif "laundry" in lowered or "storage" in lowered:
                service_spaces.append(room)

        separation_score = 1.0
        if private_votes and public_votes:
            dominant_private = 1 if sum(private_votes) >= 0 else -1
            dominant_public = 1 if sum(public_votes) >= 0 else -1
            if dominant_private == dominant_public:
                self._violate(
                    code="ZONING_RULE_FAILED",
                    reason="private zone must be separated from entry/public side",
                    rule="private-zone-separation",
                )

            for guest in guest_bathrooms:
                if room_side(guest) != dominant_public:
                    self._violate(
                        code="ZONING_RULE_FAILED",
                        reason="guest bathroom must be in public zone",
                        rule="guest-bathroom-public-zone",
                        room=guest.name,
                    )
            separation_score = 1.0

        kitchen_names = [room.name for room in rooms if room.room_type == "kitchen"]
        service_cluster_score = 1.0
        if kitchen_names:
            kitchen = room_by_name[kitchen_names[0]]
            if service_spaces:
                connected_services = [
                    room
                    for room in service_spaces
                    if room.name in wall_adjacency.get(kitchen.name, set()) or room.name in door_neighbors.get(kitchen.name, set())
                ]
                if not connected_services:
                    self._violate(
                        code="ZONING_RULE_FAILED",
                        reason="service spaces must stay adjacent to kitchen cluster",
                        rule="service-kitchen-cluster",
                    )
                service_cluster_score = len(connected_services) / len(service_spaces)
                for room in service_spaces:
                    if "laundry" not in room.name.lower():
                        continue
                    laundry_neighbors = wall_adjacency.get(room.name, set()) | door_neighbors.get(room.name, set())
                    if not any(
                        (
                            neighbor_name == kitchen.name
                            or room_by_name[neighbor_name].room_type in {"bathroom", "corridor"}
                            or "storage" in room_by_name[neighbor_name].name.lower()
                        )
                        for neighbor_name in laundry_neighbors
                        if neighbor_name in room_by_name
                    ):
                        self._violate(
                            code="ZONING_RULE_FAILED",
                            reason="laundry must stay adjacent to service cluster or corridor",
                            rule="service-kitchen-cluster",
                            room=room.name,
                        )

        return max(0.0, min(1.0, (0.6 * separation_score) + (0.4 * service_cluster_score)))

    def _check_circulation_graph(
        self,
        *,
        rooms: list[_RoomBox],
        door_neighbors: dict[str, set[str]],
        corridor: _RoomBox,
    ) -> int:
        reachable = self._bfs(adjacency=door_neighbors, start=corridor.name)
        room_names = {room.name for room in rooms}
        if reachable != room_names:
            missing = sorted(room_names - reachable)
            self._violate(
                code="CIRCULATION_RULE_FAILED",
                reason=f"graph is disconnected; unreachable rooms: {missing}",
                rule="graph-connected",
            )

        room_by_name = {room.name: room for room in rooms}
        for room in rooms:
            if room.name == corridor.name or room.room_type == "bedroom":
                continue
            if not self._reachable_without_private_bedrooms(
                adjacency=door_neighbors,
                room_by_name=room_by_name,
                start=corridor.name,
                target=room.name,
            ):
                self._violate(
                    code="CIRCULATION_RULE_FAILED",
                    reason="room requires passing through private bedroom",
                    rule="no-pass-through-bedroom",
                    room=room.name,
                )

        for room in rooms:
            if room.room_type == "bathroom" and "laundry" not in room.name.lower():
                neighbors = door_neighbors.get(room.name, set())
                if neighbors and all(
                    room_by_name[n].room_type == "bedroom" and "master" not in room_by_name[n].name.lower() for n in neighbors
                ):
                    self._violate(
                        code="CIRCULATION_RULE_FAILED",
                        reason="bathroom cannot be accessible only through unrelated bedroom",
                        rule="bathroom-access-rule",
                        room=room.name,
                    )

        distances = self._shortest_distances(adjacency=door_neighbors, start=corridor.name)
        max_depth = 0
        for room in rooms:
            if room.name == corridor.name:
                continue
            depth = distances.get(room.name)
            if depth is None:
                self._violate(
                    code="CIRCULATION_RULE_FAILED",
                    reason=f"room '{room.name}' is unreachable from corridor spine",
                    rule="graph-connected",
                    room=room.name,
                )
            max_depth = max(max_depth, depth)
            if depth > 5:
                self._violate(
                    code="CIRCULATION_RULE_FAILED",
                    reason="room circulation depth exceeds 5 transitions",
                    rule="circulation-depth-limit",
                    room=room.name,
                )

        corridor_rooms = [room for room in rooms if room.room_type == "corridor" and room.name != corridor.name]
        for room in corridor_rooms:
            degree = len(door_neighbors.get(room.name, set()))
            if degree <= 1:
                self._violate(
                    code="SPACE_WASTE_DETECTED",
                    reason="dead-end corridor branch detected",
                    rule="dead-end-corridor-branch",
                    room=room.name,
                )

        return max_depth

    @staticmethod
    def _shortest_distances(*, adjacency: dict[str, set[str]], start: str) -> dict[str, int]:
        distances: dict[str, int] = {}
        queue = deque([(start, 0)])
        while queue:
            current, depth = queue.popleft()
            if current in distances:
                continue
            distances[current] = depth
            for nxt in adjacency.get(current, set()):
                if nxt not in distances:
                    queue.append((nxt, depth + 1))
        return distances

    def _check_structural_wall_continuity(
        self,
        *,
        walls_raw: list[Any],
        boundary_width: float,
        boundary_height: float,
    ) -> float:
        if not isinstance(walls_raw, list) or not walls_raw:
            self._violate(
                code="STRUCTURAL_RULE_FAILED",
                reason="walls list is required for structural validation",
                rule="wall-continuity",
            )

        thicknesses: list[float] = []
        exterior_intervals: dict[str, list[tuple[float, float]]] = defaultdict(list)
        endpoint_degree: dict[tuple[float, float], int] = defaultdict(int)

        for raw in walls_raw:
            if not isinstance(raw, dict):
                continue
            start = raw.get("start", {})
            end = raw.get("end", {})
            x0 = float(start.get("x", 0.0))
            y0 = float(start.get("y", 0.0))
            x1 = float(end.get("x", 0.0))
            y1 = float(end.get("y", 0.0))
            thickness = float(raw.get("thickness", 0.0))
            thicknesses.append(thickness)

            horizontal = abs(y0 - y1) <= _EPSILON
            vertical = abs(x0 - x1) <= _EPSILON
            if not horizontal and not vertical:
                self._violate(
                    code="STRUCTURAL_RULE_FAILED",
                    reason="load-bearing walls must be axis-aligned",
                    rule="load-bearing-axis-alignment",
                )

            p0 = (round(x0, 4), round(y0, 4))
            p1 = (round(x1, 4), round(y1, 4))
            endpoint_degree[p0] += 1
            endpoint_degree[p1] += 1

            if horizontal and abs(y0 - 0.0) <= _EXTERIOR_CONTINUITY_TOLERANCE:
                exterior_intervals["bottom"].append((min(x0, x1), max(x0, x1)))
            if horizontal and abs(y0 - boundary_height) <= _EXTERIOR_CONTINUITY_TOLERANCE:
                exterior_intervals["top"].append((min(x0, x1), max(x0, x1)))
            if vertical and abs(x0 - 0.0) <= _EXTERIOR_CONTINUITY_TOLERANCE:
                exterior_intervals["left"].append((min(y0, y1), max(y0, y1)))
            if vertical and abs(x0 - boundary_width) <= _EXTERIOR_CONTINUITY_TOLERANCE:
                exterior_intervals["right"].append((min(y0, y1), max(y0, y1)))

        if thicknesses and max(thicknesses) - min(thicknesses) > 0.02:
            self._violate(
                code="STRUCTURAL_RULE_FAILED",
                reason="wall thickness must be consistent",
                rule="wall-thickness-consistency",
            )

        for side, limit in [("bottom", boundary_width), ("top", boundary_width), ("left", boundary_height), ("right", boundary_height)]:
            merged = self._merge_intervals(exterior_intervals.get(side, []))
            if not merged:
                self._violate(
                    code="STRUCTURAL_RULE_FAILED",
                    reason=f"missing exterior wall coverage on {side} side",
                    rule="exterior-wall-loop",
                )
            coverage = sum(end - start for start, end in merged)
            if coverage + _EXTERIOR_CONTINUITY_TOLERANCE < limit:
                self._violate(
                    code="STRUCTURAL_RULE_FAILED",
                    reason=f"exterior wall chain on {side} side is discontinuous",
                    rule="exterior-wall-loop",
                )

        for point, degree in endpoint_degree.items():
            if degree < 2:
                self._violate(
                    code="STRUCTURAL_RULE_FAILED",
                    reason=f"floating wall endpoint detected at {point}",
                    rule="wall-chain-continuity",
                )
        return self._structural_score(
            walls_raw=walls_raw,
            boundary_width=boundary_width,
            boundary_height=boundary_height,
        )

    def _check_column_grid_compatibility(
        self,
        *,
        boundary_width: float,
        boundary_height: float,
        openings: list[_OpeningCut],
    ) -> None:
        columns = self._build_column_grid(width=boundary_width, height=boundary_height)
        for opening in openings:
            for column_x, column_y in columns:
                if self._point_on_segment(
                    x=column_x,
                    y=column_y,
                    x0=opening.start_x,
                    y0=opening.start_y,
                    x1=opening.end_x,
                    y1=opening.end_y,
                ):
                    self._violate(
                        code="STRUCTURAL_RULE_FAILED",
                        reason="doors/windows cannot overlap structural columns",
                        rule="opening-column-overlap",
                        room=opening.room_name,
                    )

    def _check_furniture_clearance(self, rooms: list[_RoomBox]) -> float:
        scores: list[float] = []
        for room in rooms:
            lowered = room.name.lower()
            width = min(room.width, room.height)
            length = max(room.width, room.height)

            if room.room_type == "bedroom" and "master" in lowered:
                if width < 2.8 - _EPSILON or length < 2.6 - _EPSILON:
                    self._violate(
                        code="FURNITURE_CLEARANCE_FAILED",
                        reason="master bedroom cannot fit queen bed clearances",
                        rule="master-furniture-clearance",
                        room=room.name,
                    )
                margin = min((width - 2.8) / 0.6, (length - 2.6) / 0.8)
                scores.append(max(0.0, min(1.0, 0.7 + margin)))
            elif room.room_type == "bedroom":
                if width < 2.4 - _EPSILON or length < 2.6 - _EPSILON:
                    self._violate(
                        code="FURNITURE_CLEARANCE_FAILED",
                        reason="children bedroom cannot fit single bed + desk clearance",
                        rule="children-furniture-clearance",
                        room=room.name,
                    )
                margin = min((width - 2.4) / 0.6, (length - 2.6) / 0.8)
                scores.append(max(0.0, min(1.0, 0.7 + margin)))

            if room.room_type == "living" and "living" in lowered:
                if width < 3.5 - _EPSILON:
                    self._violate(
                        code="FURNITURE_CLEARANCE_FAILED",
                        reason="living room lacks 0.8m circulation around furniture zone",
                        rule="living-furniture-clearance",
                        room=room.name,
                    )
                margin = (width - 3.5) / 1.2
                scores.append(max(0.0, min(1.0, 0.75 + margin)))

            if room.room_type == "kitchen":
                if width < 2.4 - _EPSILON:
                    self._violate(
                        code="FURNITURE_CLEARANCE_FAILED",
                        reason="kitchen lacks 1.0m working clearance",
                        rule="kitchen-furniture-clearance",
                        room=room.name,
                    )
                margin = (width - 2.4) / 0.8
                scores.append(max(0.0, min(1.0, 0.75 + margin)))

            if room.room_type == "bathroom" and "laundry" not in lowered:
                if width < 1.2 - _EPSILON or length < 1.8 - _EPSILON:
                    self._violate(
                        code="FURNITURE_CLEARANCE_FAILED",
                        reason="bathroom fixture clearance is insufficient",
                        rule="bathroom-fixture-clearance",
                        room=room.name,
                    )
                margin = min((width - 1.2) / 0.6, (length - 1.8) / 0.8)
                scores.append(max(0.0, min(1.0, 0.7 + margin)))

        if not scores:
            return 1.0
        return max(0.0, min(1.0, sum(scores) / len(scores)))

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
            rooms.append(_RoomBox(name=name, room_type=room_type, x0=x0, y0=y0, x1=x0 + width, y1=y0 + height))
        if not rooms:
            raise RuleViolationError(
                code="LAYOUT_VALIDATION_FAILED",
                reason="no valid rooms in planned payload",
                violated_rule="layout-input",
            )
        return rooms

    @staticmethod
    def _to_openings(openings_raw: list[Any]) -> list[_OpeningCut]:
        openings: list[_OpeningCut] = []
        if not isinstance(openings_raw, list):
            return openings
        for raw in openings_raw:
            if not isinstance(raw, dict):
                continue
            start = raw.get("cut_start", {})
            end = raw.get("cut_end", {})
            openings.append(
                _OpeningCut(
                    type=str(raw.get("type", "")).lower(),
                    room_name=str(raw.get("room_name", "")),
                    wall=str(raw.get("wall", "")),
                    start_x=float(start.get("x", 0.0)),
                    start_y=float(start.get("y", 0.0)),
                    end_x=float(end.get("x", 0.0)),
                    end_y=float(end.get("y", 0.0)),
                    hinge=raw.get("hinge"),
                    swing=raw.get("swing"),
                )
            )
        return openings

    @staticmethod
    def _build_wall_adjacency(rooms: list[_RoomBox]) -> dict[str, set[str]]:
        adjacency: dict[str, set[str]] = defaultdict(set)
        for idx, room_a in enumerate(rooms):
            for room_b in rooms[idx + 1 :]:
                overlap_x = max(0.0, min(room_a.x1, room_b.x1) - max(room_a.x0, room_b.x0))
                overlap_y = max(0.0, min(room_a.y1, room_b.y1) - max(room_a.y0, room_b.y0))
                vertical_touch = min(abs(room_a.x1 - room_b.x0), abs(room_b.x1 - room_a.x0)) <= _EPSILON and overlap_y > 0.3
                horizontal_touch = min(abs(room_a.y1 - room_b.y0), abs(room_b.y1 - room_a.y0)) <= _EPSILON and overlap_x > 0.3
                if vertical_touch or horizontal_touch:
                    adjacency[room_a.name].add(room_b.name)
                    adjacency[room_b.name].add(room_a.name)
        return adjacency

    def _build_door_graph(
        self,
        openings: list[_OpeningCut],
        wall_adjacency: dict[str, set[str]],
    ) -> tuple[set[tuple[str, str]], dict[str, set[str]]]:
        door_groups: dict[tuple[str, float, float, float], list[_OpeningCut]] = defaultdict(list)
        for opening in openings:
            if opening.type != "door":
                continue
            key = self._opening_segment_key(opening)
            door_groups[key].append(opening)

        edges: set[tuple[str, str]] = set()
        neighbors: dict[str, set[str]] = defaultdict(set)
        for group in door_groups.values():
            rooms = sorted({opening.room_name for opening in group})
            if len(rooms) != 2:
                self._violate(
                    code="DOOR_GRAPH_INVALID",
                    reason="every door segment must connect exactly two rooms",
                    rule="door-pairing",
                    room=rooms[0] if rooms else None,
                )
            room_a, room_b = rooms[0], rooms[1]
            if room_b not in wall_adjacency.get(room_a, set()):
                self._violate(
                    code="DOOR_GRAPH_INVALID",
                    reason="door connects rooms that are not wall-adjacent",
                    rule="door-adjacent-walls",
                    room=room_a,
                )
            edge = tuple(sorted((room_a, room_b)))
            edges.add(edge)
            neighbors[room_a].add(room_b)
            neighbors[room_b].add(room_a)
        return edges, neighbors

    @staticmethod
    def _opening_segment_key(opening: _OpeningCut) -> tuple[str, float, float, float]:
        if abs(opening.start_x - opening.end_x) <= _EPSILON:
            lo, hi = sorted((opening.start_y, opening.end_y))
            return ("v", round(opening.start_x, 4), round(lo, 4), round(hi, 4))
        lo, hi = sorted((opening.start_x, opening.end_x))
        return ("h", round(opening.start_y, 4), round(lo, 4), round(hi, 4))

    @staticmethod
    def _find_main_corridor(rooms: list[_RoomBox]) -> _RoomBox:
        named_main = [room for room in rooms if room.name.lower() == "main corridor"]
        if named_main:
            return named_main[0]
        corridors = [room for room in rooms if room.room_type == "corridor" or "corridor" in room.name.lower()]
        if not corridors:
            raise RuleViolationError(
                code="CIRCULATION_RULE_FAILED",
                reason="central corridor spine is required",
                violated_rule="corridor-spine-required",
            )
        return max(corridors, key=lambda room: room.area)

    @staticmethod
    def _bfs(*, adjacency: dict[str, set[str]], start: str) -> set[str]:
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

    @staticmethod
    def _reachable_without_private_bedrooms(
        *,
        adjacency: dict[str, set[str]],
        room_by_name: dict[str, _RoomBox],
        start: str,
        target: str,
    ) -> bool:
        queue = deque([start])
        visited: set[str] = set()
        while queue:
            current = queue.popleft()
            if current == target:
                return True
            if current in visited:
                continue
            visited.add(current)
            for nxt in adjacency.get(current, set()):
                if nxt in visited:
                    continue
                nxt_room = room_by_name[nxt]
                if nxt != target and nxt_room.room_type == "bedroom":
                    continue
                queue.append(nxt)
        return False

    @staticmethod
    def _exterior_sides(room: _RoomBox, *, boundary_width: float, boundary_height: float) -> list[str]:
        sides: list[str] = []
        if abs(room.x0) <= _EPSILON:
            sides.append("left")
        if abs(room.x1 - boundary_width) <= _EPSILON:
            sides.append("right")
        if abs(room.y0) <= _EPSILON:
            sides.append("bottom")
        if abs(room.y1 - boundary_height) <= _EPSILON:
            sides.append("top")
        return sides

    @staticmethod
    def _segments_overlap(first: _OpeningCut, second: _OpeningCut) -> bool:
        if abs(first.start_x - first.end_x) <= _EPSILON and abs(second.start_x - second.end_x) <= _EPSILON:
            if abs(first.start_x - second.start_x) > _EPSILON:
                return False
            f0, f1 = sorted((first.start_y, first.end_y))
            s0, s1 = sorted((second.start_y, second.end_y))
            return f0 < s1 - _EPSILON and f1 > s0 + _EPSILON
        if abs(first.start_y - first.end_y) <= _EPSILON and abs(second.start_y - second.end_y) <= _EPSILON:
            if abs(first.start_y - second.start_y) > _EPSILON:
                return False
            f0, f1 = sorted((first.start_x, first.end_x))
            s0, s1 = sorted((second.start_x, second.end_x))
            return f0 < s1 - _EPSILON and f1 > s0 + _EPSILON
        return False

    @staticmethod
    def _resolve_orientation_map(extracted_payload: dict[str, Any]) -> dict[str, str]:
        constraints = extracted_payload.get("constraints")
        notes = constraints.get("notes") if isinstance(constraints, dict) else []
        text = " ".join(str(note).lower() for note in notes) if isinstance(notes, list) else ""
        top_direction = "north"
        for direction in ("north", "east", "south", "west"):
            if f"top boundary {direction}" in text or f"top is {direction}" in text or f"{direction}-facing top" in text:
                top_direction = direction
                break

        ring = ["north", "east", "south", "west"]
        idx = ring.index(top_direction)
        return {
            "top": ring[idx],
            "right": ring[(idx + 1) % 4],
            "bottom": ring[(idx + 2) % 4],
            "left": ring[(idx + 3) % 4],
        }

    @staticmethod
    def _mechanical_ventilation_allowed(extracted_payload: dict[str, Any]) -> bool:
        constraints = extracted_payload.get("constraints")
        if not isinstance(constraints, dict):
            return False
        notes = constraints.get("notes")
        if not isinstance(notes, list):
            return False
        text = " ".join(str(note).lower() for note in notes)
        return "mechanical ventilation" in text or "mech ventilation" in text

    @staticmethod
    def _merge_intervals(intervals: list[tuple[float, float]]) -> list[tuple[float, float]]:
        if not intervals:
            return []
        ordered = sorted(intervals)
        merged = [ordered[0]]
        for start, end in ordered[1:]:
            last_start, last_end = merged[-1]
            if start <= last_end + _EPSILON:
                merged[-1] = (last_start, max(last_end, end))
            else:
                merged.append((start, end))
        return merged

    def _structural_score(
        self,
        *,
        walls_raw: list[Any],
        boundary_width: float,
        boundary_height: float,
    ) -> float:
        axis_aligned = 0
        short_fragments = 0
        total_segments = 0
        for raw in walls_raw:
            if not isinstance(raw, dict):
                continue
            start = raw.get("start", {})
            end = raw.get("end", {})
            x0 = float(start.get("x", 0.0))
            y0 = float(start.get("y", 0.0))
            x1 = float(end.get("x", 0.0))
            y1 = float(end.get("y", 0.0))
            total_segments += 1
            horizontal = abs(y0 - y1) <= _EPSILON
            vertical = abs(x0 - x1) <= _EPSILON
            if horizontal or vertical:
                axis_aligned += 1
            length = abs(x1 - x0) + abs(y1 - y0)
            if length < 0.8 - _EPSILON:
                short_fragments += 1

        if total_segments == 0:
            return 0.0

        axis_score = axis_aligned / total_segments
        fragment_penalty = short_fragments / total_segments
        perimeter = 2.0 * (boundary_width + boundary_height)
        exterior_coverage = min(1.0, max(0.0, self._estimate_exterior_coverage(walls_raw, boundary_width, boundary_height) / perimeter))
        score = (0.5 * axis_score) + (0.3 * exterior_coverage) + (0.2 * (1.0 - fragment_penalty))
        return max(0.0, min(1.0, score))

    @staticmethod
    def _estimate_exterior_coverage(
        walls_raw: list[Any],
        boundary_width: float,
        boundary_height: float,
    ) -> float:
        total = 0.0
        for raw in walls_raw:
            if not isinstance(raw, dict):
                continue
            start = raw.get("start", {})
            end = raw.get("end", {})
            x0 = float(start.get("x", 0.0))
            y0 = float(start.get("y", 0.0))
            x1 = float(end.get("x", 0.0))
            y1 = float(end.get("y", 0.0))
            horizontal = abs(y0 - y1) <= _EPSILON
            vertical = abs(x0 - x1) <= _EPSILON
            if horizontal and (abs(y0 - 0.0) <= _EPSILON or abs(y0 - boundary_height) <= _EPSILON):
                total += abs(x1 - x0)
            if vertical and (abs(x0 - 0.0) <= _EPSILON or abs(x0 - boundary_width) <= _EPSILON):
                total += abs(y1 - y0)
        return total

    @staticmethod
    def _build_column_grid(*, width: float, height: float) -> list[tuple[float, float]]:
        x_lines = LayoutValidator._axis_grid(width)
        y_lines = LayoutValidator._axis_grid(height)
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
    def _point_on_segment(*, x: float, y: float, x0: float, y0: float, x1: float, y1: float) -> bool:
        if abs(x0 - x1) <= _EPSILON:
            if abs(x - x0) > _EPSILON:
                return False
            lo, hi = sorted((y0, y1))
            return lo + _EPSILON < y < hi - _EPSILON
        if abs(y0 - y1) <= _EPSILON:
            if abs(y - y0) > _EPSILON:
                return False
            lo, hi = sorted((x0, x1))
            return lo + _EPSILON < x < hi - _EPSILON
        return False

    @staticmethod
    def _violate(*, code: str, reason: str, rule: str, room: str | None = None) -> None:
        raise RuleViolationError(
            code=code,
            reason=reason,
            violated_rule=rule,
            room=room,
        )
