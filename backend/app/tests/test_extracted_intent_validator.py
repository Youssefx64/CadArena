import pytest

from app.services.design_parser.extracted_intent_validator import ExtractedIntentValidator


def _preferred_sum(payload: dict) -> float:
    return sum(
        room["preferred_area"] * room.get("count", 1)
        for room in payload["room_program"]
    )


def test_extracted_validator_normalizes_two_bedroom_apartment_program() -> None:
    validator = ExtractedIntentValidator()
    payload = {
        "boundary": {"width": 20.0, "height": 12.0},
        "room_program": [
            {"name": "Bedroom", "room_type": "bedroom", "count": 2},
            {"name": "Kitchen", "room_type": "kitchen", "count": 1},
            {"name": "Bathroom", "room_type": "bathroom", "count": 1},
        ],
        "constraints": {
            "notes": [],
            "adjacency_preferences": [["bedroom", "kitchen"], ["bathroom", "kitchen"]],
        },
    }

    normalized = validator.validate(
        payload,
        prompt="Design a 2 bedroom apartment with kitchen and bathroom",
    )

    assert normalized["boundary"] == {"width": 12.0, "height": 9.0}
    room_program = normalized["room_program"]
    assert [room["name"] for room in room_program] == [
        "Bedroom 1",
        "Bedroom 2",
        "Kitchen",
        "Bathroom",
        "Living Room",
        "Main Corridor",
    ]
    assert sum(1 for room in room_program if room["room_type"] == "bedroom") == 2
    assert sum(1 for room in room_program if room["room_type"] == "bathroom") == 1
    assert sum(1 for room in room_program if room["room_type"] == "kitchen") == 1
    assert all(room["count"] == 1 for room in room_program)
    assert all({"preferred_area", "min_area", "max_area"} <= set(room) for room in room_program)

    boundary_area = 12.0 * 9.0
    assert boundary_area * 0.80 <= _preferred_sum(normalized) <= boundary_area * 0.95
    for room in room_program:
        assert room["preferred_area"] <= boundary_area * 0.35 + 1e-6
        if room["room_type"] == "living":
            assert room["preferred_area"] <= boundary_area * 0.28 + 1e-6
        assert room["min_area"] == pytest.approx(round(room["preferred_area"] * 0.85, 2))
        assert room["max_area"] == pytest.approx(round(room["preferred_area"] * 1.15, 2))

    adjacency_preferences = normalized["constraints"]["adjacency_preferences"]
    assert ["bedroom", "bathroom"] in adjacency_preferences
    assert ["kitchen", "living"] in adjacency_preferences
    assert ["corridor", "bedroom"] in adjacency_preferences
    assert ["corridor", "bathroom"] in adjacency_preferences
    assert ["bedroom", "kitchen"] not in adjacency_preferences
    assert ["bathroom", "kitchen"] not in adjacency_preferences


def test_extracted_validator_uses_explicit_portrait_dimensions_as_landscape() -> None:
    validator = ExtractedIntentValidator()
    payload = {
        "boundary": {"width": 6.0, "height": 4.0},
        "room_program": [
            {"name": "Kitchen", "room_type": "kitchen", "count": 1},
            {"name": "Bathroom", "room_type": "bathroom", "count": 1},
        ],
        "constraints": {"notes": [], "adjacency_preferences": []},
    }

    normalized = validator.validate(
        payload,
        prompt="Create an 8x10 apartment with kitchen and bathroom",
    )

    assert normalized["boundary"] == {"width": 10.0, "height": 8.0}


def test_extracted_validator_does_not_exceed_explicit_bedroom_or_bathroom_counts() -> None:
    validator = ExtractedIntentValidator()
    payload = {
        "boundary": {"width": 20.0, "height": 12.0},
        "room_program": [
            {"name": "Bedroom", "room_type": "bedroom", "count": 4},
            {"name": "Bathroom", "room_type": "bathroom", "count": 3},
            {"name": "Kitchen", "room_type": "kitchen", "count": 1},
        ],
        "constraints": {"notes": [], "adjacency_preferences": []},
    }

    normalized = validator.validate(
        payload,
        prompt="Design a 2 bedroom apartment with 1 bathroom and 1 kitchen",
    )

    assert sum(1 for room in normalized["room_program"] if room["room_type"] == "bedroom") == 2
    assert sum(1 for room in normalized["room_program"] if room["room_type"] == "bathroom") == 1
    assert sum(1 for room in normalized["room_program"] if room["room_type"] == "kitchen") == 1
