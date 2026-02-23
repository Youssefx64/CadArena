"""Utilities to extract strict JSON payloads from model output."""

from __future__ import annotations

import json
import re
from typing import Any


_CODE_FENCE_RE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.IGNORECASE | re.DOTALL)
_DEFAULT_EXPECTED_TOP_LEVEL_KEYS = {"boundary", "rooms", "walls", "openings"}


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

    return extract_json_object_with_keys(raw_text, _DEFAULT_EXPECTED_TOP_LEVEL_KEYS)


def extract_json_object_with_keys(raw_text: str, expected_top_level_keys: set[str]) -> dict[str, Any]:
    """Extract one strict JSON object with exact provided top-level schema keys."""

    cleaned = strip_markdown_fences(raw_text)
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError("Output must be a single JSON object without surrounding prose or multiple objects") from exc

    if not isinstance(parsed, dict):
        raise ValueError("Top-level JSON value must be an object")

    keys = set(parsed.keys())
    if keys != expected_top_level_keys:
        missing = sorted(expected_top_level_keys - keys)
        extra = sorted(keys - expected_top_level_keys)
        required = ", ".join(sorted(expected_top_level_keys))
        raise ValueError(
            f"Top-level keys must be exactly {required}; "
            f"missing={missing} extra={extra}"
        )

    return parsed


def extract_json_object_permissive(raw_text: str) -> dict[str, Any]:
    """Extract the best JSON object candidate from mixed model output."""

    cleaned = strip_markdown_fences(raw_text)
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    decoder = json.JSONDecoder()
    candidates: list[dict[str, Any]] = []
    for index, char in enumerate(cleaned):
        if char != "{":
            continue
        try:
            candidate, _ = decoder.raw_decode(cleaned[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(candidate, dict):
            candidates.append(candidate)

    if not candidates:
        raise ValueError("No JSON object found in model output")

    candidates.sort(key=_score_candidate, reverse=True)
    return candidates[0]


def _score_candidate(candidate: dict[str, Any]) -> tuple[int, int, int, int, int]:
    has_boundary = isinstance(candidate.get("boundary"), dict)
    has_rooms = isinstance(candidate.get("rooms"), list)
    has_walls = isinstance(candidate.get("walls"), list)
    has_openings = isinstance(candidate.get("openings"), list)
    exact_keys = set(candidate.keys()) == _DEFAULT_EXPECTED_TOP_LEVEL_KEYS

    top_level_score = int(has_boundary) + int(has_rooms) + int(has_walls) + int(has_openings)
    room_count = len(candidate.get("rooms", [])) if has_rooms else 0
    wall_count = len(candidate.get("walls", [])) if has_walls else 0
    opening_count = len(candidate.get("openings", [])) if has_openings else 0
    return (int(exact_keys), top_level_score, room_count, wall_count, opening_count)
