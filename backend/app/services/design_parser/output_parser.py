"""Model output parsing for strict JSON intent extraction."""

from __future__ import annotations

from typing import Any

from app.utils.json_extraction import extract_json_object


class OutputParser:
    """Parses raw model text into a strict JSON object."""

    def parse(self, raw_output: str) -> dict[str, Any]:
        return extract_json_object(raw_output)

