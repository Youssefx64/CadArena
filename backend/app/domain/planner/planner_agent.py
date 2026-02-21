"""
Planner agent for automatic room placement.

This module provides a rule-based agent that automatically places rooms
within a boundary while satisfying constraints (boundary, overlap, spacing).
"""

import logging

from app.domain.entities import Room
from app.domain.entities import Point, RectangleGeometry
from app.domain.constraints.boundary import BoundaryConstraint
from app.domain.constraints.overlap import OverlapConstraint
from app.domain.constraints.spacing import SpacingConstraint
from app.domain.planner.config import MAX_PLACEMENT_TRIES, MIN_SPACING
from app.domain.planner.planning_context import PlacementRules


class PlannerAgent:
    """
    Rule-based planning agent for room placement.
    
    Uses a grid-based search strategy to find valid positions for rooms
    while satisfying boundary, overlap, and spacing constraints.
    """

    def __init__(self, boundary: RectangleGeometry):
        """
        Initialize planner agent with boundary and constraints.
        
        Args:
            boundary: Building boundary rectangle defining placement area.
        """
        self.boundary = boundary
        self.placed_rooms: list[Room] = []

        # Initialize constraint validators
        self.boundary_constraint = BoundaryConstraint()
        self.overlap_constraint = OverlapConstraint()
        self.spacing_constraint = SpacingConstraint()

        self.logger = logging.getLogger("PlannerAgent")

    def place_room(self, room: Room) -> Room:
        """
        Try to place a room using a grid-based search strategy.
        
        Searches through candidate positions in a grid pattern, testing each
        position against all constraints until a valid placement is found.
        
        Args:
            room: Room to place (must not have an origin set).
        
        Returns:
            Room with origin set to valid placement position.
        
        Raises:
            RuntimeError: If no valid placement is found after exhausting all candidates.
        """
        step = 1.0
        cols, rows = self._candidate_grid(room, step)
        total_candidates = cols * rows
        total_attempts = max(MAX_PLACEMENT_TRIES, total_candidates)

        for attempt in range(total_attempts):
            # Ensure full search coverage even when MAX_PLACEMENT_TRIES < candidate count
            candidate_idx = attempt if attempt < total_candidates else attempt % total_candidates
            origin = self._propose_position(candidate_idx, cols, step)
            room.origin = origin

            self.logger.info("Trying %s at (%s, %s)", room.name, origin.x, origin.y)

            # Test all constraints
            if not self.boundary_constraint.is_valid(room, self.boundary):
                continue

            if not self.overlap_constraint.is_valid(room, self.placed_rooms):
                continue

            if not self.spacing_constraint.is_valid(room, self.placed_rooms):
                continue

            # All constraints satisfied - place the room
            self.placed_rooms.append(room)
            self.logger.info("Placed %s successfully", room.name)
            return room

        raise RuntimeError(
            f"Failed to place room: {room.name}. "
            f"Grid searched={total_candidates} candidates, spacing={MIN_SPACING}m"
        )

    def _candidate_grid(self, room: Room, step: float) -> tuple[int, int]:
        """
        Compute candidate grid size for this room within boundary.
        
        Calculates how many grid positions are available for placing
        the room without extending beyond the boundary.
        
        Args:
            room: Room to place.
            step: Grid step size in meters.
        
        Returns:
            Tuple of (columns, rows) in the candidate grid.
        """
        max_x = max(0.0, self.boundary.width - room.width)
        max_y = max(0.0, self.boundary.height - room.height)

        cols = max(1, int(max_x // step) + 1)
        rows = max(1, int(max_y // step) + 1)

        return cols, rows

    def _propose_position(self, attempt: int, cols: int, step: float) -> Point:
        """
        Generate a candidate position from grid index.
        
        Converts a linear attempt index into 2D grid coordinates.
        
        Args:
            attempt: Linear attempt index (0-based).
            cols: Number of columns in the grid.
            step: Grid step size in meters.
        
        Returns:
            Point representing the candidate position.
        """
        x = (attempt % cols) * step
        y = (attempt // cols) * step

        return Point(x=x, y=y)

    def place_room_with_rules(self, room: Room, rules: PlacementRules) -> Room:
        """
        Place a room using rule-based candidates with fallback to grid placement.
        """
        if not rules.enabled:
            return self.place_room(room)

        candidates = self._generate_rule_candidates(room, rules)
        for origin in candidates:
            if self._try_place_room(room, origin):
                return room

        return self.place_room(room)

    def _try_place_room(self, room: Room, origin: Point) -> bool:
        room.origin = origin
        if not self.boundary_constraint.is_valid(room, self.boundary):
            return False
        if not self.overlap_constraint.is_valid(room, self.placed_rooms):
            return False
        if not self.spacing_constraint.is_valid(room, self.placed_rooms):
            return False
        self.placed_rooms.append(room)
        self.logger.info("Placed %s successfully", room.name)
        return True

    def _generate_rule_candidates(self, room: Room, rules: PlacementRules) -> list[Point]:
        candidates: list[Point] = []

        if rules.adjacency_targets:
            for target in rules.adjacency_targets:
                candidates.extend(self._adjacent_candidates(room, target, rules.side_preferences))

        if rules.enable_room_type_heuristics:
            candidates.extend(self._room_type_candidates(room))

        if rules.enable_boundary_expansion:
            candidates.extend(self._boundary_candidates(room))

        return self._dedupe_candidates(candidates)

    def _adjacent_candidates(
        self,
        room: Room,
        target: Room,
        side_preferences: tuple[str, ...],
    ) -> list[Point]:
        if target.origin is None:
            return []

        sides = list(side_preferences) if side_preferences else ["right", "left", "top", "bottom"]
        positions: list[Point] = []

        for side in sides:
            if side == "right":
                x = target.origin.x + target.width
                positions.extend(self._aligned_positions(room, target, x, axis="y"))
            elif side == "left":
                x = target.origin.x - room.width
                positions.extend(self._aligned_positions(room, target, x, axis="y"))
            elif side == "top":
                y = target.origin.y + target.height
                positions.extend(self._aligned_positions(room, target, y, axis="x"))
            elif side == "bottom":
                y = target.origin.y - room.height
                positions.extend(self._aligned_positions(room, target, y, axis="x"))

        return positions

    def _aligned_positions(
        self,
        room: Room,
        target: Room,
        fixed_value: float,
        axis: str,
    ) -> list[Point]:
        positions: list[Point] = []
        if axis == "y":
            y_candidates = [
                target.origin.y,
                target.origin.y + (target.height - room.height) / 2,
                target.origin.y + target.height - room.height,
            ]
            for y in y_candidates:
                positions.append(Point(x=fixed_value, y=y))
        else:
            x_candidates = [
                target.origin.x,
                target.origin.x + (target.width - room.width) / 2,
                target.origin.x + target.width - room.width,
            ]
            for x in x_candidates:
                positions.append(Point(x=x, y=fixed_value))
        return positions

    def _room_type_candidates(self, room: Room) -> list[Point]:
        if room.room_type == "corridor":
            return self._corridor_candidates(room)
        if room.room_type == "stairs":
            return self._stairs_candidates(room)
        return self._boundary_edge_candidates(room)

    def _corridor_candidates(self, room: Room) -> list[Point]:
        width = self.boundary.width - room.width
        height = self.boundary.height - room.height
        x_mid = width / 2 if width >= 0 else 0
        y_mid = height / 2 if height >= 0 else 0

        positions: list[Point] = []
        if room.width >= room.height:
            positions.extend(
                [
                    Point(x=0.0, y=0.0),
                    Point(x=x_mid, y=0.0),
                    Point(x=max(width, 0.0), y=0.0),
                    Point(x=0.0, y=max(height, 0.0)),
                    Point(x=x_mid, y=max(height, 0.0)),
                    Point(x=max(width, 0.0), y=max(height, 0.0)),
                ]
            )
        else:
            positions.extend(
                [
                    Point(x=0.0, y=0.0),
                    Point(x=0.0, y=y_mid),
                    Point(x=0.0, y=max(height, 0.0)),
                    Point(x=max(width, 0.0), y=0.0),
                    Point(x=max(width, 0.0), y=y_mid),
                    Point(x=max(width, 0.0), y=max(height, 0.0)),
                ]
            )
        return positions

    def _stairs_candidates(self, room: Room) -> list[Point]:
        max_x = max(self.boundary.width - room.width, 0.0)
        max_y = max(self.boundary.height - room.height, 0.0)
        return [
            Point(x=0.0, y=0.0),
            Point(x=max_x, y=0.0),
            Point(x=0.0, y=max_y),
            Point(x=max_x, y=max_y),
        ]

    def _boundary_edge_candidates(self, room: Room) -> list[Point]:
        max_x = self.boundary.width - room.width
        max_y = self.boundary.height - room.height
        x_mid = max_x / 2 if max_x >= 0 else 0
        y_mid = max_y / 2 if max_y >= 0 else 0
        return [
            Point(x=0.0, y=0.0),
            Point(x=x_mid, y=0.0),
            Point(x=max(max_x, 0.0), y=0.0),
            Point(x=0.0, y=y_mid),
            Point(x=max(max_x, 0.0), y=y_mid),
            Point(x=0.0, y=max(max_y, 0.0)),
            Point(x=x_mid, y=max(max_y, 0.0)),
            Point(x=max(max_x, 0.0), y=max(max_y, 0.0)),
        ]

    def _boundary_candidates(self, room: Room) -> list[Point]:
        return self._boundary_edge_candidates(room)

    def _dedupe_candidates(self, candidates: list[Point]) -> list[Point]:
        seen: set[tuple[float, float]] = set()
        unique: list[Point] = []
        for candidate in candidates:
            key = (round(candidate.x, 3), round(candidate.y, 3))
            if key in seen:
                continue
            seen.add(key)
            unique.append(candidate)
        return unique
