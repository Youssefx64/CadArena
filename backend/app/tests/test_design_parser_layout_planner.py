import pytest
from time import perf_counter

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
    assert abs(total_area - (24.0 * 16.0)) < 1e-3

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
