"""Prompt templates for strict architectural program extraction."""

from __future__ import annotations

import hashlib
import json
import math
import re


_SCHEMA_EXAMPLE = {
    "boundary": {"width": 12.0, "height": 9.0},
    "room_program": [
        {"name": "Bedroom 1", "room_type": "bedroom", "count": 1, "preferred_area": 19.67, "min_area": 16.72, "max_area": 22.62},
        {"name": "Bedroom 2", "room_type": "bedroom", "count": 1, "preferred_area": 19.67, "min_area": 16.72, "max_area": 22.62},
        {"name": "Bathroom", "room_type": "bathroom", "count": 1, "preferred_area": 8.74, "min_area": 7.43, "max_area": 10.05},
        {"name": "Kitchen", "room_type": "kitchen", "count": 1, "preferred_area": 13.11, "min_area": 11.14, "max_area": 15.08},
        {"name": "Living Room", "room_type": "living", "count": 1, "preferred_area": 21.85, "min_area": 18.57, "max_area": 25.13},
        {"name": "Main Corridor", "room_type": "corridor", "count": 1, "preferred_area": 8.76, "min_area": 7.45, "max_area": 10.07},
    ],
    "constraints": {
        "notes": [
            "bedrooms in private zone",
            "kitchen near living",
        ],
        "adjacency_preferences": [
            ["bedroom", "bathroom"],
            ["kitchen", "living"],
            ["corridor", "bedroom"],
            ["corridor", "bathroom"],
        ],
    },
}


def _infer_boundary_from_area(user_prompt: str) -> str:
    """
    If user mentions total area (e.g. '120 sqm', '120 متر مربع'),
    compute a landscape-oriented boundary that matches that area.
    Returns a boundary hint string, or empty string if not found.
    """
    # Match area in sq meters with various formats
    match = re.search(
        r"(\d{2,4})\s*(?:sqm|m²|m2|sq\s*m|متر\s*مربع|square\s*meters?)",
        user_prompt,
        re.IGNORECASE,
    )
    if not match:
        return ""

    try:
        area = float(match.group(1))
    except (ValueError, IndexError):
        return ""

    # Sanity clamp
    area = max(15.0, min(area, 500.0))

    # Compute landscape boundary (golden ratio ≈ 1.3 for w/h)
    h = math.sqrt(area / 1.3)
    w = area / h

    # Round to nearest 0.5m for clean dimensions
    w = round(w * 2) / 2
    h = round(h * 2) / 2

    # Ensure landscape orientation
    if w < h:
        w, h = h, w

    return (
        f"\n    AREA FROM PROMPT: User requested {area:.0f} m² total area.\n"
        f"    BOUNDARY MUST BE: width={w} m, height={h} m (landscape orientation).\n"
        f"    Do NOT default to 20x12. Do NOT use any other boundary. Use {w}x{h} EXACTLY."
    )


