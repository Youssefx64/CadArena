"""LangChain-powered prompt-engineering scaffold for CadArena."""

from __future__ import annotations

import json
import logging
from typing import Any
from urllib.parse import urlsplit, urlunsplit

try:
    from langchain_core.prompts import PromptTemplate
except (ImportError, ModuleNotFoundError):  # pragma: no cover - depends on optional local install
    PromptTemplate = None

try:
    from langchain.memory import ConversationBufferMemory
except (ImportError, ModuleNotFoundError):
    try:
        from langchain_classic.memory import ConversationBufferMemory
    except (ImportError, ModuleNotFoundError):  # pragma: no cover - depends on optional local install
        ConversationBufferMemory = None

from app.utils.json_extraction import extract_json_object_permissive

# Configure a module logger so runtime engine errors are surfaced without crashing the whole request.
logger = logging.getLogger(__name__)

# Define the intent-classification prompt as a reusable chain template.
INTENT_PROMPT = (
    PromptTemplate(
        input_variables=["user_prompt", "has_existing_layout"],
        template="""You are an architectural intent classifier.

Analyze the user message and classify it into ONE of these intents:

NEW_DESIGN      -> user wants a completely new floor plan from scratch
MODIFY_ROOM     -> user wants to change size/position of specific room(s)
ADD_ROOM        -> user wants to add a new room to existing layout
REMOVE_ROOM     -> user wants to delete a room from existing layout
SWAP_ROOMS      -> user wants to exchange positions of two rooms
ADJUST_GLOBAL   -> user wants to change overall house size or orientation
CLARIFY         -> message is unclear, need more info

Has existing layout: {has_existing_layout}
User message: {user_prompt}

Respond with ONLY a JSON object, no explanation:
{{
  "intent": "ONE_OF_THE_ABOVE",
  "confidence": 0.0-1.0,
  "target_rooms": ["room name if mentioned", ...],
  "reasoning": "one sentence why"
}}""",
    )
    if PromptTemplate is not None
    else None
)

# Define the surgical diff-extraction prompt for iterative layout edits.
DIFF_PROMPT = (
    PromptTemplate(
        input_variables=["user_prompt", "current_layout_json", "chat_history"],
        template="""You are a surgical architectural editor.

You have an existing floor plan. Extract ONLY what needs to change.

Current layout (JSON):
{current_layout_json}

Conversation so far:
{chat_history}

User instruction: {user_prompt}

Rules:
- Return ONLY the rooms and openings that need to change.
- For modified rooms: include full room object with updated values.
- For unchanged rooms: DO NOT include them.
- Dimensions must remain physically valid (min 1.5m any side).
- All rooms must still fit within the boundary.
- If adding a room: specify where it connects (adjacent_to field).

Respond with ONLY this JSON, no explanation:
{{
  "operation": "modify|add|remove|swap|adjust_boundary",
  "changes": {{
    "boundary": null or {{"width": float, "height": float}},
    "rooms_to_modify": [ ...full room objects... ],
    "rooms_to_add": [ ...new room objects with adjacent_to... ],
    "rooms_to_remove": [ "room name", ... ],
    "rooms_to_swap": [ ["room_a", "room_b"] ]
  }},
  "reasoning": "one sentence"
}}""",
    )
    if PromptTemplate is not None
    else None
)


def _normalize_ollama_base_url(ollama_url: str) -> str:
    """Convert an Ollama generate URL into the base URL expected by LangChain."""

    stripped_url = ollama_url.strip()
    parsed_url = urlsplit(stripped_url)
    normalized_path = parsed_url.path or "/"
    if normalized_path.endswith("/api/generate"):
        normalized_path = normalized_path[: -len("/api/generate")] or "/"
    rebuilt_url = parsed_url._replace(path=normalized_path, query="", fragment="")
    return urlunsplit(rebuilt_url)


def _intent_fallback_payload() -> dict[str, Any]:
    """Return the default fallback payload for intent classification failures."""

    return {
        "intent": "NEW_DESIGN",
        "confidence": 0.5,
        "target_rooms": [],
        "reasoning": "fallback",
    }


