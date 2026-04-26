from copy import deepcopy
import logging
from time import perf_counter

import pytest

from app.services.design_parser.layout_planner import (
    DeterministicLayoutPlanner,
    LayoutPlanningError,
)


def _rooms_overlap(room_a: dict, room_b: dict) -> bool:
    ax0 = room_a["origin"]["x"]
    ay0 = room_a["origin"]["y"]
    ax1 = ax0 + room_a["width"]
    ay1 = ay0 + room_a["height"]

    bx0 = room_b["origin"]["x"]
    by0 = room_b["origin"]["y"]
    bx1 = bx0 + room_b["width"]
    by1 = by0 + room_b["height"]

    overlap_x = ax0 < bx1 and ax1 > bx0
    overlap_y = ay0 < by1 and ay1 > by0
    return overlap_x and overlap_y


def test_layout_planner_is_deterministic_and_covers_boundary() -> None:
    planner = DeterministicLayoutPlanner()
    extracted = {
        "boundary": {"width": 24.0, "height": 16.0},
        "room_program": [
            {"name": "Living Room", "room_type": "living", "count": 1},
            {"name": "Kitchen", "room_type": "kitchen", "count": 1},
            {"name": "Bedroom", "room_type": "bedroom", "count": 3},
            {"name": "Bathroom", "room_type": "bathroom", "count": 2},
            {"name": "Corridor", "room_type": "corridor", "count": 1},
        ],
        "constraints": {"notes": [], "adjacency_preferences": []},
    }

    first, meta_first = planner.plan_with_metadata(extracted)
    second, meta_second = planner.plan_with_metadata(extracted)
    assert first == second
    assert meta_first == meta_second
    assert meta_first["selected_topology"] in {
        "central_corridor_spine",
        "side_corridor_spine",
        "front_public_rear_private",
        "vertical_public_private_split",
        "l_shaped_public_core",
        "side_corridor_spine_left",
    }

    rooms = first["rooms"]
    assert len(rooms) >= 8
    names = {room["name"] for room in rooms}
    assert "Living Room" in names
    assert "Kitchen" in names

    total_area = sum(room["width"] * room["height"] for room in rooms)
    assert abs(total_area - (24.0 * 16.0)) < 2.0

    for idx, room in enumerate(rooms):
        x = room["origin"]["x"]
        y = room["origin"]["y"]
        assert x >= 0 and y >= 0
        assert x + room["width"] <= 24.0 + 1e-6
        assert y + room["height"] <= 16.0 + 1e-6
        for other in rooms[idx + 1 :]:
            assert _rooms_overlap(room, other) is False


def test_layout_planner_executes_under_300ms_for_12_rooms() -> None:
    planner = DeterministicLayoutPlanner()
    extracted = {
        "boundary": {"width": 30.0, "height": 18.0},
        "room_program": [
            {"name": "Living Room", "room_type": "living", "count": 1},
            {"name": "Dining Room", "room_type": "living", "count": 1},
            {"name": "Kitchen", "room_type": "kitchen", "count": 1},
            {"name": "Master Bedroom", "room_type": "bedroom", "count": 1},
            {"name": "Children Bedroom", "room_type": "bedroom", "count": 3},
            {"name": "Shared Bathroom", "room_type": "bathroom", "count": 2},
            {"name": "Guest Bathroom", "room_type": "bathroom", "count": 1},
            {"name": "Laundry", "room_type": "bathroom", "count": 1},
            {"name": "Storage", "room_type": "corridor", "count": 1},
        ],
        "constraints": {"notes": ["Single floor"], "adjacency_preferences": []},
    }

    started = perf_counter()
    first, meta_first = planner.plan_with_metadata(extracted)
    elapsed_first = perf_counter() - started
    started = perf_counter()
    second, meta_second = planner.plan_with_metadata(extracted)
    elapsed_second = perf_counter() - started

    assert elapsed_first < 0.30
    assert elapsed_second < 0.30
    assert first == second
    assert meta_first == meta_second


