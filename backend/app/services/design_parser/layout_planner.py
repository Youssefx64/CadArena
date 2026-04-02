"""Deterministic spatial layout planning from extracted room programs."""

from __future__ import annotations
from dataclasses import dataclass
import math
from typing import Any, Literal


_EPSILON = 1e-6
_CORRIDOR_MIN_SPAN = 1.2
_CORRIDOR_MAX_SPAN = 2.0
_CORRIDOR_MAX_AREA_RATIO = 0.18
_CORRIDOR_VS_LARGEST_RATIO = 0.85
_MIN_SHORT_SIDE_FOR_CORRIDOR_ZONING = 5.5
_LIVING_SPLIT_THRESHOLD_AREA = 160.0
_LIVING_SPLIT_TARGET_AREA = 90.0
_MIN_SPLIT_ROOM_SPAN = 2.8
_MAX_TOPOLOGIES = 6
_MAX_ROOM_AREA_RATIO = 0.60
_MAX_LIVING_AREA_RATIO = 0.60
_MIN_EFFICIENCY_RATIO = 0.75
_MAX_STRUCTURAL_SPAN = 6.0

_W_AREA_BALANCE = 0.18
_W_ZONING = 0.16
_W_CIRCULATION = 0.14
_W_DAYLIGHT = 0.12
_W_STRUCTURAL = 0.10
_W_FURNITURE = 0.14
_W_EFFICIENCY = 0.16


@dataclass(frozen=True)
class _RoomRule:
    preferred_area: float
    min_area: float
    max_area: float
    min_width: float
    min_height: float


@dataclass
class _RoomPlanItem:
    index: int
    name: str
    room_type: str
    zone: Literal["public", "service", "private", "corridor"]
    preferred_area: float
    min_area: float
    max_area: float
    min_width: float
    min_height: float


@dataclass(frozen=True)
class _Rect:
    x: float
    y: float
    width: float
    height: float

    @property
    def area(self) -> float:
        return self.width * self.height


@dataclass(frozen=True)
class _TopologyCandidate:
    key: str
    orientation: Literal["vertical", "horizontal"]
    corridor_anchor: Literal["center", "min", "max"]
    public_on_low_side: bool
    public_service_split_axis: Literal["vertical", "horizontal"]


@dataclass(frozen=True)
class _TopologyScore:
    area_balance: float
    zoning: float
    circulation: float
    daylight: float
    structural: float
    furniture: float
    efficiency: float
    total: float


class LayoutPlanningError(ValueError):
    """Raised when deterministic layout generation is infeasible."""


