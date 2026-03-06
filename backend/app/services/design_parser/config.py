"""Runtime configuration for the design parser service."""

from __future__ import annotations

import os

from app.core.env_loader import load_backend_env

load_backend_env()


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        parsed = float(value)
    except ValueError:
        return default
    return parsed if parsed > 0 else default


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        parsed = int(value)
    except ValueError:
        return default
    return parsed if parsed > 0 else default


OLLAMA_MODEL_ID = "llama3.1:8b"
HF_MODEL_ID = os.getenv("HF_MODEL_NAME", os.getenv("CADARENA_HF_MODEL_ID", "LiquidAI/LFM2-1.2B-Extract"))
OLLAMA_GENERATE_URL = os.getenv("CADARENA_OLLAMA_URL", "http://localhost:11434/api/generate")
REQUEST_TIMEOUT_SECONDS = _env_float("CADARENA_PARSER_TIMEOUT_SECONDS", 20.0)
MAX_NEW_TOKENS = _env_int("CADARENA_PARSER_MAX_NEW_TOKENS", 256)
OLLAMA_NUM_CTX = _env_int("CADARENA_OLLAMA_NUM_CTX", 2048)
HF_EAGER_LOAD = _env_bool("HF_EAGER_LOAD", _env_bool("CADARENA_HF_EAGER_LOAD", True))
HF_MAX_CONCURRENCY = _env_int("HF_MAX_CONCURRENCY", _env_int("CADARENA_HF_MAX_CONCURRENCY", 2))
ENABLE_OLLAMA_TO_HF_FAILOVER = _env_bool("CADARENA_ENABLE_OLLAMA_TO_HF_FAILOVER", False)

STRICT_TOP_LEVEL_KEYS = {"boundary", "rooms", "walls", "openings"}
