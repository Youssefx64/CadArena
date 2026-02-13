"""
Planning context and rule definitions for deterministic placement.
"""

from dataclasses import dataclass, field
from typing import Iterable

from app.schemas.room import Room
from app.schemas.design_intent import RoomIntent


@dataclass(frozen=True)
class AdjacencyRule:
    """
    Rule indicating a room should be placed adjacent to another room.
    """
    room: str
    adjacent_to: str
    priority: int = 1
    side_preference: tuple[str, ...] = ()


@dataclass(frozen=True)
class PlacementRules:
    """
    Per-room placement rules derived from planning context.
    """
    enabled: bool
    adjacency_targets: tuple[Room, ...] = ()
    side_preferences: tuple[str, ...] = ()
    enable_room_type_heuristics: bool = False
    enable_boundary_expansion: bool = False

    @staticmethod
    def disabled() -> "PlacementRules":
        return PlacementRules(enabled=False)


@dataclass
class PlanningContext:
    """
    Planning context providing deterministic rules for placement.
    """
    rules_enabled: bool = False
    adjacency_rules: list[AdjacencyRule] = field(default_factory=list)
    enable_room_type_heuristics: bool = False
    enable_boundary_expansion: bool = False
    prioritize_room_types: bool = False
    room_type_priority: dict[str, int] = field(default_factory=dict)

    def has_rules(self) -> bool:
        return (
            self.rules_enabled
            and (
                bool(self.adjacency_rules)
                or self.enable_room_type_heuristics
                or self.enable_boundary_expansion
            )
        )

    def order_rooms(self, rooms: list[RoomIntent]) -> list[RoomIntent]:
        """
        Return a deterministic room order for planning.
        """
        if not self.rules_enabled or not self.prioritize_room_types:
            return list(rooms)

        fixed = [r for r in rooms if r.origin is not None]
        auto = [r for r in rooms if r.origin is None]

        def _priority(room: RoomIntent) -> int:
            return self.room_type_priority.get(room.room_type, 100)

        auto_sorted = sorted(
            enumerate(auto),
            key=lambda item: (_priority(item[1]), item[0]),
        )
        auto_ordered = [room for _, room in auto_sorted]

        return fixed + auto_ordered

    def rules_for_room(self, room: Room, placed_rooms: list[Room]) -> PlacementRules:
        """
        Build placement rules for a specific room based on already placed rooms.
        """
        if not self.has_rules():
            return PlacementRules.disabled()

        adjacency_targets: list[Room] = []
        side_preferences: list[str] = []

        for rule in sorted(
            self.adjacency_rules,
            key=lambda r: (r.priority, r.adjacent_to, r.room),
        ):
            if rule.room != room.name:
                continue
            for placed in placed_rooms:
                if placed.name == rule.adjacent_to and placed.origin is not None:
                    adjacency_targets.append(placed)
                    break
            for side in rule.side_preference:
                if side not in side_preferences:
                    side_preferences.append(side)

        return PlacementRules(
            enabled=True,
            adjacency_targets=tuple(adjacency_targets),
            side_preferences=tuple(side_preferences),
            enable_room_type_heuristics=self.enable_room_type_heuristics,
            enable_boundary_expansion=self.enable_boundary_expansion,
        )

    def normalize_adjacency_rules(self) -> None:
        """
        Deduplicate adjacency rules in a deterministic order.
        """
        if not self.adjacency_rules:
            return

        deduped: dict[tuple[str, str], AdjacencyRule] = {}
        for rule in self.adjacency_rules:
            key = (rule.room, rule.adjacent_to)
            existing = deduped.get(key)
            if existing is None or rule.priority < existing.priority:
                deduped[key] = rule

        self.adjacency_rules = sorted(
            deduped.values(),
            key=lambda r: (r.priority, r.room, r.adjacent_to),
        )
