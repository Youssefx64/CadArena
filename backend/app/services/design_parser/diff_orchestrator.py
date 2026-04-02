"""Standalone iterative diff orchestration for reliable layout edits."""

from __future__ import annotations

import copy
import functools
import logging
import re
from typing import Any
from uuid import uuid4

from app.models.design_parser import ParseDesignModel, RecoveryMode
from app.services.design_parser.config import (
    OLLAMA_API_KEY,
    OLLAMA_CLOUD_GENERATE_URL,
    OLLAMA_GENERATE_URL,
    OLLAMA_MODEL_ID,
    QWEN_CLOUD_MODEL_ID,
)
from app.services.design_parser.layout_patcher import LayoutPatcher
from app.services.design_parser.layout_validator import LayoutValidator
from app.services.design_parser.opening_planner import DeterministicOpeningPlanner
from app.services.design_parser.rule_violation import RuleViolationError
from app.services.design_parser_service import parse_design_prompt_with_metadata
from app.services.langchain_engine import CadArenaLangChainEngine

logger = logging.getLogger(__name__)


@functools.lru_cache(maxsize=1)
def _ollama_engine() -> CadArenaLangChainEngine:
    """Return the cached LangChain engine configured for iterative edits."""

    # Reuse local Ollama settings for iterative edits when local runtime is selected.
    return CadArenaLangChainEngine(OLLAMA_GENERATE_URL, OLLAMA_MODEL_ID)


@functools.lru_cache(maxsize=1)
def _qwen_cloud_engine() -> CadArenaLangChainEngine:
    """Return the cached LangChain engine configured for cloud Qwen reasoning."""

    return CadArenaLangChainEngine(
        OLLAMA_CLOUD_GENERATE_URL,
        QWEN_CLOUD_MODEL_ID,
        OLLAMA_API_KEY or None,
    )


def _resolve_langchain_engine(model_choice: ParseDesignModel) -> CadArenaLangChainEngine | None:
    """Resolve the best available LangChain engine for iterative intent and diff extraction."""

    if model_choice == ParseDesignModel.OLLAMA:
        return _ollama_engine()
    if model_choice == ParseDesignModel.QWEN_CLOUD:
        return _qwen_cloud_engine()
    if OLLAMA_API_KEY:
        return _qwen_cloud_engine()
    return None


