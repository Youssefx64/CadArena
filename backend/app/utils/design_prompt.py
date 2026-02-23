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

    return (
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
