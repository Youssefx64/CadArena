"""Runtime configuration for the design parser service."""

from __future__ import annotations

import os
from urllib.parse import urlsplit, urlunsplit

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


def _base_url_from_endpoint_url(endpoint_url: str) -> str:
    """Normalize a concrete API endpoint URL back to its base URL."""

    parsed = urlsplit(endpoint_url.strip())
    path = parsed.path or ""
    # Strip known Ollama-compatible endpoint suffixes so one base URL can drive both routes.
    for suffix in ("/api/generate", "/api/chat", "/generate", "/chat"):
        if path.endswith(suffix):
            path = path[: -len(suffix)]
            break
    return urlunsplit(parsed._replace(path=path.rstrip("/"), query="", fragment=""))


OLLAMA_MODEL_ID = "llama3.1:8b"
OLLAMA_LOCAL_MODELS: list[str] = [
    OLLAMA_MODEL_ID,
    "qwen2.5:7b-instruct",
]
HF_MODEL_ID = os.getenv("HF_MODEL_NAME", os.getenv("CADARENA_HF_MODEL_ID", "LiquidAI/LFM2-1.2B-Extract"))
OLLAMA_GENERATE_URL = os.getenv("CADARENA_OLLAMA_URL", "http://localhost:11434/api/generate")
# Keep the public cloud base configurable while preserving older endpoint-style env vars.
OLLAMA_CLOUD_BASE_URL: str = os.getenv(
    "OLLAMA_CLOUD_URL",
    _base_url_from_endpoint_url(
        os.getenv("CADARENA_OLLAMA_CLOUD_URL", "https://cloud.ollama.com")  # CLOUD-FIX: default to the Ollama Cloud base URL instead of baking in /api/generate
    )
    or "https://cloud.ollama.com",  # CLOUD-FIX: keep the normalized fallback aligned with the official Ollama Cloud base URL
)
# HOW TO SET UP OLLAMA CLOUD FREE TIER:
# 1. Go to cloud.ollama.com
# 2. Sign up for free account
# 3. Copy your API endpoint URL
# 4. Set in backend/.env:
#    OLLAMA_CLOUD_URL=https://your-endpoint.ollama.com
# Public cloud catalog exposed in the app.
OLLAMA_CLOUD_MODELS: list[str] = [
    "qwen3.5:397b-cloud",
    "gemma3:27b-cloud",
    "minimax-m2.7:cloud",
    "qwen3-coder-next:cloud",
]
QWEN_CLOUD_MODEL_ID = os.getenv("CADARENA_QWEN_CLOUD_MODEL_ID", OLLAMA_CLOUD_MODELS[0])
OLLAMA_CLOUD_GENERATE_URL = f"{OLLAMA_CLOUD_BASE_URL.rstrip('/')}/api/generate"  # CLOUD-FIX: always derive the cloud generate endpoint from the normalized base URL
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "").strip()
REQUEST_TIMEOUT_SECONDS = _env_float("CADARENA_PARSER_TIMEOUT_SECONDS", 60.0)
MAX_NEW_TOKENS = _env_int("CADARENA_PARSER_MAX_NEW_TOKENS", 256)
QWEN_MAX_NEW_TOKENS = _env_int("CADARENA_QWEN_MAX_NEW_TOKENS", max(MAX_NEW_TOKENS, 768))
OLLAMA_NUM_CTX = _env_int("CADARENA_OLLAMA_NUM_CTX", 2048)
HF_EAGER_LOAD = _env_bool("HF_EAGER_LOAD", _env_bool("CADARENA_HF_EAGER_LOAD", True))
HF_MAX_CONCURRENCY = _env_int("HF_MAX_CONCURRENCY", _env_int("CADARENA_HF_MAX_CONCURRENCY", 2))
ENABLE_OLLAMA_TO_HF_FAILOVER = _env_bool("CADARENA_ENABLE_OLLAMA_TO_HF_FAILOVER", False)
DEFAULT_PARSE_MODEL = os.getenv("CADARENA_DEFAULT_PARSE_MODEL", "huggingface").strip().lower()
ENABLE_QWEN_TO_HF_FAILOVER = _env_bool("CADARENA_ENABLE_QWEN_TO_HF_FAILOVER", True)
ENABLE_QWEN_QUALITY_GUARD = _env_bool("CADARENA_ENABLE_QWEN_QUALITY_GUARD", True)
QUALITY_GUARD_MIN_TOTAL_SCORE = _env_float("CADARENA_QUALITY_GUARD_MIN_TOTAL_SCORE", 0.64)
STRICT_MODEL_SELECTION = _env_bool("CADARENA_STRICT_MODEL_SELECTION", True)


def _default_chat_url_from_generate_url(generate_url: str) -> str:
    parsed = urlsplit(generate_url.strip())
    path = parsed.path or "/"
    if path.endswith("/api/generate"):
        path = path[: -len("/api/generate")] + "/api/chat"
    elif path.endswith("/generate"):
        path = path[: -len("/generate")] + "/chat"
    else:
        path = "/api/chat"
    return urlunsplit(parsed._replace(path=path, query="", fragment=""))


OLLAMA_CLOUD_CHAT_URL = os.getenv(
    "CADARENA_OLLAMA_CLOUD_CHAT_URL",
    _default_chat_url_from_generate_url(OLLAMA_CLOUD_GENERATE_URL),
)

STRICT_TOP_LEVEL_KEYS = {"boundary", "rooms", "walls", "openings"}