async def run_iterative_design(
    user_prompt: str,
    current_layout: dict[str, Any] | None,
    project_id: str,
    model_choice: ParseDesignModel = ParseDesignModel.HUGGINGFACE,
    recovery_mode: RecoveryMode = RecoveryMode.REPAIR,
) -> dict[str, Any]:
    """
    Route iterative design requests using only current-layout presence.

    A missing current layout triggers a fresh full parse, while an existing layout
    triggers best-effort diff extraction followed by patching and revalidation.
    """

    # Route brand-new prompts straight to the existing one-shot parser without intent classification.
    diff_engine = _resolve_langchain_engine(model_choice)
    if current_layout is None:
        logger.info("[DiffOrchestrator] project=%s path=new_design", project_id)
        return await _run_full_parse_fallback(
            user_prompt=user_prompt,
            project_id=project_id,
            intent="NEW_DESIGN",
            model_choice=model_choice,
            recovery_mode=recovery_mode,
            diff_engine=diff_engine,
        )

    # Treat the presence of current_layout as the only signal that this is an iterative edit.
    logger.info("[DiffOrchestrator] project=%s path=iterative_edit", project_id)
    diff: dict[str, Any] = {}
    if diff_engine is None:
        logger.warning("[DiffOrchestrator] no diff engine available - falling back to heuristics/full parse")
    else:
        try:
            # Try surgical diff extraction first so common edits stay scoped to the current plan.
            diff = await diff_engine.extract_diff(user_prompt, current_layout, project_id)
        except Exception as exc:
            logger.warning("[DiffOrchestrator] extract_diff failed: %s - falling back to heuristics/full parse", exc)

    # Keep a deterministic heuristic fallback for common edits when LLM diff extraction is unavailable.
    if not diff or not str(diff.get("operation", "")).strip():
        diff = _heuristic_diff_from_prompt(user_prompt, current_layout)
        logger.info("[DiffOrchestrator] heuristic_diff=%s", diff.get("operation"))

    # Regenerate the whole layout only when no usable surgical diff could be derived.
    if not diff or not str(diff.get("operation", "")).strip():
        logger.info("[DiffOrchestrator] project=%s empty_diff -> full_parse", project_id)
        return await _run_full_parse_fallback(
            user_prompt=user_prompt,
            project_id=project_id,
            intent="FULL_PARSE_FALLBACK",
            model_choice=model_choice,
            recovery_mode=recovery_mode,
            diff_engine=diff_engine,
        )

    # Patch the provided layout geometry without mutating the caller-owned input object.
    patcher = LayoutPatcher()
    try:
        patched_layout = patcher.apply(current_layout, diff)
    except Exception as exc:
        logger.warning("[DiffOrchestrator] patcher failed: %s - returning original layout", exc)
        return _iterative_failure_response(current_layout, "PATCH_FAILED", _error_messages(exc))

    extracted_payload = _synthesize_extracted_payload(patched_layout)
    finalized_layout = copy.deepcopy(patched_layout)
    opening_planner_failed = False

    # Rebuild openings for the patched layout, but keep the patched geometry usable even if this step fails.
    planner = DeterministicOpeningPlanner()
    try:
        finalized_layout = planner.plan(
            extracted_payload=extracted_payload,
            layout_payload=patched_layout,
        )
    except Exception as exc:
        logger.warning("[DiffOrchestrator] opening planner failed: %s", exc)
        opening_planner_failed = True

    # Validate fully replanned layouts, but keep patched geometry available if opening planning failed.
    if not opening_planner_failed:
        validator = LayoutValidator()
        try:
            validator.validate(
                extracted_payload=extracted_payload,
                planned_payload=finalized_layout,
                selected_topology="iterative_patch",
            )
        except Exception as exc:
            logger.warning("[DiffOrchestrator] validation error: %s - returning original layout", exc)
            return _iterative_failure_response(current_layout, "VALIDATION_FAILED", _error_messages(exc))

    # Return the fully patched layout payload with the requested iterative metadata contract.
    changed_rooms = _collect_changed_room_names(diff, finalized_layout)
    return {
        "layout": finalized_layout,
        "intent": str(diff.get("operation", "EDIT") or "EDIT").upper(),
        "changed_rooms": changed_rooms,
        "is_new_design": False,
        "self_review_triggered": False,
    }


async def _run_full_parse_fallback(
    user_prompt: str,
    project_id: str,
    intent: str,
    model_choice: ParseDesignModel,
    recovery_mode: RecoveryMode,
    diff_engine: CadArenaLangChainEngine | None,
) -> dict[str, Any]:
    """Run the untouched one-shot parser and adapt its result to iterative metadata."""

    # Reuse the existing parser flow exactly, but pin the fallback defaults decided in the plan.
    result = await parse_design_prompt_with_metadata(
        prompt=user_prompt,
        model_choice=model_choice,
        recovery_mode=recovery_mode,
        request_id=f"iterative_{project_id}_{uuid4().hex}",
    )

    # Clear project memory after a fresh full parse so future edits start from the new design baseline.
    if diff_engine is not None:
        diff_engine.clear_memory(project_id)
    return {
        "layout": copy.deepcopy(result.data),
        "intent": intent,
        "changed_rooms": [],
        "is_new_design": True,
        "self_review_triggered": result.self_review_triggered,
    }


