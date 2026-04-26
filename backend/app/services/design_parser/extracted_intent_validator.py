"""Schema validation for LLM-extracted architectural programs."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from app.models.design_parser import ExtractedDesignIntent
from app.services.design_parser.room_program_normalizer import normalize_extracted_room_program


class ExtractedIntentValidator:
    """Validates extracted LLM payload against program-only schema."""

    def validate(self, payload: dict[str, Any], *, prompt: str | None = None) -> dict[str, Any]:
        normalized_payload = normalize_extracted_room_program(payload, prompt=prompt)
        validated = ExtractedDesignIntent.model_validate(normalized_payload)
        return validated.model_dump(mode="json")

    @staticmethod
    def to_error_details(exc: ValidationError) -> list[str]:
        return [
            f"{'.'.join(str(item) for item in error['loc'])}: {error['msg']}"
            for error in exc.errors()
        ]
