"""Standalone LangChain intent-classification entrypoint for design parsing."""

from __future__ import annotations

import functools
from typing import Any

from app.models.design_parser import ParseDesignModel
from app.services.design_parser.config import (
    OLLAMA_API_KEY,
    OLLAMA_CLOUD_GENERATE_URL,
    OLLAMA_GENERATE_URL,
    OLLAMA_MODEL_ID,
    QWEN_CLOUD_MODEL_ID,
)
from app.services.langchain_engine import CadArenaLangChainEngine


def _fallback_intent(reason: str) -> dict[str, Any]:
    """Return the safe fallback intent payload used when LangChain is unavailable."""

    return {
        "intent": "NEW_DESIGN",
        "confidence": 0.5,
        "target_rooms": [],
        "reasoning": reason,
    }


@functools.lru_cache(maxsize=8)
def _get_engine(
    ollama_url: str,
    model_name: str,
    ollama_api_key: str,
) -> CadArenaLangChainEngine:
    """Return a cached LangChain engine for the requested provider runtime."""

    return CadArenaLangChainEngine(ollama_url, model_name, ollama_api_key or None)


def _resolve_langchain_backend(
    model_choice: ParseDesignModel,
) -> tuple[str, str, str] | None:
    """Resolve which Ollama-compatible backend should power intent classification."""

    if model_choice == ParseDesignModel.OLLAMA:
        return (OLLAMA_GENERATE_URL, OLLAMA_MODEL_ID, "")
    if model_choice == ParseDesignModel.QWEN_CLOUD:
        return (OLLAMA_CLOUD_GENERATE_URL, QWEN_CLOUD_MODEL_ID, OLLAMA_API_KEY)
    if OLLAMA_API_KEY:
        # Use Qwen cloud as a reasoning sidecar when the parse model is HuggingFace.
        return (OLLAMA_CLOUD_GENERATE_URL, QWEN_CLOUD_MODEL_ID, OLLAMA_API_KEY)
    return None


async def classify_user_intent(
    prompt: str,
    has_existing: bool,
    project_id: str,
    model_choice: ParseDesignModel = ParseDesignModel.HUGGINGFACE,
) -> dict[str, Any]:
    """Public entry point for LangChain-backed user intent classification."""

    runtime = _resolve_langchain_backend(model_choice)
    if runtime is None:
        return _fallback_intent("fallback due to unavailable LangChain backend")
    ollama_url, model_name, api_key = runtime
    return await _get_engine(ollama_url, model_name, api_key).classify_intent(prompt, has_existing, project_id)
