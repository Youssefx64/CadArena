"""Model output parsing for strict JSON architectural-program extraction."""

from __future__ import annotations

from typing import Any

from app.utils.json_extraction import extract_json_object_with_keys


_EXPECTED_LLM_KEYS = {"boundary", "room_program", "constraints"}


class OutputParser:
    """Parses raw model text into a strict JSON object."""

    def parse(self, raw_output: str) -> dict[str, Any]:
        return extract_json_object_with_keys(raw_output, _EXPECTED_LLM_KEYS)
