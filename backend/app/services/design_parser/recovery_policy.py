"""Explicit recovery policy for parser outputs."""

from __future__ import annotations

import math
import re
from typing import Any

from app.models.design_parser import RecoveryMode


class RecoveryPolicy:
    """Applies optional, explicit payload repair/synthesis."""

    def apply(self, payload: dict[str, Any], prompt: str, mode: RecoveryMode) -> dict[str, Any]:
        if mode == RecoveryMode.STRICT:
            return payload
        return self._repair(payload=payload, prompt=prompt)

    def _repair(self, payload: dict[str, Any], prompt: str) -> dict[str, Any]:
        candidate = payload if isinstance(payload, dict) else {}
        boundary = self._resolve_boundary(candidate, prompt)
        rooms = self._sanitize_rooms(candidate.get("rooms"), boundary)
        if not rooms or not self._rooms_satisfy_requested_counts(rooms, prompt):
            rooms = self._synthesize_rooms(prompt=prompt, boundary=boundary)

        walls = self._sanitize_walls(candidate.get("walls"), rooms)
        if not walls:
            walls = self._generate_walls(rooms)

        openings = self._sanitize_openings(candidate.get("openings"))
        return {
            "boundary": boundary,
            "rooms": rooms,
            "walls": walls,
            "openings": openings,
        }

    def _resolve_boundary(self, payload: dict[str, Any], prompt: str) -> dict[str, float]:
        boundary = payload.get("boundary")
        width = None
        height = None
        if isinstance(boundary, dict):
            width = self._positive_float(boundary.get("width"))
            height = self._positive_float(boundary.get("height"))

        if width is None:
            width = self._positive_float(payload.get("width"))
        if height is None:
            height = self._positive_float(payload.get("height"))

        p_width, p_height = self._extract_boundary_from_prompt(prompt)
        if p_width is not None:
            width = p_width
        if p_height is not None:
            height = p_height

        return {
            "width": float(width if width is not None else 20.0),
            "height": float(height if height is not None else 12.0),
        }

    def _sanitize_rooms(self, raw_rooms: Any, boundary: dict[str, float]) -> list[dict[str, Any]]:
        if not isinstance(raw_rooms, list):
            return []

        rooms: list[dict[str, Any]] = []
        names: dict[str, int] = {}

        for index, raw in enumerate(raw_rooms):
            if not isinstance(raw, dict):
                continue

            width = self._positive_float(raw.get("width"))
            height = self._positive_float(raw.get("height"))
            if width is None or height is None:
                continue

            width = min(width, boundary["width"])
            height = min(height, boundary["height"])

            origin = raw.get("origin")
            ox = self._float(origin.get("x")) if isinstance(origin, dict) else 0.0
            oy = self._float(origin.get("y")) if isinstance(origin, dict) else 0.0
            ox = max(0.0, min(ox, boundary["width"] - width))
            oy = max(0.0, min(oy, boundary["height"] - height))

            room_type = self._room_type(raw.get("room_type"), raw.get("name"))
            base_name = self._room_name(raw.get("name"), room_type, index)
            names[base_name] = names.get(base_name, 0) + 1
            room_name = base_name if names[base_name] == 1 else f"{base_name} ({names[base_name]})"

            rooms.append(
                {
                    "name": room_name,
                    "room_type": room_type,
                    "width": round(width, 3),
                    "height": round(height, 3),
                    "origin": {"x": round(ox, 3), "y": round(oy, 3)},
                }
            )

        return rooms

    def _sanitize_walls(self, raw_walls: Any, rooms: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not isinstance(raw_walls, list):
            return []
        valid_rooms = {room["name"] for room in rooms}
        valid_sides = {"top", "bottom", "left", "right"}
        walls: list[dict[str, Any]] = []

        for raw in raw_walls:
            if not isinstance(raw, dict):
                continue
            room_name = raw.get("room_name")
            wall = raw.get("wall")
            start = raw.get("start")
            end = raw.get("end")
            if (
                not isinstance(room_name, str)
                or room_name not in valid_rooms
                or wall not in valid_sides
                or not isinstance(start, dict)
                or not isinstance(end, dict)
            ):
                continue
            try:
                wall_item = {
                    "room_name": room_name.strip(),
                    "wall": wall,
                    "start": {"x": float(start["x"]), "y": float(start["y"])},
                    "end": {"x": float(end["x"]), "y": float(end["y"])},
                    "thickness": float(raw.get("thickness", 0.2)),
                }
            except (TypeError, ValueError, KeyError):
                continue
            walls.append(wall_item)
        return walls

    def _sanitize_openings(self, raw_openings: Any) -> list[dict[str, Any]]:
        if not isinstance(raw_openings, list):
            return []
        valid_sides = {"top", "bottom", "left", "right"}
        openings: list[dict[str, Any]] = []
        for raw in raw_openings:
            if not isinstance(raw, dict):
                continue
            opening_type = raw.get("type")
            room_name = raw.get("room_name")
            wall = raw.get("wall")
            cut_start = raw.get("cut_start")
            cut_end = raw.get("cut_end")
            if (
                opening_type not in {"door", "window"}
                or not isinstance(room_name, str)
                or wall not in valid_sides
                or not isinstance(cut_start, dict)
                or not isinstance(cut_end, dict)
            ):
                continue
            try:
                normalized = {
                    "type": opening_type,
                    "room_name": room_name.strip(),
                    "wall": wall,
                    "cut_start": {"x": float(cut_start["x"]), "y": float(cut_start["y"])},
                    "cut_end": {"x": float(cut_end["x"]), "y": float(cut_end["y"])},
                }
            except (TypeError, ValueError, KeyError):
                continue

            if opening_type == "door":
                hinge = raw.get("hinge")
                swing = raw.get("swing")
                normalized["hinge"] = hinge if hinge in {"left", "right"} else "left"
                normalized["swing"] = swing if swing in {"in", "out"} else "in"

            openings.append(normalized)
        return openings

    def _generate_walls(self, rooms: list[dict[str, Any]]) -> list[dict[str, Any]]:
        walls: list[dict[str, Any]] = []
        for room in rooms:
            x0 = room["origin"]["x"]
            y0 = room["origin"]["y"]
            x1 = x0 + room["width"]
            y1 = y0 + room["height"]
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

    def _synthesize_rooms(self, prompt: str, boundary: dict[str, float]) -> list[dict[str, Any]]:
        room_types = self._requested_room_types(prompt)
        total = len(room_types)
        cols = max(1, min(3, math.ceil(math.sqrt(total))))
        rows = max(1, math.ceil(total / cols))
        x_edges = [round(boundary["width"] * idx / cols, 3) for idx in range(cols + 1)]
        y_edges = [round(boundary["height"] * idx / rows, 3) for idx in range(rows + 1)]

        type_counter: dict[str, int] = {}
        rooms: list[dict[str, Any]] = []
        for idx, room_type in enumerate(room_types):
            row = idx // cols
            col = idx % cols
            x0 = x_edges[col]
            x1 = x_edges[col + 1]
            y0 = y_edges[row]
            y1 = y_edges[row + 1]
            type_counter[room_type] = type_counter.get(room_type, 0) + 1
            rooms.append(
                {
                    "name": self._default_room_name(room_type, type_counter[room_type]),
                    "room_type": room_type,
                    "width": round(x1 - x0, 3),
                    "height": round(y1 - y0, 3),
                    "origin": {"x": x0, "y": y0},
                }
            )
        return rooms

    @staticmethod
    def _extract_boundary_from_prompt(prompt: str) -> tuple[float | None, float | None]:
        text = prompt.lower()
        match = re.search(r"(\d+(?:\.\d+)?)\s*[x×]\s*(\d+(?:\.\d+)?)", text)
        if not match:
            return None, None
        return float(match.group(1)), float(match.group(2))

    @staticmethod
    def _positive_float(value: Any) -> float | None:
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            return None
        return parsed if parsed > 0 else None

    @staticmethod
    def _float(value: Any, default: float = 0.0) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _room_type(room_type: Any, name: Any) -> str:
        explicit = str(room_type or "").strip().lower()
        if explicit in {"living", "bedroom", "kitchen", "bathroom", "corridor", "stairs"}:
            return explicit
        text = f"{room_type or ''} {name or ''}".lower()
        if "kitchen" in text:
            return "kitchen"
        if "bed" in text:
            return "bedroom"
        if "bath" in text or "wc" in text:
            return "bathroom"
        if "corridor" in text or "hallway" in text:
            return "corridor"
        if "stairs" in text or "stair" in text:
            return "stairs"
        return "living"

    def _room_name(self, value: Any, room_type: str, index: int) -> str:
        cleaned = str(value or "").strip()
        if cleaned:
            return cleaned
        return self._default_room_name(room_type, index + 1)

    @staticmethod
    def _default_room_name(room_type: str, room_index: int) -> str:
        if room_type == "living":
            return "Living Room" if room_index == 1 else f"Living Room {room_index}"
        if room_type == "kitchen":
            return "Kitchen" if room_index == 1 else f"Kitchen {room_index}"
        if room_type == "bedroom":
            return f"Bedroom {room_index}"
        if room_type == "bathroom":
            return f"Bathroom {room_index}"
        if room_type == "corridor":
            return "Corridor" if room_index == 1 else f"Corridor {room_index}"
        if room_type == "stairs":
            return "Stairs" if room_index == 1 else f"Stairs {room_index}"
        return f"Room {room_index}"

    @staticmethod
    def _requested_room_types(prompt: str) -> list[str]:
        text = prompt.lower()
        room_types: list[str] = []
        if "living" in text or "lounge" in text:
            room_types.append("living")
        if "kitchen" in text:
            room_types.append("kitchen")
        bedroom_count = RecoveryPolicy._extract_count(text, r"(\d+)\s*bedrooms?", default_if_present="bedroom")
        bathroom_count = RecoveryPolicy._extract_count(text, r"(\d+)\s*bathrooms?", default_if_present="bathroom")
        room_types.extend("bedroom" for _ in range(bedroom_count))
        room_types.extend("bathroom" for _ in range(bathroom_count))
        if "corridor" in text or "hallway" in text:
            room_types.append("corridor")
        if "stairs" in text:
            room_types.append("stairs")
        return room_types or ["living"]

    @staticmethod
    def _extract_count(text: str, pattern: str, default_if_present: str) -> int:
        match = re.search(pattern, text)
        if match:
            return max(1, int(match.group(1)))
        if "two " + default_if_present in text or "two " + default_if_present + "s" in text:
            return 2
        if "three " + default_if_present in text or "three " + default_if_present + "s" in text:
            return 3
        return 1 if default_if_present in text else 0

    def _rooms_satisfy_requested_counts(self, rooms: list[dict[str, Any]], prompt: str) -> bool:
        expected = self._requested_room_type_counts(prompt)
        if not expected:
            return bool(rooms)

        actual: dict[str, int] = {}
        for room in rooms:
            room_type = room.get("room_type")
            if not isinstance(room_type, str):
                continue
            actual[room_type] = actual.get(room_type, 0) + 1

        for room_type, count in expected.items():
            if actual.get(room_type, 0) < count:
                return False
        return True

    def _requested_room_type_counts(self, prompt: str) -> dict[str, int]:
        counts: dict[str, int] = {}
        for room_type in self._requested_room_types(prompt):
            counts[room_type] = counts.get(room_type, 0) + 1
        return counts
