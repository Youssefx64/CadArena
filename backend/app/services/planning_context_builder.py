"""
Planning context builder for intent processing.
"""

from app.core.defaults import (
    DEFAULT_ENABLE_BOUNDARY_EXPANSION,
    DEFAULT_ENABLE_ROOM_TYPE_HEURISTICS,
    DEFAULT_PRIORITIZE_ROOM_TYPES,
    DEFAULT_RULES_ENABLED,
    DEFAULT_ROOM_TYPE_PRIORITY,
)
from app.core.logging import get_logger
from app.domain.planner.planning_context import AdjacencyRule, PlanningContext
from app.schemas.design_intent import RoomIntent


class PlanningContextBuilder:
    """
    Build a PlanningContext from resolved intent and optional planning hints.
    """

    def __init__(self):
        self.logger = get_logger("PlanningContextBuilder")

    def build(
        self,
        rooms: list[RoomIntent],
        planning_hints: dict | None,
    ) -> PlanningContext:
        hints = planning_hints or {}
        mode = str(hints.get("mode", "rules")).strip().lower()

        rules_enabled = DEFAULT_RULES_ENABLED if mode != "grid" else False
        enable_room_type_heuristics = bool(
            hints.get("enable_room_type_heuristics", DEFAULT_ENABLE_ROOM_TYPE_HEURISTICS)
        )
        enable_boundary_expansion = bool(
            hints.get("enable_boundary_expansion", DEFAULT_ENABLE_BOUNDARY_EXPANSION)
        )
        prioritize_room_types = bool(
            hints.get("prioritize_room_types", DEFAULT_PRIORITIZE_ROOM_TYPES)
        ) or bool(hints.get("corridor_first", False))

        if mode == "grid":
            enable_room_type_heuristics = False
            enable_boundary_expansion = False
            prioritize_room_types = False

        adjacency_rules: list[AdjacencyRule] = []
        adjacency_rules.extend(self._parse_adjacency(hints.get("adjacency", [])))

        if rules_enabled and enable_room_type_heuristics:
            adjacency_rules.extend(self._room_type_adjacency(rooms, hints))

        context = PlanningContext(
            rules_enabled=rules_enabled,
            adjacency_rules=adjacency_rules,
            enable_room_type_heuristics=enable_room_type_heuristics,
            enable_boundary_expansion=enable_boundary_expansion,
            prioritize_room_types=prioritize_room_types,
            room_type_priority=dict(DEFAULT_ROOM_TYPE_PRIORITY),
        )
        context.normalize_adjacency_rules()

        if context.has_rules():
            self.logger.info(
                "Planning rules enabled: adjacency=%s heuristics=%s boundary=%s",
                bool(context.adjacency_rules),
                enable_room_type_heuristics,
                enable_boundary_expansion,
            )

        return context

    def _parse_adjacency(self, items: list | None) -> list[AdjacencyRule]:
        if not items:
            return []
        rules: list[AdjacencyRule] = []
        for raw in items:
            if not isinstance(raw, dict):
                continue
            room = raw.get("room")
            adjacent_to = raw.get("near") or raw.get("adjacent_to")
            if not room or not adjacent_to:
                continue
            try:
                priority = int(raw.get("priority", 1))
            except (TypeError, ValueError):
                priority = 1
            side = raw.get("side") or raw.get("side_preference") or []
            if isinstance(side, str):
                side_tuple = (side,)
            elif isinstance(side, list):
                side_tuple = tuple([s for s in side if isinstance(s, str)])
            else:
                side_tuple = ()
            rules.append(
                AdjacencyRule(
                    room=str(room),
                    adjacent_to=str(adjacent_to),
                    priority=priority,
                    side_preference=side_tuple,
                )
            )
        return rules

    def _room_type_adjacency(
        self,
        rooms: list[RoomIntent],
        hints: dict,
    ) -> list[AdjacencyRule]:
        rules: list[AdjacencyRule] = []
        by_type: dict[str, list[RoomIntent]] = {}
        for room in rooms:
            by_type.setdefault(room.room_type, []).append(room)

        for room_list in by_type.values():
            room_list.sort(key=lambda r: r.name)

        def _first(room_type: str) -> RoomIntent | None:
            options = by_type.get(room_type) or []
            return options[0] if options else None

        corridor = _first("corridor")
        bathroom = _first("bathroom")
        living = _first("living")

        for bedroom in by_type.get("bedroom", []):
            if bathroom:
                rules.append(AdjacencyRule(room=bedroom.name, adjacent_to=bathroom.name, priority=2))

        for kitchen in by_type.get("kitchen", []):
            if living:
                rules.append(AdjacencyRule(room=kitchen.name, adjacent_to=living.name, priority=2))

        for bathroom_room in by_type.get("bathroom", []):
            if corridor:
                rules.append(
                    AdjacencyRule(room=bathroom_room.name, adjacent_to=corridor.name, priority=3)
                )

        for stairs in by_type.get("stairs", []):
            if corridor:
                rules.append(AdjacencyRule(room=stairs.name, adjacent_to=corridor.name, priority=2))

        corridor_spine = bool(hints.get("corridor_spine", True))
        if corridor and corridor_spine:
            for room in rooms:
                if room.room_type == "corridor":
                    continue
                rules.append(AdjacencyRule(room=room.name, adjacent_to=corridor.name, priority=4))

        return rules