def test_layout_planner_fails_on_impossible_program() -> None:
    planner = DeterministicLayoutPlanner()
    extracted = {
        "boundary": {"width": 6.0, "height": 6.0},
        "room_program": [
            {"name": "Living Room", "room_type": "living", "count": 1},
            {"name": "Kitchen", "room_type": "kitchen", "count": 1},
            {"name": "Bedroom", "room_type": "bedroom", "count": 2},
            {"name": "Bathroom", "room_type": "bathroom", "count": 1},
        ],
        "constraints": {"notes": [], "adjacency_preferences": []},
    }

    with pytest.raises(LayoutPlanningError):
        planner.plan(extracted)


def test_layout_planner_handles_narrow_boundary_with_structured_failure() -> None:
    planner = DeterministicLayoutPlanner()
    extracted = {
        "boundary": {"width": 4.0, "height": 20.0},
        "room_program": [
            {"name": "Living Room", "room_type": "living", "count": 1},
            {"name": "Kitchen", "room_type": "kitchen", "count": 1},
            {"name": "Bedroom", "room_type": "bedroom", "count": 2},
            {"name": "Bathroom", "room_type": "bathroom", "count": 1},
        ],
        "constraints": {"notes": ["Narrow lot"], "adjacency_preferences": []},
    }

    with pytest.raises(LayoutPlanningError):
        planner.plan(extracted)


def test_layout_planner_normalizer_fills_boundary_edges_and_keeps_rooms_inside() -> None:
    planner = DeterministicLayoutPlanner()
    layout = {
        "boundary": {"width": 10.0, "height": 6.0},
        "rooms": [
            {"name": "Living Room", "room_type": "living", "width": 4.95, "height": 3.0, "origin": {"x": 0.0, "y": 0.0}},
            {"name": "Kitchen", "room_type": "kitchen", "width": 5.0, "height": 3.0, "origin": {"x": 5.0, "y": 0.0}},
            {"name": "Bedroom", "room_type": "bedroom", "width": 5.0, "height": 2.95, "origin": {"x": 0.0, "y": 3.0}},
            {"name": "Bathroom", "room_type": "bathroom", "width": 5.0, "height": 2.95, "origin": {"x": 5.0, "y": 3.0}},
        ],
        "walls": [],
        "openings": [],
    }
    original = deepcopy(layout)

    normalized = planner.normalize_layout(layout)
    assert layout == original
    rooms = normalized["rooms"]
    right_edge = max(room["origin"]["x"] + room["width"] for room in rooms)
    top_edge = max(room["origin"]["y"] + room["height"] for room in rooms)
    assert abs(right_edge - 10.0) < 1e-6
    assert abs(top_edge - 6.0) < 1e-6
    for room in rooms:
        assert room["origin"]["x"] >= 0.0
        assert room["origin"]["y"] >= 0.0
        assert room["origin"]["x"] + room["width"] <= 10.0 + 1e-6
        assert room["origin"]["y"] + room["height"] <= 6.0 + 1e-6


def test_expand_program_clamps_living_room_targets_by_boundary_area() -> None:
    planner = DeterministicLayoutPlanner()
    rooms = planner._expand_program(
        [
            {
                "name": "Living Room",
                "room_type": "living",
                "count": 1,
                "preferred_area": 200.0,
            }
        ],
        boundary_area=240.0,
    )

    living_room = rooms[0]
    assert living_room.preferred_area == pytest.approx(67.2)
    assert living_room.max_area == pytest.approx(84.0)


def test_layout_planner_variety_seed_is_stable_for_same_program() -> None:
    planner = DeterministicLayoutPlanner()
    extracted = {
        "boundary": {"width": 20.0, "height": 12.0},
        "room_program": [
            {"name": "Living Room", "room_type": "living", "count": 1},
            {"name": "Kitchen", "room_type": "kitchen", "count": 1},
            {"name": "Bedroom", "room_type": "bedroom", "count": 3},
            {"name": "Bathroom", "room_type": "bathroom", "count": 2},
        ],
        "constraints": {"notes": [], "adjacency_preferences": []},
    }

    rooms = planner._expand_program(extracted["room_program"], boundary_area=20.0 * 12.0)
    rooms = planner._ensure_corridor_spine(rooms)
    rooms = planner._normalize_program_areas(
        rooms=rooms,
        boundary_area=20.0 * 12.0,
    )

    seed_first = planner._compute_variety_seed(rooms)
    seed_second = planner._compute_variety_seed(rooms)
    assert seed_first == seed_second
    assert 0 <= seed_first < 6


