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
    request_id: str | None = None,
) -> Path:
    """Persist parse-design output to a fixed folder with a logical filename."""

    PARSE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    model_token = _model_alias(model_used)
    prompt_token = _prompt_slug(prompt)
    suffix = _request_suffix(request_id)

    filename = f"design_{timestamp}_{model_token}_{prompt_token}_{suffix}.json"
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
    clipped = "-".join(parts[:6])
    return clipped[:48].rstrip("-") or "design-intent"


def _sanitize_token(value: str) -> str:
    lowered = value.strip().lower()
    cleaned = re.sub(r"[^a-z0-9]+", "_", lowered)
    cleaned = cleaned.strip("_")
    return cleaned or "model"


def _model_alias(model_used: str) -> str:
    lowered = model_used.strip().lower()
    if "llama3.1:8b" in lowered:
        return "ollama-llama3-8b"
    if "liquidai/lfm2-1.2b-extract" in lowered:
        return "hf-lfm2-1.2b"
    token = _sanitize_token(lowered).replace("_", "-")
    return token[:24].rstrip("-") or "model"


def _request_suffix(request_id: str | None) -> str:
    if request_id:
        cleaned = _sanitize_token(request_id)
        if cleaned:
            return cleaned[:6]
    return datetime.now(timezone.utc).strftime("%f")[:6]


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
