import asyncio
import json

import pytest

from app.models.design_parser import ParseDesignModel, ParseDesignRequest, RecoveryMode
from app.routers.design_parser import parse_design, router as design_parser_router
from app.services.design_parser.layout_planner import LayoutPlanningError
from app.services.design_parser_service import (
    ParseDesignServiceError,
    _ORCHESTRATOR,
    parse_design_prompt,
    parse_design_prompt_with_metadata,
)


def test_parse_design_route_is_registered() -> None:
    has_route = any(
        route.path == "/parse-design" and "POST" in route.methods
        for route in design_parser_router.routes
        if hasattr(route, "methods")
    )
    assert has_route is True


def test_parse_design_endpoint_accepts_arabic_prompt(monkeypatch: pytest.MonkeyPatch) -> None:
    extracted = {
        "boundary": {"width": 20.0, "height": 12.0},
        "room_program": [
            {"name": "Living Room", "room_type": "living", "count": 1},
            {"name": "Kitchen", "room_type": "kitchen", "count": 1},
            {"name": "Bedroom", "room_type": "bedroom", "count": 2},
            {"name": "Bathroom", "room_type": "bathroom", "count": 1},
        ],
        "constraints": {"notes": [], "adjacency_preferences": [["kitchen", "living"]]},
    }
    review = json.dumps(
        {"passed": True, "issues": [], "corrected_output": extracted},
        separators=(",", ":"),
    )

    async def _fake_generate_with_ollama(_: str, *, request_id: str) -> str:
        if request_id.endswith("_self_review"):
            return review
        return json.dumps(extracted, separators=(",", ":"))

    provider = _ORCHESTRATOR._providers[ParseDesignModel.OLLAMA]  # type: ignore[attr-defined]
    monkeypatch.setattr(provider, "generate", _fake_generate_with_ollama)

    request = ParseDesignRequest(
        prompt="اعمل مخطط بيت 20x12",
        model=ParseDesignModel.OLLAMA,
    )
    response = asyncio.run(parse_design(request))

    assert response.success is True
    assert response.data.boundary.model_dump() == {"width": 20.0, "height": 12.0}
    assert response.provider_used == "llama3.1:8b"
    assert response.failover_triggered is False