def test_layout_planner_selects_different_topology_for_different_room_programs() -> None:
    planner = DeterministicLayoutPlanner()
    two_bed = {
        "boundary": {"width": 20.0, "height": 12.0},
        "room_program": [
            {"name": "Living Room", "room_type": "living", "count": 1},
            {"name": "Kitchen", "room_type": "kitchen", "count": 1},
            {"name": "Bedroom", "room_type": "bedroom", "count": 2},
            {"name": "Bathroom", "room_type": "bathroom", "count": 1},
        ],
        "constraints": {"notes": [], "adjacency_preferences": []},
    }
    three_bed_two_bath = {
        "boundary": {"width": 20.0, "height": 12.0},
        "room_program": [
            {"name": "Living Room", "room_type": "living", "count": 1},
            {"name": "Kitchen", "room_type": "kitchen", "count": 1},
            {"name": "Bedroom", "room_type": "bedroom", "count": 3},
            {"name": "Bathroom", "room_type": "bathroom", "count": 2},
        ],
        "constraints": {"notes": [], "adjacency_preferences": []},
    }

    first_two, meta_two_first = planner.plan_with_metadata(two_bed)
    second_two, meta_two_second = planner.plan_with_metadata(two_bed)
    first_three, meta_three_first = planner.plan_with_metadata(three_bed_two_bath)
    second_three, meta_three_second = planner.plan_with_metadata(three_bed_two_bath)

    assert first_two == second_two
    assert meta_two_first == meta_two_second
    assert first_three == second_three
    assert meta_three_first == meta_three_second
    assert meta_two_first["selected_topology"] != meta_three_first["selected_topology"]


def test_layout_planner_caps_living_room_to_twenty_eight_percent_of_boundary_area() -> None:
    planner = DeterministicLayoutPlanner()
    extracted = {
        "boundary": {"width": 20.0, "height": 12.0},
        "room_program": [
            {"name": "Living Room", "room_type": "living", "count": 1},
            {"name": "Kitchen", "room_type": "kitchen", "count": 1},
            {"name": "Bedroom", "room_type": "bedroom", "count": 2},
            {"name": "Bathroom", "room_type": "bathroom", "count": 1},
        ],
        "constraints": {"notes": [], "adjacency_preferences": []},
    }

    payload, _ = planner.plan_with_metadata(extracted)
    rooms = payload["rooms"]
    living_room = next(room for room in rooms if room["name"] == "Living Room")
    living_area = living_room["width"] * living_room["height"]

    assert living_area <= 67.2 + 1e-6
    assert abs(sum(room["width"] * room["height"] for room in rooms) - 240.0) < 1e-3

    for idx, room in enumerate(rooms):
        assert room["origin"]["x"] >= 0.0
        assert room["origin"]["y"] >= 0.0
        assert room["origin"]["x"] + room["width"] <= 20.0 + 1e-6
        assert room["origin"]["y"] + room["height"] <= 12.0 + 1e-6
        for other in rooms[idx + 1 :]:
            assert _rooms_overlap(room, other) is False


def test_layout_planner_does_not_invent_extra_living_room_for_simple_one_bed_program() -> None:
    planner = DeterministicLayoutPlanner()
    extracted = {
        "boundary": {"width": 12.0, "height": 9.0},
        "room_program": [
            {"name": "Living Room", "room_type": "living", "count": 1},
            {"name": "Kitchen", "room_type": "kitchen", "count": 1},
            {"name": "Bedroom", "room_type": "bedroom", "count": 1},
            {"name": "Bathroom", "room_type": "bathroom", "count": 1},
        ],
        "constraints": {"notes": [], "adjacency_preferences": [["kitchen", "living"]]},
    }

    payload, _ = planner.plan_with_metadata(extracted)
    living_rooms = [room for room in payload["rooms"] if room["room_type"] == "living"]

    assert len(living_rooms) == 1
    assert living_rooms[0]["name"] == "Living Room"


