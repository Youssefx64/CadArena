import asyncio
import json

import pytest

from app.models.design_parser import ParseDesignModel
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
