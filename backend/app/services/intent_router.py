"""Lightweight intent routing for CadArena workspace messages.

Classifies user input before dispatching to the correct pipeline.
Regex-based for speed — runs at the API boundary before any LLM call.
"""

from __future__ import annotations

import re
from enum import Enum


class MessageIntent(str, Enum):
    DESIGN_REQUEST = "design_request"
    EDIT_REQUEST = "edit_request"
    CONVERSATION = "conversation"


_DESIGN_KEYWORDS = [
    r"\b(design|create|generate|build|make|draw|plan|sketch)\b",
    r"\b(apartment|flat|house|villa|home|office|studio|unit)\b",
    r"\b(bedroom|bathroom|kitchen|living\s+room|corridor|hallway)\b",
    r"\b(floor\s*plan|layout|blueprint|مسقط|شقة|غرفة|حمام|مطبخ)\b",
    r"\b(\d+)\s*(bed|bath|br|bdr|room|غرفة|أوضة)\b",
    r"\b(meters?|m²|m2|sqft|square)\b",
]

_EDIT_KEYWORDS = [
    r"\b(make|change|move|resize|enlarge|shrink|remove|add|swap|adjust)\b",
    r"\b(bigger|smaller|wider|narrower|larger)\b",
    r"\b(the\s+)(bedroom|bathroom|kitchen|living|corridor)\b",
]

_CONVERSATION_PATTERNS = [
    r"^(hi|hello|hey|marhaba|salam|مرحبا|اهلا|هاي|هلو)[!.,\s]*$",
    r"^(how\s+are\s+you|كيف\s+حالك|ايه\s+الاخبار)[?!.\s]*$",
    r"^(what\s+(can|do)\s+you|ماذا\s+تفعل|بتعمل\s+اي)[?!.\s]*$",
    r"^(who\s+are\s+you|من\s+انت)[?!.\s]*$",
    r"^(thank|شكرا|تمام|ok|okay|cool|great|nice|wow)[!.,\s]*$",
    r"^(help|مساعدة)[?!.\s]*$",
]


def classify_intent(
    prompt: str,
    has_existing_layout: bool = False,
) -> MessageIntent:
    """Classify a user message into DESIGN_REQUEST, EDIT_REQUEST, or CONVERSATION.

    Priority order:
    1. Pure conversation patterns → CONVERSATION
    2. Short messages with no design signals → CONVERSATION
    3. Edit keywords + existing layout → EDIT_REQUEST
    4. Any design keyword → DESIGN_REQUEST
    5. Existing layout + ambiguous → EDIT_REQUEST
    6. Default → CONVERSATION (safe fallback)
    """
    text = prompt.strip().lower()

    for pattern in _CONVERSATION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return MessageIntent.CONVERSATION

    if len(text.split()) <= 3 and not any(
        re.search(p, text, re.IGNORECASE) for p in _DESIGN_KEYWORDS
    ):
        return MessageIntent.CONVERSATION

    has_edit_signal = any(
        re.search(p, text, re.IGNORECASE) for p in _EDIT_KEYWORDS
    )
    if has_edit_signal and has_existing_layout:
        return MessageIntent.EDIT_REQUEST

    if any(re.search(p, text, re.IGNORECASE) for p in _DESIGN_KEYWORDS):
        return MessageIntent.DESIGN_REQUEST

    if has_existing_layout:
        return MessageIntent.EDIT_REQUEST

    return MessageIntent.CONVERSATION
