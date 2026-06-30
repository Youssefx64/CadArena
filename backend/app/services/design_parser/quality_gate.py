"""Architectural quality gate for generated residential layouts."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from app.models.design_parser import DesignQualityReport
from app.schemas.design_intent import DesignIntent
from app.services.design_parser.egyptian_building_code import (
    EBC_WINDOW_MIN_RATIO,
    validate_room_dimensions,
)


QUALITY_MIN_SCORE = 0.80
CODE_PROFILE = "EBC_RESIDENTIAL_V1"
_EPSILON = 1e-6
_WINDOW_HEIGHT = 1.2
_CORRIDOR_MIN_WIDTH = 1.20
_CORRIDOR_MAX_WIDTH = 2.00
_MAX_STRUCTURAL_SPAN = 7.00
_MIN_COVERAGE_STRICT = 0.75
_LOW_COVERAGE_WARNING = 0.85


class ArchitecturalQualityGate:
    """Build and enforce a production quality report for a planned layout."""

    def evaluate(
        self,
        *,
        planned_payload: dict[str, Any],
        metrics_payload: dict[str, Any] | None = None,
        used_emergency_layout: bool = False,
        repairs_applied: list[str] | None = None,
        strict_openings: bool = True,
        enforce_score: bool = True,
    ) -> DesignQualityReport:
        metrics = metrics_payload or {}
        score = self._coerce_score(metrics.get("total_score"), default=1.0)
        selected_topology = str(metrics.get("selected_topology") or "structured_intent")
        hard_failures: list[str] = []
        warnings: list[str] = []

        if used_emergency_layout:
            hard_failures.append("emergency_layout_fallback_used")

        if enforce_score and score < QUALITY_MIN_SCORE - _EPSILON:
            hard_failures.append(
                f"quality_score_below_threshold:{score:.3f}<min:{QUALITY_MIN_SCORE:.3f}"
            )

        boundary = planned_payload.get("boundary")
        rooms_raw = planned_payload.get("rooms")
        openings_raw = planned_payload.get("openings", [])
        if not isinstance(boundary, dict):
            hard_failures.append("boundary_missing")
            boundary = {}
        if not isinstance(rooms_raw, list) or not rooms_raw:
            hard_failures.append("rooms_missing")
            rooms_raw = []
        if not isinstance(openings_raw, list):
            hard_failures.append("openings_must_be_list")
            openings_raw = []

        boundary_width = self._positive_float(boundary.get("width"))
        boundary_height = self._positive_float(boundary.get("height"))
        if boundary_width is None or boundary_height is None:
            hard_failures.append("boundary_dimensions_invalid")
            boundary_width = boundary_width or 0.0
            boundary_height = boundary_height or 0.0

        rooms = [room for room in (self._room_box(raw) for raw in rooms_raw) if room is not None]
        if len(rooms) != len(rooms_raw):
            hard_failures.append("one_or_more_rooms_invalid")

        self._check_room_geometry(
            rooms=rooms,
            boundary_width=boundary_width,
            boundary_height=boundary_height,
            hard_failures=hard_failures,
            warnings=warnings,
            strict_openings=strict_openings,
        )
        openings = [
            opening
            for opening in (self._opening_box(raw) for raw in openings_raw)
            if opening is not None
        ]
        if len(openings) != len(openings_raw):
            hard_failures.append("one_or_more_openings_invalid")

        mechanical_allowed = self._mechanical_ventilation_allowed(planned_payload)
        self._check_openings(
            rooms=rooms,
            openings=openings,
            boundary_width=boundary_width,
            boundary_height=boundary_height,
            hard_failures=hard_failures,
            warnings=warnings,
            strict_openings=strict_openings,
            mechanical_allowed=mechanical_allowed,
        )

        if hard_failures:
            grade = "F"
        elif score >= 0.90:
            grade = "A"
        elif score >= 0.80:
            grade = "B"
        elif score >= 0.70:
            grade = "C"
        elif score >= 0.60:
            grade = "D"
        else:
            grade = "F"

        return DesignQualityReport(
            passed=not hard_failures,
            score=round(score, 4),
            grade=grade,
            code_profile=CODE_PROFILE,
            hard_failures=hard_failures,
            warnings=warnings,
            repairs_applied=repairs_applied or [],
            selected_topology=selected_topology,
        )

    def evaluate_design_intent(self, intent: DesignIntent) -> DesignQualityReport:
        """Return a lightweight quality report for the public structured DXF route."""

        if any(room.origin is None for room in intent.rooms):
            hard_failures: list[str] = []
            warnings = ["rooms_without_origin_will_be_auto_placed"]
            for room in intent.rooms:
                descriptor = self._ebc_descriptor(
                    {
                        "name": room.name,
                        "room_type": room.room_type,
                    }
                )
                for violation in validate_room_dimensions(descriptor, room.width, room.height):
                    hard_failures.append(f"ebc_dimension:{violation}")
            if not intent.openings:
                warnings.append("openings_missing_auto_doors_will_be_used")
            score = 1.0 if not hard_failures else 0.5
            return DesignQualityReport(
                passed=not hard_failures,
                score=score,
                grade="A" if not hard_failures else "F",
                code_profile=CODE_PROFILE,
                hard_failures=hard_failures,
                warnings=warnings,
                repairs_applied=["structured_intent_auto_placement_pending"],
                selected_topology="structured_intent",
            )

        rooms: list[dict[str, Any]] = []
        for room in intent.rooms:
            origin = room.origin
            rooms.append(
                {
                    "name": room.name,
                    "room_type": room.room_type,
                    "width": room.width,
                    "height": room.height,
                    "origin": {
                        "x": origin.x if origin is not None else 0.0,
                        "y": origin.y if origin is not None else 0.0,
                    },
                }
            )
        openings = [opening.model_dump(mode="json") for opening in intent.openings]
        payload = {
            "boundary": intent.boundary.model_dump(mode="json"),
            "rooms": rooms,
            "openings": openings,
        }
        return self.evaluate(
            planned_payload=payload,
            metrics_payload={
                "total_score": 1.0,
                "selected_topology": "structured_intent",
            },
            strict_openings=False,
            enforce_score=False,
        )

    def _check_room_geometry(
        self,
        *,
        rooms: list[dict[str, Any]],
        boundary_width: float,
        boundary_height: float,
        hard_failures: list[str],
        warnings: list[str],
        strict_openings: bool,
    ) -> None:
        if not rooms:
            return

        boundary_area = max(boundary_width * boundary_height, _EPSILON)
        covered_area = 0.0
        names: set[str] = set()

        for index, room in enumerate(rooms):
            name = room["name"]
            if name in names:
                hard_failures.append(f"duplicate_room_name:{name}")
            names.add(name)

            x0 = room["x0"]
            y0 = room["y0"]
            x1 = room["x1"]
            y1 = room["y1"]
            width = room["width"]
            height = room["height"]
            covered_area += width * height

            if x0 < -_EPSILON or y0 < -_EPSILON or x1 > boundary_width + _EPSILON or y1 > boundary_height + _EPSILON:
                hard_failures.append(f"room_outside_boundary:{name}")

            descriptor = self._ebc_descriptor(room)
            for violation in validate_room_dimensions(descriptor, width, height):
                hard_failures.append(f"ebc_dimension:{violation}")

            lowered = name.lower()
            if room["room_type"] == "corridor" and "storage" not in lowered:
                corridor_width = min(width, height)
                if corridor_width < _CORRIDOR_MIN_WIDTH - _EPSILON:
                    hard_failures.append(f"corridor_too_narrow:{name}:{corridor_width:.2f}m")
                if corridor_width > _CORRIDOR_MAX_WIDTH + _EPSILON:
                    hard_failures.append(f"corridor_too_wide:{name}:{corridor_width:.2f}m")

            if room["room_type"] in {"bedroom", "stairs"} and min(width, height) > _MAX_STRUCTURAL_SPAN + _EPSILON:
                hard_failures.append(f"structural_span_exceeded:{name}")

            for other in rooms[index + 1 :]:
                if self._rooms_overlap(room, other):
                    hard_failures.append(f"rooms_overlap:{name}:{other['name']}")

        coverage = covered_area / boundary_area
        if coverage > 1.01:
            hard_failures.append(f"room_area_exceeds_boundary:{coverage:.3f}")
        if coverage < _MIN_COVERAGE_STRICT and strict_openings:
            hard_failures.append(f"boundary_coverage_too_low:{coverage:.3f}")
        elif coverage < _LOW_COVERAGE_WARNING:
            warnings.append(f"boundary_coverage_low:{coverage:.3f}")

    def _check_openings(
        self,
        *,
        rooms: list[dict[str, Any]],
        openings: list[dict[str, Any]],
        boundary_width: float,
        boundary_height: float,
        hard_failures: list[str],
        warnings: list[str],
        strict_openings: bool,
        mechanical_allowed: bool = True,
    ) -> None:
        if not rooms:
            return

        room_by_name = {room["name"]: room for room in rooms}
        windows_by_room: dict[str, list[dict[str, Any]]] = defaultdict(list)
        doors_by_room: dict[str, list[dict[str, Any]]] = defaultdict(list)
        doors_by_room_wall: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        exterior_door_count = 0

        for opening in openings:
            room = room_by_name.get(opening["room_name"])
            if room is None:
                hard_failures.append(f"opening_unknown_room:{opening['room_name']}")
                continue
            if opening["wall"] not in {"left", "right", "top", "bottom"}:
                hard_failures.append(f"opening_invalid_wall:{opening['room_name']}:{opening['wall']}")
                continue
            if not self._opening_on_wall(opening, room):
                hard_failures.append(f"opening_not_on_room_wall:{opening['room_name']}:{opening['wall']}")
                continue
            if opening["type"] == "window":
                windows_by_room[opening["room_name"]].append(opening)
                if opening["wall"] not in self._exterior_sides(room, boundary_width, boundary_height):
                    hard_failures.append(f"window_not_exterior:{opening['room_name']}:{opening['wall']}")
            elif opening["type"] == "door":
                doors_by_room[opening["room_name"]].append(opening)
                doors_by_room_wall[(opening["room_name"], opening["wall"])].append(opening)
                if opening["wall"] in self._exterior_sides(room, boundary_width, boundary_height):
                    exterior_door_count += 1

        for room in rooms:
            if room["room_type"] != "bathroom" or "laundry" in room["name"].lower():
                continue
            bathroom_doors = doors_by_room.get(room["name"], [])
            if not bathroom_doors:
                self._add_opening_issue(
                    strict_openings,
                    hard_failures,
                    warnings,
                    f"bathroom_door_missing:{room['name']}",
                )
            if any(
                door["wall"] in self._exterior_sides(room, boundary_width, boundary_height)
                for door in bathroom_doors
            ):
                hard_failures.append(f"bathroom_exterior_door_forbidden:{room['name']}")

        for room in rooms:
            if room["room_type"] == "bedroom" and not doors_by_room.get(room["name"]):
                self._add_opening_issue(
                    strict_openings,
                    hard_failures,
                    warnings,
                    f"bedroom_door_missing:{room['name']}",
                )

        for (room_name, wall), doors in doors_by_room_wall.items():
            for door in doors:
                for window in windows_by_room.get(room_name, []):
                    if window["wall"] == wall and self._opening_segments_overlap(door, window):
                        hard_failures.append(f"door_window_overlap:{room_name}:{wall}")

        forbidden_pairs = self._door_pairs(openings=openings, rooms=rooms)
        door_neighbors_by_room: dict[str, set[str]] = defaultdict(set)
        for first_name, second_name in forbidden_pairs:
            door_neighbors_by_room[first_name].add(second_name)
            door_neighbors_by_room[second_name].add(first_name)

        for room in rooms:
            if room["room_type"] != "bathroom" or "laundry" in room["name"].lower():
                continue
            neighbors = door_neighbors_by_room.get(room["name"], set())
            non_service_neighbors = [
                name
                for name in neighbors
                if not self._is_laundry_room(room_by_name[name])
            ]
            bathroom_doors = doors_by_room.get(room["name"], [])
            if len(non_service_neighbors) > 1 or (
                len(bathroom_doors) > 1 and len(neighbors) <= 1
            ):
                hard_failures.append(
                    f"bathroom_multiple_doors:{room['name']}:{len(bathroom_doors)}"
                )

        for first_name, second_name in forbidden_pairs:
            first = room_by_name[first_name]
            second = room_by_name[second_name]
            pair_types = {first["room_type"], second["room_type"]}
            pair_names = f"{first_name.lower()} {second_name.lower()}"
            has_non_laundry_bathroom = any(
                room["room_type"] == "bathroom" and not self._is_laundry_room(room)
                for room in (first, second)
            )
            if has_non_laundry_bathroom and (
                pair_types == {"bathroom", "kitchen"} or "dining" in pair_names
            ):
                hard_failures.append(f"forbidden_door_pair:{first_name}:{second_name}")
            if (
                has_non_laundry_bathroom
                and pair_types == {"bathroom", "bedroom"}
                and not self._is_private_ensuite_pair(
                    first=first,
                    second=second,
                )
            ):
                hard_failures.append(f"forbidden_door_pair:{first_name}:{second_name}")
            if "bedroom" in pair_types and ("kitchen" in pair_types or first["room_type"] == second["room_type"] == "bedroom"):
                hard_failures.append(f"forbidden_door_pair:{first_name}:{second_name}")

        if exterior_door_count <= 0:
            if strict_openings:
                hard_failures.append("main_entry_door_missing")
            else:
                warnings.append("main_entry_door_missing")

        self._check_daylight_and_ventilation(
            rooms=rooms,
            windows_by_room=windows_by_room,
            hard_failures=hard_failures,
            warnings=warnings,
            strict_openings=strict_openings,
            mechanical_allowed=mechanical_allowed,
        )

    def _check_daylight_and_ventilation(
        self,
        *,
        rooms: list[dict[str, Any]],
        windows_by_room: dict[str, list[dict[str, Any]]],
        hard_failures: list[str],
        warnings: list[str],
        strict_openings: bool,
        mechanical_allowed: bool = True,
    ) -> None:
        for room in rooms:
            room_type = room["room_type"]
            lowered = room["name"].lower()
            room_windows = windows_by_room.get(room["name"], [])

            if room_type == "bedroom":
                if not room_windows:
                    self._add_opening_issue(
                        strict_openings,
                        hard_failures,
                        warnings,
                        f"bedroom_window_missing:{room['name']}",
                    )
                    continue
                if max((window["length"] for window in room_windows), default=0.0) < 1.0 - _EPSILON:
                    self._add_opening_issue(
                        strict_openings,
                        hard_failures,
                        warnings,
                        f"bedroom_window_too_narrow:{room['name']}",
                    )

            if room_type == "living" and any(k in lowered for k in ("living", "salon", "reception", "lounge", "sitting", "family")):
                total_window_area = sum(window["length"] * _WINDOW_HEIGHT for window in room_windows)
                required_area = room["width"] * room["height"] * EBC_WINDOW_MIN_RATIO
                if total_window_area + _EPSILON < required_area:
                    self._add_opening_issue(
                        strict_openings,
                        hard_failures,
                        warnings,
                        f"living_daylight_ratio_failed:{room['name']}",
                    )

            if room_type == "kitchen" and not room_windows and not mechanical_allowed:
                self._add_opening_issue(
                    strict_openings,
                    hard_failures,
                    warnings,
                    f"kitchen_window_missing:{room['name']}",
                )

            if room_type == "bathroom" and "laundry" not in lowered and not room_windows and not mechanical_allowed:
                self._add_opening_issue(
                    strict_openings,
                    hard_failures,
                    warnings,
                    f"bathroom_window_missing:{room['name']}",
                )

    @staticmethod
    def _add_opening_issue(
        strict_openings: bool,
        hard_failures: list[str],
        warnings: list[str],
        message: str,
    ) -> None:
        if strict_openings:
            hard_failures.append(message)
        else:
            warnings.append(message)

    @staticmethod
    def _room_box(raw: Any) -> dict[str, Any] | None:
        if not isinstance(raw, dict):
            return None
        origin = raw.get("origin")
        if not isinstance(origin, dict):
            origin = {"x": 0.0, "y": 0.0}
        try:
            name = str(raw.get("name", "")).strip()
            room_type = str(raw.get("room_type", "")).strip().lower()
            width = float(raw.get("width"))
            height = float(raw.get("height"))
            x0 = float(origin.get("x", 0.0))
            y0 = float(origin.get("y", 0.0))
        except (TypeError, ValueError):
            return None
        if not name or not room_type or width <= 0 or height <= 0:
            return None
        return {
            "name": name,
            "room_type": room_type,
            "width": width,
            "height": height,
            "x0": x0,
            "y0": y0,
            "x1": x0 + width,
            "y1": y0 + height,
        }

    @staticmethod
    def _opening_box(raw: Any) -> dict[str, Any] | None:
        if not isinstance(raw, dict):
            return None
        start = raw.get("cut_start")
        end = raw.get("cut_end")
        if not isinstance(start, dict) or not isinstance(end, dict):
            return None
        try:
            opening_type = str(raw.get("type", "")).strip().lower()
            room_name = str(raw.get("room_name", "")).strip()
            wall = str(raw.get("wall", "")).strip().lower()
            sx = float(start.get("x"))
            sy = float(start.get("y"))
            ex = float(end.get("x"))
            ey = float(end.get("y"))
        except (TypeError, ValueError):
            return None
        if opening_type not in {"door", "window"} or not room_name or not wall:
            return None
        length = abs(ey - sy) if abs(sx - ex) <= _EPSILON else abs(ex - sx)
        if length <= _EPSILON:
            return None
        return {
            "type": opening_type,
            "room_name": room_name,
            "wall": wall,
            "sx": sx,
            "sy": sy,
            "ex": ex,
            "ey": ey,
            "length": length,
        }

    @staticmethod
    def _ebc_descriptor(room: dict[str, Any]) -> str:
        name = room["name"].lower()
        room_type = room["room_type"]
        if room_type == "bedroom" and "master" in name:
            return "master_bedroom"
        if "dining" in name:
            return "dining"
        if "laundry" in name:
            return "laundry"
        if "storage" in name:
            return "storage"
        return room_type

    @staticmethod
    def _rooms_overlap(first: dict[str, Any], second: dict[str, Any]) -> bool:
        return (
            first["x0"] < second["x1"] - _EPSILON
            and first["x1"] > second["x0"] + _EPSILON
            and first["y0"] < second["y1"] - _EPSILON
            and first["y1"] > second["y0"] + _EPSILON
        )

    @staticmethod
    def _opening_on_wall(opening: dict[str, Any], room: dict[str, Any]) -> bool:
        wall = opening["wall"]
        if wall == "bottom":
            return abs(opening["sy"] - room["y0"]) <= _EPSILON and abs(opening["ey"] - room["y0"]) <= _EPSILON
        if wall == "top":
            return abs(opening["sy"] - room["y1"]) <= _EPSILON and abs(opening["ey"] - room["y1"]) <= _EPSILON
        if wall == "left":
            return abs(opening["sx"] - room["x0"]) <= _EPSILON and abs(opening["ex"] - room["x0"]) <= _EPSILON
        if wall == "right":
            return abs(opening["sx"] - room["x1"]) <= _EPSILON and abs(opening["ex"] - room["x1"]) <= _EPSILON
        return False

    @staticmethod
    def _exterior_sides(room: dict[str, Any], boundary_width: float, boundary_height: float) -> set[str]:
        sides: set[str] = set()
        if abs(room["x0"]) <= _EPSILON:
            sides.add("left")
        if abs(room["x1"] - boundary_width) <= _EPSILON:
            sides.add("right")
        if abs(room["y0"]) <= _EPSILON:
            sides.add("bottom")
        if abs(room["y1"] - boundary_height) <= _EPSILON:
            sides.add("top")
        return sides

    @staticmethod
    def _opening_segments_overlap(first: dict[str, Any], second: dict[str, Any]) -> bool:
        if abs(first["sx"] - first["ex"]) <= _EPSILON:
            a0, a1 = sorted((first["sy"], first["ey"]))
            b0, b1 = sorted((second["sy"], second["ey"]))
        else:
            a0, a1 = sorted((first["sx"], first["ex"]))
            b0, b1 = sorted((second["sx"], second["ex"]))
        return a0 < b1 - _EPSILON and a1 > b0 + _EPSILON

    @staticmethod
    def _is_private_ensuite_pair(*, first: dict[str, Any], second: dict[str, Any]) -> bool:
        if first["room_type"] == "bathroom":
            bathroom = first
            bedroom = second
        else:
            bathroom = second
            bedroom = first
        bathroom_name = bathroom["name"].lower()
        bedroom_name = bedroom["name"].lower()
        bathroom_is_private = any(
            token in bathroom_name
            for token in ("ensuite", "en-suite", "master", "private")
        )
        bedroom_is_primary = any(token in bedroom_name for token in ("master", "primary"))
        return bathroom_is_private and bedroom_is_primary

    @staticmethod
    def _is_laundry_room(room: dict[str, Any]) -> bool:
        return room["room_type"] == "bathroom" and "laundry" in room["name"].lower()

    @staticmethod
    def _door_pairs(*, openings: list[dict[str, Any]], rooms: list[dict[str, Any]]) -> set[tuple[str, str]]:
        by_signature: dict[tuple[str, float, float, float], list[str]] = defaultdict(list)
        room_names = {room["name"] for room in rooms}
        for opening in openings:
            if opening["type"] != "door" or opening["room_name"] not in room_names:
                continue
            if abs(opening["sx"] - opening["ex"]) <= _EPSILON:
                signature = (
                    "vertical",
                    round(opening["sx"], 6),
                    round(min(opening["sy"], opening["ey"]), 6),
                    round(max(opening["sy"], opening["ey"]), 6),
                )
            else:
                signature = (
                    "horizontal",
                    round(opening["sy"], 6),
                    round(min(opening["sx"], opening["ex"]), 6),
                    round(max(opening["sx"], opening["ex"]), 6),
                )
            by_signature[signature].append(opening["room_name"])

        pairs: set[tuple[str, str]] = set()
        for names in by_signature.values():
            if len(names) < 2:
                continue
            unique = sorted(set(names))
            for index, first in enumerate(unique):
                for second in unique[index + 1 :]:
                    pairs.add((first, second))
        return pairs

    @staticmethod
    def _mechanical_ventilation_allowed(planned_payload: dict[str, Any]) -> bool:
        return True

    @staticmethod
    def _positive_float(value: Any) -> float | None:
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            return None
        if parsed <= 0:
            return None
        return parsed

    @staticmethod
    def _coerce_score(value: Any, *, default: float) -> float:
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            return default
        return max(0.0, min(1.0, parsed))
