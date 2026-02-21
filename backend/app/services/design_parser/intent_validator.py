"""Schema validation for parsed design intents."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from app.models.design_parser import ParsedDesignIntent


class IntentValidator:
    """Validates parsed JSON payloads against strict schema constraints."""

    def validate(self, payload: dict[str, Any]) -> dict[str, Any]:
        validated = ParsedDesignIntent.model_validate(payload)
        return validated.model_dump(mode="json")

    @staticmethod
    def to_error_details(exc: ValidationError) -> list[str]:
        return [
            f"{'.'.join(str(item) for item in error['loc'])}: {error['msg']}"
            for error in exc.errors()
        ]

