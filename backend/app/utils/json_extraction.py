"""Utilities to extract strict JSON payloads from model output."""

from __future__ import annotations

import json
import re
from typing import Any


_CODE_FENCE_RE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.IGNORECASE | re.DOTALL)
_EXPECTED_TOP_LEVEL_KEYS = {"boundary", "rooms", "walls", "openings"}


def strip_markdown_fences(text: str) -> str:
    """Remove top-level markdown code fences from model output."""

    raw = text.strip()
    fenced = _CODE_FENCE_RE.match(raw)
    if fenced:
        return fenced.group(1).strip()

    if raw.startswith("```") and raw.endswith("```"):
        lines = raw.splitlines()
        if len(lines) >= 2:
            body = "\n".join(lines[1:-1])
            return body.strip()
    return raw


def extract_json_object(raw_text: str) -> dict[str, Any]:
    """Extract one strict JSON object with exact top-level schema keys."""

    cleaned = strip_markdown_fences(raw_text)
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError("Output must be a single JSON object without surrounding prose or multiple objects") from exc

    if not isinstance(parsed, dict):
        raise ValueError("Top-level JSON value must be an object")

    keys = set(parsed.keys())
    if keys != _EXPECTED_TOP_LEVEL_KEYS:
        missing = sorted(_EXPECTED_TOP_LEVEL_KEYS - keys)
        extra = sorted(keys - _EXPECTED_TOP_LEVEL_KEYS)
        raise ValueError(
            "Top-level keys must be exactly boundary, rooms, walls, openings; "
            f"missing={missing} extra={extra}"
        )

    return parsed
