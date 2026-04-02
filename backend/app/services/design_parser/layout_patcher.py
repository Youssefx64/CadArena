"""Iterative layout patching utilities for surgical design edits."""

from __future__ import annotations

import copy
import math
from typing import Any


class LayoutPatcher:
    """
    Applies surgical edits to an existing CadArena layout JSON.

    Never regenerates the full layout and never mutates the input layout.
    Each operation returns a patched deep copy of the provided layout.
    """

    WALL_CLR = 0.15
    MIN_ROOM_SIDE = 1.5
    WALL_THICKNESS = 0.2
    GRID_STEP = 0.5

    def apply(self, current: dict[str, Any], diff: dict[str, Any]) -> dict[str, Any]:
        """
        Apply a diff operation to a deep-copied layout and return the result.

        Unknown operations return the copied layout unchanged.
        """

        # Clone the current layout first so callers never see in-place mutations.
        layout = copy.deepcopy(current)
        op = str(diff.get("operation", "") or "")
        raw_changes = diff.get("changes", {})
        changes = copy.deepcopy(raw_changes) if isinstance(raw_changes, dict) else {}

        # Route the deep-copied layout through the requested surgical operation.
        if op == "modify":
            layout = self._modify_rooms(layout, changes)
        elif op == "add":
            layout = self._add_rooms(layout, changes)
        elif op == "remove":
            layout = self._remove_rooms(layout, changes)
        elif op == "swap":
            layout = self._swap_rooms(layout, changes)
        elif op == "adjust_boundary":
            layout = self._adjust_boundary(layout, changes)
        else:
            return layout

        # Rebuild walls after any recognized patch so geometry stays internally consistent.
        layout["walls"] = self._build_walls(layout.get("rooms", []))
        return layout

    def _modify_rooms(self, layout: dict[str, Any], changes: dict[str, Any]) -> dict[str, Any]:
        """
        Update room size, position, and type using only provided patch fields.

        Width and height are clamped to the boundary, while missing fields are preserved.
        """

        # Index incoming patches by room name for fast lookups during iteration.
        rooms_to_modify = changes.get("rooms_to_modify", [])
        patches_by_name = {
            str(room_patch.get("name", "")).strip(): room_patch
            for room_patch in rooms_to_modify
            if isinstance(room_patch, dict) and str(room_patch.get("name", "")).strip()
        }
        boundary_width, boundary_height = self._boundary_size(layout)

        # Walk existing rooms and update only the targeted ones.
        for room in self._iter_rooms(layout):
            room_name = str(room.get("name", "")).strip()
            patch = patches_by_name.get(room_name)
            if patch is None:
                continue

            # Read the current room geometry before merging in optional patch fields.
            origin = room.setdefault("origin", {"x": 0.0, "y": 0.0})
            current_x = self._finite_float(origin.get("x"), 0.0)
            current_y = self._finite_float(origin.get("y"), 0.0)
            target_origin_raw = patch.get("origin")
            target_x = current_x
            target_y = current_y
            if isinstance(target_origin_raw, dict):
                target_x = self._finite_float(target_origin_raw.get("x"), current_x)
                target_y = self._finite_float(target_origin_raw.get("y"), current_y)

            # Apply dimension updates first so origin clamping can use the final room size.
            width = self._finite_float(room.get("width"), self.MIN_ROOM_SIDE)
            height = self._finite_float(room.get("height"), self.MIN_ROOM_SIDE)
            if "width" in patch:
                width = self._finite_float(patch.get("width"), width)
            if "height" in patch:
                height = self._finite_float(patch.get("height"), height)
            room["width"] = self._clamp_room_side(width, boundary_width)
            room["height"] = self._clamp_room_side(height, boundary_height)

            # Clamp the final origin so the modified room remains inside the boundary.
            origin["x"] = self._clamp_coordinate(target_x, boundary_width - float(room["width"]))
            origin["y"] = self._clamp_coordinate(target_y, boundary_height - float(room["height"]))

            # Preserve type unless an explicit room_type change was requested.
            if "room_type" in patch and patch.get("room_type") is not None:
                room["room_type"] = patch["room_type"]

        return layout

    def _add_rooms(self, layout: dict[str, Any], changes: dict[str, Any]) -> dict[str, Any]:
        """
        Append newly requested rooms when a valid placement can be found.

        Placement prefers adjacency targets first, then falls back to a grid scan.
        """

        # Normalize candidate additions into the standard room payload shape.
        additions = changes.get("rooms_to_add", [])
        normalized_additions = [
            self._normalize_room_addition(raw_room)
            for raw_room in additions
            if isinstance(raw_room, dict)
        ]

        # Place each room only if it fits without overlapping the current layout.
        for candidate in normalized_additions:
            if candidate is None:
                continue
            room_payload, adjacent_to = candidate
            origin = self._find_placement(layout, room_payload, adjacent_to)
            if origin is None:
                continue
            room_to_add = copy.deepcopy(room_payload)
            room_to_add["origin"] = origin
            layout.setdefault("rooms", []).append(room_to_add)

        return layout

    def _remove_rooms(self, layout: dict[str, Any], changes: dict[str, Any]) -> dict[str, Any]:
        """
        Remove rooms by exact name and drop any openings that belong to them.
        """

        # Build the exact-name removal set once before filtering rooms and openings.
        raw_names = changes.get("rooms_to_remove", [])
        names_to_remove = {
            str(name).strip()
            for name in raw_names
            if isinstance(name, str) and str(name).strip()
        }
        if not names_to_remove:
            return layout

        # Keep only rooms not targeted by the diff.
        layout["rooms"] = [
            room
            for room in self._iter_rooms(layout)
            if str(room.get("name", "")).strip() not in names_to_remove
        ]

        # Drop stale openings that reference rooms removed from the layout.
        layout["openings"] = [
            opening
            for opening in self._iter_openings(layout)
            if str(opening.get("room_name", "")).strip() not in names_to_remove
        ]
        return layout

    def _swap_rooms(self, layout: dict[str, Any], changes: dict[str, Any]) -> dict[str, Any]:
        """
        Swap the origins of named room pairs while preserving their sizes and types.
        """

        # Build a mutable name-to-room index so swaps can update room origins in place.
        room_by_name = {
            str(room.get("name", "")).strip(): room
            for room in self._iter_rooms(layout)
            if str(room.get("name", "")).strip()
        }

        # Swap only valid pairs that point to two existing rooms.
        for raw_pair in changes.get("rooms_to_swap", []):
            if not isinstance(raw_pair, list) or len(raw_pair) != 2:
                continue
            first_name = str(raw_pair[0]).strip()
            second_name = str(raw_pair[1]).strip()
            room_a = room_by_name.get(first_name)
            room_b = room_by_name.get(second_name)
            if room_a is None or room_b is None:
                continue
            room_a["origin"], room_b["origin"] = (
                copy.deepcopy(room_b.get("origin", {})),
                copy.deepcopy(room_a.get("origin", {})),
            )

        return layout

    def _adjust_boundary(self, layout: dict[str, Any], changes: dict[str, Any]) -> dict[str, Any]:
        """
        Scale room geometry proportionally into a new boundary envelope.

        The boundary is updated first, then each room is rescaled and clamped inside it.
        """

        # Validate the requested boundary payload before applying any scaling math.
        new_boundary_raw = changes.get("boundary")
        if not isinstance(new_boundary_raw, dict):
            return layout
        new_width = self._finite_float(new_boundary_raw.get("width"), 0.0)
        new_height = self._finite_float(new_boundary_raw.get("height"), 0.0)
        if new_width <= 0 or new_height <= 0:
            return layout

        # Read the current boundary dimensions to compute proportional scale factors.
        old_width, old_height = self._boundary_size(layout)
        if old_width <= 0 or old_height <= 0:
            return layout
        scale_x = new_width / old_width
        scale_y = new_height / old_height
        layout["boundary"] = {"width": round(new_width, 4), "height": round(new_height, 4)}

        # Rescale each room and clamp it so the new boundary never overflows.
        for room in self._iter_rooms(layout):
            origin = room.setdefault("origin", {"x": 0.0, "y": 0.0})
            scaled_x = round(self._finite_float(origin.get("x"), 0.0) * scale_x, 4)
            scaled_y = round(self._finite_float(origin.get("y"), 0.0) * scale_y, 4)
            scaled_width = round(self._finite_float(room.get("width"), self.MIN_ROOM_SIDE) * scale_x, 4)
            scaled_height = round(self._finite_float(room.get("height"), self.MIN_ROOM_SIDE) * scale_y, 4)
            room["width"] = self._clamp_room_side(scaled_width, new_width)
            room["height"] = self._clamp_room_side(scaled_height, new_height)
            origin["x"] = self._clamp_coordinate(scaled_x, new_width - float(room["width"]))
            origin["y"] = self._clamp_coordinate(scaled_y, new_height - float(room["height"]))

        return layout

    def _find_placement(
        self,
        layout: dict[str, Any],
        new_room: dict[str, Any],
        adjacent_to: str | None,
    ) -> dict[str, float] | None:
        """
        Find a valid origin for a new room with adjacency-first placement behavior.

        If no adjacent placement works, a simple clearance-aware grid scan is used.
        """

        # Read boundary and room dimensions once before trying candidate coordinates.
        boundary_width, boundary_height = self._boundary_size(layout)
        room_width = self._finite_float(new_room.get("width"), 0.0)
        room_height = self._finite_float(new_room.get("height"), 0.0)
        if room_width <= 0 or room_height <= 0:
            return None

        # Try adjacency placements around the named reference room first.
        if adjacent_to:
            reference_room = next(
                (
                    room
                    for room in self._iter_rooms(layout)
                    if str(room.get("name", "")).strip() == adjacent_to
                ),
                None,
            )
            if isinstance(reference_room, dict):
                for candidate_x, candidate_y in self._adjacent_origins(reference_room, room_width, room_height):
                    if self._can_place_room(
                        rooms=self._iter_rooms(layout),
                        x=candidate_x,
                        y=candidate_y,
                        width=room_width,
                        height=room_height,
                        boundary_width=boundary_width,
                        boundary_height=boundary_height,
                        use_clearance=False,
                    ):
                        return {"x": round(candidate_x, 4), "y": round(candidate_y, 4)}

        # Fall back to a simple scanning strategy that respects a boundary clearance margin.
        x = self.WALL_CLR
        while x + room_width <= boundary_width - self.WALL_CLR + 1e-9:
            y = self.WALL_CLR
            while y + room_height <= boundary_height - self.WALL_CLR + 1e-9:
                if self._can_place_room(
                    rooms=self._iter_rooms(layout),
                    x=x,
                    y=y,
                    width=room_width,
                    height=room_height,
                    boundary_width=boundary_width,
                    boundary_height=boundary_height,
                    use_clearance=True,
                ):
                    return {"x": round(x, 4), "y": round(y, 4)}
                y = round(y + self.GRID_STEP, 4)
            x = round(x + self.GRID_STEP, 4)

        return None

    @staticmethod
    def _overlaps_any(
        rooms: list[dict[str, Any]],
        x: float,
        y: float,
        w: float,
        h: float,
    ) -> bool:
        """Return True when the candidate rectangle overlaps any existing room."""

        # Test the candidate rectangle against every room box already in the layout.
        for room in rooms:
            origin = room.get("origin")
            if not isinstance(origin, dict):
                continue
            origin_x = float(origin.get("x", 0.0))
            origin_y = float(origin.get("y", 0.0))
            room_width = float(room.get("width", 0.0))
            room_height = float(room.get("height", 0.0))
            if not (
                x + w <= origin_x
                or x >= origin_x + room_width
                or y + h <= origin_y
                or y >= origin_y + room_height
            ):
                return True
        return False

    @staticmethod
    def _build_walls(rooms: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Rebuild wall segments from the current room geometry."""

        # Emit the four canonical wall segments for each valid rectangular room.
        walls: list[dict[str, Any]] = []
        for room in rooms:
            origin = room.get("origin")
            if not isinstance(origin, dict):
                continue
            name = str(room.get("name", "")).strip()
            width = float(room.get("width", 0.0))
            height = float(room.get("height", 0.0))
            if not name or width <= 0 or height <= 0:
                continue
            x0 = float(origin.get("x", 0.0))
            y0 = float(origin.get("y", 0.0))
            x1 = x0 + width
            y1 = y0 + height
            walls.extend(
                [
                    {
                        "room_name": name,
                        "wall": "bottom",
                        "start": {"x": round(x0, 4), "y": round(y0, 4)},
                        "end": {"x": round(x1, 4), "y": round(y0, 4)},
                        "thickness": LayoutPatcher.WALL_THICKNESS,
                    },
                    {
                        "room_name": name,
                        "wall": "right",
                        "start": {"x": round(x1, 4), "y": round(y0, 4)},
                        "end": {"x": round(x1, 4), "y": round(y1, 4)},
                        "thickness": LayoutPatcher.WALL_THICKNESS,
                    },
                    {
                        "room_name": name,
                        "wall": "top",
                        "start": {"x": round(x1, 4), "y": round(y1, 4)},
                        "end": {"x": round(x0, 4), "y": round(y1, 4)},
                        "thickness": LayoutPatcher.WALL_THICKNESS,
                    },
                    {
                        "room_name": name,
                        "wall": "left",
                        "start": {"x": round(x0, 4), "y": round(y1, 4)},
                        "end": {"x": round(x0, 4), "y": round(y0, 4)},
                        "thickness": LayoutPatcher.WALL_THICKNESS,
                    },
                ]
            )
        return walls

    def _normalize_room_addition(
        self,
        raw_room: dict[str, Any],
    ) -> tuple[dict[str, Any], str | None] | None:
        """Normalize a raw diff room-add payload into a standard room dict."""

        # Copy addition payload values into the exact room shape expected by the layout schema.
        name = str(raw_room.get("name", "")).strip()
        room_type = str(raw_room.get("room_type", "")).strip().lower()
        width = self._finite_float(raw_room.get("width"), 0.0)
        height = self._finite_float(raw_room.get("height"), 0.0)
        if not name or not room_type or width <= 0 or height <= 0:
            return None
        room_payload = {
            "name": name,
            "room_type": room_type,
            "width": round(max(width, self.MIN_ROOM_SIDE), 4),
            "height": round(max(height, self.MIN_ROOM_SIDE), 4),
        }
        adjacent_raw = raw_room.get("adjacent_to")
        adjacent_to = str(adjacent_raw).strip() if isinstance(adjacent_raw, str) and adjacent_raw.strip() else None
        return room_payload, adjacent_to

    def _can_place_room(
        self,
        rooms: list[dict[str, Any]],
        x: float,
        y: float,
        width: float,
        height: float,
        boundary_width: float,
        boundary_height: float,
        use_clearance: bool,
    ) -> bool:
        """Return True when a candidate room fits inside the boundary without overlaps."""

        # Apply either strict clearance-aware or direct boundary containment checks.
        min_x = self.WALL_CLR if use_clearance else 0.0
        min_y = self.WALL_CLR if use_clearance else 0.0
        max_x = boundary_width - width - (self.WALL_CLR if use_clearance else 0.0)
        max_y = boundary_height - height - (self.WALL_CLR if use_clearance else 0.0)
        if x < min_x - 1e-9 or y < min_y - 1e-9:
            return False
        if x > max_x + 1e-9 or y > max_y + 1e-9:
            return False

        # Reject placements that intersect any room already present in the layout.
        return not self._overlaps_any(rooms, x, y, width, height)

    def _adjacent_origins(
        self,
        reference_room: dict[str, Any],
        width: float,
        height: float,
    ) -> list[tuple[float, float]]:
        """Return candidate adjacent origins around a reference room."""

        # Generate a deterministic order of edge-touching placements around the reference room.
        origin = reference_room.get("origin", {})
        ref_x = self._finite_float(origin.get("x"), 0.0)
        ref_y = self._finite_float(origin.get("y"), 0.0)
        ref_width = self._finite_float(reference_room.get("width"), 0.0)
        ref_height = self._finite_float(reference_room.get("height"), 0.0)
        return [
            (ref_x + ref_width, ref_y),
            (ref_x, ref_y + ref_height),
            (ref_x - width, ref_y),
            (ref_x, ref_y - height),
        ]

    def _boundary_size(self, layout: dict[str, Any]) -> tuple[float, float]:
        """Read the boundary width and height from a layout payload."""

        # Normalize missing or non-finite boundary values to safe numeric defaults.
        boundary = layout.get("boundary", {})
        if not isinstance(boundary, dict):
            return 0.0, 0.0
        return (
            self._finite_float(boundary.get("width"), 0.0),
            self._finite_float(boundary.get("height"), 0.0),
        )

    @staticmethod
    def _iter_rooms(layout: dict[str, Any]) -> list[dict[str, Any]]:
        """Return the layout room list or an empty list when absent."""

        # Keep room iteration helpers centralized so patch methods stay concise.
        rooms = layout.get("rooms", [])
        return rooms if isinstance(rooms, list) else []

    @staticmethod
    def _iter_openings(layout: dict[str, Any]) -> list[dict[str, Any]]:
        """Return the layout opening list or an empty list when absent."""

        # Keep opening iteration helpers centralized so patch methods stay concise.
        openings = layout.get("openings", [])
        return openings if isinstance(openings, list) else []

    @staticmethod
    def _finite_float(value: Any, default: float) -> float:
        """Convert a raw numeric value into a finite float with a safe default."""

        # Coerce arbitrary numeric-like values while guarding against NaN and infinity.
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            return default
        return parsed if math.isfinite(parsed) else default

    def _clamp_room_side(self, value: float, boundary_side: float) -> float:
        """Clamp a room side length to the layout minimum and current boundary span."""

        # Respect the minimum room side while ensuring the result can fit in the boundary.
        if math.isfinite(boundary_side) and boundary_side > 0:
            return round(min(max(value, self.MIN_ROOM_SIDE), boundary_side), 4)
        return round(max(value, self.MIN_ROOM_SIDE), 4)

    @staticmethod
    def _clamp_coordinate(value: float, max_value: float) -> float:
        """Clamp a coordinate into the inclusive layout range."""

        # Keep coordinate clamping centralized for origin updates and boundary scaling.
        finite_max = max(0.0, max_value)
        return round(min(max(value, 0.0), finite_max), 4)
