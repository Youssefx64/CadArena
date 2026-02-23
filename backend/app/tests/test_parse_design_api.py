import asyncio
import json

import pytest

from app.models.design_parser import ParseDesignModel, ParseDesignRequest, RecoveryMode
from app.routers.design_parser import parse_design, router as design_parser_router
from app.services.design_parser_service import (
    ParseDesignServiceError,
    _ORCHESTRATOR,
    parse_design_prompt,
)


def test_parse_design_route_is_registered() -> None:
    has_route = any(
        route.path == "/parse-design" and "POST" in route.methods
        for route in design_parser_router.routes
        if hasattr(route, "methods")
    )
    assert has_route is True


def test_parse_design_endpoint_rejects_non_english_prompt() -> None:
    request = ParseDesignRequest(
        prompt="اعمل مخطط بيت 20x12",
        model=ParseDesignModel.OLLAMA,
    )
    response = asyncio.run(parse_design(request))

    assert response.status_code == 400
    body = json.loads(response.body.decode("utf-8"))
    assert body["success"] is False
    assert body["error"]["code"] == "PROMPT_ENGLISH_ONLY"
    assert body["provider_used"] == "llama3.1:8b"
    assert body["failover_triggered"] is False


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


def test_parse_design_rejects_prose_wrapped_json_for_hf(monkeypatch: pytest.MonkeyPatch) -> None:
    wrapped = (
        "Here is your result:\n"
        '{"boundary":{"width":20.0,"height":12.0},"room_program":[{"name":"Living Room","room_type":"living","count":1}],"constraints":{"notes":[],"adjacency_preferences":[]}}'
    )

    async def _fake_generate_with_hf(_: str, *, request_id: str) -> str:
        return wrapped

    provider = _ORCHESTRATOR._providers[ParseDesignModel.HUGGINGFACE]  # type: ignore[attr-defined]
    monkeypatch.setattr(provider, "generate", _fake_generate_with_hf)

    with pytest.raises(ParseDesignServiceError) as exc_info:
        asyncio.run(
            parse_design_prompt(
                prompt="Create a 20x12 house with one living room.",
                model_choice=ParseDesignModel.HUGGINGFACE,
                recovery_mode=RecoveryMode.REPAIR,
            )
        )

    assert exc_info.value.code == "INVALID_JSON_OUTPUT"


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
    assert len(data_first["rooms"]) == 6
    assert len(data_first["walls"]) == 24
    assert sum(1 for room in data_first["rooms"] if room["room_type"] == "bedroom") == 2
    assert sum(1 for room in data_first["rooms"] if room["room_type"] == "bathroom") == 1
    assert sum(1 for room in data_first["rooms"] if room["room_type"] == "corridor") == 1

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