def _synthesize_extracted_payload(layout: dict[str, Any]) -> dict[str, Any]:
    """Build the minimal extracted payload required by validator and opening planner."""

    # Copy only the fields the downstream deterministic components expect to read.
    boundary_raw = layout.get("boundary", {})
    boundary = copy.deepcopy(boundary_raw) if isinstance(boundary_raw, dict) else {}
    room_program: list[dict[str, Any]] = []
    for room in layout.get("rooms", []):
        if not isinstance(room, dict):
            continue
        name = str(room.get("name", "")).strip()
        room_type = str(room.get("room_type", "")).strip().lower()
        if not name or not room_type:
            continue
        room_program.append(
            {
                "name": name,
                "room_type": room_type,
                "count": 1,
            }
        )

    # Provide empty constraints because iterative current_layout inputs do not preserve extraction metadata.
    return {
        "boundary": boundary,
        "room_program": room_program,
        "constraints": {
            "notes": [],
            "adjacency_preferences": [],
        },
    }


def _collect_changed_room_names(
    diff: dict[str, Any],
    patched_layout: dict[str, Any],
) -> list[str]:
    """Derive a stable list of changed room names from the diff payload."""

    # Read the diff operation once so the name-collection logic can stay explicit and deterministic.
    operation = str(diff.get("operation", "") or "").strip().lower()
    changes = diff.get("changes", {})
    if not isinstance(changes, dict):
        return []

    # Gather room names according to the requested metadata contract for each operation type.
    names: list[str] = []
    if operation == "modify":
        names.extend(
            str(room.get("name", "")).strip()
            for room in changes.get("rooms_to_modify", [])
            if isinstance(room, dict)
        )
    elif operation == "add":
        names.extend(
            str(room.get("name", "")).strip()
            for room in changes.get("rooms_to_add", [])
            if isinstance(room, dict)
        )
    elif operation == "remove":
        names.extend(
            str(name).strip()
            for name in changes.get("rooms_to_remove", [])
            if isinstance(name, str)
        )
    elif operation == "swap":
        for pair in changes.get("rooms_to_swap", []):
            if not isinstance(pair, list):
                continue
            names.extend(str(name).strip() for name in pair if isinstance(name, str))
    elif operation == "adjust_boundary":
        names.extend(
            str(room.get("name", "")).strip()
            for room in patched_layout.get("rooms", [])
            if isinstance(room, dict)
        )

    # Deduplicate names while preserving the first observed order.
    return _unique_names(names)


def _iterative_failure_response(
    current_layout: dict[str, Any],
    intent: str,
    issues: list[str],
) -> dict[str, Any]:
    """Return the original layout plus structured error details after iterative failure."""

    # Hand the caller back the untouched original layout rather than a partially broken patch.
    return {
        "layout": copy.deepcopy(current_layout),
        "intent": intent,
        "changed_rooms": [],
        "is_new_design": False,
        "self_review_triggered": False,
        "error": issues,
    }


def _error_messages(error: Exception) -> list[str]:
    """Convert validation or opening-planner exceptions into API-friendly strings."""

    # Preserve structured rule messages when deterministic rule violations are available.
    if isinstance(error, RuleViolationError):
        return [error.to_detail_message()]
    message = str(error).strip()
    return [message or error.__class__.__name__]


def _unique_names(names: list[str]) -> list[str]:
    """Return unique non-empty names while preserving the input order."""

    # Deduplicate change metadata without scrambling room ordering for callers.
    unique: list[str] = []
    seen: set[str] = set()
    for name in names:
        cleaned = str(name).strip()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        unique.append(cleaned)
    return unique