def test_layout_planner_normalizer_eliminates_large_gap_without_overlaps() -> None:
    planner = DeterministicLayoutPlanner()
    layout = {
        "boundary": {"width": 12.0, "height": 10.0},
        "rooms": [
            {"name": "Living Room", "room_type": "living", "width": 6.0, "height": 5.0, "origin": {"x": 0.0, "y": 0.0}},
            {"name": "Kitchen", "room_type": "kitchen", "width": 6.0, "height": 5.0, "origin": {"x": 6.0, "y": 0.0}},
            {"name": "Bedroom", "room_type": "bedroom", "width": 8.0, "height": 5.0, "origin": {"x": 0.0, "y": 5.0}},
            {"name": "Bathroom", "room_type": "bathroom", "width": 2.0, "height": 5.0, "origin": {"x": 8.0, "y": 5.0}},
        ],
        "walls": [],
        "openings": [],
    }
    original = deepcopy(layout)
    area_before = sum(room["width"] * room["height"] for room in layout["rooms"])

    normalized = planner.normalize_layout(layout)

    assert layout == original
    rooms = normalized["rooms"]
    area_after = sum(room["width"] * room["height"] for room in rooms)
    assert area_after > area_before

    bathroom = next(room for room in rooms if room["name"] == "Bathroom")
    assert bathroom["width"] > 2.0

    for idx, room in enumerate(rooms):
        assert room["origin"]["x"] >= 0.0
        assert room["origin"]["y"] >= 0.0
        assert room["origin"]["x"] + room["width"] <= 12.0 + 1e-6
        assert room["origin"]["y"] + room["height"] <= 10.0 + 1e-6
        for other in rooms[idx + 1 :]:
            assert _rooms_overlap(room, other) is False


def test_layout_planner_normalizer_caps_living_room_and_recovers_minimum_room_areas(
    caplog: pytest.LogCaptureFixture,
) -> None:
    planner = DeterministicLayoutPlanner()
    layout = {
        "boundary": {"width": 12.0, "height": 10.0},
        "rooms": [
            {"name": "Living Room", "room_type": "living", "width": 10.0, "height": 6.0, "origin": {"x": 0.0, "y": 0.0}},
            {"name": "Kitchen", "room_type": "kitchen", "width": 2.0, "height": 2.5, "origin": {"x": 10.0, "y": 0.0}},
            {"name": "Bedroom", "room_type": "bedroom", "width": 2.0, "height": 4.0, "origin": {"x": 10.0, "y": 2.5}},
            {"name": "Bathroom", "room_type": "bathroom", "width": 2.0, "height": 1.5, "origin": {"x": 10.0, "y": 6.5}},
        ],
        "walls": [],
        "openings": [],
    }
    original = deepcopy(layout)

    with caplog.at_level(logging.INFO):
        normalized = planner.normalize_layout(layout)

    assert layout == original
    rooms = normalized["rooms"]

    living_room = next(room for room in rooms if room["name"] == "Living Room")
    kitchen = next(room for room in rooms if room["name"] == "Kitchen")
    bedroom = next(room for room in rooms if room["name"] == "Bedroom")
    bathroom = next(room for room in rooms if room["name"] == "Bathroom")

    assert living_room["width"] * living_room["height"] <= 36.0 + 1e-6
    assert kitchen["width"] * kitchen["height"] >= 6.0 - 1e-6
    assert bedroom["width"] * bedroom["height"] >= 9.0 - 1e-6
    assert bathroom["width"] * bathroom["height"] >= 3.5 - 1e-6
    assert "[LivingCap] reduced from" in caplog.text

    for idx, room in enumerate(rooms):
        assert room["origin"]["x"] >= 0.0
        assert room["origin"]["y"] >= 0.0
        assert room["origin"]["x"] + room["width"] <= 12.0 + 1e-6
        assert room["origin"]["y"] + room["height"] <= 10.0 + 1e-6
        for other in rooms[idx + 1 :]:
            assert _rooms_overlap(room, other) is False