def build_design_parser_prompt(user_prompt: str) -> str:
    """Build a strict prompt that extracts room program intent only."""

    schema_example = json.dumps(_SCHEMA_EXAMPLE, ensure_ascii=False, separators=(",", ":"))

    # Variety seed — unique context per prompt to fight template repetition
    variety_seed = hashlib.md5(user_prompt.encode()).hexdigest()[:8]

    # Reinforce explicit counts from the prompt
    bedroom_match = re.search(r"(\d+)\s*(?:bedroom|bed\s*room|br|غرفة|أوضة)", user_prompt, re.I)
    bedroom_hint = (
        f"\n    BEDROOM COUNT FROM PROMPT: {bedroom_match.group(1)} bedrooms — this is SACRED, match exactly."
        if bedroom_match else ""
    )

    boundary_match = re.search(r"(\d+(?:\.\d+)?)\s*[xX×]\s*(\d+(?:\.\d+)?)\s*(?:m|meter)?", user_prompt, re.I)
    boundary_hint = (
        f"\n    BOUNDARY FROM PROMPT: {boundary_match.group(1)}x{boundary_match.group(2)} — use EXACTLY these dimensions."
        if boundary_match else ""
    )

    # Add area-based boundary inference when user specifies total area
    area_hint = _infer_boundary_from_area(user_prompt) if not boundary_hint else ""

    CRITICAL_RULES = f"""
    REQUEST_SEED: {variety_seed}

    CRITICAL EXTRACTION RULES — violating any rule = invalid output:

    ROLE:
      You are an expert architectural spatial planner inside CadArena.
      Convert natural language into one strict JSON room program only.
      Think like a licensed architect: exact counts, plausible sizes, clean zoning.
      {bedroom_hint}{boundary_hint}{area_hint}

    RULE 1 — BOUNDARY (read user dimensions first):
      If user says "10x8 meters" or "12x10m" -> use those dimensions EXACTLY.
      Always output landscape orientation: boundary.width >= boundary.height.
      If no dimensions are present, infer from requested room count:
        1-2 rooms -> 8x6 m | 3-4 rooms -> 12x9 m | 5-6 rooms -> 16x10 m | 7+ rooms -> 20x12 m
      Structural living/corridor defaults do not inflate this boundary bucket.
      FORBIDDEN: Never default to 20x12 for a small apartment.

    RULE 2 — ROOM COUNT IS SACRED:
      "2 bedrooms" -> exactly 2 bedroom entries, each count=1.
      "a bathroom" -> exactly 1 bathroom entry, count=1.
      "kitchen" -> exactly 1 kitchen entry, count=1.
      NEVER add extra bedrooms or bathrooms beyond requested count.
      NEVER add dining room, office, garage, family lounge, or duplicate living spaces unless explicitly requested.

    RULE 3 — IMPLIED ESSENTIALS:
      If no public-zone room exists, silently add exactly 1 Living Room.
      If bedroom_count >= 2, silently add exactly 1 Main Corridor.
      These are structural defaults, not user-requested count additions.
      Nothing else implied.

    RULE 4 — CANONICAL ROOM TYPES ONLY:
      Use ONLY: bedroom, bathroom, kitchen, living, corridor, stairs
      Dining, reception, salon, and lounge use room_type="living".
      Master bedroom uses room_type="bedroom".
      NEVER invent new room_type values.

    RULE 5 — AREA RULES:
      Every room entry must include preferred_area, min_area, and max_area.
      min_area must equal preferred_area * 0.85.
      max_area must equal preferred_area * 1.15.
      Sum(preferred_area * count) must be 80%-95% of boundary area.
      Target 85% coverage when distributing areas.
      living room <= 28% of boundary area.
      any single room <= 35% of boundary area.
      Minimum usable room sizes: bedroom 9 m2, bathroom 3.5 m2, kitchen 6 m2, living 12 m2, corridor width 1.2 m.

    RULE 6 — AREA CALCULATION:
      total_area = boundary.width * boundary.height.
      bedroom target = total_area * 0.18 each (capped at total_area * 0.25).
      bathroom target = total_area * 0.08 each.
      kitchen target = total_area * 0.12.
      corridor target = total_area * 0.08 if needed.
      living receives remaining target area, capped at total_area * 0.28.
      Distribute remaining area proportionally without violating caps.

    RULE 7 — ADJACENCY:
      Include adjacency_preferences for bedroom-bathroom when both exist.
      Include adjacency_preferences for kitchen-living when both exist.
      Include corridor-bedroom and corridor-bathroom when corridor exists.
      NEVER include bedroom-kitchen or bathroom-kitchen adjacency.

    RULE 8 — OUTPUT ONLY VALID JSON:
      No markdown. No code fences. No comments. No explanation.
      Top-level keys must be exactly: boundary, room_program, constraints.

    FORBIDDEN OUTPUT PATTERNS:
      - boundary width=20, height=12 for a 2-3 room apartment
      - "Family Lounge", "Lounge 1", "Reception Room" as room names
      - living room preferred_area > 50 m2 in a small apartment
      - More bedrooms than the user requested
      - room_type values not in the canonical list
    """

    return (
        f"{CRITICAL_RULES.strip()}\n\n"
        "Architectural intent extractor for CAD generation.\n"
        "Input may be English or Arabic. Output text values MUST be English.\n"
        "Convert this request into exactly one valid JSON object.\n"
        f"Schema example: {schema_example}\n"
        f"User request: {user_prompt.strip()}\n"
        "JSON output:"
    )