def _heuristic_diff_from_prompt(
    user_prompt: str,
    current_layout: dict[str, Any],
) -> dict[str, Any]:
    """
    Extract a best-effort diff from the user prompt using
    simple keyword heuristics - no LLM call required.

    Used as fallback when LangChain/Ollama is unavailable.
    Returns a valid diff dict or empty dict if nothing matched.

    Supported patterns:
      add:    "add a bathroom", "add bedroom"
      remove: "remove the kitchen", "delete bathroom"
      modify: "make the bedroom bigger", "enlarge kitchen"
              "shrink the living room", "make X smaller"
      swap:   "swap kitchen and bathroom"
    """
    import re

    prompt_lower = user_prompt.lower().strip()
    rooms = current_layout.get("rooms", [])
    room_names = [r["name"] for r in rooms]

    room_type_map = {
        "bedroom": "bedroom",
        "bed room": "bedroom",
        "bathroom": "bathroom",
        "toilet": "bathroom",
        "wc": "bathroom",
        "kitchen": "kitchen",
        "cooking": "kitchen",
        "living": "living",
        "living room": "living",
        "lounge": "living",
        "dining": "living",
        "dining room": "living",
        "corridor": "corridor",
        "hallway": "corridor",
    }

    # Remove an existing room by matching the prompt text against current room names.
    remove_match = re.search(
        r"(?:remove|delete|get rid of)\s+(?:the\s+)?(.+?)(?:\s*$|\s+and\b)",
        prompt_lower,
    )
    if remove_match:
        target = remove_match.group(1).strip()
        matched = [name for name in room_names if target in name.lower()]
        if matched:
            return {
                "operation": "remove",
                "changes": {"rooms_to_remove": matched[:1]},
            }

    # Swap two existing rooms when both prompt fragments resolve against the layout.
    swap_match = re.search(
        r"swap\s+(.+?)\s+and\s+(.+?)(?:\s*$)",
        prompt_lower,
    )
    if swap_match:
        a_hint = swap_match.group(1).strip()
        b_hint = swap_match.group(2).strip()
        room_a = next((name for name in room_names if a_hint in name.lower()), None)
        room_b = next((name for name in room_names if b_hint in name.lower()), None)
        if room_a and room_b:
            return {
                "operation": "swap",
                "changes": {"rooms_to_swap": [[room_a, room_b]]},
            }

    # Scale an existing room up or down based on simple resize language.
    modify_match = re.search(
        r"(?:make|enlarge|expand|increase|shrink|reduce|decrease|resize)"
        r"\s+(?:the\s+)?(.+?)"
        r"\s+(?:bigger|larger|smaller|wider|narrower|more\s+\w+)?",
        prompt_lower,
    )
    if modify_match:
        target = modify_match.group(1).strip()
        matched_room = next(
            (room for room in rooms if target in room["name"].lower()),
            None,
        )
        if matched_room:
            is_shrink = any(
                keyword in prompt_lower
                for keyword in ["smaller", "shrink", "reduce", "decrease", "narrower"]
            )
            scale = 0.75 if is_shrink else 1.30
            return {
                "operation": "modify",
                "changes": {
                    "rooms_to_modify": [
                        {
                            "name": matched_room["name"],
                            "room_type": matched_room["room_type"],
                            "width": round(matched_room["width"] * scale, 3),
                            "height": round(matched_room["height"] * scale, 3),
                            "origin": matched_room["origin"],
                        }
                    ]
                },
            }

    # Add a new room type using boundary-scaled defaults when no exact geometry is supplied.
    add_match = re.search(
        r"add\s+(?:a\s+|an\s+)?(.+?)(?:\s*$|\s+(?:to|next|beside)\b)",
        prompt_lower,
    )
    if add_match:
        room_hint = add_match.group(1).strip()
        room_type = next(
            (value for key, value in room_type_map.items() if key in room_hint),
            "living",
        )
        name = room_hint.title() if room_hint else room_type.title()
        boundary = current_layout.get("boundary", {})
        bw = boundary.get("width", 10.0)
        bh = boundary.get("height", 10.0)
        default_w = min(bw * 0.25, 4.0)
        default_h = min(bh * 0.25, 3.5)
        return {
            "operation": "add",
            "changes": {
                "rooms_to_add": [
                    {
                        "name": name,
                        "room_type": room_type,
                        "width": round(default_w, 2),
                        "height": round(default_h, 2),
                    }
                ]
            },
        }

    return {}