class CadArenaLangChainEngine:
    """LangChain engine for CadArena prompt engineering."""

    def __init__(self, ollama_url: str, model_name: str, ollama_api_key: str | None = None) -> None:
        """Initialize the LangChain engine with the configured Ollama backend."""

        if PromptTemplate is None or ConversationBufferMemory is None:
            raise RuntimeError("LangChain dependencies are not installed")

        # Import the POST-based Ollama client lazily so the runtime uses the modern LangChain transport.
        from langchain_ollama import OllamaLLM

        llm_kwargs: dict[str, Any] = {
            "base_url": _normalize_ollama_base_url(ollama_url),
            "model": model_name,
            "temperature": 0.1,
            "num_predict": 2048,
        }
        cleaned_api_key = (ollama_api_key or "").strip()
        if cleaned_api_key:
            auth_headers = {"Authorization": f"Bearer {cleaned_api_key}"}
            llm_kwargs["client_kwargs"] = {"headers": auth_headers}
            llm_kwargs["async_client_kwargs"] = {"headers": auth_headers}

        # Configure a deterministic Ollama-backed LangChain LLM for JSON-heavy tasks.
        self.llm: OllamaLLM = OllamaLLM(
            **llm_kwargs,
        )
        # Keep project conversations isolated so iterative editing can reuse context safely.
        self._memories: dict[str, ConversationBufferMemory] = {}

    @staticmethod
    def _safe_json(raw_text: str) -> dict[str, Any] | None:
        """Return the best-effort JSON object parsed from model output text."""

        # Preserve the permissive JSON extraction behavior used by the previous implementation.
        try:
            return extract_json_object_permissive(raw_text)
        except ValueError:
            return None

    def get_memory(self, project_id: str) -> ConversationBufferMemory:
        """Return or create isolated LangChain conversation memory for a project."""

        # Lazily create project-scoped conversation memory on first use.
        if project_id not in self._memories:
            self._memories[project_id] = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True,
                input_key="user_prompt",
                output_key="response",
            )
        return self._memories[project_id]

    def clear_memory(self, project_id: str) -> None:
        """Clear the stored LangChain memory for a single project."""

        # Remove the project memory entirely when a fresh design session is needed.
        if project_id in self._memories:
            del self._memories[project_id]

    async def classify_intent(
        self,
        user_prompt: str,
        has_existing_layout: bool,
        project_id: str,
    ) -> dict[str, Any]:
        """Classify whether the prompt requests a new design or an iterative edit."""

        # Build a modern runnable sequence with prompt piping instead of deprecated LLMChain usage.
        chain = INTENT_PROMPT | self.llm

        # Execute intent classification with defensive fallback so engine transport errors do not crash the flow.
        try:
            result = await chain.ainvoke(
                {
                    "user_prompt": user_prompt,
                    "has_existing_layout": str(has_existing_layout),
                }
            )
        except Exception as exc:
            logger.warning("[LangChainEngine] classify_intent failed: %s", exc)
            return {
                "intent": "NEW_DESIGN",
                "confidence": 0.5,
                "target_rooms": [],
                "reasoning": "fallback due to engine error",
            }

        # Parse the response as JSON and fall back to the requested default payload on malformed output.
        return self._safe_json(str(result)) or _intent_fallback_payload()

    async def extract_diff(
        self,
        user_prompt: str,
        current_layout: dict[str, Any],
        project_id: str,
    ) -> dict[str, Any]:
        """Extract the minimal layout diff needed to satisfy an iterative instruction."""

        # Reuse project-scoped conversation memory and serialize the accumulated history for the diff prompt.
        memory = self.get_memory(project_id)
        history = memory.load_memory_variables({}).get("chat_history", "")

        # Build a modern runnable sequence with prompt piping instead of deprecated chain classes.
        chain = DIFF_PROMPT | self.llm

        # Execute diff extraction with defensive fallback so transport or provider failures return an empty diff.
        try:
            result = await chain.ainvoke(
                {
                    "user_prompt": user_prompt,
                    "current_layout_json": json.dumps(current_layout, indent=2),
                    "chat_history": str(history),
                }
            )
        except Exception as exc:
            logger.warning("[LangChainEngine] extract_diff failed: %s", exc)
            return {}

        # Save the exchange manually because RunnableSequence does not attach conversation memory automatically.
        memory.save_context(
            {"user_prompt": user_prompt},
            {"response": str(result)},
        )

        # Parse the response as JSON and return an empty diff on extraction failure.
        return self._safe_json(str(result)) or {}
