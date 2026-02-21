"""Facade for design parser orchestration."""

from __future__ import annotations

from app.models.design_parser import ParseDesignModel, RecoveryMode
from app.services.design_parser import (
    DesignParseOrchestrator,
    ParseDesignServiceError,
    ParseOrchestrationResult,
)

_ORCHESTRATOR = DesignParseOrchestrator()


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
    recovery_mode: RecoveryMode = RecoveryMode.STRICT,
    request_id: str = "",
) -> ParseOrchestrationResult:
    """Parse user prompt and return provider metadata with validated payload."""

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
    recovery_mode: RecoveryMode = RecoveryMode.STRICT,
    request_id: str = "",
) -> tuple[str, dict]:
    """Backward-compatible parse API."""

    result = await parse_design_prompt_with_metadata(
        prompt=prompt,
        model_choice=model_choice,
        recovery_mode=recovery_mode,
        request_id=request_id,
    )
    return result.model_used, result.data

