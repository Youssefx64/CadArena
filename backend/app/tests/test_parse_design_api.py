import asyncio
import json

import pytest

from app.models.design_parser import ParseDesignModel, RecoveryMode
from app.routers.design_parser import parse_design, router as design_parser_router
from app.models.design_parser import ParseDesignRequest
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


def test_parse_design_repair_mode_accepts_prose_wrapped_json(monkeypatch: pytest.MonkeyPatch) -> None:
    wrapped = (
        "Sure, here is the result:\n"
        '{'
        '"boundary":{"width":20.0,"height":12.0},'
        '"rooms":[{"name":"Living Room","room_type":"living","width":10.0,"height":6.0,"origin":{"x":0.0,"y":0.0}}],'
        '"walls":[{"room_name":"Living Room","wall":"bottom","start":{"x":0.0,"y":0.0},"end":{"x":10.0,"y":0.0},"thickness":0.2}],'
        '"openings":[]'
        "}\n"
        "Thanks."
    )

    async def _fake_generate_with_ollama(_: str, *, request_id: str) -> str:
        return wrapped

    provider = _ORCHESTRATOR._providers[ParseDesignModel.OLLAMA]  # type: ignore[attr-defined]
    monkeypatch.setattr(provider, "generate", _fake_generate_with_ollama)

    model_used, data = asyncio.run(
        parse_design_prompt(
            prompt="Create a 20x12 house with one living room.",
            model_choice=ParseDesignModel.OLLAMA,
            recovery_mode=RecoveryMode.REPAIR,
        )
    )

    assert model_used == "llama3.1:8b"
    assert data["boundary"]["width"] == 20.0


def test_parse_design_repair_mode_enforces_requested_room_counts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    under_specified = (
        "{"
        '"boundary":{"width":20.0,"height":12.0},'
        '"rooms":['
        '{"name":"Living Room","room_type":"living","width":10.0,"height":6.0,"origin":{"x":0.0,"y":0.0}},'
        '{"name":"Kitchen","room_type":"kitchen","width":10.0,"height":6.0,"origin":{"x":10.0,"y":0.0}},'
        '{"name":"Bedroom 1","room_type":"bedroom","width":10.0,"height":6.0,"origin":{"x":0.0,"y":6.0}},'
        '{"name":"Bathroom 1","room_type":"bathroom","width":10.0,"height":6.0,"origin":{"x":10.0,"y":6.0}}'
        "],"
        '"walls":[],'
        '"openings":[]'
        "}"
    )

    async def _fake_generate_with_ollama(_: str, *, request_id: str) -> str:
        return under_specified

    provider = _ORCHESTRATOR._providers[ParseDesignModel.OLLAMA]  # type: ignore[attr-defined]
    monkeypatch.setattr(provider, "generate", _fake_generate_with_ollama)

    _, data = asyncio.run(
        parse_design_prompt(
            prompt="Create a 20x12 house with a living room, kitchen, 2 bedrooms, and 1 bathroom.",
            model_choice=ParseDesignModel.OLLAMA,
            recovery_mode=RecoveryMode.REPAIR,
        )
    )

    bedroom_count = sum(1 for room in data["rooms"] if room["room_type"] == "bedroom")
    bathroom_count = sum(1 for room in data["rooms"] if room["room_type"] == "bathroom")
    assert bedroom_count >= 2
    assert bathroom_count >= 1


def test_parse_design_repair_mode_prioritizes_prompt_boundary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    wrong_boundary = (
        "{"
        '"boundary":{"width":17.0,"height":10.0},'
        '"rooms":['
        '{"name":"Living Room","room_type":"living","width":8.5,"height":10.0,"origin":{"x":0.0,"y":0.0}},'
        '{"name":"Kitchen","room_type":"kitchen","width":8.5,"height":10.0,"origin":{"x":8.5,"y":0.0}}'
        "],"
        '"walls":[],'
        '"openings":[]'
        "}"
    )

    async def _fake_generate_with_ollama(_: str, *, request_id: str) -> str:
        return wrong_boundary

    provider = _ORCHESTRATOR._providers[ParseDesignModel.OLLAMA]  # type: ignore[attr-defined]
    monkeypatch.setattr(provider, "generate", _fake_generate_with_ollama)

    _, data = asyncio.run(
        parse_design_prompt(
            prompt="Create a 20x12 house with one living room and one kitchen.",
            model_choice=ParseDesignModel.OLLAMA,
            recovery_mode=RecoveryMode.REPAIR,
        )
    )

    assert data["boundary"]["width"] == 20.0
    assert data["boundary"]["height"] == 12.0
