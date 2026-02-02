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
    """

    def __init__(self, boundary: RectangleGeometry):
        self.boundary = boundary
        self.placed_rooms: list[Room] = []

        self.boundary_constraint = BoundaryConstraint()
        self.overlap_constraint = OverlapConstraint()
        self.spacing_constraint = SpacingConstraint()

        self.logger = get_logger("PlannerAgent")

    def place_room(self, room: Room) -> Room:
        """
        Try to place a room using an agent loop.
        """

        for attempt in range(PlannerConfig.MAX_PLACEMENT_TRIES):
            origin = self._propose_position(attempt)
            room.origin = origin

            self.logger.info(
                "Trying %s at (%s, %s)",
                room.name,
                origin.x,
                origin.y
            )

            if not self.boundary_constraint.is_valid(room, self.boundary):
                continue

            if not self.overlap_constraint.is_valid(room, self.placed_rooms):
                continue

            if not self.spacing_constraint.is_valid(room, self.placed_rooms):
                continue

            # ✅ Accepted
            self.placed_rooms.append(room)
            self.logger.info("Placed %s successfully", room.name)
            return room

        raise RuntimeError(f"Failed to place room: {room.name}")

    def _propose_position(self, attempt: int) -> Point:
        """
        Simple grid-based proposal strategy.
        """
        step = 1.0  # meters
        cols = int(self.boundary.width // step)

        x = (attempt % cols) * step
        y = (attempt // cols) * step

        return Point(x=x, y=y)
