"""Prompt templates for strict architectural program extraction."""

from __future__ import annotations

import json


_SCHEMA_EXAMPLE = {
    "boundary": {"width": 24.0, "height": 16.0},
    "room_program": [
        {"name": "Master Bedroom", "room_type": "bedroom", "count": 1, "preferred_area": 18.0},
        {"name": "Children Bedroom", "room_type": "bedroom", "count": 2, "preferred_area": 14.0},
        {"name": "Shared Bathroom", "room_type": "bathroom", "count": 1, "preferred_area": 6.0},
        {"name": "Kitchen", "room_type": "kitchen", "count": 1, "preferred_area": 12.0},
        {"name": "Dining Area", "room_type": "living", "count": 1, "preferred_area": 10.0},
    ],
    "constraints": {
        "notes": [
            "Keep private rooms away from main entrance side",
            "Prefer practical circulation",
        ],
        "adjacency_preferences": [["kitchen", "living"], ["bedroom", "bathroom"]],
    },
}


def build_design_parser_prompt(user_prompt: str) -> str:
    """Build a strict prompt that extracts room program intent only."""

    schema_example = json.dumps(_SCHEMA_EXAMPLE, ensure_ascii=False, separators=(",", ":"))
    CRITICAL_RULES = """
    CRITICAL EXTRACTION RULES — violating any rule = invalid output:

    RULE ARABIC:
      Prompts may include translated Arabic keywords.
      Always extract room counts and dimensions from any numbers present.
      If the prompt says "2 bedrooms" extract exactly 2 bedrooms.
      If the prompt says "large" for a room, increase its area by 20%.

    RULE 1 — ROOM COUNT IS SACRED:
      "1 bedroom"  → exactly 1 bedroom in room_program with count=1
      "2 bedrooms" → exactly 1 entry with count=2 OR 2 entries count=1
      NEVER add rooms the user did not request.
      NEVER split one requested room into two entries.
      Synonyms: bedroom=room=chamber | bathroom=toilet=WC=restroom
                kitchen=cooking area | living=lounge=salon=reception

    RULE 2 — BOUNDARY MATH:
      Sum of room areas must be 85%-100% of boundary area.
      No room width < 1.8m. No room height < 1.8m.
      No room width > boundary_width * 0.80.

    RULE 3 — CANONICAL ROOM TYPES ONLY:
      Use ONLY: bedroom, bathroom, kitchen, living, corridor, stairs
      For master bedroom: room_type="bedroom", name="Master Bedroom"
      For dining: room_type="living", name="Dining Area"
      NEVER invent new room_type values.

    RULE 4 — MINIMUM PROPORTIONS:
      living room  → min 25% of total floor area
      each bedroom → min 12% of total floor area
      kitchen      → min 8%  of total floor area
      bathroom     → min 5%  of total floor area

    RULE 5 — OUTPUT ONLY VALID JSON. No markdown. No explanation.

    RULE 6 — LIVING ROOM PROPORTION CAP:
      Living room must NOT exceed 40% of total floor area.
      If the user requests a large living room, still cap at 40%.
      The remaining 60% must be distributed among other rooms.
    """

    return (
        # Keep the critical extraction rules first so room-count and boundary constraints are the highest-priority instructions.
        f"{CRITICAL_RULES.strip()}\n\n"
        "You are an architectural intent extractor for CAD generation.\n"
        "Input is English only.\n"
        "All output text values MUST be English only.\n"
        "Convert the user request into EXACTLY one valid JSON object.\n"
        "Do not output markdown, code fences, comments, or explanatory text.\n"
        "Top-level keys must be exactly: boundary, room_program, constraints.\n"
        "Rules:\n"
        "1) boundary.width > 0 and boundary.height > 0.\n"
        "2) room_program entries must include: name, room_type, count.\n"
        "3) room_type must be one of: living, bedroom, kitchen, bathroom, corridor, stairs.\n"
        "4) Optional area fields per program entry: preferred_area, min_area, max_area.\n"
        "5) constraints may include notes and adjacency_preferences only.\n"
        "6) Never include room coordinates, walls, or opening geometry.\n"
        "7) No extra keys anywhere.\n"
        "8) Return JSON only.\n"
        "JSON schema example:\n"
        f"{schema_example}\n"
        "User request:\n"
        f"{user_prompt.strip()}\n"
    )
