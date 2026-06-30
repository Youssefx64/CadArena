from copy import deepcopy
import logging

import pytest

from app.services.design_parser.opening_planner import (
    MIN_DOOR_CORNER_CLEARANCE,
    DeterministicOpeningPlanner,
    _RoomBox,
    _SharedBoundary,
)
from app.services.design_parser.rule_violation import RuleViolationError


def _door_openings_for_pair(room_a: _RoomBox, room_b: _RoomBox) -> list[dict]:
    planner = DeterministicOpeningPlanner()
    rooms = [room_a, room_b]
    by_name = {room.name: room for room in rooms}
    shared_boundaries = planner._build_shared_boundaries(rooms)
    openings: list[dict] = []
    planner._add_door_between(
        room_a=room_a.name,
        room_b=room_b.name,
        by_name=by_name,
        shared_boundaries=shared_boundaries,
        columns=[],
        occupied={},
        openings=openings,
        door_pairs_done=set(),
        reason_rule="unit-test",
    )
    return openings


def _door_pairs_for_rooms(
    planner: DeterministicOpeningPlanner,
    rooms: list[_RoomBox],
    openings: list[dict],
) -> set[tuple[str, str]]:
    by_name = {room.name: room for room in rooms}
    shared_boundaries = planner._build_connectivity_shared_boundaries(rooms)
    return planner._door_pairs_from_openings(
        openings=openings,
        by_name=by_name,
        shared_boundaries=shared_boundaries,
    )


def test_bedroom_to_corridor_door_swings_into_bedroom_and_out_of_corridor() -> None:
    openings = _door_openings_for_pair(
        _RoomBox(name="Bedroom", room_type="bedroom", x0=0.0, y0=0.0, x1=4.0, y1=4.0),
        _RoomBox(name="Main Corridor", room_type="corridor", x0=4.0, y0=0.0, x1=6.0, y1=4.0),
    )

    by_room = {opening["room_name"]: opening for opening in openings}
    assert by_room["Bedroom"]["swing"] == "in"
    assert by_room["Bedroom"]["hinge"] == "left"
    assert by_room["Main Corridor"]["swing"] == "out"
    assert by_room["Main Corridor"]["hinge"] == "left"


def test_bathroom_door_uses_bathroom_hinge_rule_and_inward_swing() -> None:
    openings = _door_openings_for_pair(
        _RoomBox(name="Bathroom", room_type="bathroom", x0=0.0, y0=2.0, x1=3.0, y1=5.0),
        _RoomBox(name="Main Corridor", room_type="corridor", x0=0.0, y0=0.0, x1=3.0, y1=2.0),
    )

    by_room = {opening["room_name"]: opening for opening in openings}
    assert by_room["Bathroom"]["wall"] == "bottom"
    assert by_room["Bathroom"]["hinge"] == "right"
    assert by_room["Bathroom"]["swing"] == "in"
    assert by_room["Main Corridor"]["swing"] == "out"


def test_opening_planner_rejects_shared_bathroom_to_bedroom_door() -> None:
    planner = DeterministicOpeningPlanner()
    rooms = [
        _RoomBox(name="Bathroom", room_type="bathroom", x0=0.0, y0=0.0, x1=3.0, y1=3.0),
        _RoomBox(name="Bedroom 1", room_type="bedroom", x0=3.0, y0=0.0, x1=7.0, y1=3.0),
    ]
    by_name = {room.name: room for room in rooms}

    with pytest.raises(RuleViolationError) as exc_info:
        planner._add_door_between(
            room_a="Bathroom",
            room_b="Bedroom 1",
            by_name=by_name,
            shared_boundaries=planner._build_shared_boundaries(rooms),
            columns=[],
            occupied={},
            openings=[],
            door_pairs_done=set(),
            reason_rule="unit-test",
        )

    assert exc_info.value.violated_rule == "bathroom-door-forbidden-bedroom"


def test_non_corridor_non_bathroom_doors_default_to_left_hinge_and_inward_swing() -> None:
    openings = _door_openings_for_pair(
        _RoomBox(name="Living Room", room_type="living", x0=0.0, y0=0.0, x1=4.0, y1=4.0),
        _RoomBox(name="Dining Room", room_type="living", x0=4.0, y0=0.0, x1=8.0, y1=4.0),
    )

    for opening in openings:
        assert opening["hinge"] == "left"
        assert opening["swing"] == "in"


