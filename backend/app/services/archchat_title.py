from __future__ import annotations

import logging
import re

import httpx

from app.services.design_parser.config import OLLAMA_GENERATE_URL, OLLAMA_MODEL_ID

logger = logging.getLogger(__name__)

_WHITESPACE_RE = re.compile(r"\s+")


def _fallback_title(first_user_message: str) -> str:
    cleaned = _WHITESPACE_RE.sub(" ", first_user_message.strip())
    if not cleaned:
        return "New chat"
    if len(cleaned) <= 48:
        return cleaned
    return f"{cleaned[:48].rstrip()}…"


async def generate_thread_title(first_user_message: str) -> str:
    """
    Generate a short title from the first user message.

    Uses Ollama generate endpoint when available (same default model as backend chat assistant),
    and falls back to a deterministic title if unavailable.
    """
    prompt = first_user_message.strip()
    if not prompt:
        return "New chat"

    system = (
        "You generate short chat thread titles.\n"
        "Return ONLY the title, no quotes.\n"
        "Constraints:\n"
        "- 3 to 6 words\n"
        "- Title case if English\n"
        "- If Arabic, keep it natural and short\n"
    )
    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            payload = {
                "model": OLLAMA_MODEL_ID,
                "prompt": f"{system}\n\nUser message:\n{prompt}\n\nTitle:",
                "stream": False,
                "options": {"num_predict": 24, "temperature": 0.2},
            }
            resp = await client.post(OLLAMA_GENERATE_URL, json=payload)
            resp.raise_for_status()
            data = resp.json()
            title = str(data.get("response", "")).strip().strip('"').strip("'")
            title = _WHITESPACE_RE.sub(" ", title)
            if 3 <= len(title) <= 160:
                return title
    except Exception as exc:
        logger.debug("Thread title generation unavailable: %s", exc)

    return _fallback_title(first_user_message)

