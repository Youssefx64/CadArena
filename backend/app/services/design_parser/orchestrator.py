"""Thin orchestration layer for parse-design service flow."""

from __future__ import annotations

import json
import math
import re
import unicodedata
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any

from pydantic import ValidationError

from app.core.logging import get_logger
from app.models.design_parser import ParseDesignModel, RecoveryMode
from app.services.design_parser.config import (
    ENABLE_OLLAMA_TO_HF_FAILOVER,
    ENABLE_QWEN_QUALITY_GUARD,
    ENABLE_QWEN_TO_HF_FAILOVER,
    QUALITY_GUARD_MIN_TOTAL_SCORE,
    STRICT_MODEL_SELECTION,
)
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
    QwenCloudProviderClient,
)
from app.services.design_parser.rule_violation import RuleViolationError
from app.utils.json_extraction import (
    extract_json_object_with_keys,
    extract_json_object_with_keys_permissive,
)

logger = get_logger(__name__)

ARABIC_CHAR_RE = re.compile(r"[\u0600-\u06FF]")
LATIN_CHAR_RE = re.compile(r"[A-Za-z]")
SELF_REVIEW_KEYS = {"passed", "issues", "corrected_output"}
SELF_REVIEW_ALLOWED_ROOM_TYPES = {"living", "bedroom", "kitchen", "bathroom", "corridor", "stairs"}
SELF_REVIEW_MIN_DIMENSION_M = 1.5
SELF_REVIEW_MAX_DIMENSION_M = 30.0
SELF_REVIEW_MIN_AREA_M2 = 20.0
SELF_REVIEW_MAX_AREA_M2 = 1000.0
EXTRACTION_TOP_LEVEL_KEYS = {"boundary", "room_program", "constraints"}
# Keep renderer furniture hints request-scoped so concurrent parses do not leak room presets across users.
_RENDER_FURNITURE_PRESETS: ContextVar[dict[str, str] | None] = ContextVar(
    "render_furniture_presets",
    default=None,
)
FAILOVER_CODES = {
    "OLLAMA_TIMEOUT",
    "OLLAMA_CONNECTION_ERROR",
    "OLLAMA_HTTP_ERROR",
    "OLLAMA_EMPTY_OUTPUT",
    "OLLAMA_INVALID_RESPONSE",
    "QWEN_CLOUD_TIMEOUT",
    "QWEN_CLOUD_CONNECTION_ERROR",
    "QWEN_CLOUD_HTTP_ERROR",
    "QWEN_CLOUD_EMPTY_OUTPUT",
    "QWEN_CLOUD_INVALID_RESPONSE",
}

_ARABIC_ARCH_KEYWORDS: dict[str, str] = {
    # Room types
    "ريسبشن وسفرة": "reception and dining room",
    "ثلاث غرف نوم": "3 bedrooms",
    "ثلاثة غرف نوم": "3 bedrooms",
    "ثلاث أوض نوم": "3 bedrooms",
    "تلات أوض نوم": "3 bedrooms",
    "تلاتة أوض نوم": "3 bedrooms",
    "أربع غرف نوم": "4 bedrooms",
    "أربعة غرف نوم": "4 bedrooms",
    "أربع أوض نوم": "4 bedrooms",
    "خمس غرف نوم": "5 bedrooms",
    "غرفة نوم واحدة": "1 bedroom",
    "أوضة نوم واحدة": "1 bedroom",
    "أوضه نوم واحدة": "1 bedroom",
    "غرفتين نوم": "2 bedrooms",
    "أوضتين نوم": "2 bedrooms",
    "غرفة نوم": "bedroom",
    "غرف نوم": "bedrooms",
    "أوضة نوم": "bedroom",
    "أوض نوم": "bedrooms",
    "أوضه نوم": "bedroom",
    "ثلاثة حمامات": "3 bathrooms",
    "أربعة حمامات": "4 bathrooms",
    "غرفة واحدة": "1 room",
    "أوضة واحدة": "1 room",
    "أوضه واحدة": "1 room",
    "حمام واحد": "1 bathroom",
    "أوضتين": "2 rooms",
    "غرفة": "room",
    "غرف": "rooms",
    "أوضة": "room",
    "أوضه": "room",
    "أوض": "rooms",
    "صالة": "living room",
    "صاله": "living room",
    "صالون": "living room",
    "غرفة معيشة": "living room",
    "مطبخ": "kitchen",
    "حمام": "bathroom",
    "حمامين": "2 bathrooms",
    "حمامات": "bathrooms",
    "دورة مياه": "bathroom",
    "ممر": "corridor",
    "كوريدور": "corridor",
    "مدخل": "entrance",
    "غرفة جلوس": "living room",
    "ريسبشن": "reception",
    # Sizes and dimensions
    "متر ونص": "1.5 meters",
    "متر مربع": "square meters",
    "متر": "meters",
    "أمتار": "meters",
    "طول": "length",
    "عرض": "width",
    # Numbers (Arabic-Indic digits)
    "٠": "0",
    "١": "1",
    "٢": "2",
    "٣": "3",
    "٤": "4",
    "٥": "5",
    "٦": "6",
    "٧": "7",
    "٨": "8",
    "٩": "9",
    # Common descriptors
    "كبيرة": "large",
    "كبير": "large",
    "صغيرة": "small",
    "صغير": "small",
    "مستطيل": "rectangular",
    "مربع": "square",
    "شقة": "apartment",
    "بيت": "house",
    "فيلا": "villa",
    "أدوار": "floors",
    "دور": "floor",
    "بمساحة": "with area",
    "مساحة": "area",
    "تصميم": "design",
    "صمم": "design",
    "أريد": "I want",
    "عاوز": "I want",
    "عايز": "I want",
    "ابني": "build",
    "اعمل": "make",
    "إلى": "to",
    "على": "on",
    "مع": "with",
    "من": "from",
    "في": "in",
    "واحد ": "1 ",
    "واحدة ": "1 ",
    "اثنين ": "2 ",
    "اثنان ": "2 ",
    "ثلاثة ": "3 ",
    "ثلاث ": "3 ",
    "تلاتة ": "3 ",
    "تلات ": "3 ",
    "أربعة ": "4 ",
    "أربع ": "4 ",
    "خمسة ": "5 ",
    "خمس ": "5 ",
    "ستة ": "6 ",
    "ست ": "6 ",
    "نص": "half",
    "وصف": "half",
    "و": "and",
}


def _normalize_prompt_for_extraction(prompt: str) -> str:
    """
    Normalize an architectural prompt for LLM extraction.

    If the prompt contains Arabic characters:
      1. Replace known architectural keywords with English
      2. Replace Arabic-Indic numerals with ASCII digits
      3. Remove remaining Arabic characters (keep English parts)
      4. Add a structured English context wrapper

    If the prompt is already in English: return as-is.
    """

    normalized_prompt = unicodedata.normalize("NFKC", str(prompt or "")).strip()
    has_arabic = any("\u0600" <= ch <= "\u06ff" for ch in normalized_prompt)
    if not has_arabic:
        return normalized_prompt

    translated = normalized_prompt
    sorted_keywords = sorted(
        _ARABIC_ARCH_KEYWORDS.items(),
        key=lambda item: len(item[0]),
        reverse=True,
    )
    for arabic, english in sorted_keywords:
        translated = translated.replace(arabic, f" {english} ")

    translated = re.sub(r"[\u0600-\u06ff\u0750-\u077f]+", " ", translated)
    translated = re.sub(r"\s+", " ", translated).strip()

    if not translated:
        return "Design a standard apartment with living room, bedroom, kitchen, and bathroom"

    return (
        f"Design an architectural floor plan with: {translated}. "
        "Generate a complete room layout with all rooms."
    )


@dataclass
class ParseOrchestrationResult:
    model_used: str
    provider_used: str
    failover_triggered: bool
    self_review_triggered: bool
    data: dict[str, Any]
    metrics: dict[str, Any]


@dataclass
class _SelfReviewResult:
    passed: bool
    issues: list[str]
    corrected_output: dict[str, Any]


