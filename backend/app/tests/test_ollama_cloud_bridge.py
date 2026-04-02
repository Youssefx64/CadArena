import asyncio

import pytest

from app.services.design_parser import provider_client as provider_client_module
from app.models.design_parser import ParseDesignModel, RecoveryMode
from app.models.workspace import (
    WorkspaceGenerateDxfForCurrentUserRequest,
    WorkspaceGenerateDxfRequest,
)
from app.routers.design_parser import parse_design_models
from app.services.design_parser.config import OLLAMA_CLOUD_MODELS, OLLAMA_LOCAL_MODELS, OLLAMA_MODEL_ID
from app.services.design_parser.errors import ParseDesignServiceError
from app.services.design_parser.orchestrator import ParseOrchestrationResult
from app.services.design_parser.provider_client import (
    OllamaProviderClient,
    generate_with_ollama_cloud,
)
from app.services.design_parser_service import _ORCHESTRATOR, parse_design_prompt_with_metadata


def test_parse_design_models_exposes_public_cloud_catalog() -> None:
    payload = parse_design_models()
    cloud_entries = [item for item in payload["models"] if item["provider"] == "ollama_cloud"]
    local_ollama_entries = [item for item in payload["models"] if item["provider"] == "ollama"]
    local_ollama_display_names = [item["display_name"] for item in local_ollama_entries]

    assert [item["model_id"] for item in cloud_entries] == OLLAMA_CLOUD_MODELS
    assert all(item["request_value"] == f"ollama_cloud::{item['model_id']}" for item in cloud_entries)
    assert {item["model_id"] for item in local_ollama_entries} == set(OLLAMA_LOCAL_MODELS)
    assert payload["models"][0]["display_name"] == f"Ollama Cloud ({OLLAMA_CLOUD_MODELS[0]})"
    assert local_ollama_display_names == [
        "Ollama Local (qwen2.5:7b-instruct)",
        f"Ollama Local ({OLLAMA_MODEL_ID})",
    ]
    assert payload["models"][-1]["display_name"].startswith("HuggingFace Local (")


def test_workspace_generate_dxf_requests_accept_model_id() -> None:
    guest_request = WorkspaceGenerateDxfRequest(
        user_id="guest-1",
        prompt="Design a compact house",
        model=ParseDesignModel.OLLAMA,
        model_id="qwen2.5:7b-instruct",
    )
    auth_request = WorkspaceGenerateDxfForCurrentUserRequest(
        prompt="Design a compact house",
        model=ParseDesignModel.OLLAMA,
        model_id="qwen2.5:7b-instruct",
    )

    assert guest_request.model_id == "qwen2.5:7b-instruct"
    assert auth_request.model_id == "qwen2.5:7b-instruct"


def test_generate_with_ollama_cloud_returns_cloud_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _fake_generate(self: OllamaProviderClient, compiled_prompt: str, *, request_id: str) -> str:
        assert self.model_id == "qwen3.5:397b-cloud"
        assert compiled_prompt == "Return JSON only"
        assert request_id == "req-cloud-success"
        assert self._generate_url == provider_client_module.OLLAMA_GENERATE_URL
        return "cloud result"

    monkeypatch.setattr(OllamaProviderClient, "generate", _fake_generate)

    result = asyncio.run(
        generate_with_ollama_cloud(
            prompt="Return JSON only",
            model_id="qwen3.5:397b-cloud",
            request_id="req-cloud-success",
        )
    )

    assert result == "cloud result"


