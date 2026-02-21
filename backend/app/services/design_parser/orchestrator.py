"""Thin orchestration layer for parse-design service flow."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from pydantic import ValidationError

from app.core.logging import get_logger
from app.models.design_parser import ParseDesignModel, RecoveryMode
from app.services.design_parser.config import ENABLE_OLLAMA_TO_HF_FAILOVER
from app.services.design_parser.errors import ParseDesignServiceError
from app.services.design_parser.intent_validator import IntentValidator
from app.services.design_parser.output_parser import OutputParser
from app.services.design_parser.prompt_compiler import PromptCompiler
from app.services.design_parser.provider_client import (
    HuggingFaceProviderClient,
    OllamaProviderClient,
    ProviderClient,
)
from app.services.design_parser.recovery_policy import RecoveryPolicy

logger = get_logger(__name__)

ARABIC_CHAR_RE = re.compile(r"[\u0600-\u06FF]")
LATIN_CHAR_RE = re.compile(r"[A-Za-z]")
FAILOVER_CODES = {
    "OLLAMA_TIMEOUT",
    "OLLAMA_CONNECTION_ERROR",
    "OLLAMA_HTTP_ERROR",
    "OLLAMA_EMPTY_OUTPUT",
    "OLLAMA_INVALID_RESPONSE",
}


@dataclass
class ParseOrchestrationResult:
    model_used: str
    provider_used: str
    failover_triggered: bool
    data: dict[str, Any]


class DesignParseOrchestrator:
    """Coordinates prompt compile, generation, parsing, and validation."""

    def __init__(self) -> None:
        self._prompt_compiler = PromptCompiler()
        self._output_parser = OutputParser()
        self._intent_validator = IntentValidator()
        self._recovery_policy = RecoveryPolicy()

        self._providers: dict[ParseDesignModel, ProviderClient] = {
            ParseDesignModel.OLLAMA: OllamaProviderClient(),
            ParseDesignModel.HUGGINGFACE: HuggingFaceProviderClient(),
        }

    async def startup(self) -> None:
        await self._providers[ParseDesignModel.HUGGINGFACE].startup()

    async def shutdown(self) -> None:
        await self._providers[ParseDesignModel.HUGGINGFACE].shutdown()

    async def parse(
        self,
        *,
        prompt: str,
        model_choice: ParseDesignModel,
        recovery_mode: RecoveryMode,
        request_id: str,
    ) -> ParseOrchestrationResult:
        requested_provider = self._providers[model_choice]
        self._validate_prompt_language(prompt, requested_provider.model_id)
        compiled_prompt = self._prompt_compiler.compile(prompt)

        failover_triggered = False
        provider = requested_provider

        try:
            raw_output = await provider.generate(compiled_prompt, request_id=request_id)
        except ParseDesignServiceError as primary_exc:
            if (
                model_choice == ParseDesignModel.OLLAMA
                and ENABLE_OLLAMA_TO_HF_FAILOVER
                and primary_exc.code in FAILOVER_CODES
            ):
                failover_triggered = True
                provider = self._providers[ParseDesignModel.HUGGINGFACE]
                logger.warning(
                    "request_id=%s provider=%s event=failover reason=%s",
                    request_id,
                    primary_exc.provider_used,
                    primary_exc.code,
                )
                try:
                    raw_output = await provider.generate(compiled_prompt, request_id=request_id)
                except ParseDesignServiceError as failover_exc:
                    failover_exc.failover_triggered = True
                    failover_exc.details = primary_exc.details + failover_exc.details
                    raise failover_exc from failover_exc
            else:
                raise primary_exc from primary_exc

        try:
            parsed_payload = self._output_parser.parse(raw_output)
        except ValueError as exc:
            if recovery_mode == RecoveryMode.REPAIR:
                try:
                    parsed_payload = self._output_parser.parse_permissive(raw_output)
                    logger.warning(
                        "request_id=%s provider=%s event=json_repair_fallback reason=%s",
                        request_id,
                        provider.model_id,
                        str(exc),
                    )
                except ValueError:
                    logger.warning(
                        "request_id=%s provider=%s event=json_rejected reason=%s",
                        request_id,
                        provider.model_id,
                        str(exc),
                    )
                    raise ParseDesignServiceError(
                        code="INVALID_JSON_OUTPUT",
                        message="Model output is not strict JSON",
                        status_code=502,
                        model_used=provider.model_id,
                        provider_used=provider.model_id,
                        failover_triggered=failover_triggered,
                        details=[str(exc)],
                    ) from exc
            else:
                logger.warning(
                    "request_id=%s provider=%s event=json_rejected reason=%s",
                    request_id,
                    provider.model_id,
                    str(exc),
                )
                raise ParseDesignServiceError(
                    code="INVALID_JSON_OUTPUT",
                    message="Model output is not strict JSON",
                    status_code=502,
                    model_used=provider.model_id,
                    provider_used=provider.model_id,
                    failover_triggered=failover_triggered,
                    details=[str(exc)],
                ) from exc
        except Exception as exc:
            logger.warning(
                "request_id=%s provider=%s event=json_rejected reason=%s",
                request_id,
                provider.model_id,
                str(exc),
            )
            raise ParseDesignServiceError(
                code="INVALID_JSON_OUTPUT",
                message="Model output is not strict JSON",
                status_code=502,
                model_used=provider.model_id,
                provider_used=provider.model_id,
                failover_triggered=failover_triggered,
                details=[str(exc)],
            ) from exc

        candidate_payload = self._recovery_policy.apply(parsed_payload, prompt, recovery_mode)
        try:
            validated_payload = self._intent_validator.validate(candidate_payload)
        except ValidationError as exc:
            if recovery_mode == RecoveryMode.REPAIR:
                try:
                    synthesized_payload = self._recovery_policy.apply({}, prompt, RecoveryMode.REPAIR)
                    validated_payload = self._intent_validator.validate(synthesized_payload)
                    logger.warning(
                        "request_id=%s provider=%s event=repair_synthesized_fallback reason=%s",
                        request_id,
                        provider.model_id,
                        self._intent_validator.to_error_details(exc)[0] if exc.errors() else "validation_error",
                    )
                    return ParseOrchestrationResult(
                        model_used=provider.model_id,
                        provider_used=provider.model_id,
                        failover_triggered=failover_triggered,
                        data=validated_payload,
                    )
                except ValidationError:
                    pass
            raise ParseDesignServiceError(
                code="INVALID_STRUCTURED_OUTPUT",
                message="Model output failed schema validation",
                status_code=422,
                model_used=provider.model_id,
                provider_used=provider.model_id,
                failover_triggered=failover_triggered,
                details=self._intent_validator.to_error_details(exc),
            ) from exc

        return ParseOrchestrationResult(
            model_used=provider.model_id,
            provider_used=provider.model_id,
            failover_triggered=failover_triggered,
            data=validated_payload,
        )

    @staticmethod
    def _validate_prompt_language(prompt: str, model_used: str) -> None:
        text = prompt.strip()
        if ARABIC_CHAR_RE.search(text):
            raise ParseDesignServiceError(
                code="PROMPT_ENGLISH_ONLY",
                message="Prompt must be English only. Arabic prompts are currently disabled.",
                status_code=400,
                model_used=model_used,
                provider_used=model_used,
                details=["Use English prompt text only."],
            )
        if not LATIN_CHAR_RE.search(text):
            raise ParseDesignServiceError(
                code="PROMPT_ENGLISH_ONLY",
                message="Prompt must contain English text.",
                status_code=400,
                model_used=model_used,
                provider_used=model_used,
                details=["Use alphabetic English prompt text."],
            )