# The DXF renderer reads these request-local room presets after planning so it can honor `"furniture": "default"` or `"none"`.
def get_render_furniture_preset(room_name: str) -> str | None:
    presets = _RENDER_FURNITURE_PRESETS.get()
    if presets is None:
        return None
    return presets.get(room_name.strip())


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
            ParseDesignModel.QWEN_CLOUD: QwenCloudProviderClient(),
        }

    async def startup(self) -> None:
        await self._providers[ParseDesignModel.HUGGINGFACE].startup()

    async def shutdown(self) -> None:
        await self._providers[ParseDesignModel.HUGGINGFACE].shutdown()

    def _select_review_provider(
        self,
        *,
        requested_model: ParseDesignModel,
        generation_provider: ProviderClient,
    ) -> ProviderClient:
        """Pick the provider that performs self-review quality checks."""

        if requested_model == ParseDesignModel.QWEN_CLOUD:
            return self._providers[ParseDesignModel.HUGGINGFACE]
        return generation_provider

    async def parse(
        self,
        *,
        prompt: str,
        model_choice: ParseDesignModel,
        recovery_mode: RecoveryMode,
        request_id: str,
        _quality_guard_retry: bool = False,
        _quality_guard_origin_model: ParseDesignModel | None = None,
    ) -> ParseOrchestrationResult:
        requested_provider = self._providers[model_choice]
        prompt = _normalize_prompt_for_extraction(prompt)
        self._validate_prompt_language(prompt, requested_provider.model_id)
        compiled_prompt = self._prompt_compiler.compile(prompt)
        quality_guard_model = _quality_guard_origin_model or model_choice

        failover_triggered = False
        provider = requested_provider

        try:
            raw_output = await provider.generate(compiled_prompt, request_id=request_id)
        except ParseDesignServiceError as primary_exc:
            if (
                model_choice in {ParseDesignModel.OLLAMA, ParseDesignModel.QWEN_CLOUD}
                and not STRICT_MODEL_SELECTION
                and (
                    (model_choice == ParseDesignModel.OLLAMA and ENABLE_OLLAMA_TO_HF_FAILOVER)
                    or (model_choice == ParseDesignModel.QWEN_CLOUD and ENABLE_QWEN_TO_HF_FAILOVER)
                )
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

        parsed_payload = await self._parse_initial_output_with_repair(
            raw_output=raw_output,
            prompt=prompt,
            recovery_mode=recovery_mode,
            provider=provider,
            request_id=request_id,
            failover_triggered=failover_triggered,
        )

        # Run a second model pass as a strict self-review before the deterministic planner sees the payload.
        review_provider = self._select_review_provider(
            requested_model=model_choice,
            generation_provider=provider,
        )
        reviewed_payload, self_review_triggered = await self._run_self_review(
            parsed_payload=parsed_payload,
            provider=review_provider,
            request_id=request_id,
            failover_triggered=failover_triggered,
        )
        # Keep furniture directives for DXF rendering, but strip them before strict schema validation because the public contract is unchanged.
        reviewed_payload_with_furniture = self._apply_default_furniture_markers(reviewed_payload)
        parsed_payload = self._strip_room_program_furniture(reviewed_payload_with_furniture)

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

        # QUALITY FIX: validate requested numeric room counts before deterministic layout planning.
        quality_violations = self._validate_room_count(
            extracted=validated_extracted_payload,
            original_prompt=prompt,
        )
        if quality_violations:
            logger.warning(
                "request_id=%s provider=%s event=room_count_violations violations=%s",
                request_id,
                provider.model_id,
                quality_violations,
            )
            (
                validated_extracted_payload,
                reviewed_payload_with_furniture,
                correction_self_review_triggered,
            ) = await self._run_quality_correction_retry(
                original_prompt=prompt,
                recovery_mode=recovery_mode,
                provider=provider,
                request_id=request_id,
                failover_triggered=failover_triggered,
                violations=quality_violations,
            )
            self_review_triggered = self_review_triggered or correction_self_review_triggered

        used_emergency_layout = False
        selected_topology = "unknown"
        metrics_payload: dict[str, Any] | None = None

        try:
            effective_extracted_payload = validated_extracted_payload
            candidate_payload: dict[str, Any] | None = None
            planner_meta: dict[str, Any] = {}
            layout_failures: list[str] = []
            try:
                candidate_payload, planner_meta = self._layout_planner.plan_with_metadata(effective_extracted_payload)
            except LayoutPlanningError as primary_layout_exc:
                layout_failures.append(str(primary_layout_exc))
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
                    # Reproject any self-review furniture directives onto the retried program so the renderer still sees `"default"`/`"none"` hints.
                    reviewed_payload_with_furniture = self._project_furniture_preferences(
                        source_payload=reviewed_payload_with_furniture,
                        target_payload=effective_extracted_payload,
                    )
                    try:
                        candidate_payload, planner_meta = self._layout_planner.plan_with_metadata(effective_extracted_payload)
                    except LayoutPlanningError as derived_layout_exc:
                        layout_failures.append(str(derived_layout_exc))

                if candidate_payload is None and recovery_mode == RecoveryMode.REPAIR:
                    logger.warning(
                        "request_id=%s provider=%s event=layout_emergency_fallback reason=%s",
                        request_id,
                        provider.model_id,
                        " | ".join(layout_failures),
                    )
                    try:
                        emergency_extracted_payload = self._build_layout_emergency_payload(
                            prompt=prompt,
                            extracted_payload=effective_extracted_payload,
                        )
                        emergency_extracted_payload = self._extracted_intent_validator.validate(
                            emergency_extracted_payload
                        )
                    except ValidationError as emergency_validation_exc:
                        layout_failures.append(
                            "emergency_payload_validation: "
                            + "; ".join(
                                self._extracted_intent_validator.to_error_details(
                                    emergency_validation_exc
                                )
                            )
                        )
                    except Exception as emergency_exc:
                        layout_failures.append(f"emergency_payload_build: {emergency_exc}")
                    else:
                        effective_extracted_payload = emergency_extracted_payload
                        reviewed_payload_with_furniture = self._project_furniture_preferences(
                            source_payload=reviewed_payload_with_furniture,
                            target_payload=effective_extracted_payload,
                        )
                        try:
                            candidate_payload, planner_meta = self._layout_planner.plan_with_metadata(
                                effective_extracted_payload,
                                optimize_efficiency=True,
                            )
                        except LayoutPlanningError as emergency_layout_exc:
                            layout_failures.append(str(emergency_layout_exc))

                if candidate_payload is None and recovery_mode == RecoveryMode.REPAIR:
                    logger.warning(
                        "request_id=%s provider=%s event=layout_geometry_emergency_fallback reason=%s",
                        request_id,
                        provider.model_id,
                        " | ".join(layout_failures) if layout_failures else "planner produced no candidate",
                    )
                    candidate_payload = self._build_emergency_layout_payload(effective_extracted_payload)
                    planner_meta = {"selected_topology": "emergency_grid_fallback"}
                    used_emergency_layout = True

                if candidate_payload is None:
                    raise LayoutPlanningError(" | ".join(layout_failures))

            selected_topology = str(planner_meta.get("selected_topology", "unknown"))

            if not used_emergency_layout:
                try:
                    candidate_payload = self._opening_planner.plan(
                        extracted_payload=effective_extracted_payload,
                        layout_payload=candidate_payload,
                    )
                except RuleViolationError as opening_exc:
                    if recovery_mode != RecoveryMode.REPAIR:
                        raise opening_exc from opening_exc
                    logger.warning(
                        "request_id=%s provider=%s event=opening_geometry_emergency_fallback reason=%s",
                        request_id,
                        provider.model_id,
                        opening_exc.to_detail_message(),
                    )
                    candidate_payload = self._build_emergency_layout_payload(effective_extracted_payload)
                    selected_topology = "emergency_grid_fallback"
                    used_emergency_layout = True
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
            if recovery_mode == RecoveryMode.REPAIR and not used_emergency_layout:
                logger.warning(
                    "request_id=%s provider=%s event=intent_geometry_emergency_fallback reason=%s",
                    request_id,
                    provider.model_id,
                    "; ".join(self._intent_validator.to_error_details(exc)),
                )
                candidate_payload = self._build_emergency_layout_payload(validated_extracted_payload)
                selected_topology = "emergency_grid_fallback"
                used_emergency_layout = True
                try:
                    validated_payload = self._intent_validator.validate(candidate_payload)
                except ValidationError as emergency_exc:
                    raise ParseDesignServiceError(
                        code="INVALID_STRUCTURED_OUTPUT",
                        message="Deterministic layout failed schema validation",
                        status_code=422,
                        model_used=provider.model_id,
                        provider_used=provider.model_id,
                        failover_triggered=failover_triggered,
                        details=self._intent_validator.to_error_details(emergency_exc),
                    ) from emergency_exc
            else:
                raise ParseDesignServiceError(
                    code="INVALID_STRUCTURED_OUTPUT",
                    message="Deterministic layout failed schema validation",
                    status_code=422,
                    model_used=provider.model_id,
                    provider_used=provider.model_id,
                    failover_triggered=failover_triggered,
                    details=self._intent_validator.to_error_details(exc),
                ) from exc

        if used_emergency_layout:
            metrics_payload = self._build_emergency_metrics(selected_topology)
        else:
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

                if exc is not None and recovery_mode == RecoveryMode.REPAIR:
                    logger.warning(
                        "request_id=%s provider=%s event=validation_geometry_emergency_fallback reason=%s",
                        request_id,
                        provider.model_id,
                        exc.to_detail_message(),
                    )
                    candidate_payload = self._build_emergency_layout_payload(validated_extracted_payload)
                    selected_topology = "emergency_grid_fallback"
                    used_emergency_layout = True
                    validated_payload = self._intent_validator.validate(candidate_payload)
                    metrics_payload = self._build_emergency_metrics(selected_topology)
                    exc = None

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
                if recovery_mode == RecoveryMode.REPAIR:
                    logger.warning(
                        "request_id=%s provider=%s event=validator_geometry_emergency_fallback reason=%s",
                        request_id,
                        provider.model_id,
                        str(exc),
                    )
                    candidate_payload = self._build_emergency_layout_payload(validated_extracted_payload)
                    selected_topology = "emergency_grid_fallback"
                    used_emergency_layout = True
                    validated_payload = self._intent_validator.validate(candidate_payload)
                    metrics_payload = self._build_emergency_metrics(selected_topology)
                else:
                    raise ParseDesignServiceError(
                        code="LAYOUT_VALIDATION_FAILED",
                        message="Deterministic layout failed semantic validation",
                        status_code=422,
                        model_used=provider.model_id,
                        provider_used=provider.model_id,
                        failover_triggered=failover_triggered,
                        details=[str(exc)],
                    ) from exc

            if metrics_payload is None:
                metrics_payload = {
                    "area_balance": metrics.area_balance,
                    "zoning": metrics.zoning,
                    "circulation": metrics.circulation,
                    "daylight": metrics.daylight,
                    "structural": metrics.structural,
                    "furniture": metrics.furniture,
                    "efficiency": metrics.efficiency,
                    "total_score": metrics.total_score,
                    "selected_topology": metrics.selected_topology,
                }

        quality_guard_issues = self._collect_quality_guard_issues(
            quality_guard_model=quality_guard_model,
            used_emergency_layout=used_emergency_layout,
            planned_payload=validated_payload,
            metrics_payload=metrics_payload,
        )
        if (
            quality_guard_issues
            and recovery_mode == RecoveryMode.REPAIR
            and not _quality_guard_retry
            and quality_guard_model == ParseDesignModel.QWEN_CLOUD
            and ENABLE_QWEN_QUALITY_GUARD
            and not STRICT_MODEL_SELECTION
        ):
            logger.warning(
                "request_id=%s provider=%s event=quality_guard_retry issues=%s",
                request_id,
                provider.model_id,
                quality_guard_issues,
            )
            quality_retry_prompt = self._build_quality_guard_retry_prompt(
                prompt=prompt,
                issues=quality_guard_issues,
            )
            quality_retry_result = await self.parse(
                prompt=quality_retry_prompt,
                model_choice=ParseDesignModel.HUGGINGFACE,
                recovery_mode=recovery_mode,
                request_id=f"{request_id}_quality_guard",
                _quality_guard_retry=True,
                _quality_guard_origin_model=quality_guard_model,
            )
            return ParseOrchestrationResult(
                model_used=quality_retry_result.model_used,
                provider_used=quality_retry_result.provider_used,
                failover_triggered=quality_retry_result.failover_triggered or failover_triggered,
                self_review_triggered=quality_retry_result.self_review_triggered or self_review_triggered,
                data=quality_retry_result.data,
                metrics=quality_retry_result.metrics,
            )
        if (
            quality_guard_issues
            and quality_guard_model == ParseDesignModel.QWEN_CLOUD
            and ENABLE_QWEN_QUALITY_GUARD
            and STRICT_MODEL_SELECTION
        ):
            raise ParseDesignServiceError(
                code="LAYOUT_QUALITY_REJECTED",
                message="Selected model output failed quality guard under strict model selection",
                status_code=422,
                model_used=provider.model_id,
                provider_used=provider.model_id,
                failover_triggered=failover_triggered,
                details=quality_guard_issues,
            )
        if (
            quality_guard_issues
            and _quality_guard_retry
            and quality_guard_model == ParseDesignModel.QWEN_CLOUD
            and ENABLE_QWEN_QUALITY_GUARD
        ):
            raise ParseDesignServiceError(
                code="LAYOUT_QUALITY_REJECTED",
                message="Generated layout did not pass quality guard checks",
                status_code=422,
                model_used=provider.model_id,
                provider_used=provider.model_id,
                failover_triggered=failover_triggered,
                details=quality_guard_issues,
            )

        # Publish request-scoped room presets only after planning succeeds so the DXF renderer sees the final room program for this request.
        self._publish_render_furniture_presets(
            self._project_furniture_preferences(
                source_payload=reviewed_payload_with_furniture,
                target_payload=validated_extracted_payload,
            )
        )

        return ParseOrchestrationResult(
            model_used=provider.model_id,
            provider_used=provider.model_id,
            failover_triggered=failover_triggered,
            self_review_triggered=self_review_triggered,
            data=validated_payload,
            metrics=metrics_payload or self._build_emergency_metrics("emergency_grid_fallback"),
        )

    # Parse model extraction output with resilient fallback (strict -> permissive -> repair call) before failing.
    async def _parse_initial_output_with_repair(
        self,
        *,
        raw_output: str,
        prompt: str,
        recovery_mode: RecoveryMode,
        provider: ProviderClient,
        request_id: str,
        failover_triggered: bool,
    ) -> dict[str, Any]:
        errors: list[str] = []

        try:
            return self._output_parser.parse(raw_output)
        except Exception as exc:
            errors.append(f"strict_parse: {exc}")

        try:
            parsed_payload = extract_json_object_with_keys_permissive(
                raw_output,
                EXTRACTION_TOP_LEVEL_KEYS,
            )
        except ValueError as exc:
            errors.append(f"permissive_parse: {exc}")
        else:
            logger.warning(
                "request_id=%s provider=%s event=json_salvaged strategy=permissive reason=%s",
                request_id,
                provider.model_id,
                errors[-1],
            )
            return parsed_payload

        repair_prompt = self._build_json_repair_prompt(raw_output)
        try:
            repaired_output = await provider.generate(
                repair_prompt,
                request_id=f"{request_id}_json_repair",
            )
        except ParseDesignServiceError as exc:
            errors.append(f"repair_call: {exc.code} {exc.message}")
            self._raise_initial_json_error(
                provider=provider,
                failover_triggered=failover_triggered,
                request_id=request_id,
                errors=errors,
            )

        try:
            parsed_payload = self._output_parser.parse(repaired_output)
        except Exception as exc:
            errors.append(f"repair_strict_parse: {exc}")
        else:
            logger.warning(
                "request_id=%s provider=%s event=json_salvaged strategy=repair_strict",
                request_id,
                provider.model_id,
            )
            return parsed_payload

        try:
            parsed_payload = extract_json_object_with_keys_permissive(
                repaired_output,
                EXTRACTION_TOP_LEVEL_KEYS,
            )
        except ValueError as exc:
            errors.append(f"repair_permissive_parse: {exc}")
        else:
            logger.warning(
                "request_id=%s provider=%s event=json_salvaged strategy=repair_permissive",
                request_id,
                provider.model_id,
            )
            return parsed_payload

        if recovery_mode == RecoveryMode.REPAIR:
            try:
                prompt_fallback_payload = self._build_prompt_fallback_payload(prompt)
                parsed_payload = self._extracted_intent_validator.validate(prompt_fallback_payload)
            except ValidationError as exc:
                errors.append(
                    "prompt_fallback_validation: "
                    + "; ".join(self._extracted_intent_validator.to_error_details(exc))
                )
            except Exception as exc:
                errors.append(f"prompt_fallback: {exc}")
            else:
                logger.warning(
                    "request_id=%s provider=%s event=json_salvaged strategy=prompt_fallback",
                    request_id,
                    provider.model_id,
                )
                return parsed_payload

        self._raise_initial_json_error(
            provider=provider,
            failover_triggered=failover_triggered,
            request_id=request_id,
            errors=errors,
        )

    # Build a strict repair prompt that asks the same model/provider to normalize its previous output into pure JSON.
    @staticmethod
    def _build_json_repair_prompt(raw_output: str) -> str:
        trimmed_output = raw_output.strip()
        if len(trimmed_output) > 12000:
            trimmed_output = trimmed_output[:12000] + "\n...[truncated]"

        return (
            "You are a JSON repair assistant for architectural extraction output.\n"
            "Convert the content below into EXACTLY one valid JSON object.\n"
            "Do not output markdown, code fences, explanations, comments, or extra text.\n"
            "Required top-level keys (exactly): boundary, room_program, constraints.\n"
            "Do not invent unrelated fields.\n"
            "Input content:\n"
            f"{trimmed_output}\n"
        )

    # Build a deterministic extraction payload from prompt text as a last resort in repair mode.
    def _build_prompt_fallback_payload(self, prompt: str) -> dict[str, Any]:
        baseline_payload = {
            "boundary": {"width": 20.0, "height": 12.0},
            "room_program": [
                {"name": "Living Room", "room_type": "living", "count": 1},
                {"name": "Bedroom", "room_type": "bedroom", "count": 1},
                {"name": "Kitchen", "room_type": "kitchen", "count": 1},
                {"name": "Bathroom", "room_type": "bathroom", "count": 1},
            ],
            "constraints": {
                "notes": ["Generated from deterministic prompt fallback"],
                "adjacency_preferences": [],
            },
        }
        return self._prompt_program_deriver.derive(
            prompt=prompt,
            extracted_payload=baseline_payload,
        )

    # Build a compact, planner-friendly room program derived from boundary size for emergency layout recovery.
    def _build_layout_emergency_payload(
        self,
        *,
        prompt: str,
        extracted_payload: dict[str, Any],
    ) -> dict[str, Any]:
        derived = self._prompt_program_deriver.derive(
            prompt=prompt,
            extracted_payload=extracted_payload,
        )
        boundary = derived.get("boundary") if isinstance(derived.get("boundary"), dict) else {}
        width = float(boundary.get("width") or 20.0)
        height = float(boundary.get("height") or 12.0)
        footprint_area = max(width * height, 1.0)

        if footprint_area < 75.0:
            bedroom_count = 1
            bathroom_count = 1
        elif footprint_area < 140.0:
            bedroom_count = 2
            bathroom_count = 1
        else:
            bedroom_count = 3
            bathroom_count = 2

        source_program = derived.get("room_program")
        stairs_requested = "stairs" in prompt.lower()
        if isinstance(source_program, list):
            stairs_requested = stairs_requested or any(
                isinstance(item, dict)
                and str(item.get("room_type", "")).strip().lower() == "stairs"
                for item in source_program
            )

        room_program: list[dict[str, Any]] = [
            {"name": "Living Room", "room_type": "living", "count": 1},
            {"name": "Kitchen", "room_type": "kitchen", "count": 1},
            {"name": "Bedroom", "room_type": "bedroom", "count": bedroom_count},
            {"name": "Bathroom", "room_type": "bathroom", "count": bathroom_count},
        ]
        if stairs_requested and footprint_area >= 90.0:
            room_program.append({"name": "Stairs", "room_type": "stairs", "count": 1})

        return {
            "boundary": {"width": width, "height": height},
            "room_program": room_program,
            "constraints": {
                "notes": ["Emergency fallback program for feasible deterministic layout"],
                "adjacency_preferences": [],
            },
        }

    # Build a guaranteed non-overlapping fallback geometry when planner/opening stages keep failing in repair mode.
    def _build_emergency_layout_payload(self, extracted_payload: dict[str, Any]) -> dict[str, Any]:
        boundary = extracted_payload.get("boundary")
        width = self._positive_float(boundary.get("width")) if isinstance(boundary, dict) else None
        height = self._positive_float(boundary.get("height")) if isinstance(boundary, dict) else None
        width = width or 20.0
        height = height or 12.0

        room_program = extracted_payload.get("room_program")
        expanded_rooms = self._expand_room_program_for_emergency(room_program)
        if not expanded_rooms:
            expanded_rooms = [{"name": "Living Room", "room_type": "living"}]

        room_count = len(expanded_rooms)
        aspect = width / max(height, 1e-6)
        grid_cols = int(round(math.sqrt(room_count * max(aspect, 1e-6))))
        grid_cols = max(1, min(room_count, grid_cols))
        grid_rows = int(math.ceil(room_count / grid_cols))

        cell_width = width / grid_cols
        cell_height = height / grid_rows
        layout_rooms: list[dict[str, Any]] = []
        for index, room in enumerate(expanded_rooms):
            col = index % grid_cols
            row = index // grid_cols
            x0 = col * cell_width
            y0 = row * cell_height
            x1 = width if col == grid_cols - 1 else (col + 1) * cell_width
            y1 = height if row == grid_rows - 1 else (row + 1) * cell_height
            layout_rooms.append(
                {
                    "name": room["name"],
                    "room_type": room["room_type"],
                    "width": max(0.01, x1 - x0),
                    "height": max(0.01, y1 - y0),
                    "origin": {"x": x0, "y": y0},
                }
            )

        return {
            "boundary": {"width": width, "height": height},
            "rooms": layout_rooms,
            "walls": self._build_emergency_walls(layout_rooms),
            "openings": [],
        }

    # Expand room_program deterministically (respecting count + unique names) for emergency geometry generation.
    @staticmethod
    def _expand_room_program_for_emergency(room_program: Any) -> list[dict[str, str]]:
        if not isinstance(room_program, list):
            return []

        expanded: list[dict[str, str]] = []
        seen_names: set[str] = set()
        for raw_room in room_program:
            if not isinstance(raw_room, dict):
                continue
            base_name = str(raw_room.get("name", "")).strip() or "Room"
            room_type = str(raw_room.get("room_type", "")).strip().lower()
            if room_type not in SELF_REVIEW_ALLOWED_ROOM_TYPES:
                room_type = "living"
            count = raw_room.get("count", 1)
            room_count = count if isinstance(count, int) and count > 0 else 1

            for index in range(room_count):
                candidate_name = base_name if room_count == 1 else f"{base_name} {index + 1}"
                normalized_name = candidate_name
                dedupe = 2
                while normalized_name in seen_names:
                    normalized_name = f"{candidate_name} {dedupe}"
                    dedupe += 1
                seen_names.add(normalized_name)
                expanded.append({"name": normalized_name, "room_type": room_type})
        return expanded

    # Build four explicit wall segments per room so the fallback payload still matches ParsedDesignIntent schema.
    @staticmethod
    def _build_emergency_walls(rooms: list[dict[str, Any]]) -> list[dict[str, Any]]:
        walls: list[dict[str, Any]] = []
        for room in rooms:
            x0 = float(room["origin"]["x"])
            y0 = float(room["origin"]["y"])
            x1 = x0 + float(room["width"])
            y1 = y0 + float(room["height"])
            walls.extend(
                [
                    {
                        "room_name": room["name"],
                        "wall": "bottom",
                        "start": {"x": x0, "y": y0},
                        "end": {"x": x1, "y": y0},
                        "thickness": 0.2,
                    },
                    {
                        "room_name": room["name"],
                        "wall": "right",
                        "start": {"x": x1, "y": y0},
                        "end": {"x": x1, "y": y1},
                        "thickness": 0.2,
                    },
                    {
                        "room_name": room["name"],
                        "wall": "top",
                        "start": {"x": x1, "y": y1},
                        "end": {"x": x0, "y": y1},
                        "thickness": 0.2,
                    },
                    {
                        "room_name": room["name"],
                        "wall": "left",
                        "start": {"x": x0, "y": y1},
                        "end": {"x": x0, "y": y0},
                        "thickness": 0.2,
                    },
                ]
            )
        return walls

    # Keep API metrics contract stable even when we skip deterministic scoring in emergency geometry mode.
    @staticmethod
    def _build_emergency_metrics(selected_topology: str) -> dict[str, Any]:
        return {
            "area_balance": 0.55,
            "zoning": 0.52,
            "circulation": 0.5,
            "daylight": 0.5,
            "structural": 0.6,
            "furniture": 0.5,
            "efficiency": 0.5,
            "total_score": 0.53,
            "selected_topology": selected_topology or "emergency_grid_fallback",
        }

    def _collect_quality_guard_issues(
        self,
        *,
        quality_guard_model: ParseDesignModel,
        used_emergency_layout: bool,
        planned_payload: dict[str, Any],
        metrics_payload: dict[str, Any],
    ) -> list[str]:
        """Collect quality issues that should trigger a stronger-model recovery retry."""

        if quality_guard_model != ParseDesignModel.QWEN_CLOUD:
            return []

        issues: list[str] = []
        if used_emergency_layout:
            issues.append("emergency_layout_fallback_used")

        total_score = self._safe_metric(metrics_payload.get("total_score"), default=0.0)
        if total_score < QUALITY_GUARD_MIN_TOTAL_SCORE:
            issues.append(
                f"low_total_score:{total_score:.3f}<min:{QUALITY_GUARD_MIN_TOTAL_SCORE:.3f}"
            )

        rooms = planned_payload.get("rooms", [])
        if isinstance(rooms, list) and rooms:
            boundary = planned_payload.get("boundary", {})
            boundary_w = self._safe_metric(boundary.get("width"), default=0.0)
            boundary_h = self._safe_metric(boundary.get("height"), default=0.0)
            boundary_area = max(boundary_w * boundary_h, 1.0)

            dominant_living_area = 0.0
            repetitive_dims: list[tuple[float, float]] = []
            non_corridor_dims: list[tuple[float, float]] = []
            for room in rooms:
                if not isinstance(room, dict):
                    continue
                room_type = str(room.get("room_type", "")).strip().lower()
                width = self._safe_metric(room.get("width"), default=0.0)
                height = self._safe_metric(room.get("height"), default=0.0)
                if width <= 0 or height <= 0:
                    continue
                if room_type != "corridor":
                    dims = (round(width, 2), round(height, 2))
                    non_corridor_dims.append(dims)
                if room_type == "living":
                    dominant_living_area = max(dominant_living_area, width * height)

            if dominant_living_area / boundary_area > 0.62:
                issues.append("living_room_area_too_dominant")

            if len(non_corridor_dims) >= 4:
                counts: dict[tuple[float, float], int] = {}
                for dims in non_corridor_dims:
                    counts[dims] = counts.get(dims, 0) + 1
                repetitive_dims = [dims for dims, count in counts.items() if count >= 3]
                if repetitive_dims:
                    issues.append("excessive_repeated_room_dimensions")

        return issues

    @staticmethod
    def _build_quality_guard_retry_prompt(*, prompt: str, issues: list[str]) -> str:
        """Append quality-correction requirements before retrying with a stronger model."""

        normalized_issues = [str(issue).strip() for issue in issues if str(issue).strip()]
        issues_text = " | ".join(normalized_issues) if normalized_issues else "low_quality_layout"
        return (
            f"{prompt.rstrip()}\n\n"
            "QUALITY CORRECTION REQUIREMENTS:\n"
            f"- Previous candidate failed quality checks: {issues_text}\n"
            "- Keep exact requested room counts.\n"
            "- Avoid repetitive equal-size room boxes unless explicitly requested.\n"
            "- Maintain realistic zoning: living room not excessively dominant.\n"
            "- Preserve practical circulation and adjacency quality.\n"
            "- Return valid architectural extraction JSON only.\n"
        )

    @staticmethod
    def _safe_metric(value: Any, *, default: float) -> float:
        """Coerce unknown numeric-like values into float safely."""

        try:
            parsed = float(value)
        except (TypeError, ValueError):
            return default
        if math.isnan(parsed) or math.isinf(parsed):
            return default
        return parsed

    # Raise the canonical INVALID_JSON_OUTPUT error with aggregated diagnostics from all parse/repair attempts.
    def _raise_initial_json_error(
        self,
        *,
        provider: ProviderClient,
        failover_triggered: bool,
        request_id: str,
        errors: list[str],
    ) -> None:
        logger.warning(
            "request_id=%s provider=%s event=json_rejected reason=%s",
            request_id,
            provider.model_id,
            " | ".join(errors),
        )
        raise ParseDesignServiceError(
            code="INVALID_JSON_OUTPUT",
            message="Model output is not strict JSON",
            status_code=502,
            model_used=provider.model_id,
            provider_used=provider.model_id,
            failover_triggered=failover_triggered,
            details=errors,
        )

    # Ask the same provider to audit and optionally repair its own extraction before planning begins.
    async def _run_self_review(
        self,
        *,
        parsed_payload: dict[str, Any],
        provider: ProviderClient,
        request_id: str,
        failover_triggered: bool,
    ) -> tuple[dict[str, Any], bool]:
        review_prompt = self._build_self_review_prompt(parsed_payload)

        try:
            raw_review_output = await provider.generate(
                review_prompt,
                request_id=f"{request_id}_self_review",
            )
        except ParseDesignServiceError as exc:
            logger.warning(
                "request_id=%s provider=%s event=self_review_fallback reason=%s code=%s",
                request_id,
                provider.model_id,
                exc.message,
                exc.code,
            )  # New block: self-review transport/provider failures now fall back to deterministic local review.
            review_result = self._build_local_self_review_result(parsed_payload)
        else:
            try:
                review_result = self._parse_self_review_output(
                    raw_review_output=raw_review_output,
                    provider=provider,
                    failover_triggered=failover_triggered,
                )
            except ParseDesignServiceError as exc:
                logger.warning(
                    "request_id=%s provider=%s event=self_review_fallback reason=%s code=%s",
                    request_id,
                    provider.model_id,
                    exc.message,
                    exc.code,
                )  # New block: malformed review JSON no longer aborts generation.
                review_result = self._build_local_self_review_result(parsed_payload)
        logger.info("[SelfReview] passed=%s issues=%s", review_result.passed, review_result.issues)

        if review_result.passed:
            return parsed_payload, False

        corrected_payload = self._validate_self_review_correction(
            corrected_output=review_result.corrected_output,
            issues=review_result.issues,
            provider=provider,
            failover_triggered=failover_triggered,
        )
        return corrected_payload, True

    # Build a program-schema-preserving review prompt so the model can fix extraction mistakes without changing interfaces.
    @staticmethod
    def _build_self_review_prompt(parsed_payload: dict[str, Any]) -> str:
        payload_json = json.dumps(parsed_payload, ensure_ascii=False, separators=(",", ":"))
        return (
            "You are reviewing your own architectural extraction output.\n"
            "Return EXACTLY one JSON object with top-level keys: passed, issues, corrected_output.\n"
            "Do not output markdown, code fences, comments, or prose.\n"
            "The corrected_output must keep the same extraction schema as the original output:\n"
            "- top-level keys: boundary, room_program, constraints\n"
            "- room_program entry keys allowed: name, room_type, count, preferred_area, min_area, max_area, furniture\n"
            "- constraints keys allowed: notes, adjacency_preferences\n"
            "Review rules:\n"
            "1) Every room has: name, width_m, height_m, and a valid room_type.\n"
            "2) width_m and height_m are both > 1.5 and < 30.\n"
            "3) No two rooms share the exact same name.\n"
            "4) Total floor area (sum of width*height) is between 20 m^2 and 1000 m^2.\n"
            "5) If adjacency list exists, all referenced room names actually exist.\n"
            "6) If room_type is bedroom, master_bedroom, bathroom, kitchen, living_room, dining_room, or office and the room has no furniture key, add \"furniture\": \"default\".\n"
            "   If furniture is already \"none\", keep it as \"none\" and do not add furniture.\n"
            "Important adaptation for this system:\n"
            "- corrected_output must remain program-only JSON, so do NOT add width_m or height_m keys.\n"
            "- Use preferred_area/min_area/max_area to make implied room dimensions plausible.\n"
            "- If adjacency_preferences uses room types, rewrite them to concrete room names when possible.\n"
            "If the payload passes, return passed=true, issues=[], and corrected_output equal to the original output.\n"
            "Original output:\n"
            f"{payload_json}\n"
        )

    def _build_local_self_review_result(self, parsed_payload: dict[str, Any]) -> _SelfReviewResult:
        corrected_output = self._apply_default_furniture_markers(parsed_payload)  # New block: deterministic fallback also injects renderer defaults when the model review is unavailable.
        issues = self._collect_review_rule_issues(corrected_output)  # New block: deterministic backup review so malformed model review output cannot block the pipeline.
        return _SelfReviewResult(
            passed=not issues,
            issues=issues,
            corrected_output=corrected_output,
        )

    # Parse the review response with an exact top-level contract so bad self-review JSON cannot slip through.
    def _parse_self_review_output(
        self,
        *,
        raw_review_output: str,
        provider: ProviderClient,
        failover_triggered: bool,
    ) -> _SelfReviewResult:
        try:
            parsed_review = extract_json_object_with_keys(raw_review_output, SELF_REVIEW_KEYS)
        except ValueError as exc:
            try:
                parsed_review = extract_json_object_with_keys_permissive(
                    raw_review_output,
                    SELF_REVIEW_KEYS,
                )  # New block: salvage JSON objects wrapped in prose or code fences before giving up.
            except ValueError as permissive_exc:
                raise ParseDesignServiceError(
                    code="INVALID_JSON_OUTPUT",
                    message="Self-review output is not strict JSON",
                    status_code=502,
                    model_used=provider.model_id,
                    provider_used=provider.model_id,
                    failover_triggered=failover_triggered,
                    details=[str(permissive_exc)],
                ) from permissive_exc

        passed = parsed_review.get("passed")
        issues = parsed_review.get("issues")
        corrected_output = parsed_review.get("corrected_output")

        if not isinstance(passed, bool):
            raise ParseDesignServiceError(
                code="INVALID_STRUCTURED_OUTPUT",
                message="Self-review output failed validation",
                status_code=502,
                model_used=provider.model_id,
                provider_used=provider.model_id,
                failover_triggered=failover_triggered,
                details=["self-review.passed must be a boolean"],
            )
        if not isinstance(issues, list) or any(not isinstance(item, str) for item in issues):
            raise ParseDesignServiceError(
                code="INVALID_STRUCTURED_OUTPUT",
                message="Self-review output failed validation",
                status_code=502,
                model_used=provider.model_id,
                provider_used=provider.model_id,
                failover_triggered=failover_triggered,
                details=["self-review.issues must be a list of strings"],
            )
        if not isinstance(corrected_output, dict):
            raise ParseDesignServiceError(
                code="INVALID_STRUCTURED_OUTPUT",
                message="Self-review output failed validation",
                status_code=502,
                model_used=provider.model_id,
                provider_used=provider.model_id,
                failover_triggered=failover_triggered,
                details=["self-review.corrected_output must be a JSON object"],
            )

        normalized_issues = [item.strip() for item in issues if item.strip()]
        return _SelfReviewResult(
            passed=passed,
            issues=normalized_issues,
            corrected_output=corrected_output,
        )

    # Refuse to continue when the model says correction is needed but the repaired payload still fails schema/rule checks.
    def _validate_self_review_correction(
        self,
        *,
        corrected_output: dict[str, Any],
        issues: list[str],
        provider: ProviderClient,
        failover_triggered: bool,
    ) -> dict[str, Any]:
        normalized_issues = issues or ["Self-review rejected the original output."]
        prepared_output = self._apply_default_furniture_markers(corrected_output)  # New block: preserve furniture defaults internally while validating against the unchanged public schema.
        schema_safe_output = self._strip_room_program_furniture(prepared_output)

        try:
            validated_output = self._extracted_intent_validator.validate(schema_safe_output)
        except ValidationError as exc:
            validation_issues = normalized_issues + self._extracted_intent_validator.to_error_details(exc)
            self._raise_self_review_failure(
                issues=validation_issues,
                provider=provider,
                failover_triggered=failover_triggered,
            )

        correction_issues = self._collect_review_rule_issues(validated_output)
        if correction_issues:
            self._raise_self_review_failure(
                issues=normalized_issues + correction_issues,
                provider=provider,
                failover_triggered=failover_triggered,
            )

        return prepared_output

    # Normalize room-level furniture hints deterministically so the renderer does not depend on the model remembering `"furniture": "default"`.
    def _apply_default_furniture_markers(self, payload: dict[str, Any]) -> dict[str, Any]:
        room_program = payload.get("room_program")
        if not isinstance(room_program, list):
            return payload

        normalized_payload = dict(payload)
        normalized_rooms: list[Any] = []
        for raw_room in room_program:
            if not isinstance(raw_room, dict):
                normalized_rooms.append(raw_room)
                continue

            room_copy = dict(raw_room)
            normalized_furniture = self._normalize_furniture_value(room_copy.get("furniture"))
            if normalized_furniture is not None:
                room_copy["furniture"] = normalized_furniture
            elif self._furniture_preset_key(room_copy) is not None:
                room_copy["furniture"] = "default"

            normalized_rooms.append(room_copy)

        normalized_payload["room_program"] = normalized_rooms
        return normalized_payload

    # Remove internal furniture directives before strict schema validation because routers and validators still expose the old contract.
    @staticmethod
    def _strip_room_program_furniture(payload: dict[str, Any]) -> dict[str, Any]:
        room_program = payload.get("room_program")
        if not isinstance(room_program, list):
            return payload

        normalized_payload = dict(payload)
        normalized_payload["room_program"] = [
            {key: value for key, value in raw_room.items() if key != "furniture"} if isinstance(raw_room, dict) else raw_room
            for raw_room in room_program
        ]
        return normalized_payload

    # Carry explicit `"none"` or `"default"` hints across program-derivation retries by matching the original room-program item names.
    def _project_furniture_preferences(
        self,
        *,
        source_payload: dict[str, Any],
        target_payload: dict[str, Any],
    ) -> dict[str, Any]:
        room_program = target_payload.get("room_program")
        if not isinstance(room_program, list):
            return target_payload

        source_preferences = self._room_program_preferences_by_name(source_payload)
        projected_payload = self._apply_default_furniture_markers(target_payload)
        projected_rooms: list[Any] = []

        for raw_room in projected_payload.get("room_program", []):
            if not isinstance(raw_room, dict):
                projected_rooms.append(raw_room)
                continue

            room_copy = dict(raw_room)
            normalized_name = str(room_copy.get("name", "")).strip()
            inherited_preference = source_preferences.get(normalized_name)
            if inherited_preference is not None:
                room_copy["furniture"] = inherited_preference
            projected_rooms.append(room_copy)

        projected_payload["room_program"] = projected_rooms
        return projected_payload

    # Publish final per-room renderer presets into a request-local context so DXF rendering can honor `"default"` versus `"none"` without changing APIs.
    def _publish_render_furniture_presets(self, payload: dict[str, Any]) -> None:
        room_program = payload.get("room_program")
        if not isinstance(room_program, list):
            _RENDER_FURNITURE_PRESETS.set({})
            return

        expanded_presets: dict[str, str] = {}
        for raw_room in room_program:
            if not isinstance(raw_room, dict):
                continue

            name = str(raw_room.get("name", "")).strip()
            if not name:
                continue

            count = raw_room.get("count", 1)
            room_count = count if isinstance(count, int) and count > 0 else 1
            furniture_mode = self._normalize_furniture_value(raw_room.get("furniture"))
            preset_key = self._furniture_preset_key(raw_room)
            for index in range(room_count):
                expanded_name = name if room_count == 1 else f"{name} {index + 1}"
                if furniture_mode == "none":
                    expanded_presets[expanded_name] = "none"
                elif preset_key is not None:
                    expanded_presets[expanded_name] = preset_key

        _RENDER_FURNITURE_PRESETS.set(expanded_presets)

    # Keep room-name matching simple and deterministic because the planner expands counts into `Name 1`, `Name 2`, ...`.
    @staticmethod
    def _room_program_preferences_by_name(payload: dict[str, Any]) -> dict[str, str]:
        room_program = payload.get("room_program")
        if not isinstance(room_program, list):
            return {}

        preferences: dict[str, str] = {}
        for raw_room in room_program:
            if not isinstance(raw_room, dict):
                continue
            name = str(raw_room.get("name", "")).strip()
            furniture = DesignParseOrchestrator._normalize_furniture_value(raw_room.get("furniture"))
            if name and furniture is not None:
                preferences[name] = furniture
        return preferences

    # Normalize the optional furniture flag to the only two values the renderer currently understands.
    @staticmethod
    def _normalize_furniture_value(value: Any) -> str | None:
        if value is None:
            return None
        cleaned = str(value).strip().lower()
        if cleaned in {"default", "none"}:
            return cleaned
        return None

    # Convert canonical room types plus room-name hints into the richer renderer presets requested for DXF furniture.
    @staticmethod
    def _furniture_preset_key(raw_room: dict[str, Any]) -> str | None:
        name = str(raw_room.get("name", "")).strip().lower()
        room_type = str(raw_room.get("room_type", "")).strip().lower()

        if room_type == "bedroom":
            if "master" in name:
                return "master_bedroom"
            if "office" in name or "study" in name:
                return "office"
            return "bedroom"
        if room_type == "bathroom":
            return "bathroom"
        if room_type == "kitchen":
            return "kitchen"
        if room_type == "living":
            if "dining" in name:
                return "dining_room"
            return "living_room"
        if room_type == "office":
            return "office"
        if room_type == "master_bedroom":
            return "master_bedroom"
        if room_type == "living_room":
            return "living_room"
        if room_type == "dining_room":
            return "dining_room"
        return None

    # Mirror the requested review rules with deterministic checks so rejected corrections cannot silently pass through.
    @staticmethod
    def _collect_review_rule_issues(payload: dict[str, Any]) -> list[str]:
        issues: list[str] = []
        room_program = payload.get("room_program")
        if not isinstance(room_program, list):
            return ["room_program must be a list"]

        room_names: set[str] = set()
        room_types: set[str] = set()
        total_area = 0.0
        all_rooms_have_area_signal = True  # New block: fallback review only enforces area totals when the payload actually contains area hints.

        for index, raw_room in enumerate(room_program):
            if not isinstance(raw_room, dict):
                issues.append(f"room_program[{index}] must be an object")
                all_rooms_have_area_signal = False
                continue

            name = str(raw_room.get("name", "")).strip()
            if not name:
                issues.append(f"room_program[{index}] missing name")
            elif name in room_names:
                issues.append(f"duplicate room name: {name}")
            else:
                room_names.add(name)

            room_type = str(raw_room.get("room_type", "")).strip().lower()
            if room_type not in SELF_REVIEW_ALLOWED_ROOM_TYPES:
                issues.append(
                    f"room_program[{index}] has invalid room_type: {raw_room.get('room_type')!r}"
                )
            elif room_type:
                room_types.add(room_type)

            count = raw_room.get("count", 1)
            room_count = count if isinstance(count, int) and count > 0 else 1
            estimated_area = DesignParseOrchestrator._estimate_room_area(raw_room)
            if estimated_area is None:
                all_rooms_have_area_signal = False
                continue

            implied_dimension = estimated_area ** 0.5
            if not (SELF_REVIEW_MIN_DIMENSION_M < implied_dimension < SELF_REVIEW_MAX_DIMENSION_M):
                issues.append(
                    f"room_program[{index}] implied dimensions are out of bounds: "
                    f"{implied_dimension:.2f}m x {implied_dimension:.2f}m"
                )

            total_area += estimated_area * room_count

        if all_rooms_have_area_signal and not (SELF_REVIEW_MIN_AREA_M2 <= total_area <= SELF_REVIEW_MAX_AREA_M2):
            issues.append(
                f"total inferred floor area must be between {SELF_REVIEW_MIN_AREA_M2:.0f} and "
                f"{SELF_REVIEW_MAX_AREA_M2:.0f} square meters"
            )

        constraints = payload.get("constraints")
        adjacency_preferences = constraints.get("adjacency_preferences") if isinstance(constraints, dict) else None
        if isinstance(adjacency_preferences, list):
            for pair_index, pair in enumerate(adjacency_preferences):
                if not isinstance(pair, list):
                    issues.append(f"constraints.adjacency_preferences[{pair_index}] must be a list")
                    continue
                for name in pair:
                    if not isinstance(name, str) or not name.strip():
                        issues.append(
                            f"constraints.adjacency_preferences[{pair_index}] contains an empty room reference"
                        )
                        continue
                    normalized_name = name.strip()
                    if normalized_name not in room_names and normalized_name.lower() not in room_types:
                        issues.append(
                            f"constraints.adjacency_preferences[{pair_index}] references unknown room: {normalized_name}"
                        )

        return issues

    # Infer an area hint from the program-only schema so the requested width/height review can still run before planning.
    @staticmethod
    def _estimate_room_area(raw_room: dict[str, Any]) -> float | None:
        preferred_area = DesignParseOrchestrator._positive_float(raw_room.get("preferred_area"))
        min_area = DesignParseOrchestrator._positive_float(raw_room.get("min_area"))
        max_area = DesignParseOrchestrator._positive_float(raw_room.get("max_area"))

        if preferred_area is not None:
            return preferred_area
        if min_area is not None and max_area is not None:
            return (min_area + max_area) / 2.0
        return min_area if min_area is not None else max_area

    # Keep numeric parsing local so malformed review payloads become explicit issues instead of planner-side surprises.
    @staticmethod
    def _positive_float(value: Any) -> float | None:
        if isinstance(value, bool):
            return None
        if isinstance(value, (int, float)) and float(value) > 0:
            return float(value)
        return None

    # Reuse the existing parser error type and surface the review issues directly instead of continuing with broken data.
    def _raise_self_review_failure(
        self,
        *,
        issues: list[str],
        provider: ProviderClient,
        failover_triggered: bool,
    ) -> None:
        unique_issues = [issue for issue in dict.fromkeys(issue.strip() for issue in issues) if issue]
        message = "; ".join(unique_issues) or "Self-review rejected the model output."
        raise ParseDesignServiceError(
            code="INVALID_STRUCTURED_OUTPUT",
            message=message,
            status_code=422,
            model_used=provider.model_id,
            provider_used=provider.model_id,
            failover_triggered=failover_triggered,
            details=unique_issues,
        )

    # QUALITY FIX: build a one-time correction prompt that asks the same model to fix room-count violations.
    @staticmethod
    def _build_quality_correction_prompt(original_prompt: str, violations: list[str]) -> str:
        correction = "\n".join(issue.strip() for issue in violations if issue.strip())
        return (
            f"{original_prompt}\n\n"
            f"CORRECTION NEEDED:\n{correction}\n"
            "Fix and re-output JSON only."
        )

    # QUALITY FIX: retry extraction once with explicit correction feedback before raising a parser error.
    async def _run_quality_correction_retry(
        self,
        *,
        original_prompt: str,
        recovery_mode: RecoveryMode,
        provider: ProviderClient,
        request_id: str,
        failover_triggered: bool,
        violations: list[str],
    ) -> tuple[dict[str, Any], dict[str, Any], bool]:
        correction_prompt = self._build_quality_correction_prompt(original_prompt, violations)
        raw_output = await provider.generate(
            correction_prompt,
            request_id=f"{request_id}_quality_correction",
        )

        parsed_payload = await self._parse_initial_output_with_repair(
            raw_output=raw_output,
            prompt=original_prompt,
            recovery_mode=recovery_mode,
            provider=provider,
            request_id=f"{request_id}_quality_correction",
            failover_triggered=failover_triggered,
        )

        reviewed_payload, self_review_triggered = await self._run_self_review(
            parsed_payload=parsed_payload,
            provider=provider,
            request_id=f"{request_id}_quality_correction",
            failover_triggered=failover_triggered,
        )
        reviewed_payload_with_furniture = self._apply_default_furniture_markers(reviewed_payload)
        parsed_payload = self._strip_room_program_furniture(reviewed_payload_with_furniture)

        try:
            validated_extracted_payload = self._extracted_intent_validator.validate(parsed_payload)
        except ValidationError as exc:
            raise ParseDesignServiceError(
                code="INVALID_STRUCTURED_OUTPUT",
                message="Corrected model output failed extraction schema validation",
                status_code=422,
                model_used=provider.model_id,
                provider_used=provider.model_id,
                failover_triggered=failover_triggered,
                details=self._extracted_intent_validator.to_error_details(exc),
            ) from exc

        second_pass_violations = self._validate_room_count(
            extracted=validated_extracted_payload,
            original_prompt=original_prompt,
        )
        if second_pass_violations:
            raise ParseDesignServiceError(
                code="ROOM_COUNT_VALIDATION_FAILED",
                message=f"Room count mismatch after retry: {second_pass_violations}",
                status_code=422,
                model_used=provider.model_id,
                provider_used=provider.model_id,
                failover_triggered=failover_triggered,
                details=second_pass_violations,
            )

        return validated_extracted_payload, reviewed_payload_with_furniture, self_review_triggered

    # QUALITY FIX: check extracted room_program against the user's explicit numeric room requests.
    def _validate_room_count(
        self,
        *,
        extracted: dict[str, Any],
        original_prompt: str,
    ) -> list[str]:
        violations: list[str] = []
        prompt_lower = original_prompt.lower()
        room_program = extracted.get("room_program", [])
        families = {
            "bedroom": r"(\d+)\s*(?:bedroom|room|chamber|sleeping\s*room)s?",
            "bathroom": r"(\d+)\s*(?:bathroom|toilet|wc|restroom)s?",
            "kitchen": r"(\d+)\s*(?:kitchen|cooking\s*area)s?",
        }

        for family, pattern in families.items():
            matches = re.findall(pattern, prompt_lower)
            if not matches:
                continue
            requested = sum(int(match) for match in matches)
            actual = 0
            if isinstance(room_program, list):
                for entry in room_program:
                    if not isinstance(entry, dict):
                        continue
                    room_type = str(entry.get("room_type", "")).lower()
                    room_name = str(entry.get("name", "")).lower()
                    count = entry.get("count", 1)
                    room_count = count if isinstance(count, int) and count > 0 else 1
                    if family == "bedroom":
                        if "bedroom" in room_type or "bedroom" in room_name:
                            actual += room_count
                    elif family in room_type or family in room_name:
                        actual += room_count
            if actual != requested:
                violations.append(
                    f"ROOM COUNT MISMATCH: user requested {requested} {family}(s) but extracted {actual}. "
                    f"Fix room_program to have exactly {requested} {family}(s)."
                )

        return violations

    # Keep the older quality-gate name as a thin wrapper so existing internal callers stay compatible during the upgrade.
    def _validate_room_program_quality(
        self,
        *,
        extracted: dict[str, Any],
        original_prompt: str,
    ) -> list[str]:
        return self._validate_room_count(extracted=extracted, original_prompt=original_prompt)

    # QUALITY FIX: map user-count language (including requested synonyms) to canonical room families.
    @staticmethod
    def _extract_requested_room_counts(prompt_text: str) -> dict[str, int]:
        number_words: dict[str, int] = {
            "one": 1,
            "two": 2,
            "three": 3,
            "four": 4,
            "five": 5,
            "six": 6,
            "seven": 7,
            "eight": 8,
            "nine": 9,
            "ten": 10,
            "eleven": 11,
            "twelve": 12,
        }

        def parse_count(token: str) -> int | None:
            if token.isdigit():
                parsed = int(token)
                return parsed if parsed > 0 else None
            return number_words.get(token)

        def count_matches(pattern: str) -> int:
            total = 0
            for token in re.findall(pattern, prompt_text):
                parsed = parse_count(str(token).strip().lower())
                if parsed is not None:
                    total += parsed
            return total

        result: dict[str, int] = {}
        bedroom_count = count_matches(
            r"\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s*"
            r"(?:bedrooms?|rooms?|chambers?|sleeping\s+rooms?)\b"
        )
        if bedroom_count > 0:
            result["bedroom"] = bedroom_count

        bathroom_count = count_matches(
            r"\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s*"
            r"(?:bathrooms?|toilets?|wc|restrooms?)\b"
        )
        if bathroom_count > 0:
            result["bathroom"] = bathroom_count

        kitchen_count = count_matches(
            r"\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s*"
            r"(?:kitchens?|cooking\s+areas?)\b"
        )
        if kitchen_count > 0:
            result["kitchen"] = kitchen_count

        living_count = count_matches(
            r"\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s*"
            r"(?:living\s+rooms?|lounges?|salons?|receptions?|dining\s+rooms?|dining\s+areas?)\b"
        )
        if living_count > 0:
            result["living"] = living_count

        corridor_count = count_matches(
            r"\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s*"
            r"(?:corridors?|hallways?|passages?)\b"
        )
        if corridor_count > 0:
            result["corridor"] = corridor_count

        stairs_count = count_matches(
            r"\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s*"
            r"(?:stairs?|staircases?)\b"
        )
        if stairs_count > 0:
            result["stairs"] = stairs_count

        return result

    # QUALITY FIX: aggregate extracted counts from room_program.count in canonical type space.
    @staticmethod
    def _actual_room_program_counts(extracted: dict[str, Any]) -> dict[str, int]:
        room_program = extracted.get("room_program")
        if not isinstance(room_program, list):
            return {}

        counts: dict[str, int] = {}
        for raw_room in room_program:
            if not isinstance(raw_room, dict):
                continue
            room_type = str(raw_room.get("room_type", "")).strip().lower()
            if not room_type:
                continue
            count_value = raw_room.get("count", 1)
            if isinstance(count_value, bool):
                continue
            if isinstance(count_value, int):
                room_count = count_value if count_value > 0 else 1
            else:
                room_count = 1
            counts[room_type] = counts.get(room_type, 0) + room_count
        return counts

    @staticmethod
    def _validate_prompt_language(prompt: str, model_used: str) -> None:
        text = prompt.strip()
        if not LATIN_CHAR_RE.search(text) and not ARABIC_CHAR_RE.search(text):
            raise ParseDesignServiceError(
                code="PROMPT_ENGLISH_ONLY",
                message="Prompt must contain English or Arabic text.",
                status_code=400,
                model_used=model_used,
                provider_used=model_used,
                details=["Use alphabetic English or Arabic prompt text."],
            )