class DeterministicLayoutPlanner:
    """Plans deterministic room geometry using zoning + recursive subdivision."""

    def plan(self, extracted_payload: dict[str, Any], *, optimize_efficiency: bool = False) -> dict[str, Any]:
        payload, _ = self.plan_with_metadata(extracted_payload, optimize_efficiency=optimize_efficiency)
        return payload

    def plan_with_metadata(
        self,
        extracted_payload: dict[str, Any],
        *,
        optimize_efficiency: bool = False,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        boundary = extracted_payload.get("boundary")
        room_program = extracted_payload.get("room_program")

        if not isinstance(boundary, dict) or not isinstance(room_program, list):
            raise LayoutPlanningError("Missing boundary or room_program in extracted payload")

        width = float(boundary["width"])
        height = float(boundary["height"])
        if width <= 0 or height <= 0:
            raise LayoutPlanningError("Boundary dimensions must be positive")
        self._validate_boundary_dimensions(width=width, height=height)

        rooms = self._expand_program(room_program)
        rooms = self._ensure_corridor_spine(rooms)
        if not rooms:
            raise LayoutPlanningError("Room program is empty")

        boundary_area = width * height
        rooms = self._normalize_program_areas(rooms=rooms, boundary_area=boundary_area)
        self._validate_program_feasibility(rooms=rooms, boundary_area=boundary_area)

        corridor_item = next(item for item in rooms if item.zone == "corridor")
        non_corridor = [item for item in rooms if item.zone != "corridor"]
        public_rooms = [item for item in non_corridor if item.zone == "public"]
        service_rooms = [item for item in non_corridor if item.zone == "service"]
        private_rooms = [item for item in non_corridor if item.zone == "private"]

        private_core_rooms, private_flexible_rooms = self._split_private_rooms(private_rooms)
        split_variants: list[tuple[list[_RoomPlanItem], list[_RoomPlanItem]]] = [(service_rooms, private_rooms)]
        if private_flexible_rooms:
            if len(private_flexible_rooms) > 1:
                split_variants.append(
                    (
                        service_rooms + private_flexible_rooms[:1],
                        private_core_rooms + private_flexible_rooms[1:],
                    )
                )
            split_variants.append((service_rooms + private_flexible_rooms, private_core_rooms))

        topology_candidates = self._generate_topology_candidates(width=width, height=height)
        ranked: list[tuple[_TopologyScore, int, _TopologyCandidate, list[dict[str, Any]]]] = []
        failure_reason = "Unable to construct deterministic layout"
        for topology_order, topology in enumerate(topology_candidates):
            for service_variant, private_variant in split_variants:
                try:
                    if topology.orientation == "horizontal":
                        assignments = self._plan_horizontal(
                            boundary_width=width,
                            boundary_height=height,
                            corridor_item=corridor_item,
                            public_rooms=public_rooms,
                            service_rooms=service_variant,
                            private_rooms=private_variant,
                            optimize_efficiency=optimize_efficiency,
                            corridor_anchor=topology.corridor_anchor,
                            public_on_low_side=topology.public_on_low_side,
                            public_service_split_axis=topology.public_service_split_axis,
                        )
                    else:
                        assignments = self._plan_vertical(
                            boundary_width=width,
                            boundary_height=height,
                            corridor_item=corridor_item,
                            public_rooms=public_rooms,
                            service_rooms=service_variant,
                            private_rooms=private_variant,
                            optimize_efficiency=optimize_efficiency,
                            corridor_anchor=topology.corridor_anchor,
                            public_on_low_side=topology.public_on_low_side,
                            public_service_split_axis=topology.public_service_split_axis,
                        )
                    layout_rooms = self._build_layout_rooms(
                        rooms=rooms,
                        assignments=assignments,
                        boundary_width=width,
                        boundary_height=height,
                    )
                    layout_rooms = self._subdivide_oversized_living_rooms(layout_rooms)
                    self._enforce_hard_constraints(
                        rooms=layout_rooms,
                        boundary_width=width,
                        boundary_height=height,
                    )
                    score = self._score_topology_candidate(
                        rooms=layout_rooms,
                        boundary_width=width,
                        boundary_height=height,
                    )
                    ranked.append((score, topology_order, topology, layout_rooms))
                    break
                except LayoutPlanningError as exc:
                    failure_reason = f"{topology.key}: {exc}"

        if not ranked:
            raise LayoutPlanningError(failure_reason)

        ranked.sort(
            key=lambda item: (
                -item[0].total,
                -item[0].efficiency,
                -item[0].zoning,
                item[1],
                item[2].key,
            )
        )
        selected_score, _, selected_topology, selected_rooms = ranked[0]
        # QUALITY FIX: run post-placement normalization before final payload serialization.
        base_payload: dict[str, Any] = {
            "boundary": {"width": width, "height": height},
            "rooms": selected_rooms,
            "walls": [],
            "openings": [],
        }
        normalized_payload = self.normalize_layout(
            {
                "boundary": {"width": width, "height": height},
                "rooms": selected_rooms,
                "walls": [],
                "openings": [],
            }
        )
        try:
            self._enforce_hard_constraints(
                rooms=normalized_payload["rooms"],
                boundary_width=width,
                boundary_height=height,
            )
            payload = normalized_payload
        except LayoutPlanningError:
            # QUALITY FIX: keep deterministic feasible geometry if normalization introduces a constraint regression.
            payload = base_payload

        self._enforce_hard_constraints(
            rooms=payload["rooms"],
            boundary_width=width,
            boundary_height=height,
        )
        payload["walls"] = self._build_walls(payload["rooms"])
        payload = {
            "boundary": payload["boundary"],
            "rooms": payload["rooms"],
            "walls": payload["walls"],
            "openings": payload.get("openings", []),
        }
        metadata = {
            "selected_topology": selected_topology.key,
            "topology_metrics": {
                "area_balance": round(selected_score.area_balance, 4),
                "zoning": round(selected_score.zoning, 4),
                "circulation": round(selected_score.circulation, 4),
                "daylight": round(selected_score.daylight, 4),
                "structural": round(selected_score.structural, 4),
                "furniture": round(selected_score.furniture, 4),
                "efficiency": round(selected_score.efficiency, 4),
                "total_score": round(selected_score.total, 4),
            },
        }
        return payload, metadata

    def _build_layout_rooms(
        self,
        *,
        rooms: list[_RoomPlanItem],
        assignments: dict[int, _Rect],
        boundary_width: float,
        boundary_height: float,
    ) -> list[dict[str, Any]]:
        layout_rooms: list[dict[str, Any]] = []
        balanced = self._normalize_area_assignments(rooms, assignments)
        balanced = self._rebalance_named_priorities(rooms, balanced)
        balanced = self._rebalance_exterior_requirements(
            rooms=rooms,
            assignments=balanced,
            boundary_width=boundary_width,
            boundary_height=boundary_height,
        )
        for item in sorted(rooms, key=lambda current: current.index):
            rect = balanced[item.index]
            room_payload = {
                "name": item.name,
                "room_type": item.room_type,
                "width": rect.width,
                "height": rect.height,
            }
            # Keep corridor geometry oriented by its narrow side before placement is serialized.
            room_payload = _enforce_corridor_dimensions(
                room_payload,
                boundary_width,
                boundary_height,
            )
            if item.room_type == "corridor":
                # Preserve the planner's exact long-axis partition line so corridor normalization
                # does not introduce micro-overlaps before the later global normalization pass.
                if float(room_payload.get("width", 0.0)) <= float(room_payload.get("height", 0.0)):
                    room_payload["height"] = min(float(room_payload.get("height", rect.height)), rect.height)
                else:
                    room_payload["width"] = min(float(room_payload.get("width", rect.width)), rect.width)
            room_payload["origin"] = {"x": rect.x, "y": rect.y}
            layout_rooms.append(room_payload)
        return layout_rooms

    @staticmethod
    def _generate_topology_candidates(*, width: float, height: float) -> list[_TopologyCandidate]:
        default_vertical = width >= height
        candidates = [
            _TopologyCandidate(
                key="central_corridor_spine",
                orientation="vertical" if default_vertical else "horizontal",
                corridor_anchor="center",
                public_on_low_side=True,
                public_service_split_axis="horizontal" if default_vertical else "vertical",
            ),
            _TopologyCandidate(
                key="side_corridor_spine",
                orientation="vertical",
                corridor_anchor="max",
                public_on_low_side=True,
                public_service_split_axis="horizontal",
            ),
            _TopologyCandidate(
                key="front_public_rear_private",
                orientation="horizontal",
                corridor_anchor="center",
                public_on_low_side=True,
                public_service_split_axis="vertical",
            ),
            _TopologyCandidate(
                key="vertical_public_private_split",
                orientation="vertical",
                corridor_anchor="center",
                public_on_low_side=False,
                public_service_split_axis="horizontal",
            ),
            _TopologyCandidate(
                key="l_shaped_public_core",
                orientation="horizontal",
                corridor_anchor="max",
                public_on_low_side=True,
                public_service_split_axis="vertical",
            ),
            _TopologyCandidate(
                key="side_corridor_spine_left",
                orientation="vertical",
                corridor_anchor="min",
                public_on_low_side=True,
                public_service_split_axis="horizontal",
            ),
        ]
        return candidates[:_MAX_TOPOLOGIES]

    @staticmethod
    def _validate_boundary_dimensions(*, width: float, height: float) -> None:
        short_side = min(width, height)
        if short_side + _EPSILON < _MIN_SHORT_SIDE_FOR_CORRIDOR_ZONING:
            raise LayoutPlanningError(
                "Boundary short side is too narrow for deterministic corridor-based residential planning"
            )

    @staticmethod
    def _split_private_rooms(
        private_rooms: list[_RoomPlanItem],
    ) -> tuple[list[_RoomPlanItem], list[_RoomPlanItem]]:
        core: list[_RoomPlanItem] = []
        flexible: list[_RoomPlanItem] = []
        for item in private_rooms:
            lowered = item.name.lower()
            generic_bathroom = lowered == "bathroom" or lowered.startswith("bathroom ")
            if item.room_type == "bathroom" and generic_bathroom:
                flexible.append(item)
                continue
            core.append(item)
        return core, flexible

    def _enforce_hard_constraints(
        self,
        *,
        rooms: list[dict[str, Any]],
        boundary_width: float,
        boundary_height: float,
    ) -> None:
        boundary_area = boundary_width * boundary_height
        corridor_area = 0.0
        total_area = 0.0
        largest_non_corridor = 0.0
        normalized: list[tuple[str, str, float, float, float, float, float]] = []

        for room in rooms:
            name = str(room.get("name", ""))
            room_type = str(room.get("room_type", "")).lower()
            x0 = float(room.get("origin", {}).get("x", 0.0))
            y0 = float(room.get("origin", {}).get("y", 0.0))
            width = float(room.get("width", 0.0))
            height = float(room.get("height", 0.0))
            if width <= 0 or height <= 0:
                raise LayoutPlanningError(f"Room '{name}' has non-positive dimensions")
            x1 = x0 + width
            y1 = y0 + height
            if x0 < -_EPSILON or y0 < -_EPSILON or x1 > boundary_width + _EPSILON or y1 > boundary_height + _EPSILON:
                raise LayoutPlanningError(f"Room '{name}' exceeds boundary")

            lowered_name = name.lower()
            requires_exterior = (
                room_type == "bedroom"
                or room_type == "kitchen"
                or (room_type == "living" and "living" in lowered_name)
            )
            if requires_exterior:
                has_exterior = (
                    abs(x0 - 0.0) <= _EPSILON
                    or abs(y0 - 0.0) <= _EPSILON
                    or abs(x1 - boundary_width) <= _EPSILON
                    or abs(y1 - boundary_height) <= _EPSILON
                )
                if not has_exterior:
                    raise LayoutPlanningError(f"Room '{name}' lacks exterior wall access")

            area = width * height
            total_area += area
            if area - (boundary_area * _MAX_ROOM_AREA_RATIO) > _EPSILON:
                raise LayoutPlanningError(f"Room '{name}' exceeds 60% of boundary area")
            if room_type == "living" and "living" in name.lower():
                if area - (boundary_area * _MAX_LIVING_AREA_RATIO) > _EPSILON:
                    raise LayoutPlanningError("Living room exceeds 60% of boundary area")

            if (room_type == "corridor" or "corridor" in name.lower()) and "storage" not in name.lower():
                corridor_area += area
            else:
                largest_non_corridor = max(largest_non_corridor, area)

            ratio = max(width, height) / max(min(width, height), _EPSILON)
            if room_type != "corridor" and ratio - 4.0 > _EPSILON:
                raise LayoutPlanningError(f"Room '{name}' aspect ratio exceeds 1:4")

            if room_type in {"bedroom", "bathroom", "stairs"} and min(width, height) - _MAX_STRUCTURAL_SPAN > _EPSILON:
                raise LayoutPlanningError(f"Room '{name}' exceeds unsupported structural span of 6m")

            normalized.append((name, room_type, x0, y0, x1, y1, area))

        if corridor_area - (boundary_area * _CORRIDOR_MAX_AREA_RATIO) > _EPSILON:
            raise LayoutPlanningError("Corridor area exceeds 18% of boundary area")
        if largest_non_corridor > _EPSILON:
            if corridor_area - largest_non_corridor > -_EPSILON:
                raise LayoutPlanningError("Corridor cannot be the largest room")
            if corridor_area - (largest_non_corridor * _CORRIDOR_VS_LARGEST_RATIO) > _EPSILON:
                raise LayoutPlanningError("Corridor area exceeds 85% of the largest room")

        for idx, room_a in enumerate(normalized):
            _, _, ax0, ay0, ax1, ay1, _ = room_a
            for room_b in normalized[idx + 1 :]:
                _, _, bx0, by0, bx1, by1, _ = room_b
                overlap_x = ax0 < bx1 - _EPSILON and ax1 > bx0 + _EPSILON
                overlap_y = ay0 < by1 - _EPSILON and ay1 > by0 + _EPSILON
                if overlap_x and overlap_y:
                    raise LayoutPlanningError("Generated rooms overlap")

        adjacency = self._room_adjacency(rooms)
        corridor_names = {
            str(room.get("name", ""))
            for room in rooms
            if str(room.get("room_type", "")).lower() == "corridor"
            or "corridor" in str(room.get("name", "")).lower()
        }
        for room in rooms:
            room_name = str(room.get("name", ""))
            room_type = str(room.get("room_type", "")).lower()
            is_main_living = room_type == "living" and "living" in room_name.lower()
            requires_corridor_contact = room_type == "bedroom" or is_main_living
            if not requires_corridor_contact:
                continue
            if room_name not in adjacency:
                raise LayoutPlanningError(f"Room '{room_name}' has no wall adjacency graph node")
            if not adjacency[room_name].intersection(corridor_names):
                raise LayoutPlanningError(f"Room '{room_name}' must share a wall with circulation spine")

        efficiency = (total_area - corridor_area) / max(boundary_area, _EPSILON)
        if efficiency + _EPSILON < _MIN_EFFICIENCY_RATIO:
            raise LayoutPlanningError("Layout efficiency is below 0.75")

    def _score_topology_candidate(
        self,
        *,
        rooms: list[dict[str, Any]],
        boundary_width: float,
        boundary_height: float,
    ) -> _TopologyScore:
        boundary_area = boundary_width * boundary_height
        area_balance = self._area_balance_score(rooms=rooms, boundary_area=boundary_area)
        zoning = self._zoning_proxy_score(rooms=rooms)
        circulation = self._circulation_proxy_score(rooms=rooms)
        daylight = self._daylight_proxy_score(
            rooms=rooms,
            boundary_width=boundary_width,
            boundary_height=boundary_height,
        )
        structural = self._structural_proxy_score(rooms=rooms)
        furniture = self._furniture_proxy_score(rooms=rooms)
        efficiency = self._efficiency_proxy_score(rooms=rooms, boundary_area=boundary_area)
        total = (
            (_W_AREA_BALANCE * area_balance)
            + (_W_ZONING * zoning)
            + (_W_CIRCULATION * circulation)
            + (_W_DAYLIGHT * daylight)
            + (_W_STRUCTURAL * structural)
            + (_W_FURNITURE * furniture)
            + (_W_EFFICIENCY * efficiency)
        )
        return _TopologyScore(
            area_balance=max(0.0, min(1.0, area_balance)),
            zoning=max(0.0, min(1.0, zoning)),
            circulation=max(0.0, min(1.0, circulation)),
            daylight=max(0.0, min(1.0, daylight)),
            structural=max(0.0, min(1.0, structural)),
            furniture=max(0.0, min(1.0, furniture)),
            efficiency=max(0.0, min(1.0, efficiency)),
            total=max(0.0, min(1.0, total)),
        )

    def _area_balance_score(self, *, rooms: list[dict[str, Any]], boundary_area: float) -> float:
        zone_areas = {"public": 0.0, "private": 0.0, "service": 0.0}
        areas_for_hierarchy: list[float] = []
        for room in rooms:
            area = float(room.get("width", 0.0)) * float(room.get("height", 0.0))
            zone = self._zone_for_room(room)
            if zone in zone_areas:
                zone_areas[zone] += area
            name = str(room.get("name", "")).lower()
            if "storage" not in name and zone != "corridor":
                areas_for_hierarchy.append(area)

        def band(value: float, lower: float, upper: float) -> float:
            ratio = value / max(boundary_area, _EPSILON)
            if lower <= ratio <= upper:
                return 1.0
            if ratio < lower:
                return max(0.0, 1.0 - ((lower - ratio) / max(lower, _EPSILON)))
            return max(0.0, 1.0 - ((ratio - upper) / max(1.0 - upper, _EPSILON)))

        zone_score = (
            band(zone_areas["public"], 0.30, 0.45)
            + band(zone_areas["private"], 0.30, 0.45)
            + band(zone_areas["service"], 0.15, 0.25)
        ) / 3.0

        hierarchy_score = 1.0
        if len(areas_for_hierarchy) >= 2:
            largest = max(areas_for_hierarchy)
            smallest = max(min(areas_for_hierarchy), _EPSILON)
            ratio = largest / smallest
            if ratio > 2.5:
                hierarchy_score = max(0.0, 1.0 - ((ratio - 2.5) / 2.5))

        return (0.75 * zone_score) + (0.25 * hierarchy_score)

    def _zoning_proxy_score(self, *, rooms: list[dict[str, Any]]) -> float:
        corridor = next(
            (
                room
                for room in rooms
                if str(room.get("room_type", "")).lower() == "corridor"
                or "corridor" in str(room.get("name", "")).lower()
            ),
            None,
        )
        if corridor is None:
            return 0.0

        cx = float(corridor["origin"]["x"]) + (float(corridor["width"]) / 2.0)
        cy = float(corridor["origin"]["y"]) + (float(corridor["height"]) / 2.0)
        horizontal = float(corridor["width"]) >= float(corridor["height"])

        public_votes: list[int] = []
        private_votes: list[int] = []
        for room in rooms:
            if room is corridor:
                continue
            zone = self._zone_for_room(room)
            if zone not in {"public", "private"}:
                continue
            room_cx = float(room["origin"]["x"]) + (float(room["width"]) / 2.0)
            room_cy = float(room["origin"]["y"]) + (float(room["height"]) / 2.0)
            side = 1 if (room_cy >= cy if horizontal else room_cx >= cx) else -1
            if zone == "public":
                public_votes.append(side)
            else:
                private_votes.append(side)

        separation = 0.6
        if public_votes and private_votes:
            separation = 1.0 if (sum(public_votes) * sum(private_votes)) < 0 else 0.3

        adjacency = self._room_adjacency(rooms)
        kitchen_names = [
            str(room.get("name", ""))
            for room in rooms
            if str(room.get("room_type", "")).lower() == "kitchen"
        ]
        service_names = [
            str(room.get("name", ""))
            for room in rooms
            if self._zone_for_room(room) == "service"
        ]
        service_score = 1.0
        if kitchen_names and service_names:
            kitchen = kitchen_names[0]
            connected = sum(1 for room_name in service_names if room_name in adjacency.get(kitchen, set()))
            service_score = connected / max(len(service_names), 1)

        return max(0.0, min(1.0, (0.7 * separation) + (0.3 * service_score)))

    def _circulation_proxy_score(self, *, rooms: list[dict[str, Any]]) -> float:
        corridor_name = next(
            (
                str(room.get("name", ""))
                for room in rooms
                if str(room.get("room_type", "")).lower() == "corridor"
                or "corridor" in str(room.get("name", "")).lower()
            ),
            "",
        )
        if not corridor_name:
            return 0.0

        adjacency = self._room_adjacency(rooms)
        distances: dict[str, int] = {}
        queue: list[tuple[str, int]] = [(corridor_name, 0)]
        while queue:
            current, depth = queue.pop(0)
            if current in distances:
                continue
            distances[current] = depth
            for nxt in sorted(adjacency.get(current, set())):
                if nxt not in distances:
                    queue.append((nxt, depth + 1))

        if len(distances) != len(rooms):
            return 0.0

        max_depth = max((depth for name, depth in distances.items() if name != corridor_name), default=0)
        if max_depth <= 2:
            depth_score = 1.0
        elif max_depth == 3:
            depth_score = 0.85
        elif max_depth == 4:
            depth_score = 0.65
        else:
            depth_score = 0.45

        dead_end_corridors = 0
        for room in rooms:
            name = str(room.get("name", ""))
            room_type = str(room.get("room_type", "")).lower()
            if name == corridor_name:
                continue
            if room_type != "corridor":
                continue
            if len(adjacency.get(name, set())) <= 1:
                dead_end_corridors += 1
        dead_end_penalty = max(0.0, 1.0 - (0.25 * dead_end_corridors))
        return max(0.0, min(1.0, (0.75 * depth_score) + (0.25 * dead_end_penalty)))

    def _daylight_proxy_score(
        self,
        *,
        rooms: list[dict[str, Any]],
        boundary_width: float,
        boundary_height: float,
    ) -> float:
        required = 0
        with_exterior = 0
        for room in rooms:
            room_type = str(room.get("room_type", "")).lower()
            name = str(room.get("name", "")).lower()
            needs_window = (
                room_type == "bedroom"
                or room_type == "kitchen"
                or (room_type == "living" and "living" in name)
                or (room_type == "bathroom" and "laundry" not in name)
            )
            if not needs_window:
                continue
            required += 1
            x0 = float(room["origin"]["x"])
            y0 = float(room["origin"]["y"])
            x1 = x0 + float(room["width"])
            y1 = y0 + float(room["height"])
            if (
                abs(x0 - 0.0) <= _EPSILON
                or abs(y0 - 0.0) <= _EPSILON
                or abs(x1 - boundary_width) <= _EPSILON
                or abs(y1 - boundary_height) <= _EPSILON
            ):
                with_exterior += 1
        if required == 0:
            return 1.0
        return with_exterior / required

    def _structural_proxy_score(self, *, rooms: list[dict[str, Any]]) -> float:
        aligned = 0
        total_checks = 0
        short_fragments = 0
        for room in rooms:
            width = float(room.get("width", 0.0))
            height = float(room.get("height", 0.0))
            for value in (width, height):
                total_checks += 1
                if 3.0 - _EPSILON <= value <= 6.0 + _EPSILON:
                    aligned += 1
                if value < 1.0 - _EPSILON:
                    short_fragments += 1
        if total_checks == 0:
            return 0.0
        alignment_score = aligned / total_checks
        fragment_penalty = short_fragments / total_checks
        return max(0.0, min(1.0, (0.8 * alignment_score) + (0.2 * (1.0 - fragment_penalty))))

    def _furniture_proxy_score(self, *, rooms: list[dict[str, Any]]) -> float:
        checks = 0
        passed = 0
        for room in rooms:
            room_type = str(room.get("room_type", "")).lower()
            name = str(room.get("name", "")).lower()
            width = min(float(room.get("width", 0.0)), float(room.get("height", 0.0)))
            length = max(float(room.get("width", 0.0)), float(room.get("height", 0.0)))

            if room_type == "bedroom" and "master" in name:
                checks += 1
                if width >= 2.8 - _EPSILON and length >= 2.6 - _EPSILON:
                    passed += 1
            elif room_type == "bedroom":
                checks += 1
                if width >= 2.4 - _EPSILON and length >= 2.6 - _EPSILON:
                    passed += 1

            if room_type == "living" and "living" in name:
                checks += 1
                if width >= 3.5 - _EPSILON:
                    passed += 1

            if room_type == "kitchen":
                checks += 1
                if width >= 2.4 - _EPSILON:
                    passed += 1

            if room_type == "bathroom" and "laundry" not in name:
                checks += 1
                if width >= 1.2 - _EPSILON and length >= 1.8 - _EPSILON:
                    passed += 1

        if checks == 0:
            return 1.0
        return passed / checks

    @staticmethod
    def _efficiency_proxy_score(*, rooms: list[dict[str, Any]], boundary_area: float) -> float:
        corridor_area = 0.0
        usable_area = 0.0
        for room in rooms:
            area = float(room.get("width", 0.0)) * float(room.get("height", 0.0))
            room_type = str(room.get("room_type", "")).lower()
            name = str(room.get("name", "")).lower()
            if room_type == "corridor" or "corridor" in name:
                corridor_area += area
            else:
                usable_area += area
        _ = corridor_area
        return max(0.0, min(1.0, usable_area / max(boundary_area, _EPSILON)))

    @staticmethod
    def _zone_for_room(room: dict[str, Any]) -> Literal["public", "private", "service", "corridor"]:
        room_type = str(room.get("room_type", "")).lower()
        name = str(room.get("name", "")).lower()
        if "storage" in name or "laundry" in name:
            return "service"
        if room_type == "corridor" or "corridor" in name:
            return "corridor"
        if room_type == "bedroom":
            return "private"
        if room_type == "kitchen":
            return "service"
        if room_type == "bathroom":
            if "guest" in name:
                return "public"
            if "laundry" in name:
                return "service"
            return "private"
        if "storage" in name or "laundry" in name:
            return "service"
        return "public"

    @staticmethod
    def _room_adjacency(rooms: list[dict[str, Any]]) -> dict[str, set[str]]:
        boxes: list[tuple[str, float, float, float, float]] = []
        for room in rooms:
            name = str(room.get("name", ""))
            x0 = float(room.get("origin", {}).get("x", 0.0))
            y0 = float(room.get("origin", {}).get("y", 0.0))
            x1 = x0 + float(room.get("width", 0.0))
            y1 = y0 + float(room.get("height", 0.0))
            boxes.append((name, x0, y0, x1, y1))

        adjacency: dict[str, set[str]] = {name: set() for name, *_ in boxes}
        for idx, (name_a, ax0, ay0, ax1, ay1) in enumerate(boxes):
            for name_b, bx0, by0, bx1, by1 in boxes[idx + 1 :]:
                overlap_x = max(0.0, min(ax1, bx1) - max(ax0, bx0))
                overlap_y = max(0.0, min(ay1, by1) - max(ay0, by0))
                touches_vertical = min(abs(ax1 - bx0), abs(bx1 - ax0)) <= _EPSILON and overlap_y > 0.3
                touches_horizontal = min(abs(ay1 - by0), abs(by1 - ay0)) <= _EPSILON and overlap_x > 0.3
                if touches_vertical or touches_horizontal:
                    adjacency[name_a].add(name_b)
                    adjacency[name_b].add(name_a)
        return adjacency

    def _normalize_area_assignments(
        self,
        rooms: list[_RoomPlanItem],
        assignments: dict[int, _Rect],
    ) -> dict[int, _Rect]:
        output = dict(assignments)
        grouped: dict[str, list[_RoomPlanItem]] = {}
        for item in rooms:
            if item.zone == "corridor":
                continue
            grouped.setdefault(item.zone, []).append(item)

        for group_items in grouped.values():
            ranked_items = sorted(
                group_items,
                key=lambda item: (-item.preferred_area, -item.min_area, item.index, item.name),
            )
            ranked_rects = sorted(
                (output[item.index] for item in group_items),
                key=lambda rect: (-rect.area, rect.x, rect.y),
            )
            for item, rect in zip(ranked_items, ranked_rects, strict=False):
                output[item.index] = rect
        return output

    def _rebalance_named_priorities(
        self,
        rooms: list[_RoomPlanItem],
        assignments: dict[int, _Rect],
    ) -> dict[int, _Rect]:
        output = dict(assignments)
        bedroom_items = [item for item in rooms if item.room_type == "bedroom"]
        if len(bedroom_items) < 2:
            return output

        prioritized_bedrooms = sorted(
            bedroom_items,
            key=lambda item: (
                -self._bedroom_priority(item.name),
                item.index,
                item.name,
            ),
        )
        ranked_rects = sorted(
            (output[item.index] for item in bedroom_items),
            key=lambda rect: (-rect.area, rect.x, rect.y),
        )

        for item, rect in zip(prioritized_bedrooms, ranked_rects, strict=False):
            output[item.index] = rect
        return output

    def _rebalance_exterior_requirements(
        self,
        *,
        rooms: list[_RoomPlanItem],
        assignments: dict[int, _Rect],
        boundary_width: float,
        boundary_height: float,
    ) -> dict[int, _Rect]:
        output = dict(assignments)
        by_index = {item.index: item for item in rooms}
        required = [item for item in rooms if self._requires_exterior_opening(item)]
        donor_order = sorted(
            rooms,
            key=lambda item: (
                int(self._requires_exterior_opening(item)),
                item.index,
                item.name,
            ),
        )

        max_passes = max(1, len(rooms) * len(rooms) * 2)
        seen_signatures: set[tuple[tuple[int, float, float, float, float], ...]] = set()
        for _ in range(max_passes):
            signature = tuple(
                sorted(
                    (
                        index,
                        round(rect.x, 6),
                        round(rect.y, 6),
                        round(rect.width, 6),
                        round(rect.height, 6),
                    )
                    for index, rect in output.items()
                )
            )
            if signature in seen_signatures:
                break
            seen_signatures.add(signature)

            changed = False
            for item in required:
                current_rect = output[item.index]
                if self._rect_has_exterior(
                    rect=current_rect,
                    boundary_width=boundary_width,
                    boundary_height=boundary_height,
                ):
                    continue

                for donor in donor_order:
                    if donor.index == item.index:
                        continue
                    donor_rect = output[donor.index]
                    if not self._rect_has_exterior(
                        rect=donor_rect,
                        boundary_width=boundary_width,
                        boundary_height=boundary_height,
                    ):
                        continue
                    if not self._rect_fits_item(item=item, rect=donor_rect):
                        continue
                    if not self._rect_fits_item(item=by_index[donor.index], rect=current_rect):
                        continue

                    output[item.index], output[donor.index] = donor_rect, current_rect
                    changed = True
                    break
            if not changed:
                break
        return output

    @staticmethod
    def _bedroom_priority(name: str) -> int:
        lowered = name.lower()
        if "master" in lowered:
            return 3
        if "child" in lowered or "kid" in lowered:
            return 1
        return 2

    def _expand_program(self, room_program: list[Any]) -> list[_RoomPlanItem]:
        items: list[_RoomPlanItem] = []
        sequence = 0
        for raw in room_program:
            if not isinstance(raw, dict):
                raise LayoutPlanningError("room_program entries must be objects")

            name = str(raw.get("name", "")).strip()
            room_type = str(raw.get("room_type", "")).strip().lower()
            count = int(raw.get("count", 1))
            if not name:
                raise LayoutPlanningError("room_program.name is required")
            if count <= 0:
                raise LayoutPlanningError("room_program.count must be positive")

            for idx in range(count):
                indexed_name = name if count == 1 else f"{name} {idx + 1}"
                rule, zone, normalized_type = self._infer_room_rule(indexed_name, room_type)
                explicit_min = self._positive_float(raw.get("min_area"))
                explicit_max = self._positive_float(raw.get("max_area"))
                explicit_pref = self._positive_float(raw.get("preferred_area"))

                # Keep deterministic hard bounds from residential standards.
                # LLM size hints are treated as soft preferences only.
                min_area = rule.min_area
                max_area = rule.max_area

                preferred_hint = rule.preferred_area
                if explicit_pref is not None:
                    preferred_hint = explicit_pref
                elif explicit_min is not None and explicit_max is not None and explicit_min <= explicit_max:
                    preferred_hint = (explicit_min + explicit_max) / 2.0
                elif explicit_min is not None:
                    preferred_hint = explicit_min
                elif explicit_max is not None:
                    preferred_hint = explicit_max

                preferred = min(max(preferred_hint, min_area), max_area)

                items.append(
                    _RoomPlanItem(
                        index=sequence,
                        name=indexed_name,
                        room_type=normalized_type,
                        zone=zone,
                        preferred_area=preferred,
                        min_area=min_area,
                        max_area=max_area,
                        min_width=rule.min_width,
                        min_height=rule.min_height,
                    )
                )
                sequence += 1
        return items

    def _ensure_corridor_spine(self, items: list[_RoomPlanItem]) -> list[_RoomPlanItem]:
        has_corridor = any(item.zone == "corridor" for item in items)
        if has_corridor:
            return items

        next_index = max((item.index for item in items), default=-1) + 1
        corridor_rule = _RoomRule(
            preferred_area=14.0,
            min_area=6.0,
            max_area=10000.0,
            min_width=_CORRIDOR_MIN_SPAN,
            min_height=_CORRIDOR_MIN_SPAN,
        )
        items.append(
            _RoomPlanItem(
                index=next_index,
                name="Main Corridor",
                room_type="corridor",
                zone="corridor",
                preferred_area=corridor_rule.preferred_area,
                min_area=corridor_rule.min_area,
                max_area=corridor_rule.max_area,
                min_width=corridor_rule.min_width,
                min_height=corridor_rule.min_height,
            )
        )
        return items

    def _validate_program_feasibility(self, *, rooms: list[_RoomPlanItem], boundary_area: float) -> None:
        min_area_sum = sum(item.min_area for item in rooms)
        max_area_sum = sum(item.max_area for item in rooms)
        if min_area_sum - boundary_area > _EPSILON:
            raise LayoutPlanningError(
                f"Requested minimum room area ({min_area_sum:.3f}) exceeds boundary area ({boundary_area:.3f})"
            )
        if boundary_area - max_area_sum > _EPSILON:
            raise LayoutPlanningError(
                f"Requested maximum room area ({max_area_sum:.3f}) is below boundary area ({boundary_area:.3f})"
            )

    def _normalize_program_areas(self, *, rooms: list[_RoomPlanItem], boundary_area: float) -> list[_RoomPlanItem]:
        corridor_items = [item for item in rooms if item.zone == "corridor"]
        usable_items = [item for item in rooms if item.zone != "corridor"]
        if not usable_items:
            return rooms

        corridor_preferred_sum = sum(item.preferred_area for item in corridor_items)
        target_usable_area = boundary_area - corridor_preferred_sum
        usable_min = sum(item.min_area for item in usable_items)
        usable_max = sum(item.max_area for item in usable_items)
        target_usable_area = min(max(target_usable_area, usable_min), usable_max)

        tolerance = boundary_area * 0.01
        for _ in range(12):
            total_preferred = sum(item.preferred_area for item in usable_items)
            delta = target_usable_area - total_preferred
            if abs(delta) <= tolerance:
                break

            if delta > 0:
                expandable = [item for item in usable_items if item.preferred_area < item.max_area - _EPSILON]
                if not expandable:
                    break
                capacity = sum(item.max_area - item.preferred_area for item in expandable)
                if capacity <= _EPSILON:
                    break
                scale = min(1.0, delta / capacity)
                for item in sorted(expandable, key=lambda current: current.index):
                    item.preferred_area += (item.max_area - item.preferred_area) * scale
            else:
                shrinkable = [item for item in usable_items if item.preferred_area > item.min_area + _EPSILON]
                if not shrinkable:
                    break
                capacity = sum(item.preferred_area - item.min_area for item in shrinkable)
                if capacity <= _EPSILON:
                    break
                scale = min(1.0, (-delta) / capacity)
                for item in sorted(shrinkable, key=lambda current: current.index):
                    item.preferred_area -= (item.preferred_area - item.min_area) * scale

        for item in usable_items:
            item.preferred_area = min(max(item.preferred_area, item.min_area), item.max_area)
        return rooms

    def _plan_horizontal(
        self,
        *,
        boundary_width: float,
        boundary_height: float,
        corridor_item: _RoomPlanItem,
        public_rooms: list[_RoomPlanItem],
        service_rooms: list[_RoomPlanItem],
        private_rooms: list[_RoomPlanItem],
        optimize_efficiency: bool,
        corridor_anchor: Literal["center", "min", "max"],
        public_on_low_side: bool,
        public_service_split_axis: Literal["vertical", "horizontal"],
    ) -> dict[int, _Rect]:
        total_area = boundary_width * boundary_height
        public_service_rooms = public_rooms + service_rooms
        if public_on_low_side:
            low_rooms = public_service_rooms
            high_rooms = private_rooms
        else:
            low_rooms = private_rooms
            high_rooms = public_service_rooms

        low_bounds = self._group_area_bounds(low_rooms)
        high_bounds = self._group_area_bounds(high_rooms)
        low_pref = sum(item.preferred_area for item in low_rooms) or 1.0
        high_pref = sum(item.preferred_area for item in high_rooms) or 1.0

        last_error = "Unable to split zones around corridor with usable heights"
        for corridor_height in self._corridor_span_candidates(
            boundary_span=boundary_height,
            orthogonal_span=boundary_width,
            total_area=total_area,
            optimize_efficiency=optimize_efficiency,
        ):
            corridor_area = boundary_width * corridor_height
            if corridor_area + _EPSILON < corridor_item.min_area:
                last_error = "Unable to satisfy corridor minimum area"
                continue
            if corridor_area - corridor_item.max_area > _EPSILON:
                last_error = "Unable to satisfy corridor maximum area"
                continue

            usable_height = boundary_height - corridor_height
            if usable_height <= 2.0:
                last_error = "Boundary is too narrow to host corridor and zones"
                continue

            usable_area = boundary_width * usable_height
            low_area_candidates = self._low_zone_area_candidates(
                usable_area=usable_area,
                low_bounds=low_bounds,
                high_bounds=high_bounds,
                low_pref=low_pref,
                high_pref=high_pref,
            )
            if not low_area_candidates:
                last_error = "Unable to split private/public zones with area constraints"
                continue

            for low_area in low_area_candidates:
                low_height = low_area / boundary_width
                high_height = usable_height - low_height
                if low_height <= 1.5 or high_height <= 1.5:
                    last_error = "Unable to split zones around corridor with usable heights"
                    continue

                if corridor_anchor == "center":
                    low_rect = _Rect(x=0.0, y=0.0, width=boundary_width, height=low_height)
                    corridor_rect = _Rect(x=0.0, y=low_height, width=boundary_width, height=corridor_height)
                    high_rect = _Rect(
                        x=0.0,
                        y=low_height + corridor_height,
                        width=boundary_width,
                        height=high_height,
                    )
                elif corridor_anchor == "min":
                    corridor_rect = _Rect(x=0.0, y=0.0, width=boundary_width, height=corridor_height)
                    low_rect = _Rect(x=0.0, y=corridor_height, width=boundary_width, height=low_height)
                    high_rect = _Rect(
                        x=0.0,
                        y=corridor_height + low_height,
                        width=boundary_width,
                        height=high_height,
                    )
                else:
                    low_rect = _Rect(x=0.0, y=0.0, width=boundary_width, height=low_height)
                    high_rect = _Rect(x=0.0, y=low_height, width=boundary_width, height=high_height)
                    corridor_rect = _Rect(
                        x=0.0,
                        y=boundary_height - corridor_height,
                        width=boundary_width,
                        height=corridor_height,
                    )

                try:
                    zone_assignments = self._pack_low_high_zones(
                        low_rect=low_rect,
                        high_rect=high_rect,
                        public_on_low_side=public_on_low_side,
                        public_rooms=public_rooms,
                        service_rooms=service_rooms,
                        private_rooms=private_rooms,
                        public_service_split_axis=public_service_split_axis,
                        private_preferred_axis="vertical",
                    )
                except LayoutPlanningError as exc:
                    last_error = str(exc)
                    continue

                assignments: dict[int, _Rect] = {corridor_item.index: corridor_rect}
                assignments.update(zone_assignments)
                self._validate_assignments(
                    assignments=assignments,
                    boundary_width=boundary_width,
                    boundary_height=boundary_height,
                )
                return assignments

        raise LayoutPlanningError(last_error)

    def _plan_vertical(
        self,
        *,
        boundary_width: float,
        boundary_height: float,
        corridor_item: _RoomPlanItem,
        public_rooms: list[_RoomPlanItem],
        service_rooms: list[_RoomPlanItem],
        private_rooms: list[_RoomPlanItem],
        optimize_efficiency: bool,
        corridor_anchor: Literal["center", "min", "max"],
        public_on_low_side: bool,
        public_service_split_axis: Literal["vertical", "horizontal"],
    ) -> dict[int, _Rect]:
        total_area = boundary_width * boundary_height
        public_service_rooms = public_rooms + service_rooms
        if public_on_low_side:
            low_rooms = public_service_rooms
            high_rooms = private_rooms
        else:
            low_rooms = private_rooms
            high_rooms = public_service_rooms
        low_bounds = self._group_area_bounds(low_rooms)
        high_bounds = self._group_area_bounds(high_rooms)
        low_pref = sum(item.preferred_area for item in low_rooms) or 1.0
        high_pref = sum(item.preferred_area for item in high_rooms) or 1.0

        last_error = "Unable to split vertical zones with usable widths"
        for corridor_width in self._corridor_span_candidates(
            boundary_span=boundary_width,
            orthogonal_span=boundary_height,
            total_area=total_area,
            optimize_efficiency=optimize_efficiency,
        ):
            corridor_area = boundary_height * corridor_width
            if corridor_area + _EPSILON < corridor_item.min_area:
                last_error = "Unable to satisfy corridor minimum area"
                continue
            if corridor_area - corridor_item.max_area > _EPSILON:
                last_error = "Unable to satisfy corridor maximum area"
                continue

            usable_width = boundary_width - corridor_width
            if usable_width <= 2.0:
                last_error = "Boundary is too narrow to host corridor and zones"
                continue

            usable_area = boundary_height * usable_width
            low_area_candidates = self._low_zone_area_candidates(
                usable_area=usable_area,
                low_bounds=low_bounds,
                high_bounds=high_bounds,
                low_pref=low_pref,
                high_pref=high_pref,
            )
            if not low_area_candidates:
                last_error = "Unable to split private/public zones with area constraints"
                continue

            for low_area in low_area_candidates:
                low_width = low_area / boundary_height
                high_width = usable_width - low_width
                if low_width <= 1.5 or high_width <= 1.5:
                    last_error = "Unable to split vertical zones with usable widths"
                    continue

                if corridor_anchor == "center":
                    low_rect = _Rect(x=0.0, y=0.0, width=low_width, height=boundary_height)
                    corridor_rect = _Rect(x=low_width, y=0.0, width=corridor_width, height=boundary_height)
                    high_rect = _Rect(
                        x=low_width + corridor_width,
                        y=0.0,
                        width=high_width,
                        height=boundary_height,
                    )
                elif corridor_anchor == "min":
                    corridor_rect = _Rect(x=0.0, y=0.0, width=corridor_width, height=boundary_height)
                    low_rect = _Rect(x=corridor_width, y=0.0, width=low_width, height=boundary_height)
                    high_rect = _Rect(
                        x=corridor_width + low_width,
                        y=0.0,
                        width=high_width,
                        height=boundary_height,
                    )
                else:
                    low_rect = _Rect(x=0.0, y=0.0, width=low_width, height=boundary_height)
                    high_rect = _Rect(x=low_width, y=0.0, width=high_width, height=boundary_height)
                    corridor_rect = _Rect(
                        x=boundary_width - corridor_width,
                        y=0.0,
                        width=corridor_width,
                        height=boundary_height,
                    )

                try:
                    zone_assignments = self._pack_low_high_zones(
                        low_rect=low_rect,
                        high_rect=high_rect,
                        public_on_low_side=public_on_low_side,
                        public_rooms=public_rooms,
                        service_rooms=service_rooms,
                        private_rooms=private_rooms,
                        public_service_split_axis=public_service_split_axis,
                        private_preferred_axis="horizontal",
                    )
                except LayoutPlanningError as exc:
                    last_error = str(exc)
                    continue

                assignments: dict[int, _Rect] = {corridor_item.index: corridor_rect}
                assignments.update(zone_assignments)
                self._validate_assignments(
                    assignments=assignments,
                    boundary_width=boundary_width,
                    boundary_height=boundary_height,
                )
                return assignments

        raise LayoutPlanningError(last_error)

    @staticmethod
    def _low_zone_area_candidates(
        *,
        usable_area: float,
        low_bounds: tuple[float, float],
        high_bounds: tuple[float, float],
        low_pref: float,
        high_pref: float,
    ) -> list[float]:
        low_ratio = low_pref / (low_pref + high_pref) if (low_pref + high_pref) > _EPSILON else 0.5
        low_target_area = usable_area * low_ratio
        low_min = max(low_bounds[0], usable_area - high_bounds[1])
        low_max = min(low_bounds[1], usable_area - high_bounds[0])
        if low_min - low_max > _EPSILON:
            return []
        return DeterministicLayoutPlanner._area_candidates(low=low_min, high=low_max, target=low_target_area)

    def _pack_low_high_zones(
        self,
        *,
        low_rect: _Rect,
        high_rect: _Rect,
        public_on_low_side: bool,
        public_rooms: list[_RoomPlanItem],
        service_rooms: list[_RoomPlanItem],
        private_rooms: list[_RoomPlanItem],
        public_service_split_axis: Literal["vertical", "horizontal"],
        private_preferred_axis: Literal["vertical", "horizontal"],
    ) -> dict[int, _Rect]:
        if public_on_low_side:
            public_rect = low_rect
            private_rect = high_rect
        else:
            public_rect = high_rect
            private_rect = low_rect

        output: dict[int, _Rect] = {}
        output.update(
            self._split_public_service(
                rect=public_rect,
                public_rooms=public_rooms,
                service_rooms=service_rooms,
                split_axis=public_service_split_axis,
            )
        )
        output.update(
            self._pack_zone_recursive(
                rect=private_rect,
                rooms=private_rooms,
                preferred_axis=private_preferred_axis,
            )
        )
        return output

    def _split_public_service(
        self,
        *,
        rect: _Rect,
        public_rooms: list[_RoomPlanItem],
        service_rooms: list[_RoomPlanItem],
        split_axis: Literal["vertical", "horizontal"],
    ) -> dict[int, _Rect]:
        if public_rooms and service_rooms:
            public_pref = sum(item.preferred_area for item in public_rooms)
            service_pref = sum(item.preferred_area for item in service_rooms)
            total = public_pref + service_pref
            ratio = public_pref / total if total > _EPSILON else 0.5
            public_area_bounds = self._group_area_bounds(public_rooms)
            service_area_bounds = self._group_area_bounds(service_rooms)
            for trial_ratio in self._ratio_candidates(ratio):
                try:
                    primary, secondary = self._split_rect(
                        rect=rect,
                        ratio=trial_ratio,
                        axis=split_axis,
                        first_min=self._group_min_span(public_rooms, split_axis),
                        second_min=self._group_min_span(service_rooms, split_axis),
                        first_area_bounds=public_area_bounds,
                        second_area_bounds=service_area_bounds,
                    )
                except LayoutPlanningError:
                    continue

                try:
                    public_assignments = self._pack_zone_recursive(
                        rect=primary,
                        rooms=public_rooms,
                        preferred_axis="vertical" if split_axis == "vertical" else "horizontal",
                    )
                    service_assignments = self._pack_zone_recursive(
                        rect=secondary,
                        rooms=service_rooms,
                        preferred_axis="vertical" if split_axis == "vertical" else "horizontal",
                    )
                except LayoutPlanningError:
                    continue

                output = {}
                output.update(public_assignments)
                output.update(service_assignments)
                return output
            combined = public_rooms + service_rooms
            return self._pack_zone_recursive(
                rect=rect,
                rooms=combined,
                preferred_axis="vertical" if split_axis == "vertical" else "horizontal",
            )

        if public_rooms:
            return self._pack_zone_recursive(rect=rect, rooms=public_rooms, preferred_axis="vertical")
        if service_rooms:
            return self._pack_zone_recursive(rect=rect, rooms=service_rooms, preferred_axis="vertical")
        return {}

    def _pack_zone_recursive(
        self,
        *,
        rect: _Rect,
        rooms: list[_RoomPlanItem],
        preferred_axis: Literal["vertical", "horizontal"],
    ) -> dict[int, _Rect]:
        if not rooms:
            return {}

        if len(rooms) == 1:
            room = rooms[0]
            area = rect.area
            if area + _EPSILON < room.min_area:
                raise LayoutPlanningError(
                    f"Room '{room.name}' below minimum area ({area:.3f} < {room.min_area:.3f})"
                )
            if area - room.max_area > 1e-3:
                raise LayoutPlanningError(
                    f"Room '{room.name}' above maximum area ({area:.3f} > {room.max_area:.3f})"
                )
            if rect.width + _EPSILON < room.min_width or rect.height + _EPSILON < room.min_height:
                raise LayoutPlanningError(f"Room '{room.name}' below minimum dimension bounds")
            return {room.index: rect}

        group_a, group_b = self._balanced_partition(rooms)
        area_a = sum(item.preferred_area for item in group_a)
        area_b = sum(item.preferred_area for item in group_b)
        total = area_a + area_b
        ratio = area_a / total if total > _EPSILON else 0.5
        area_a_bounds = self._group_area_bounds(group_a)
        area_b_bounds = self._group_area_bounds(group_b)

        axes = [preferred_axis, "horizontal" if preferred_axis == "vertical" else "vertical"]
        for axis in axes:
            for trial_ratio in self._ratio_candidates(ratio):
                try:
                    rect_a, rect_b = self._split_rect(
                        rect=rect,
                        ratio=trial_ratio,
                        axis=axis,
                        first_min=self._group_min_span(group_a, axis),
                        second_min=self._group_min_span(group_b, axis),
                        first_area_bounds=area_a_bounds,
                        second_area_bounds=area_b_bounds,
                    )
                except LayoutPlanningError:
                    continue

                if rect_a.area + _EPSILON < sum(item.min_area for item in group_a):
                    continue
                if rect_b.area + _EPSILON < sum(item.min_area for item in group_b):
                    continue

                child_preferred = "vertical" if axis == "horizontal" else "horizontal"
                try:
                    output = self._pack_zone_recursive(rect=rect_a, rooms=group_a, preferred_axis=child_preferred)
                    output.update(self._pack_zone_recursive(rect=rect_b, rooms=group_b, preferred_axis=child_preferred))
                    return output
                except LayoutPlanningError:
                    continue

        raise LayoutPlanningError("Unable to recursively subdivide zone with given constraints")

    def _balanced_partition(self, rooms: list[_RoomPlanItem]) -> tuple[list[_RoomPlanItem], list[_RoomPlanItem]]:
        ordered = sorted(rooms, key=lambda item: (-item.preferred_area, item.index, item.name))

        # Keep very small wet/service spaces separate from bedroom clusters to
        # avoid infeasible mixed-group splits in narrow private bands.
        if len(ordered) >= 3:
            bathrooms = [item for item in ordered if item.room_type == "bathroom"]
            bedrooms = [item for item in ordered if item.room_type == "bedroom"]
            others = [item for item in ordered if item.room_type not in {"bedroom", "bathroom"}]
            if bathrooms and bedrooms and len(bedrooms) >= 2:
                group_a = bedrooms + others
                group_b = bathrooms
                if group_a and group_b:
                    return group_a, group_b

        group_a: list[_RoomPlanItem] = []
        group_b: list[_RoomPlanItem] = []
        sum_a = 0.0
        sum_b = 0.0
        for item in ordered:
            if sum_a <= sum_b:
                group_a.append(item)
                sum_a += item.preferred_area
            else:
                group_b.append(item)
                sum_b += item.preferred_area

        if not group_a or not group_b:
            pivot = len(ordered) // 2
            group_a = ordered[:pivot]
            group_b = ordered[pivot:]
        return group_a, group_b

    def _split_rect(
        self,
        *,
        rect: _Rect,
        ratio: float,
        axis: Literal["vertical", "horizontal"],
        first_min: float,
        second_min: float,
        first_area_bounds: tuple[float, float],
        second_area_bounds: tuple[float, float],
    ) -> tuple[_Rect, _Rect]:
        total_area = rect.area
        target_first_area = total_area * ratio
        low = max(first_area_bounds[0], total_area - second_area_bounds[1])
        high = min(first_area_bounds[1], total_area - second_area_bounds[0])
        if low - high > _EPSILON:
            raise LayoutPlanningError("Split is infeasible for room area constraints")

        if axis == "vertical":
            low = max(low, max(first_min, 0.5) * rect.height)
            high = min(high, total_area - max(second_min, 0.5) * rect.height)
            if low - high > _EPSILON:
                raise LayoutPlanningError("Vertical split is infeasible for zone constraints")
            first_area = min(max(target_first_area, low), high)
            split = first_area / rect.height
            left = _Rect(x=rect.x, y=rect.y, width=split, height=rect.height)
            right = _Rect(x=rect.x + split, y=rect.y, width=rect.width - split, height=rect.height)
            return left, right

        low = max(low, max(first_min, 0.5) * rect.width)
        high = min(high, total_area - max(second_min, 0.5) * rect.width)
        if low - high > _EPSILON:
            raise LayoutPlanningError("Horizontal split is infeasible for zone constraints")
        first_area = min(max(target_first_area, low), high)
        split = first_area / rect.width
        bottom = _Rect(x=rect.x, y=rect.y, width=rect.width, height=split)
        top = _Rect(x=rect.x, y=rect.y + split, width=rect.width, height=rect.height - split)
        return bottom, top

    @staticmethod
    def _group_min_span(rooms: list[_RoomPlanItem], axis: Literal["vertical", "horizontal"]) -> float:
        if not rooms:
            return 0.5
        if axis == "vertical":
            return max(item.min_width for item in rooms)
        return max(item.min_height for item in rooms)

    @staticmethod
    def _group_area_bounds(rooms: list[_RoomPlanItem]) -> tuple[float, float]:
        if not rooms:
            return (0.0, 0.0)
        min_sum = sum(item.min_area for item in rooms)
        max_sum = sum(item.max_area for item in rooms)
        return (min_sum, max_sum)

    @staticmethod
    def _ratio_candidates(base_ratio: float) -> list[float]:
        clamped = min(max(base_ratio, 0.05), 0.95)
        candidates = [clamped, 0.5, 0.38, 0.62, 0.25, 0.75]
        deduped: list[float] = []
        for value in candidates:
            if all(abs(value - existing) > 1e-6 for existing in deduped):
                deduped.append(value)
        return deduped

    @staticmethod
    def _area_candidates(*, low: float, high: float, target: float) -> list[float]:
        if low > high:
            return []
        clamped_target = min(max(target, low), high)
        midpoint = (low + high) / 2.0
        weighted_upper = (2.0 * high + low) / 3.0
        weighted_lower = (2.0 * low + high) / 3.0
        raw = [
            clamped_target,
            midpoint,
            weighted_upper,
            weighted_lower,
            high,
            low,
        ]
        ordered = sorted(raw, key=lambda value: (abs(value - clamped_target), -value))
        deduped: list[float] = []
        for value in ordered:
            if value < low - _EPSILON or value > high + _EPSILON:
                continue
            if all(abs(value - existing) > 1e-6 for existing in deduped):
                deduped.append(value)
        return deduped

    @staticmethod
    def _corridor_span_candidates(
        *,
        boundary_span: float,
        orthogonal_span: float,
        total_area: float,
        optimize_efficiency: bool,
    ) -> list[float]:
        max_span_by_ratio = (_CORRIDOR_MAX_AREA_RATIO * total_area) / max(orthogonal_span, _EPSILON)
        upper = min(_CORRIDOR_MAX_SPAN, boundary_span - 2.0, max_span_by_ratio)
        lower = max(_CORRIDOR_MIN_SPAN, 1.0)
        if upper < lower - _EPSILON:
            return []

        preferred = min(max(1.2, lower), upper)
        midpoint = (lower + upper) / 2.0
        raw = [preferred, midpoint, lower, upper]
        if optimize_efficiency:
            ordered = sorted(raw)
        else:
            ordered = sorted(raw, key=lambda value: (abs(value - preferred), value))
        deduped: list[float] = []
        for value in ordered:
            if value < lower - _EPSILON or value > upper + _EPSILON:
                continue
            if all(abs(value - existing) > 1e-6 for existing in deduped):
                deduped.append(value)
        return deduped

    @staticmethod
    def _validate_assignments(
        *,
        assignments: dict[int, _Rect],
        boundary_width: float,
        boundary_height: float,
    ) -> None:
        for rect in assignments.values():
            if rect.x < -_EPSILON or rect.y < -_EPSILON:
                raise LayoutPlanningError("Generated room has negative origin")
            if rect.x + rect.width > boundary_width + _EPSILON:
                raise LayoutPlanningError("Generated room exceeds boundary width")
            if rect.y + rect.height > boundary_height + _EPSILON:
                raise LayoutPlanningError("Generated room exceeds boundary height")

    # QUALITY FIX: normalize room geometry after placement to remove seams and reduce unusable leftover space.
    def normalize_layout(self, layout: dict[str, Any]) -> dict[str, Any]:
        return normalize_layout(layout)

    # QUALITY FIX: compute available rightward growth for a room without introducing overlaps.
    @staticmethod
    def _available_expand_width(
        *,
        rooms: list[dict[str, Any]],
        index: int,
        boundary_width: float,
    ) -> float:
        room = rooms[index]
        x0 = float(room["origin"]["x"])
        y0 = float(room["origin"]["y"])
        x1 = x0 + float(room["width"])
        y1 = y0 + float(room["height"])
        available = max(0.0, boundary_width - x1)

        for other_index, other in enumerate(rooms):
            if other_index == index:
                continue
            ox0 = float(other["origin"]["x"])
            oy0 = float(other["origin"]["y"])
            ox1 = ox0 + float(other["width"])
            oy1 = oy0 + float(other["height"])
            overlap_y = max(0.0, min(y1, oy1) - max(y0, oy0))
            if overlap_y <= _EPSILON:
                continue
            if ox0 + _EPSILON >= x1:
                available = min(available, max(0.0, ox0 - x1))
            elif ox1 > x1 + _EPSILON:
                available = 0.0
        return max(0.0, available)

    # QUALITY FIX: compute available upward growth for a room without introducing overlaps.
    @staticmethod
    def _available_expand_height(
        *,
        rooms: list[dict[str, Any]],
        index: int,
        boundary_height: float,
    ) -> float:
        room = rooms[index]
        x0 = float(room["origin"]["x"])
        y0 = float(room["origin"]["y"])
        x1 = x0 + float(room["width"])
        y1 = y0 + float(room["height"])
        available = max(0.0, boundary_height - y1)

        for other_index, other in enumerate(rooms):
            if other_index == index:
                continue
            ox0 = float(other["origin"]["x"])
            oy0 = float(other["origin"]["y"])
            ox1 = ox0 + float(other["width"])
            oy1 = oy0 + float(other["height"])
            overlap_x = max(0.0, min(x1, ox1) - max(x0, ox0))
            if overlap_x <= _EPSILON:
                continue
            if oy0 + _EPSILON >= y1:
                available = min(available, max(0.0, oy0 - y1))
            elif oy1 > y1 + _EPSILON:
                available = 0.0
        return max(0.0, available)

    @staticmethod
    def _build_walls(rooms: list[dict[str, Any]]) -> list[dict[str, Any]]:
        walls: list[dict[str, Any]] = []
        for room in rooms:
            x0 = float(room["origin"]["x"])
            y0 = float(room["origin"]["y"])
            x1 = x0 + float(room["width"])
            y1 = y0 + float(room["height"])
            walls.extend(
                [
                    {
                        "room_name": room["name"],
                        "wall": "bottom",
                        "start": {"x": x0, "y": y0},
                        "end": {"x": x1, "y": y0},
                        "thickness": 0.2,
                    },
                    {
                        "room_name": room["name"],
                        "wall": "right",
                        "start": {"x": x1, "y": y0},
                        "end": {"x": x1, "y": y1},
                        "thickness": 0.2,
                    },
                    {
                        "room_name": room["name"],
                        "wall": "top",
                        "start": {"x": x1, "y": y1},
                        "end": {"x": x0, "y": y1},
                        "thickness": 0.2,
                    },
                    {
                        "room_name": room["name"],
                        "wall": "left",
                        "start": {"x": x0, "y": y1},
                        "end": {"x": x0, "y": y0},
                        "thickness": 0.2,
                    },
                ]
            )
        return walls

    def _infer_room_rule(
        self,
        room_name: str,
        room_type: str,
    ) -> tuple[_RoomRule, Literal["public", "service", "private", "corridor"], str]:
        text = room_name.lower()
        normalized_type = room_type

        if room_type == "corridor":
            if "storage" in text:
                return (
                    _RoomRule(preferred_area=4.0, min_area=2.0, max_area=6.0, min_width=1.2, min_height=1.2),
                    "service",
                    "corridor",
                )
            return (
                _RoomRule(
                    preferred_area=14.0,
                    min_area=6.0,
                    max_area=10000.0,
                    min_width=_CORRIDOR_MIN_SPAN,
                    min_height=_CORRIDOR_MIN_SPAN,
                ),
                "corridor",
                "corridor",
            )

        if room_type == "kitchen":
            return (
                _RoomRule(preferred_area=12.0, min_area=8.0, max_area=18.0, min_width=2.4, min_height=2.4),
                "service",
                "kitchen",
            )

        if room_type == "bedroom":
            if "master" in text:
                return (
                    _RoomRule(preferred_area=16.0, min_area=12.0, max_area=25.0, min_width=3.0, min_height=3.0),
                    "private",
                    "bedroom",
                )
            if "child" in text or "kid" in text:
                return (
                    _RoomRule(preferred_area=12.0, min_area=9.0, max_area=16.0, min_width=2.6, min_height=2.6),
                    "private",
                    "bedroom",
                )
            return (
                _RoomRule(preferred_area=14.0, min_area=9.0, max_area=25.0, min_width=2.8, min_height=2.8),
                "private",
                "bedroom",
            )

        if room_type == "bathroom":
            if "guest" in text:
                return (
                    _RoomRule(preferred_area=4.0, min_area=3.0, max_area=6.0, min_width=1.5, min_height=1.5),
                    "public",
                    "bathroom",
                )
            if "laundry" in text:
                return (
                    _RoomRule(preferred_area=4.5, min_area=3.0, max_area=8.0, min_width=1.5, min_height=1.5),
                    "service",
                    "bathroom",
                )
            if "private" in text or "master" in text:
                return (
                    _RoomRule(preferred_area=5.0, min_area=3.0, max_area=6.0, min_width=1.5, min_height=1.5),
                    "private",
                    "bathroom",
                )
            return (
                _RoomRule(preferred_area=5.0, min_area=3.0, max_area=6.0, min_width=1.5, min_height=1.5),
                "private",
                "bathroom",
            )

        if room_type == "living":
            if "dining" in text:
                return (
                    _RoomRule(preferred_area=12.0, min_area=10.0, max_area=20.0, min_width=2.8, min_height=2.8),
                    "public",
                    "living",
                )
            if "storage" in text:
                return (
                    _RoomRule(preferred_area=4.0, min_area=2.0, max_area=6.0, min_width=1.2, min_height=1.2),
                    "service",
                    "corridor",
                )
            if "laundry" in text:
                return (
                    _RoomRule(preferred_area=4.5, min_area=3.0, max_area=8.0, min_width=1.5, min_height=1.5),
                    "service",
                    "bathroom",
                )
            return (
                _RoomRule(preferred_area=20.0, min_area=16.0, max_area=10000.0, min_width=3.5, min_height=3.5),
                "public",
                "living",
            )

        if room_type == "stairs":
            return (
                _RoomRule(preferred_area=9.0, min_area=4.0, max_area=16.0, min_width=2.0, min_height=2.0),
                "private",
                "stairs",
            )

        # Fallback normalization for unexpected but validated types.
        return (
            _RoomRule(preferred_area=10.0, min_area=6.0, max_area=20.0, min_width=2.5, min_height=2.5),
            "public",
            normalized_type,
        )

    @staticmethod
    def _requires_exterior_opening(item: _RoomPlanItem) -> bool:
        lowered = item.name.lower()
        if item.room_type == "bedroom":
            return True
        if item.room_type == "living" and "living" in lowered:
            return True
        if item.room_type == "kitchen":
            return True
        if item.room_type == "bathroom" and "laundry" not in lowered:
            return True
        return False

    @staticmethod
    def _rect_has_exterior(*, rect: _Rect, boundary_width: float, boundary_height: float) -> bool:
        return (
            abs(rect.x - 0.0) <= _EPSILON
            or abs(rect.y - 0.0) <= _EPSILON
            or abs((rect.x + rect.width) - boundary_width) <= _EPSILON
            or abs((rect.y + rect.height) - boundary_height) <= _EPSILON
        )

    @staticmethod
    def _rect_fits_item(*, item: _RoomPlanItem, rect: _Rect) -> bool:
        area = rect.area
        if area + _EPSILON < item.min_area:
            return False
        if area - item.max_area > _EPSILON:
            return False
        if rect.width + _EPSILON < item.min_width:
            return False
        if rect.height + _EPSILON < item.min_height:
            return False
        return True

    def _subdivide_oversized_living_rooms(self, rooms: list[dict[str, Any]]) -> list[dict[str, Any]]:
        corridor_rooms = [
            room
            for room in rooms
            if str(room.get("room_type", "")).lower() == "corridor"
            or "corridor" in str(room.get("name", "")).lower()
        ]
        corridor = next((room for room in corridor_rooms if str(room.get("name", "")).lower() == "main corridor"), None)
        if corridor is None and corridor_rooms:
            corridor = max(
                corridor_rooms,
                key=lambda current: float(current.get("width", 0.0)) * float(current.get("height", 0.0)),
            )
        main_corridor_name = str(corridor.get("name", "")).lower() if corridor is not None else ""
        boundary_max_x = max(
            (
                float(current.get("origin", {}).get("x", 0.0))
                + float(current.get("width", 0.0))
            )
            for current in rooms
        )
        boundary_max_y = max(
            (
                float(current.get("origin", {}).get("y", 0.0))
                + float(current.get("height", 0.0))
            )
            for current in rooms
        )
        existing_names = {str(room.get("name", "")) for room in rooms}
        output: list[dict[str, Any]] = []
        lounge_counter = 1

        for room in rooms:
            name = str(room.get("name", ""))
            room_type = str(room.get("room_type", ""))
            if room_type != "living" or "living" not in name.lower():
                output.append(room)
                continue

            width = float(room.get("width", 0.0))
            height = float(room.get("height", 0.0))
            area = width * height
            boundary_area = max(boundary_max_x * boundary_max_y, _EPSILON)
            dynamic_threshold = min(_LIVING_SPLIT_THRESHOLD_AREA, boundary_area * _MAX_LIVING_AREA_RATIO)
            if area <= dynamic_threshold + _EPSILON:
                output.append(room)
                continue

            max_living_area = max(boundary_area * _MAX_LIVING_AREA_RATIO, _EPSILON)
            by_target = int(math.ceil(area / _LIVING_SPLIT_TARGET_AREA))
            by_ratio_cap = int(math.ceil(area / max_living_area))
            split_count = max(2, min(6, max(by_target, by_ratio_cap)))
            x0 = float(room["origin"]["x"])
            y0 = float(room["origin"]["y"])

            shares_vertical = False
            shares_horizontal = False
            corridor_on_positive_side = True
            if corridor is not None:
                cx0 = float(corridor["origin"]["x"])
                cy0 = float(corridor["origin"]["y"])
                cwidth = float(corridor["width"])
                cheight = float(corridor["height"])
                cx1 = cx0 + cwidth
                cy1 = cy0 + cheight
                x1 = x0 + width
                y1 = y0 + height

                overlap_y = max(0.0, min(y1, cy1) - max(y0, cy0))
                overlap_x = max(0.0, min(x1, cx1) - max(x0, cx0))
                if overlap_y > 0.25:
                    if abs(x1 - cx0) <= _EPSILON:
                        shares_vertical = True
                        corridor_on_positive_side = True
                    elif abs(x0 - cx1) <= _EPSILON:
                        shares_vertical = True
                        corridor_on_positive_side = False
                if overlap_x > 0.25 and not shares_vertical:
                    if abs(y1 - cy0) <= _EPSILON:
                        shares_horizontal = True
                        corridor_on_positive_side = True
                    elif abs(y0 - cy1) <= _EPSILON:
                        shares_horizontal = True
                        corridor_on_positive_side = False

            axis: Literal["vertical", "horizontal"]
            if shares_vertical:
                # Keep all split segments touching corridor when the shared edge is vertical.
                axis = "horizontal"
            elif shares_horizontal:
                # Keep all split segments touching corridor when the shared edge is horizontal.
                axis = "vertical"
            else:
                axis = "vertical" if width >= height else "horizontal"

            if axis == "vertical":
                while split_count >= 2:
                    segment_width = width / split_count
                    segment_height = height
                    ratio = max(segment_width, segment_height) / max(min(segment_width, segment_height), _EPSILON)
                    if segment_width >= (_MIN_SPLIT_ROOM_SPAN - _EPSILON) and ratio <= 4.0 + _EPSILON:
                        break
                    split_count -= 1
            else:
                while split_count >= 2:
                    segment_width = width
                    segment_height = height / split_count
                    ratio = max(segment_width, segment_height) / max(min(segment_width, segment_height), _EPSILON)
                    if segment_height >= (_MIN_SPLIT_ROOM_SPAN - _EPSILON) and ratio <= 4.0 + _EPSILON:
                        break
                    split_count -= 1
            if split_count < 2:
                output.append(room)
                continue

            if axis == "horizontal":
                touches_bottom = abs(y0 - 0.0) <= _EPSILON
                touches_top = abs((y0 + height) - boundary_max_y) <= _EPSILON
                if touches_bottom and not touches_top:
                    living_index = 0
                elif touches_top and not touches_bottom:
                    living_index = split_count - 1
                else:
                    living_index = split_count - 1 if corridor_on_positive_side else 0
            else:
                touches_left = abs(x0 - 0.0) <= _EPSILON
                touches_right = abs((x0 + width) - boundary_max_x) <= _EPSILON
                if touches_left and not touches_right:
                    living_index = 0
                elif touches_right and not touches_left:
                    living_index = split_count - 1
                else:
                    living_index = split_count - 1 if corridor_on_positive_side else 0

            if axis == "vertical":
                step = width / split_count
                segments = [
                    _Rect(x=x0 + (idx * step), y=y0, width=step, height=height)
                    for idx in range(split_count)
                ]
            else:
                step = height / split_count
                segments = [
                    _Rect(x=x0, y=y0 + (idx * step), width=width, height=step)
                    for idx in range(split_count)
                ]

            if corridor_rooms:
                best_overlap = 0.0
                best_index: int | None = None
                best_is_main = False
                for idx, segment in enumerate(segments):
                    sx0 = segment.x
                    sy0 = segment.y
                    sx1 = sx0 + segment.width
                    sy1 = sy0 + segment.height
                    segment_overlap = 0.0
                    segment_is_main = False
                    for corridor_room in corridor_rooms:
                        cx0 = float(corridor_room["origin"]["x"])
                        cy0 = float(corridor_room["origin"]["y"])
                        cx1 = cx0 + float(corridor_room["width"])
                        cy1 = cy0 + float(corridor_room["height"])
                        overlap = 0.0
                        if abs(sx1 - cx0) <= _EPSILON or abs(sx0 - cx1) <= _EPSILON:
                            overlap = max(overlap, max(0.0, min(sy1, cy1) - max(sy0, cy0)))
                        if abs(sy1 - cy0) <= _EPSILON or abs(sy0 - cy1) <= _EPSILON:
                            overlap = max(overlap, max(0.0, min(sx1, cx1) - max(sx0, cx0)))
                        if overlap > segment_overlap + _EPSILON:
                            segment_overlap = overlap
                            segment_is_main = str(corridor_room.get("name", "")).lower() == main_corridor_name
                        elif abs(overlap - segment_overlap) <= _EPSILON:
                            if str(corridor_room.get("name", "")).lower() == main_corridor_name:
                                segment_is_main = True
                    if segment_overlap > best_overlap + _EPSILON:
                        best_overlap = segment_overlap
                        best_index = idx
                        best_is_main = segment_is_main
                    elif abs(segment_overlap - best_overlap) <= _EPSILON and segment_overlap > 0.25:
                        if segment_is_main and not best_is_main:
                            best_index = idx
                            best_is_main = True
                if best_index is not None and best_overlap > 0.25:
                    living_index = best_index

            for idx, segment in enumerate(segments):
                if idx == living_index:
                    output.append(
                        {
                            "name": name,
                            "room_type": "living",
                            "width": segment.width,
                            "height": segment.height,
                            "origin": {"x": segment.x, "y": segment.y},
                        }
                    )
                    continue

                while True:
                    lounge_name = f"Family Lounge {lounge_counter}"
                    lounge_counter += 1
                    if lounge_name not in existing_names:
                        existing_names.add(lounge_name)
                        break
                output.append(
                    {
                        "name": lounge_name,
                        "room_type": "living",
                        "width": segment.width,
                        "height": segment.height,
                        "origin": {"x": segment.x, "y": segment.y},
                    }
                )

        return output

    @staticmethod
    def _positive_float(value: Any) -> float | None:
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            return None
        return parsed if parsed > 0 else None


def normalize_layout(layout: dict[str, Any]) -> dict[str, Any]:
    """
    Post-placement normalizer.
    Snaps edges, fills boundary gaps, enforces minimum proportions.
    Never mutates input — works on a deepcopy.
    """
    import copy

    normalized_layout = copy.deepcopy(layout)
    boundary = normalized_layout.get("boundary")
    rooms = normalized_layout.get("rooms")
    if not isinstance(boundary, dict) or not isinstance(rooms, list):
        return normalized_layout

    bw = float(boundary.get("width", 0.0))
    bh = float(boundary.get("height", 0.0))
    if bw <= 0.0 or bh <= 0.0 or not rooms:
        return normalized_layout

    wall = 0.20
    snap = 0.05
    # Preserve the original boundary contacts so normalization does not detach rooms from the building edge.
    anchors: list[dict[str, bool]] = []
    for room in rooms:
        if not isinstance(room, dict):
            anchors.append({"left": False, "right": False, "bottom": False, "top": False})
            continue
        x0 = float(room.get("origin", {}).get("x", 0.0))
        y0 = float(room.get("origin", {}).get("y", 0.0))
        x1 = x0 + float(room.get("width", 0.0))
        y1 = y0 + float(room.get("height", 0.0))
        anchors.append(
            {
                "left": abs(x0 - 0.0) <= snap,
                "bottom": abs(y0 - 0.0) <= snap,
                "right": abs(x1 - bw) <= snap,
                "top": abs(y1 - bh) <= snap,
            }
        )

    # Step 1 — snap near-shared edges so micro-gaps collapse into one shared wall line.
    for first_index, first_room in enumerate(rooms):
        if not isinstance(first_room, dict):
            continue
        for second_index in range(first_index + 1, len(rooms)):
            second_room = rooms[second_index]
            if not isinstance(second_room, dict):
                continue

            first_right = float(first_room.get("origin", {}).get("x", 0.0)) + float(first_room.get("width", 0.0))
            second_left = float(second_room.get("origin", {}).get("x", 0.0))
            gap_x = second_left - first_right
            if 0.0 < gap_x < snap:
                midpoint = (first_right + second_left) / 2.0
                first_room["width"] = midpoint - float(first_room.get("origin", {}).get("x", 0.0))
                second_room.setdefault("origin", {})["x"] = midpoint

            first_top = float(first_room.get("origin", {}).get("y", 0.0)) + float(first_room.get("height", 0.0))
            second_bottom = float(second_room.get("origin", {}).get("y", 0.0))
            gap_y = second_bottom - first_top
            if 0.0 < gap_y < snap:
                midpoint = (first_top + second_bottom) / 2.0
                first_room["height"] = midpoint - float(first_room.get("origin", {}).get("y", 0.0))
                second_room.setdefault("origin", {})["y"] = midpoint

    # Step 2 — fill small right and top boundary gaps without stretching rooms across large unused spans.
    rightmost = max(
        (room for room in rooms if isinstance(room, dict)),
        key=lambda room: float(room.get("origin", {}).get("x", 0.0)) + float(room.get("width", 0.0)),
        default=None,
    )
    if rightmost is not None:
        gap = bw - (
            float(rightmost.get("origin", {}).get("x", 0.0)) + float(rightmost.get("width", 0.0))
        )
        if 0.0 < gap < 1.0:
            rightmost["width"] = float(rightmost.get("width", 0.0)) + gap

    topmost = max(
        (room for room in rooms if isinstance(room, dict)),
        key=lambda room: float(room.get("origin", {}).get("y", 0.0)) + float(room.get("height", 0.0)),
        default=None,
    )
    if topmost is not None:
        gap = bh - (
            float(topmost.get("origin", {}).get("y", 0.0)) + float(topmost.get("height", 0.0))
        )
        if 0.0 < gap < 1.0:
            topmost["height"] = float(topmost.get("height", 0.0)) + gap

    total_area = bw * bh
    min_ratios = {"living": 0.25, "bedroom": 0.12, "kitchen": 0.08, "bathroom": 0.05}
    # Step 3 — grow undersized rooms toward the requested minimum proportions without pushing them outside the boundary.
    for room_index, room in enumerate(rooms):
        if not isinstance(room, dict):
            continue
        room_type = str(room.get("room_type", "")).strip().lower()
        if room_type == "corridor":
            continue
        width = float(room.get("width", 0.0))
        height = float(room.get("height", 0.0))
        current_area = width * height
        if current_area <= _EPSILON:
            continue
        min_area = total_area * min_ratios.get(room_type, 0.05)
        if current_area >= min_area:
            continue

        scale = math.sqrt(min_area / current_area)
        width_cap = width + DeterministicLayoutPlanner._available_expand_width(
            rooms=rooms,
            index=room_index,
            boundary_width=bw,
        )
        height_cap = height + DeterministicLayoutPlanner._available_expand_height(
            rooms=rooms,
            index=room_index,
            boundary_height=bh,
        )
        room["width"] = min(width * scale, width_cap, bw - float(room.get("origin", {}).get("x", 0.0)) - wall)
        room["height"] = min(height * scale, height_cap, bh - float(room.get("origin", {}).get("y", 0.0)) - wall)

    # Step 4 — cap any dominant room before final corridor and boundary cleanup.
    rooms = _cap_dominant_room(rooms, bw, bh)

    # Step 5 — restore corridor rooms so their 1.2m side remains the narrow dimension.
    for room_index, room in enumerate(rooms):
        if not isinstance(room, dict):
            continue
        if room.get("room_type") == "corridor":
            rooms[room_index] = _enforce_corridor_dimensions(room, bw, bh)

    # Clamp, round, and restore edge anchors so normalized rooms stay inside the boundary and preserve exterior contacts.
    for room_index, room in enumerate(rooms):
        if not isinstance(room, dict):
            continue
        room_origin = room.setdefault("origin", {})
        x0 = max(0.0, min(float(room_origin.get("x", 0.0)), bw))
        y0 = max(0.0, min(float(room_origin.get("y", 0.0)), bh))
        room_type = str(room.get("room_type", "")).strip().lower()
        min_span = _CORRIDOR_MIN_SPAN if room_type == "corridor" else 1.5
        width = min(max(float(room.get("width", 0.0)), min_span), max(0.01, bw - x0))
        height = min(max(float(room.get("height", 0.0)), min_span), max(0.01, bh - y0))

        room_anchor = anchors[room_index]
        if room_anchor["left"]:
            x0 = 0.0
        if room_anchor["bottom"]:
            y0 = 0.0
        if room_anchor["right"] and not room_anchor["left"]:
            x0 = max(0.0, bw - width)
        if room_anchor["top"] and not room_anchor["bottom"]:
            y0 = max(0.0, bh - height)
        if room_anchor["left"] and room_anchor["right"]:
            x0 = 0.0
            width = bw
        if room_anchor["bottom"] and room_anchor["top"]:
            y0 = 0.0
            height = bh

        room_origin["x"] = round(x0, 4)
        room_origin["y"] = round(y0, 4)
        room["width"] = round(min(width, max(0.01, bw - x0)), 4)
        room["height"] = round(min(height, max(0.01, bh - y0)), 4)

    normalized_layout["rooms"] = rooms
    return normalized_layout


def _cap_dominant_room(
    rooms: list[dict[str, Any]],
    boundary_w: float,
    boundary_h: float,
) -> list[dict[str, Any]]:
    """
    Prevent any single room from taking more than 40%
    of the total floor area (except when there is only
    1 non-corridor room).

    When a room exceeds the cap:
      1. Calculate how much to trim (excess area).
      2. Trim from the longer dimension.
      3. The freed space is NOT redistributed automatically
         (the normalizer's gap-fill handles that).
    """
    area_cap_ratio = 0.40
    total_area = boundary_w * boundary_h
    max_area = total_area * area_cap_ratio

    non_corridor = [room for room in rooms if room.get("room_type") != "corridor"]
    if len(non_corridor) <= 1:
        return rooms

    for room in rooms:
        if room.get("room_type") == "corridor":
            continue
        w = float(room.get("width", 0))
        h = float(room.get("height", 0))
        current_area = w * h
        if current_area <= max_area:
            continue

        # Trim the longer dimension proportionally.
        scale = (max_area / current_area) ** 0.5
        new_w = max(1.8, w * scale)
        new_h = max(1.8, h * scale)
        room["width"] = round(new_w, 4)
        room["height"] = round(new_h, 4)

    return rooms


def _enforce_corridor_dimensions(
    room: dict[str, Any],
    boundary_w: float,
    boundary_h: float,
) -> dict[str, Any]:
    """
    Enforce that corridor rooms always have their 1.2m
    dimension as the NARROW side.

    If both dimensions are > 1.5, assume the larger one
    should span the full available length and force 1.2m
    on the narrower axis.
    """
    if room.get("room_type") != "corridor":
        return room
    if "storage" in str(room.get("name", "")).lower():
        return room

    w = float(room.get("width", 0))
    h = float(room.get("height", 0))
    corridor_width = _CORRIDOR_MIN_SPAN

    # Case: both are large (bug: 12.0 x 1.1 swapped)
    if w > 2.0 and h > 2.0:
        # Keep the larger dimension, force 1.2 on the smaller.
        if w >= h:
            room["width"] = round(w, 4)
            room["height"] = corridor_width
        else:
            room["width"] = corridor_width
            room["height"] = round(h, 4)

    # Case: narrow dimension already set correctly.
    elif w <= 1.5:
        room["width"] = corridor_width
        room["height"] = round(h, 4)
    elif h <= 1.5:
        room["width"] = round(w, 4)
        room["height"] = corridor_width

    return room
