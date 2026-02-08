"""
Planner agent for automatic room placement.

This module provides a rule-based agent that automatically places rooms
within a boundary while satisfying constraints (boundary, overlap, spacing).
"""

from app.schemas.room import Room
from app.schemas.geometry import Point, RectangleGeometry
from app.domain.constraints.boundary import BoundaryConstraint
from app.domain.constraints.overlap import OverlapConstraint
from app.domain.constraints.spacing import SpacingConstraint
from app.core.config import PlannerConfig
from app.core.logging import get_logger


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

        self.logger = get_logger("PlannerAgent")

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
        total_attempts = max(PlannerConfig.MAX_PLACEMENT_TRIES, total_candidates)

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
            f"Grid searched={total_candidates} candidates, spacing={PlannerConfig.MIN_SPACING}m"
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
