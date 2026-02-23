"""Thin orchestration layer for parse-design service flow."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from pydantic import ValidationError

from app.core.logging import get_logger
from app.models.design_parser import ParseDesignModel, RecoveryMode
from app.services.design_parser.config import ENABLE_OLLAMA_TO_HF_FAILOVER
from app.services.design_parser.extracted_intent_validator import ExtractedIntentValidator
from app.services.design_parser.errors import ParseDesignServiceError
from app.services.design_parser.intent_validator import IntentValidator
from app.services.design_parser.layout_planner import (
    DeterministicLayoutPlanner,
    LayoutPlanningError,
)
from app.services.design_parser.layout_validator import LayoutValidator
from app.services.design_parser.opening_planner import DeterministicOpeningPlanner
from app.services.design_parser.output_parser import OutputParser
from app.services.design_parser.prompt_compiler import PromptCompiler
from app.services.design_parser.prompt_program_deriver import PromptProgramDeriver
from app.services.design_parser.provider_client import (
    HuggingFaceProviderClient,
    OllamaProviderClient,
    ProviderClient,
)
from app.services.design_parser.rule_violation import RuleViolationError

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
    metrics: dict[str, Any]


class DesignParseOrchestrator:
    """Coordinates prompt compile, generation, parsing, and validation."""

    def __init__(self) -> None:
        self._prompt_compiler = PromptCompiler()
        self._output_parser = OutputParser()
        self._extracted_intent_validator = ExtractedIntentValidator()
        self._prompt_program_deriver = PromptProgramDeriver()
        self._layout_planner = DeterministicLayoutPlanner()
        self._opening_planner = DeterministicOpeningPlanner()
        self._layout_validator = LayoutValidator()
        self._intent_validator = IntentValidator()

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
        _ = recovery_mode  # Kept for API compatibility; silent repair paths are disabled.
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

        try:
            validated_extracted_payload = self._extracted_intent_validator.validate(parsed_payload)
        except ValidationError as exc:
            raise ParseDesignServiceError(
                code="INVALID_STRUCTURED_OUTPUT",
                message="Model output failed extraction schema validation",
                status_code=422,
                model_used=provider.model_id,
                provider_used=provider.model_id,
                failover_triggered=failover_triggered,
                details=self._extracted_intent_validator.to_error_details(exc),
            ) from exc

        try:
            effective_extracted_payload = validated_extracted_payload
            selected_topology = "unknown"
            try:
                candidate_payload, planner_meta = self._layout_planner.plan_with_metadata(effective_extracted_payload)
                selected_topology = str(planner_meta.get("selected_topology", "unknown"))
            except LayoutPlanningError as primary_layout_exc:
                derived_extracted_payload = self._prompt_program_deriver.derive(
                    prompt=prompt,
                    extracted_payload=effective_extracted_payload,
                )
                if derived_extracted_payload != effective_extracted_payload:
                    logger.warning(
                        "request_id=%s provider=%s event=program_derivation_retry reason=%s",
                        request_id,
                        provider.model_id,
                        str(primary_layout_exc),
                    )
                    effective_extracted_payload = derived_extracted_payload
                    candidate_payload, planner_meta = self._layout_planner.plan_with_metadata(effective_extracted_payload)
                    selected_topology = str(planner_meta.get("selected_topology", "unknown"))
                else:
                    raise

            candidate_payload = self._opening_planner.plan(
                extracted_payload=effective_extracted_payload,
                layout_payload=candidate_payload,
            )
            validated_extracted_payload = effective_extracted_payload
        except LayoutPlanningError as exc:
            raise ParseDesignServiceError(
                code="LAYOUT_PLANNING_FAILED",
                message="Deterministic layout planning failed",
                status_code=422,
                model_used=provider.model_id,
                provider_used=provider.model_id,
                failover_triggered=failover_triggered,
                details=[str(exc)],
            ) from exc
        except RuleViolationError as exc:
            raise ParseDesignServiceError(
                code=exc.code,
                message="Deterministic opening/layout rule failed",
                status_code=422,
                model_used=provider.model_id,
                provider_used=provider.model_id,
                failover_triggered=failover_triggered,
                reason=exc.reason,
                violated_rule=exc.violated_rule,
                room=exc.room,
                details=[exc.to_detail_message()],
            ) from exc

        try:
            validated_payload = self._intent_validator.validate(candidate_payload)
        except ValidationError as exc:
            raise ParseDesignServiceError(
                code="INVALID_STRUCTURED_OUTPUT",
                message="Deterministic layout failed schema validation",
                status_code=422,
                model_used=provider.model_id,
                provider_used=provider.model_id,
                failover_triggered=failover_triggered,
                details=self._intent_validator.to_error_details(exc),
            ) from exc

        try:
            metrics = self._layout_validator.validate(
                extracted_payload=validated_extracted_payload,
                planned_payload=validated_payload,
                selected_topology=selected_topology,
            )
        except RuleViolationError as exc:
            if exc.code == "LAYOUT_EFFICIENCY_FAILED":
                try:
                    candidate_payload, planner_meta = self._layout_planner.plan_with_metadata(
                        validated_extracted_payload,
                        optimize_efficiency=True,
                    )
                    selected_topology = str(planner_meta.get("selected_topology", selected_topology))
                    candidate_payload = self._opening_planner.plan(
                        extracted_payload=validated_extracted_payload,
                        layout_payload=candidate_payload,
                    )
                    validated_payload = self._intent_validator.validate(candidate_payload)
                    metrics = self._layout_validator.validate(
                        extracted_payload=validated_extracted_payload,
                        planned_payload=validated_payload,
                        selected_topology=selected_topology,
                    )
                    exc = None
                except (LayoutPlanningError, ValidationError, RuleViolationError) as rebalance_exc:
                    if isinstance(rebalance_exc, RuleViolationError):
                        exc = rebalance_exc
                    else:
                        raise ParseDesignServiceError(
                            code="LAYOUT_PLANNING_FAILED",
                            message="Deterministic layout planning failed",
                            status_code=422,
                            model_used=provider.model_id,
                            provider_used=provider.model_id,
                            failover_triggered=failover_triggered,
                            details=[str(rebalance_exc)],
                        ) from rebalance_exc

            if exc is not None:
                raise ParseDesignServiceError(
                    code=exc.code,
                    message="Deterministic layout failed semantic validation",
                    status_code=422,
                    model_used=provider.model_id,
                    provider_used=provider.model_id,
                    failover_triggered=failover_triggered,
                    reason=exc.reason,
                    violated_rule=exc.violated_rule,
                    room=exc.room,
                    details=[exc.to_detail_message()],
                ) from exc

        except ValueError as exc:
            raise ParseDesignServiceError(
                code="LAYOUT_VALIDATION_FAILED",
                message="Deterministic layout failed semantic validation",
                status_code=422,
                model_used=provider.model_id,
                provider_used=provider.model_id,
                failover_triggered=failover_triggered,
                details=[str(exc)],
            ) from exc

        return ParseOrchestrationResult(
            model_used=provider.model_id,
            provider_used=provider.model_id,
            failover_triggered=failover_triggered,
            data=validated_payload,
            metrics={
                "area_balance": metrics.area_balance,
                "zoning": metrics.zoning,
                "circulation": metrics.circulation,
                "daylight": metrics.daylight,
                "structural": metrics.structural,
                "furniture": metrics.furniture,
                "efficiency": metrics.efficiency,
                "total_score": metrics.total_score,
                "selected_topology": metrics.selected_topology,
            },
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