def test_generate_with_ollama_cloud_falls_back_to_local_ollama(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen_routes: list[tuple[str, str]] = []

    async def _fake_generate(self: OllamaProviderClient, compiled_prompt: str, *, request_id: str) -> str:
        seen_routes.append((self.model_id, self._generate_url))
        if self.model_id == "qwen3.5:397b-cloud" and self._generate_url == provider_client_module.OLLAMA_GENERATE_URL:
            raise ParseDesignServiceError(
                code="QWEN_CLOUD_CONNECTION_ERROR",
                message="local proxy unavailable",
                status_code=503,
                model_used=self.model_id,
                provider_used=self.model_id,
            )
        if self.model_id == "qwen3.5:397b-cloud" and self._generate_url == provider_client_module.OLLAMA_CLOUD_GENERATE_URL:
            raise ParseDesignServiceError(
                code="QWEN_CLOUD_CONNECTION_ERROR",
                message="direct cloud unavailable",
                status_code=503,
                model_used=self.model_id,
                provider_used=self.model_id,
            )
        assert self.model_id == OLLAMA_MODEL_ID
        return "local fallback"

    monkeypatch.setattr(OllamaProviderClient, "generate", _fake_generate)

    result = asyncio.run(
        generate_with_ollama_cloud(
            prompt="Return JSON only",
            model_id="qwen3.5:397b-cloud",
            request_id="req-cloud-fallback",
        )
    )

    assert result == "local fallback"
    assert seen_routes == [
        ("qwen3.5:397b-cloud", provider_client_module.OLLAMA_GENERATE_URL),
        ("qwen3.5:397b-cloud", provider_client_module.OLLAMA_CLOUD_GENERATE_URL),
        (OLLAMA_MODEL_ID, provider_client_module.OLLAMA_GENERATE_URL),
    ]


def test_parse_design_prompt_with_metadata_bridges_public_cloud_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_provider = _ORCHESTRATOR._providers[ParseDesignModel.QWEN_CLOUD]  # type: ignore[attr-defined]
    captured: dict[str, str] = {}

    async def _fake_parse(**kwargs) -> ParseOrchestrationResult:
        captured["model_choice"] = kwargs["model_choice"].value
        captured["provider_model_id"] = _ORCHESTRATOR._providers[ParseDesignModel.QWEN_CLOUD].model_id  # type: ignore[attr-defined]
        return ParseOrchestrationResult(
            model_used=captured["provider_model_id"],
            provider_used=captured["provider_model_id"],
            failover_triggered=False,
            self_review_triggered=False,
            data={"boundary": {"width": 1.0, "height": 1.0}, "rooms": [], "walls": [], "openings": []},
            metrics={},
        )

    # Replace orchestration with a probe so we can observe the temporary provider swap directly.
    monkeypatch.setattr(_ORCHESTRATOR, "parse", _fake_parse)

    result = asyncio.run(
        parse_design_prompt_with_metadata(
            prompt="Design a compact house",
            model_choice=ParseDesignModel.OLLAMA_CLOUD,
            model_id="gemma3:27b-cloud",
            recovery_mode=RecoveryMode.REPAIR,
            request_id="req-cloud-bridge",
        )
    )

    assert captured == {
        "model_choice": ParseDesignModel.QWEN_CLOUD.value,
        "provider_model_id": "gemma3:27b-cloud",
    }
    assert result.model_used == "gemma3:27b-cloud"
    assert _ORCHESTRATOR._providers[ParseDesignModel.QWEN_CLOUD] is original_provider  # type: ignore[attr-defined]


def test_parse_design_prompt_with_metadata_restores_cloud_provider_on_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_provider = _ORCHESTRATOR._providers[ParseDesignModel.QWEN_CLOUD]  # type: ignore[attr-defined]

    async def _fake_parse(**kwargs) -> ParseOrchestrationResult:
        assert kwargs["model_choice"] == ParseDesignModel.QWEN_CLOUD
        assert _ORCHESTRATOR._providers[ParseDesignModel.QWEN_CLOUD].model_id == "qwen3.5:397b-cloud"  # type: ignore[attr-defined]
        raise RuntimeError("boom")

    # Force a failure inside orchestration to verify the provider slot is still restored in finally.
    monkeypatch.setattr(_ORCHESTRATOR, "parse", _fake_parse)

    with pytest.raises(RuntimeError, match="boom"):
        asyncio.run(
            parse_design_prompt_with_metadata(
                prompt="Design a compact house",
                model_choice=ParseDesignModel.OLLAMA_CLOUD,
                model_id="qwen3.5:397b-cloud",
                recovery_mode=RecoveryMode.REPAIR,
                request_id="req-cloud-error",
            )
        )

    assert _ORCHESTRATOR._providers[ParseDesignModel.QWEN_CLOUD] is original_provider  # type: ignore[attr-defined]


def test_parse_design_prompt_with_metadata_bridges_local_ollama_model_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_provider = _ORCHESTRATOR._providers[ParseDesignModel.OLLAMA]  # type: ignore[attr-defined]
    captured: dict[str, str] = {}

    async def _fake_parse(**kwargs) -> ParseOrchestrationResult:
        captured["model_choice"] = kwargs["model_choice"].value
        captured["provider_model_id"] = _ORCHESTRATOR._providers[ParseDesignModel.OLLAMA].model_id  # type: ignore[attr-defined]
        return ParseOrchestrationResult(
            model_used=captured["provider_model_id"],
            provider_used=captured["provider_model_id"],
            failover_triggered=False,
            self_review_triggered=False,
            data={"boundary": {"width": 1.0, "height": 1.0}, "rooms": [], "walls": [], "openings": []},
            metrics={},
        )

    monkeypatch.setattr(_ORCHESTRATOR, "parse", _fake_parse)

    result = asyncio.run(
        parse_design_prompt_with_metadata(
            prompt="Design a compact house",
            model_choice=ParseDesignModel.OLLAMA,
            model_id="qwen2.5:7b-instruct",
            recovery_mode=RecoveryMode.REPAIR,
            request_id="req-local-ollama-bridge",
        )
    )

    assert captured == {
        "model_choice": ParseDesignModel.OLLAMA.value,
        "provider_model_id": "qwen2.5:7b-instruct",
    }
    assert result.model_used == "qwen2.5:7b-instruct"
    assert _ORCHESTRATOR._providers[ParseDesignModel.OLLAMA] is original_provider  # type: ignore[attr-defined]
