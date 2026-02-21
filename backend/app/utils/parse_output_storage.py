"""Utilities for persisting parse-design JSON outputs."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PARSE_OUTPUT_DIR = Path(__file__).resolve().parents[2] / "output" / "parse_design_json"


def save_parse_design_output(
    *,
    prompt: str,
    model_used: str,
    parsed_data: dict[str, Any],
) -> Path:
    """Persist parse-design output to a fixed folder with a logical filename."""

    PARSE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
    model_token = _sanitize_token(model_used)
    prompt_token = _prompt_slug(prompt)

    filename = f"parse_design_{timestamp}_{model_token}_{prompt_token}.json"
    output_path = PARSE_OUTPUT_DIR / filename

    payload = build_dxf_ready_payload(parsed_data)

    with output_path.open("w", encoding="utf-8") as file_obj:
        json.dump(payload, file_obj, indent=2, ensure_ascii=False)

    return output_path


def _prompt_slug(prompt: str) -> str:
    normalized = " ".join(prompt.strip().split())
    lowered = normalized.lower()
    cleaned = re.sub(r"[^a-z0-9]+", "-", lowered)
    cleaned = cleaned.strip("-")

    if not cleaned:
        return "design-intent"

    parts = [part for part in cleaned.split("-") if part]
    clipped = "-".join(parts[:10])
    return clipped[:80].rstrip("-") or "design-intent"


def _sanitize_token(value: str) -> str:
    lowered = value.strip().lower()
    cleaned = re.sub(r"[^a-z0-9]+", "_", lowered)
    cleaned = cleaned.strip("_")
    return cleaned or "model"


def build_dxf_ready_payload(parsed_data: dict[str, Any]) -> dict[str, Any]:
    """Return only the fields required by the DXF generation endpoint."""

    boundary = parsed_data.get("boundary") if isinstance(parsed_data, dict) else {}
    rooms = parsed_data.get("rooms") if isinstance(parsed_data, dict) else []
    openings = parsed_data.get("openings") if isinstance(parsed_data, dict) else []

    if not isinstance(boundary, dict):
        boundary = {}
    if not isinstance(rooms, list):
        rooms = []
    if not isinstance(openings, list):
        openings = []

    return {
        "boundary": boundary,
        "rooms": rooms,
        "openings": openings,
    }