def test_allocate_cut_prefers_door_corner_clearance_on_long_wall() -> None:
    planner = DeterministicOpeningPlanner()
    boundary = _SharedBoundary(
        room_a="Room A",
        room_b="Room B",
        axis="horizontal",
        coordinate=0.0,
        start=0.0,
        end=4.0,
    )

    cut = planner._allocate_cut(
        boundary=boundary,
        requested_width=0.9,
        blocked=[],
        end_clearance=0.25,
        corner_clearance=MIN_DOOR_CORNER_CLEARANCE,
    )

    assert cut.start >= MIN_DOOR_CORNER_CLEARANCE - 1e-6
    assert cut.end <= 4.0 - MIN_DOOR_CORNER_CLEARANCE + 1e-6


def test_allocate_cut_falls_back_to_centered_short_wall_placement() -> None:
    planner = DeterministicOpeningPlanner()
    boundary = _SharedBoundary(
        room_a="Room A",
        room_b="Room B",
        axis="horizontal",
        coordinate=0.0,
        start=0.0,
        end=1.5,
    )

    cut = planner._allocate_cut(
        boundary=boundary,
        requested_width=0.9,
        blocked=[],
        end_clearance=0.25,
        corner_clearance=MIN_DOOR_CORNER_CLEARANCE,
    )

    assert cut.start < MIN_DOOR_CORNER_CLEARANCE
    assert abs(cut.start - 0.3) < 1e-6
    assert abs(cut.end - 1.2) < 1e-6


def test_door_pair_reconstruction_finds_existing_connectivity_and_unreachable_room() -> None:
    planner = DeterministicOpeningPlanner()
    rooms = [
        _RoomBox(name="Bedroom", room_type="bedroom", x0=0.0, y0=4.0, x1=4.0, y1=8.0),
        _RoomBox(name="Main Corridor", room_type="corridor", x0=4.0, y0=4.0, x1=6.0, y1=8.0),
        _RoomBox(name="Kitchen", room_type="kitchen", x0=6.0, y0=4.0, x1=10.0, y1=8.0),
    ]

    openings = _door_openings_for_pair(rooms[0], rooms[1])
    door_pairs = _door_pairs_for_rooms(planner, rooms, openings)
    adjacency = planner._door_adjacency(
        room_names=sorted(room.name for room in rooms),
        door_pairs_done=door_pairs,
    )

    assert door_pairs == {("Bedroom", "Main Corridor")}
    assert planner._bfs(start="Main Corridor", adjacency=adjacency) == {"Bedroom", "Main Corridor"}


def test_ensure_room_connectivity_adds_missing_doors_for_rooms_below_horizontal_corridor() -> None:
    planner = DeterministicOpeningPlanner()
    rooms = [
        _RoomBox(name="Bedroom 1", room_type="bedroom", x0=0.0, y0=6.0, x1=5.0, y1=10.0),
        _RoomBox(name="Bathroom", room_type="bathroom", x0=5.0, y0=6.0, x1=10.0, y1=10.0),
        _RoomBox(name="Main Corridor", room_type="corridor", x0=0.0, y0=4.5, x1=10.0, y1=6.0),
        _RoomBox(name="Living Room", room_type="living", x0=0.0, y0=0.0, x1=4.0, y1=4.5),
        _RoomBox(name="Kitchen", room_type="kitchen", x0=4.0, y0=0.0, x1=10.0, y1=4.5),
    ]
    by_name = {room.name: room for room in rooms}
    shared_boundaries = planner._build_shared_boundaries(rooms)
    openings: list[dict] = []
    occupied = {}
    door_pairs_done: set[tuple[str, str]] = set()

    planner._add_door_between(
        room_a="Bedroom 1",
        room_b="Main Corridor",
        by_name=by_name,
        shared_boundaries=shared_boundaries,
        columns=[],
        occupied=occupied,
        openings=openings,
        door_pairs_done=door_pairs_done,
        reason_rule="unit-test",
    )
    planner._add_door_between(
        room_a="Bathroom",
        room_b="Main Corridor",
        by_name=by_name,
        shared_boundaries=shared_boundaries,
        columns=[],
        occupied=occupied,
        openings=openings,
        door_pairs_done=door_pairs_done,
        reason_rule="unit-test",
    )

    initial_openings = deepcopy(openings)
    result = planner._ensure_room_connectivity(
        rooms=rooms,
        openings=openings,
        boundary_width=10.0,
        boundary_height=10.0,
    )

    assert result[: len(initial_openings)] == initial_openings
    assert len(result) == len(initial_openings) + 4

    door_pairs = _door_pairs_for_rooms(planner, rooms, result)
    adjacency = planner._door_adjacency(
        room_names=sorted(room.name for room in rooms),
        door_pairs_done=door_pairs,
    )

    assert ("Living Room", "Main Corridor") in door_pairs
    assert ("Kitchen", "Main Corridor") in door_pairs
    assert planner._bfs(start="Main Corridor", adjacency=adjacency) == {room.name for room in rooms}