def test_parse_design_json_validation_path(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _fake_generate_with_ollama(_: str, *, request_id: str) -> str:
        return "not-json-output"

    provider = _ORCHESTRATOR._providers[ParseDesignModel.OLLAMA]  # type: ignore[attr-defined]
    monkeypatch.setattr(provider, "generate", _fake_generate_with_ollama)

    with pytest.raises(ParseDesignServiceError) as exc_info:
        asyncio.run(
            parse_design_prompt(
                prompt="Create a 20x12 house with one living room and one kitchen.",
                model_choice=ParseDesignModel.OLLAMA,
            )
        )

    assert exc_info.value.code == "INVALID_JSON_OUTPUT"


def test_parse_design_salvages_prose_wrapped_json_for_hf(monkeypatch: pytest.MonkeyPatch) -> None:
    extracted = {
        "boundary": {"width": 20.0, "height": 12.0},
        "room_program": [
            {"name": "Living Room", "room_type": "living", "count": 1},
            {"name": "Kitchen", "room_type": "kitchen", "count": 1},
            {"name": "Bedroom", "room_type": "bedroom", "count": 2},
            {"name": "Bathroom", "room_type": "bathroom", "count": 1},
        ],
        "constraints": {"notes": [], "adjacency_preferences": [["kitchen", "living"]]},
    }
    wrapped = "Here is your result:\n" + json.dumps(extracted, separators=(",", ":"))
    review = json.dumps(
        {"passed": True, "issues": [], "corrected_output": extracted},
        separators=(",", ":"),
    )

    async def _fake_generate_with_hf(_: str, *, request_id: str) -> str:
        if request_id.endswith("_self_review"):
            return review
        return wrapped

    provider = _ORCHESTRATOR._providers[ParseDesignModel.HUGGINGFACE]  # type: ignore[attr-defined]
    monkeypatch.setattr(provider, "generate", _fake_generate_with_hf)

    result = asyncio.run(
        parse_design_prompt_with_metadata(
            prompt="Create a 20x12 house with a living room, kitchen, bedrooms, and bathroom.",
            model_choice=ParseDesignModel.HUGGINGFACE,
            recovery_mode=RecoveryMode.REPAIR,
        )
    )

    assert result.data["boundary"] == {"width": 20.0, "height": 12.0}
    assert len(result.data["rooms"]) >= 5


def test_parse_design_uses_json_repair_call_when_first_output_is_not_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    extracted = {
        "boundary": {"width": 20.0, "height": 12.0},
        "room_program": [
            {"name": "Living Room", "room_type": "living", "count": 1},
            {"name": "Kitchen", "room_type": "kitchen", "count": 1},
            {"name": "Bedroom", "room_type": "bedroom", "count": 2},
            {"name": "Bathroom", "room_type": "bathroom", "count": 1},
        ],
        "constraints": {"notes": [], "adjacency_preferences": [["kitchen", "living"]]},
    }
    review = json.dumps(
        {"passed": True, "issues": [], "corrected_output": extracted},
        separators=(",", ":"),
    )
    request_ids: list[str] = []

    async def _fake_generate_with_ollama(_: str, *, request_id: str) -> str:
        request_ids.append(request_id)
        if request_id.endswith("_self_review"):
            return review
        if request_id.endswith("_json_repair"):
            return json.dumps(extracted, separators=(",", ":"))
        return "I understood your request and can produce a plan."

    provider = _ORCHESTRATOR._providers[ParseDesignModel.OLLAMA]  # type: ignore[attr-defined]
    monkeypatch.setattr(provider, "generate", _fake_generate_with_ollama)

    result = asyncio.run(
        parse_design_prompt_with_metadata(
            prompt="Create a 20x12 house with a living room, kitchen, bedrooms, and bathroom.",
            model_choice=ParseDesignModel.OLLAMA,
        )
    )

    assert any(request_id.endswith("_json_repair") for request_id in request_ids)
    assert result.data["boundary"] == {"width": 20.0, "height": 12.0}


def test_parse_design_uses_prompt_fallback_when_json_and_repair_both_fail(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request_ids: list[str] = []
    review_payload = {
        "passed": True,
        "issues": [],
        "corrected_output": {
            "boundary": {"width": 20.0, "height": 12.0},
            "room_program": [{"name": "Living Room", "room_type": "living", "count": 1}],
            "constraints": {"notes": [], "adjacency_preferences": []},
        },
    }

    async def _fake_generate_with_ollama(prompt_text: str, *, request_id: str) -> str:
        request_ids.append(request_id)
        if request_id.endswith("_self_review"):
            return json.dumps(review_payload, separators=(",", ":"))
        if request_id.endswith("_json_repair"):
            return "still not json after repair"
        return "This is not JSON and includes prose."

    provider = _ORCHESTRATOR._providers[ParseDesignModel.OLLAMA]  # type: ignore[attr-defined]
    monkeypatch.setattr(provider, "generate", _fake_generate_with_ollama)

    result = asyncio.run(
        parse_design_prompt_with_metadata(
            prompt="Design a 14x10 house with 2 bedrooms, 1 kitchen, 1 living room, and 1 bathroom.",
            model_choice=ParseDesignModel.OLLAMA,
            recovery_mode=RecoveryMode.REPAIR,
        )
    )

    assert any(request_id.endswith("_json_repair") for request_id in request_ids)
    assert result.data["boundary"] == {"width": 14.0, "height": 10.0}
    names = {room["name"] for room in result.data["rooms"]}
    assert "Living Room" in names


def test_parse_design_uses_layout_emergency_fallback_on_planner_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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
    review = json.dumps(
        {"passed": True, "issues": [], "corrected_output": extracted},
        separators=(",", ":"),
    )
    real_plan_with_metadata = _ORCHESTRATOR._layout_planner.plan_with_metadata  # type: ignore[attr-defined]

    async def _fake_generate(_: str, *, request_id: str) -> str:
        if request_id.endswith("_self_review"):
            return review
        return json.dumps(extracted, separators=(",", ":"))

    def _fake_plan_with_metadata(
        payload,
        *,
        optimize_efficiency: bool = False,
        selection_offset: int = 0,
        relax_kitchen_slack: bool = True,
    ):
        notes = (payload.get("constraints") or {}).get("notes") if isinstance(payload, dict) else []
        if isinstance(notes, list) and any("Emergency fallback program" in str(note) for note in notes):
            return real_plan_with_metadata(
                payload,
                optimize_efficiency=optimize_efficiency,
                selection_offset=selection_offset,
                relax_kitchen_slack=relax_kitchen_slack,
            )
        raise LayoutPlanningError("Mock topology failure for primary planning pass")

    provider = _ORCHESTRATOR._providers[ParseDesignModel.OLLAMA]  # type: ignore[attr-defined]
    monkeypatch.setattr(provider, "generate", _fake_generate)
    monkeypatch.setattr(_ORCHESTRATOR._layout_planner, "plan_with_metadata", _fake_plan_with_metadata)

    result = asyncio.run(
        parse_design_prompt_with_metadata(
            prompt="Design a 20x12 house for a family with practical layout.",
            model_choice=ParseDesignModel.OLLAMA,
            recovery_mode=RecoveryMode.REPAIR,
        )
    )

    assert result.metrics["selected_topology"] != "unknown"
    assert len(result.data["rooms"]) >= 5


def test_parse_design_small_house_program_is_deterministic(monkeypatch: pytest.MonkeyPatch) -> None:
    extracted = {
        "boundary": {"width": 20.0, "height": 12.0},
        "room_program": [
            {"name": "Living Room", "room_type": "living", "count": 1},
            {"name": "Kitchen", "room_type": "kitchen", "count": 1},
            {"name": "Bedroom", "room_type": "bedroom", "count": 2},
            {"name": "Bathroom", "room_type": "bathroom", "count": 1},
        ],
        "constraints": {"notes": ["Keep circulation practical"], "adjacency_preferences": [["kitchen", "living"]]},
    }

    async def _fake_generate_with_ollama(_: str, *, request_id: str) -> str:
        return json.dumps(extracted, separators=(",", ":"))

    provider = _ORCHESTRATOR._providers[ParseDesignModel.OLLAMA]  # type: ignore[attr-defined]
    monkeypatch.setattr(provider, "generate", _fake_generate_with_ollama)

    _, data_first = asyncio.run(
        parse_design_prompt(
            prompt="Create a 20x12 house with a living room, kitchen, 2 bedrooms, and 1 bathroom.",
            model_choice=ParseDesignModel.OLLAMA,
        )
    )
    _, data_second = asyncio.run(
        parse_design_prompt(
            prompt="Create a 20x12 house with a living room, kitchen, 2 bedrooms, and 1 bathroom.",
            model_choice=ParseDesignModel.OLLAMA,
        )
    )

    assert data_first == data_second
    assert data_first["boundary"] == {"width": 20.0, "height": 12.0}
    # The planner now keeps the main living room within the stricter 28% cap
    # without inventing an extra lounge segment.
    assert len(data_first["rooms"]) == 6
    assert len(data_first["walls"]) == 24
    assert sum(1 for room in data_first["rooms"] if room["room_type"] == "bedroom") == 2
    assert sum(1 for room in data_first["rooms"] if room["room_type"] == "bathroom") == 1
    assert sum(1 for room in data_first["rooms"] if room["room_type"] == "corridor") == 1
    living_room = next(room for room in data_first["rooms"] if room["name"] == "Living Room")
    assert living_room["width"] * living_room["height"] <= 67.2 + 1e-6

    for room in data_first["rooms"]:
        x = room["origin"]["x"]
        y = room["origin"]["y"]
        assert x >= 0 and y >= 0
        assert x + room["width"] <= 20.0 + 1e-6
        assert y + room["height"] <= 12.0 + 1e-6


def test_parse_design_complex_program_contains_all_requested_elements(monkeypatch: pytest.MonkeyPatch) -> None:
    extracted = {
        "boundary": {"width": 24.0, "height": 16.0},
        "room_program": [
            {"name": "Master Bedroom", "room_type": "bedroom", "count": 1},
            {"name": "Children Bedroom", "room_type": "bedroom", "count": 2},
            {"name": "Shared Bathroom", "room_type": "bathroom", "count": 1},
            {"name": "Guest Bathroom", "room_type": "bathroom", "count": 1},
            {"name": "Living Room", "room_type": "living", "count": 1},
            {"name": "Dining Room", "room_type": "living", "count": 1},
            {"name": "Kitchen", "room_type": "kitchen", "count": 1},
            {"name": "Laundry", "room_type": "bathroom", "count": 1},
            {"name": "Storage", "room_type": "corridor", "count": 1},
        ],
        "constraints": {
            "notes": ["Single floor", "Practical circulation"],
            "adjacency_preferences": [["kitchen", "living"], ["bedroom", "bathroom"]],
        },
    }

    async def _fake_generate_with_hf(_: str, *, request_id: str) -> str:
        return json.dumps(extracted, separators=(",", ":"))

    provider = _ORCHESTRATOR._providers[ParseDesignModel.HUGGINGFACE]  # type: ignore[attr-defined]
    monkeypatch.setattr(provider, "generate", _fake_generate_with_hf)

    _, data = asyncio.run(
        parse_design_prompt(
            prompt=(
                "Design a single-floor 24x16 meter family house for 5 people. Include: "
                "1 master bedroom with private bathroom, 2 children bedrooms, 1 shared bathroom, "
                "1 guest bathroom, 1 living room, 1 dining room, 1 kitchen, 1 laundry, and 1 storage room."
            ),
            model_choice=ParseDesignModel.HUGGINGFACE,
        )
    )

    names = {room["name"] for room in data["rooms"]}
    assert data["boundary"] == {"width": 24.0, "height": 16.0}
    assert len(data["rooms"]) >= 11
    assert "Master Bedroom" in names
    assert "Children Bedroom 1" in names
    assert "Children Bedroom 2" in names
    assert "Shared Bathroom" in names
    assert "Guest Bathroom" in names
    assert "Laundry" in names
    assert "Storage" in names
    assert "Main Corridor" in names


def test_parse_design_fails_when_area_constraints_are_impossible(monkeypatch: pytest.MonkeyPatch) -> None:
    impossible = {
        "boundary": {"width": 6.0, "height": 6.0},
        "room_program": [
            {"name": "Living Room", "room_type": "living", "count": 1, "min_area": 30.0},
            {"name": "Bedroom", "room_type": "bedroom", "count": 1, "min_area": 30.0},
        ],
        "constraints": {"notes": [], "adjacency_preferences": []},
    }

    async def _fake_generate_with_ollama(_: str, *, request_id: str) -> str:
        return json.dumps(impossible, separators=(",", ":"))

    provider = _ORCHESTRATOR._providers[ParseDesignModel.OLLAMA]  # type: ignore[attr-defined]
    monkeypatch.setattr(provider, "generate", _fake_generate_with_ollama)

    with pytest.raises(ParseDesignServiceError) as exc_info:
        asyncio.run(
            parse_design_prompt(
                prompt="Create a 6x6 house with large rooms.",
                model_choice=ParseDesignModel.OLLAMA,
            )
        )

    assert exc_info.value.code == "LAYOUT_PLANNING_FAILED"


def test_parse_design_retries_with_prompt_program_derivation(monkeypatch: pytest.MonkeyPatch) -> None:
    sparse_extracted = {
        "boundary": {"width": 24.0, "height": 16.0},
        "room_program": [
            {"name": "Kitchen", "room_type": "kitchen", "count": 1},
            {"name": "Bedroom", "room_type": "bedroom", "count": 2},
            {"name": "Bathroom", "room_type": "bathroom", "count": 1},
        ],
        "constraints": {"notes": [], "adjacency_preferences": []},
    }

    async def _fake_generate_with_hf(_: str, *, request_id: str) -> str:
        return json.dumps(sparse_extracted, separators=(",", ":"))

    provider = _ORCHESTRATOR._providers[ParseDesignModel.HUGGINGFACE]  # type: ignore[attr-defined]
    monkeypatch.setattr(provider, "generate", _fake_generate_with_hf)

    _, data = asyncio.run(
        parse_design_prompt(
            prompt=(
                "Design a single-floor 24x16 meter family house for 5 people. Include: "
                "1 master bedroom with private bathroom, 2 children bedrooms, 1 shared bathroom, "
                "1 guest bathroom, 1 living room, 1 dining room, 1 kitchen, 1 laundry, and 1 storage room."
            ),
            model_choice=ParseDesignModel.HUGGINGFACE,
        )
    )

    names = {room["name"] for room in data["rooms"]}
    assert "Living Room" in names
    assert "Kitchen" in names
    assert "Master Bedroom" in names
    assert "Children Bedroom 1" in names
    assert "Children Bedroom 2" in names


def test_parse_design_self_review_accepts_wrapped_json(monkeypatch: pytest.MonkeyPatch) -> None:
    extracted = {
        "boundary": {"width": 20.0, "height": 12.0},
        "room_program": [
            {"name": "Living Room", "room_type": "living", "count": 1, "preferred_area": 20.0},
            {"name": "Kitchen", "room_type": "kitchen", "count": 1, "preferred_area": 9.0},
            {"name": "Bedroom", "room_type": "bedroom", "count": 2, "preferred_area": 16.0},
            {"name": "Bathroom", "room_type": "bathroom", "count": 1, "preferred_area": 4.0},
        ],
        "constraints": {"notes": [], "adjacency_preferences": [["kitchen", "living"]]},
    }
    wrapped_review = (
        "Here is the review:\n"
        '{"passed":true,"issues":[],"corrected_output":{"boundary":{"width":20.0,"height":12.0},'
        '"room_program":[{"name":"Living Room","room_type":"living","count":1,"preferred_area":20.0},'
        '{"name":"Kitchen","room_type":"kitchen","count":1,"preferred_area":9.0},'
        '{"name":"Bedroom","room_type":"bedroom","count":2,"preferred_area":16.0},'
        '{"name":"Bathroom","room_type":"bathroom","count":1,"preferred_area":4.0}],'
        '"constraints":{"notes":[],"adjacency_preferences":[["kitchen","living"]]}}}'
    )

    async def _fake_generate(_: str, *, request_id: str) -> str:
        if request_id.endswith("_self_review"):
            return wrapped_review
        return json.dumps(extracted, separators=(",", ":"))

    provider = _ORCHESTRATOR._providers[ParseDesignModel.OLLAMA]  # type: ignore[attr-defined]
    monkeypatch.setattr(provider, "generate", _fake_generate)

    result = asyncio.run(
        parse_design_prompt_with_metadata(
            prompt="Create a 20x12 house with a living room, kitchen, 2 bedrooms, and bathroom.",
            model_choice=ParseDesignModel.OLLAMA,
        )
    )

    assert result.self_review_triggered is False
    assert result.data["boundary"] == {"width": 20.0, "height": 12.0}


def test_parse_design_self_review_falls_back_when_review_is_not_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    extracted = {
        "boundary": {"width": 20.0, "height": 12.0},
        "room_program": [
            {"name": "Living Room", "room_type": "living", "count": 1},
            {"name": "Kitchen", "room_type": "kitchen", "count": 1},
            {"name": "Bedroom", "room_type": "bedroom", "count": 2},
            {"name": "Bathroom", "room_type": "bathroom", "count": 1},
        ],
        "constraints": {"notes": [], "adjacency_preferences": [["kitchen", "living"]]},
    }

    async def _fake_generate(_: str, *, request_id: str) -> str:
        if request_id.endswith("_self_review"):
            return "Looks good overall."
        return json.dumps(extracted, separators=(",", ":"))

    provider = _ORCHESTRATOR._providers[ParseDesignModel.OLLAMA]  # type: ignore[attr-defined]
    monkeypatch.setattr(provider, "generate", _fake_generate)

    result = asyncio.run(
        parse_design_prompt_with_metadata(
            prompt="Create a 20x12 house with a living room, kitchen, 2 bedrooms, and bathroom.",
            model_choice=ParseDesignModel.OLLAMA,
        )
    )

    assert result.self_review_triggered is False
    assert len(result.data["rooms"]) >= 5


def test_parse_design_corrects_room_count_without_retry(monkeypatch: pytest.MonkeyPatch) -> None:
    initial_extracted = {
        "boundary": {"width": 20.0, "height": 12.0},
        "room_program": [
            {"name": "Living Room", "room_type": "living", "count": 1},
            {"name": "Kitchen", "room_type": "kitchen", "count": 1},
            {"name": "Bedroom", "room_type": "bedroom", "count": 1},
            {"name": "Bathroom", "room_type": "bathroom", "count": 1},
        ],
        "constraints": {"notes": [], "adjacency_preferences": []},
    }
    review_initial = {"passed": True, "issues": [], "corrected_output": initial_extracted}
    request_ids: list[str] = []

    async def _fake_generate(_: str, *, request_id: str) -> str:
        request_ids.append(request_id)
        if request_id.endswith("_self_review"):
            return json.dumps(review_initial, separators=(",", ":"))
        return json.dumps(initial_extracted, separators=(",", ":"))

    provider = _ORCHESTRATOR._providers[ParseDesignModel.OLLAMA]  # type: ignore[attr-defined]
    monkeypatch.setattr(provider, "generate", _fake_generate)

    _, data = asyncio.run(
        parse_design_prompt(
            prompt="Create a 20x12 house with 2 bedrooms, 1 kitchen, 1 living room, and 1 bathroom.",
            model_choice=ParseDesignModel.OLLAMA,
        )
    )

    assert not any(request_id.endswith("_quality_correction") for request_id in request_ids)
    assert sum(1 for room in data["rooms"] if room["room_type"] == "bedroom") == 2


def test_parse_design_corrects_summed_room_count_entries_for_arabic_prompt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    wrong_extracted = {
        "boundary": {"width": 20.0, "height": 12.0},
        "room_program": [
            {"name": "Living Room", "room_type": "living", "count": 1},
            {"name": "Kitchen", "room_type": "kitchen", "count": 1},
            {"name": "Bedroom", "room_type": "bedroom", "count": 3},
            {"name": "Bathroom", "room_type": "bathroom", "count": 2},
        ],
        "constraints": {"notes": [], "adjacency_preferences": []},
    }
    review_wrong = {"passed": True, "issues": [], "corrected_output": wrong_extracted}
    request_ids: list[str] = []

    async def _fake_generate(_: str, *, request_id: str) -> str:
        request_ids.append(request_id)
        if request_id.endswith("_self_review"):
            return json.dumps(review_wrong, separators=(",", ":"))
        return json.dumps(wrong_extracted, separators=(",", ":"))

    provider = _ORCHESTRATOR._providers[ParseDesignModel.OLLAMA]  # type: ignore[attr-defined]
    monkeypatch.setattr(provider, "generate", _fake_generate)

    _, data = asyncio.run(
        parse_design_prompt(
            prompt="عاوز شقة فيها غرفتين نوم ومطبخ وحمام",
            model_choice=ParseDesignModel.OLLAMA,
        )
    )

    assert not any(request_id.endswith("_quality_correction") for request_id in request_ids)
    assert sum(1 for room in data["rooms"] if room["room_type"] == "bedroom") == 2
    assert sum(1 for room in data["rooms"] if room["room_type"] == "bathroom") == 1
    assert sum(1 for room in data["rooms"] if room["room_type"] == "kitchen") == 1


def test_parse_design_simple_one_bedroom_program_stays_single_living_room(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    extracted = {
        "boundary": {"width": 12.0, "height": 9.0},
        "room_program": [
            {"name": "Bedroom", "room_type": "bedroom", "count": 1},
            {"name": "Bathroom", "room_type": "bathroom", "count": 1},
            {"name": "Kitchen", "room_type": "kitchen", "count": 1},
            {"name": "Living Room", "room_type": "living", "count": 1},
        ],
        "constraints": {"notes": [], "adjacency_preferences": [["bedroom", "bathroom"], ["kitchen", "living"]]},
    }
    review = {"passed": True, "issues": [], "corrected_output": extracted}

    async def _fake_generate(_: str, *, request_id: str) -> str:
        if request_id.endswith("_self_review"):
            return json.dumps(review, separators=(",", ":"))
        return json.dumps(extracted, separators=(",", ":"))

    provider = _ORCHESTRATOR._providers[ParseDesignModel.OLLAMA]  # type: ignore[attr-defined]
    monkeypatch.setattr(provider, "generate", _fake_generate)

    _, data = asyncio.run(
        parse_design_prompt(
            prompt="Design a 1 bedroom apartment with kitchen and bathroom",
            model_choice=ParseDesignModel.OLLAMA,
        )
    )

    living_rooms = [room for room in data["rooms"] if room["room_type"] == "living"]
    assert len(living_rooms) == 1
    assert living_rooms[0]["name"] == "Living Room"
    assert "Family Lounge 1" not in {room["name"] for room in data["rooms"]}


def test_enforce_room_counts_reduces_existing_count_before_removing_entries() -> None:
    payload = {
        "boundary": {"width": 20.0, "height": 12.0},
        "room_program": [
            {"name": "Bedroom", "room_type": "bedroom", "count": 3, "preferred_area": 16.0},
            {"name": "Kitchen", "room_type": "kitchen", "count": 1},
        ],
        "constraints": {"notes": [], "adjacency_preferences": []},
    }

    corrected = _ORCHESTRATOR._enforce_room_counts_from_prompt(  # type: ignore[attr-defined]
        payload,
        {"bedroom": 2},
    )

    bedroom_entries = [
        room for room in corrected["room_program"] if room.get("room_type") == "bedroom"
    ]
    assert len(bedroom_entries) == 1
    assert bedroom_entries[0]["count"] == 2


def test_enforce_room_counts_prefers_increasing_existing_entry_count() -> None:
    payload = {
        "boundary": {"width": 20.0, "height": 12.0},
        "room_program": [
            {"name": "Bedroom", "room_type": "bedroom", "count": 1, "preferred_area": 16.0},
            {"name": "Kitchen", "room_type": "kitchen", "count": 1},
        ],
        "constraints": {"notes": [], "adjacency_preferences": []},
    }

    corrected = _ORCHESTRATOR._enforce_room_counts_from_prompt(  # type: ignore[attr-defined]
        payload,
        {"bedroom": 3},
    )

    bedroom_entries = [
        room for room in corrected["room_program"] if room.get("room_type") == "bedroom"
    ]
    assert len(bedroom_entries) == 1
    assert bedroom_entries[0]["count"] == 3
