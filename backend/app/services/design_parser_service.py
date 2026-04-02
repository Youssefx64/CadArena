"""Facade for design parser orchestration."""

from __future__ import annotations

import asyncio

from app.models.design_parser import ParseDesignModel, RecoveryMode
from app.services.design_parser import (
    DesignParseOrchestrator,
    ParseDesignServiceError as _ParseDesignServiceError,
    ParseOrchestrationResult,
)
from app.services.design_parser.config import OLLAMA_CLOUD_MODELS, OLLAMA_MODEL_ID, QWEN_CLOUD_MODEL_ID
from app.services.design_parser.provider_client import OllamaProviderClient, QwenCloudProviderClient

_ORCHESTRATOR = DesignParseOrchestrator()
ParseDesignServiceError = _ParseDesignServiceError
_PROVIDER_OVERRIDE_LOCK = asyncio.Lock()


def _clean_model_id(model_id: str | None) -> str | None:
    """Return a stripped model id or None when the caller did not provide one."""

    if not isinstance(model_id, str):
        return None
    cleaned = model_id.strip()
    return cleaned or None


def _resolve_cloud_model_id(
    model_choice: ParseDesignModel,
    model_id: str | None,
) -> str | None:
    """Resolve the effective cloud model id for public and legacy cloud selections."""

    cleaned = _clean_model_id(model_id)
    if cleaned is not None and model_choice in {ParseDesignModel.OLLAMA_CLOUD, ParseDesignModel.QWEN_CLOUD}:
        return cleaned
    if model_choice == ParseDesignModel.OLLAMA_CLOUD:
        return OLLAMA_CLOUD_MODELS[0]
    if model_choice == ParseDesignModel.QWEN_CLOUD:
        return QWEN_CLOUD_MODEL_ID
    return None


async def _parse_with_cloud_provider_override(
    *,
    prompt: str,
    model_choice: ParseDesignModel,
    recovery_mode: RecoveryMode,
    request_id: str,
    model_id: str,
) -> ParseOrchestrationResult:
    """Temporarily swap the internal cloud provider so model ids stay request-scoped."""

    providers = _ORCHESTRATOR._providers  # type: ignore[attr-defined]
    original_provider = providers[ParseDesignModel.QWEN_CLOUD]
    override_provider = QwenCloudProviderClient(model_id=model_id)

    async with _PROVIDER_OVERRIDE_LOCK:
        # Swap the internal qwen-cloud slot only while this request is active.
        providers[ParseDesignModel.QWEN_CLOUD] = override_provider
        try:
            internal_choice = (
                ParseDesignModel.QWEN_CLOUD
                if model_choice == ParseDesignModel.OLLAMA_CLOUD
                else model_choice
            )
            return await _ORCHESTRATOR.parse(
                prompt=prompt,
                model_choice=internal_choice,
                recovery_mode=recovery_mode,
                request_id=request_id,
            )
        finally:
            providers[ParseDesignModel.QWEN_CLOUD] = original_provider


async def _parse_with_ollama_provider_override(
    *,
    prompt: str,
    recovery_mode: RecoveryMode,
    request_id: str,
    model_id: str,
) -> ParseOrchestrationResult:
    """Temporarily swap the local Ollama provider so request-scoped model ids work."""

    providers = _ORCHESTRATOR._providers  # type: ignore[attr-defined]
    original_provider = providers[ParseDesignModel.OLLAMA]
    override_provider = OllamaProviderClient(model_id=model_id)

    async with _PROVIDER_OVERRIDE_LOCK:
        # Swap the internal ollama slot only while this request is active.
        providers[ParseDesignModel.OLLAMA] = override_provider
        try:
            return await _ORCHESTRATOR.parse(
                prompt=prompt,
                model_choice=ParseDesignModel.OLLAMA,
                recovery_mode=recovery_mode,
                request_id=request_id,
            )
        finally:
            providers[ParseDesignModel.OLLAMA] = original_provider


async def startup_design_parser_service() -> None:
    """Initialize parser dependencies."""

    await _ORCHESTRATOR.startup()


async def shutdown_design_parser_service() -> None:
    """Shutdown parser dependencies."""

    await _ORCHESTRATOR.shutdown()


async def parse_design_prompt_with_metadata(
    *,
    prompt: str,
    model_choice: ParseDesignModel,
    model_id: str | None = None,
    recovery_mode: RecoveryMode = RecoveryMode.STRICT,
    request_id: str = "",
) -> ParseOrchestrationResult:
    """Parse user prompt and return provider metadata with validated payload."""

    # Bridge the new public ollama_cloud provider onto the existing internal qwen-cloud slot.
    resolved_cloud_model_id = _resolve_cloud_model_id(model_choice, model_id)
    if resolved_cloud_model_id is not None:
        return await _parse_with_cloud_provider_override(
            prompt=prompt,
            model_choice=model_choice,
            recovery_mode=recovery_mode,
            request_id=request_id,
            model_id=resolved_cloud_model_id,
        )

    resolved_local_ollama_model_id = _clean_model_id(model_id)
    if model_choice == ParseDesignModel.OLLAMA and resolved_local_ollama_model_id not in {None, OLLAMA_MODEL_ID}:
        return await _parse_with_ollama_provider_override(
            prompt=prompt,
            recovery_mode=recovery_mode,
            request_id=request_id,
            model_id=resolved_local_ollama_model_id,
        )

    return await _ORCHESTRATOR.parse(
        prompt=prompt,
        model_choice=model_choice,
        recovery_mode=recovery_mode,
        request_id=request_id,
    )


async def parse_design_prompt(
    *,
    prompt: str,
    model_choice: ParseDesignModel,
    model_id: str | None = None,
    recovery_mode: RecoveryMode = RecoveryMode.STRICT,
    request_id: str = "",
) -> tuple[str, dict]:
    """Backward-compatible parse API."""

    result = await parse_design_prompt_with_metadata(
        prompt=prompt,
        model_choice=model_choice,
        model_id=model_id,
        recovery_mode=recovery_mode,
        request_id=request_id,
    )
    return result.model_used, result.data