def test_ensure_room_connectivity_prefers_longest_reachable_wall_and_keeps_bathroom_width() -> None:
    planner = DeterministicOpeningPlanner()
    rooms = [
        _RoomBox(name="Main Corridor", room_type="corridor", x0=0.0, y0=0.0, x1=2.0, y1=8.0),
        _RoomBox(name="Living Room", room_type="living", x0=2.0, y0=0.0, x1=6.0, y1=5.0),
        _RoomBox(name="Dining Room", room_type="living", x0=2.0, y0=5.0, x1=6.0, y1=8.0),
        _RoomBox(name="Bathroom", room_type="bathroom", x0=6.0, y0=0.0, x1=8.0, y1=8.0),
    ]
    by_name = {room.name: room for room in rooms}
    shared_boundaries = planner._build_shared_boundaries(rooms)
    openings: list[dict] = []
    occupied = {}
    door_pairs_done: set[tuple[str, str]] = set()

    planner._add_door_between(
        room_a="Main Corridor",
        room_b="Living Room",
        by_name=by_name,
        shared_boundaries=shared_boundaries,
        columns=[],
        occupied=occupied,
        openings=openings,
        door_pairs_done=door_pairs_done,
        reason_rule="unit-test",
    )
    planner._add_door_between(
        room_a="Main Corridor",
        room_b="Dining Room",
        by_name=by_name,
        shared_boundaries=shared_boundaries,
        columns=[],
        occupied=occupied,
        openings=openings,
        door_pairs_done=door_pairs_done,
        reason_rule="unit-test",
    )

    result = planner._ensure_room_connectivity(
        rooms=rooms,
        openings=openings,
        boundary_width=8.0,
        boundary_height=8.0,
    )
    door_pairs = _door_pairs_for_rooms(planner, rooms, result)

    assert ("Bathroom", "Living Room") in door_pairs
    assert ("Bathroom", "Dining Room") not in door_pairs

    bathroom_opening = next(
        opening
        for opening in result
        if opening["type"] == "door" and opening["room_name"] == "Bathroom"
    )
    assert bathroom_opening["hinge"] == "left"
    assert bathroom_opening["swing"] == "in"
    # EBC-FIX: Door width is now bilateral minimum — bathroom 0.70m per EBC (not hardcoded 0.8)
    assert bathroom_opening["cut_end"]["y"] - bathroom_opening["cut_start"]["y"] == pytest.approx(0.7)


def test_ensure_room_connectivity_uses_living_room_as_hub_when_no_corridor_exists() -> None:
    planner = DeterministicOpeningPlanner()
    rooms = [
        _RoomBox(name="Living Room", room_type="living", x0=0.0, y0=0.0, x1=4.0, y1=4.0),
        _RoomBox(name="Bedroom", room_type="bedroom", x0=4.0, y0=0.0, x1=8.0, y1=4.0),
    ]

    result = planner._ensure_room_connectivity(
        rooms=rooms,
        openings=[],
        boundary_width=8.0,
        boundary_height=4.0,
    )

    assert _door_pairs_for_rooms(planner, rooms, result) == {("Bedroom", "Living Room")}


