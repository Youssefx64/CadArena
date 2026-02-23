"""Schema validation for LLM-extracted architectural programs."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from app.models.design_parser import ExtractedDesignIntent


class ExtractedIntentValidator:
    """Validates extracted LLM payload against program-only schema."""

    def validate(self, payload: dict[str, Any]) -> dict[str, Any]:
        validated = ExtractedDesignIntent.model_validate(payload)
        return validated.model_dump(mode="json")

    @staticmethod
    def to_error_details(exc: ValidationError) -> list[str]:
        return [
            f"{'.'.join(str(item) for item in error['loc'])}: {error['msg']}"
            for error in exc.errors()
        ]