def _resolve_room_name(
    fragment: str,
    room_names: list[str],
    lowered_names: dict[str, str],
) -> str | None:
    """Resolve fuzzy room name text into an existing room name from the current layout."""

    cleaned = re.sub(r"\s+", " ", str(fragment or "").strip().lower())
    cleaned = re.sub(r"^(the|a|an)\s+", "", cleaned)
    if not cleaned:
        return None
    if cleaned in lowered_names:
        return lowered_names[cleaned]

    for room_name in room_names:
        lowered = room_name.lower()
        if cleaned in lowered or lowered in cleaned:
            return room_name

    cleaned_compact = re.sub(r"[^a-z0-9]+", "", cleaned)
    for room_name in room_names:
        lowered_compact = re.sub(r"[^a-z0-9]+", "", room_name.lower())
        if cleaned_compact and cleaned_compact in lowered_compact:
            return room_name
    return None


def _canonical_room_type(raw_text: str) -> str | None:
    """Map fuzzy room labels into canonical CadArena room types."""

    cleaned = re.sub(r"\s+", " ", str(raw_text or "").strip().lower())
    room_type_map = {
        "master bedroom": "bedroom",
        "bedroom": "bedroom",
        "bathroom": "bathroom",
        "toilet": "bathroom",
        "wc": "bathroom",
        "restroom": "bathroom",
        "kitchen": "kitchen",
        "living room": "living",
        "living": "living",
        "lounge": "living",
        "corridor": "corridor",
        "hallway": "corridor",
        "stairs": "stairs",
        "stair": "stairs",
    }
    return room_type_map.get(cleaned)


def _default_room_name(room_type: str) -> str:
    """Return the base display name for a canonical room type."""

    base_names = {
        "bedroom": "Bedroom",
        "bathroom": "Bathroom",
        "kitchen": "Kitchen",
        "living": "Living Room",
        "corridor": "Corridor",
        "stairs": "Stairs",
    }
    return base_names.get(room_type, "Room")


def _default_room_size(room_type: str) -> tuple[float, float]:
    """Return default heuristic room dimensions for room additions."""

    default_sizes = {
        "bedroom": (3.2, 3.2),
        "bathroom": (2.0, 2.0),
        "kitchen": (3.0, 2.6),
        "living": (4.2, 3.6),
        "corridor": (1.5, 3.0),
        "stairs": (2.5, 3.0),
    }
    return default_sizes.get(room_type, (2.5, 2.5))


def _next_room_name(current_layout: dict[str, Any], base_name: str) -> str:
    """Return a unique room name derived from the current layout contents."""

    existing_names = {
        str(room.get("name", "")).strip()
        for room in current_layout.get("rooms", [])
        if isinstance(room, dict)
    }
    if base_name not in existing_names:
        return base_name

    index = 2
    while f"{base_name} {index}" in existing_names:
        index += 1
    return f"{base_name} {index}"


def _default_adjacent_room_name(current_layout: dict[str, Any], room_type: str) -> str | None:
    """Pick a stable adjacency hint for heuristic room additions."""

    rooms = [
        room
        for room in current_layout.get("rooms", [])
        if isinstance(room, dict) and str(room.get("name", "")).strip()
    ]
    preferred_types = ["corridor", "living", "kitchen", "bedroom"]
    if room_type == "living":
        preferred_types = ["corridor", "kitchen", "bedroom"]

    for preferred_type in preferred_types:
        for room in rooms:
            if str(room.get("room_type", "")).strip().lower() == preferred_type:
                return str(room.get("name", "")).strip()
    return str(rooms[0].get("name", "")).strip() if rooms else None


def _find_room_by_name(current_layout: dict[str, Any], room_name: str | None) -> dict[str, Any] | None:
    """Return the existing room payload for an exact room name match."""

    cleaned_name = str(room_name or "").strip()
    if not cleaned_name:
        return None
    for room in current_layout.get("rooms", []):
        if not isinstance(room, dict):
            continue
        if str(room.get("name", "")).strip() == cleaned_name:
            return room
    return None