def test_ensure_room_connectivity_logs_warning_when_no_shared_wall_exists(caplog: pytest.LogCaptureFixture) -> None:
    planner = DeterministicOpeningPlanner()
    rooms = [
        _RoomBox(name="Living Room", room_type="living", x0=0.0, y0=0.0, x1=4.0, y1=4.0),
        _RoomBox(name="Bedroom", room_type="bedroom", x0=5.0, y0=0.0, x1=9.0, y1=4.0),
    ]

    with caplog.at_level(logging.WARNING):
        result = planner._ensure_room_connectivity(
            rooms=rooms,
            openings=[],
            boundary_width=9.0,
            boundary_height=4.0,
        )

    assert result == []
    assert "unreachable rooms remain after connectivity pass" in caplog.text
    assert "rooms still lack door openings after connectivity pass" in caplog.text


def test_opening_planner_adds_exterior_main_entry_door() -> None:
    planner = DeterministicOpeningPlanner()
    layout = {
        "boundary": {"width": 20.0, "height": 12.0},
        "rooms": [
            {"name": "Living Room", "room_type": "living", "width": 6.0, "height": 5.0, "origin": {"x": 0.0, "y": 0.0}},
            {"name": "Kitchen", "room_type": "kitchen", "width": 5.0, "height": 5.0, "origin": {"x": 6.0, "y": 0.0}},
            {"name": "Main Corridor", "room_type": "corridor", "width": 20.0, "height": 1.2, "origin": {"x": 0.0, "y": 5.0}},
            {"name": "Bedroom", "room_type": "bedroom", "width": 10.0, "height": 5.8, "origin": {"x": 0.0, "y": 6.2}},
            {"name": "Bathroom", "room_type": "bathroom", "width": 9.0, "height": 5.8, "origin": {"x": 11.0, "y": 6.2}},
        ],
        "walls": [],
        "openings": [],
    }
    result = planner.plan(extracted_payload={"constraints": {"notes": []}}, layout_payload=layout)

    exterior_doors = [
        opening
        for opening in result["openings"]
        if opening["type"] == "door"
        and (
            (opening["wall"] == "bottom" and opening["cut_start"]["y"] == 0.0)
            or (opening["wall"] == "top" and opening["cut_start"]["y"] == 12.0)
            or (opening["wall"] == "left" and opening["cut_start"]["x"] == 0.0)
            or (opening["wall"] == "right" and opening["cut_start"]["x"] == 20.0)
        )
    ]

    assert exterior_doors
    assert max(abs(door["cut_end"]["x"] - door["cut_start"]["x"]) + abs(door["cut_end"]["y"] - door["cut_start"]["y"]) for door in exterior_doors) >= 1.0


def test_opening_planner_rejects_bedroom_that_can_only_pass_through_bathroom() -> None:
    planner = DeterministicOpeningPlanner()
    layout = {
        "boundary": {"width": 16.0, "height": 10.0},
        "rooms": [
            {
                "name": "Kitchen",
                "room_type": "kitchen",
                "width": 6.03,
                "height": 4.25,
                "origin": {"x": 0.0, "y": 5.75},
            },
            {
                "name": "Bathroom",
                "room_type": "bathroom",
                "width": 8.77,
                "height": 2.30,
                "origin": {"x": 7.23, "y": 7.70},
            },
            {
                "name": "Bedroom 1",
                "room_type": "bedroom",
                "width": 4.39,
                "height": 7.70,
                "origin": {"x": 7.23, "y": 0.0},
            },
            {
                "name": "Bedroom 2",
                "room_type": "bedroom",
                "width": 4.39,
                "height": 7.70,
                "origin": {"x": 11.61, "y": 0.0},
            },
            {
                "name": "Main Corridor",
                "room_type": "corridor",
                "width": 1.2,
                "height": 10.0,
                "origin": {"x": 6.03, "y": 0.0},
            },
            {
                "name": "Living Room",
                "room_type": "living",
                "width": 6.03,
                "height": 5.75,
                "origin": {"x": 0.0, "y": 0.0},
            },
        ],
        "walls": [],
        "openings": [],
    }

    with pytest.raises(RuleViolationError) as exc_info:
        planner.plan(extracted_payload={"constraints": {"notes": []}}, layout_payload=layout)

    assert exc_info.value.violated_rule == "bedroom-door-policy"
