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

    ════════════════════════════════════════════════════════════════════════════════
    EGYPTIAN BUILDING CODE (EBC 2023) — الكود المصري للمباني ٢٠٢٣
    Mandatory minimum dimensions per EBC Chapter 7 and Law 119/2008
    ════════════════════════════════════════════════════════════════════════════════

    BEDROOM:       min 9.0 m²,   min side 2.75 m (EBC Chapter 7)
    BATHROOM:      min 2.5 m²,   min side 1.20 m (EBC Chapter 7)
    KITCHEN:       min 4.0 m²,   min side 1.80 m (EBC Chapter 7)
    LIVING ROOM:   min 12.0 m²,  min side 3.00 m (EBC Chapter 7)
    CORRIDOR:      min width 1.20 m (Law 119/2008 Article 74 — HARD LIMIT, NEVER smaller)
    ENTRANCE:      min 3.0 m²,   min side 1.50 m
    BALCONY:       min 3.0 m²,   min depth 1.20 m

    EBC FORBIDDEN ADJACENCIES (violations trigger re-generation):
      ✗ Bathroom door opening directly to Kitchen (regulatory violation)
      ✗ Bathroom door opening to Dining room
      ✗ Bedroom door directly to Kitchen

    DOOR WIDTH STANDARDS (EBC Chapter 9, minimum clear opening):
      Main Entry:    1.00 m
      Bedroom:       0.90 m
      Kitchen:       0.80 m
      Bathroom:      0.70 m (or 0.80 m if accessible)
      Corridor:      0.90 m

    APARTMENT TYPE BENCHMARKS (Egyptian Housing Ministry — معايير الإسكان المصرية):
      Studio:        25–45 m²
      1-Bedroom:     45–75 m²
      2-Bedroom:     75–120 m²
      3-Bedroom:     100–160 m²
      4-Bedroom:     140–220 m²
      Villa:         200–500 m²

    ════════════════════════════════════════════════════════════════════════════════
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
      Minimum usable room sizes per EBC 2023: bedroom 9 m², bathroom 2.5 m², kitchen 4 m², living 12 m², corridor width 1.2 m.

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


# Normalized Arabic letters mapping (Alef to bare Alef, Teh Marbutah to Ha, Alef Maksura to Yeh)
_ARABIC_TO_ENGLISH_MAP = {
    # Duals (with different spelling variations normalized to Teh Marbutah/Ha/Alef Maksura/Yeh)
    "حمامين": "2 bathrooms",
    "حمامان": "2 bathrooms",
    "غرفتين": "2 bedrooms",
    "غرفتان": "2 bedrooms",
    "اوضتين": "2 bedrooms",
    "اوضتان": "2 bedrooms",
    "نومين": "2 bedrooms",
    "مطبخين": "2 kitchens",
    "مطبخان": "2 kitchens",
    "ممرين": "2 corridors",
    "ممران": "2 corridors",
    "سلمين": "2 stairs",
    "سلمان": "2 stairs",

    # Plurals & Phrases
    "غرف نوم": "bedrooms",
    "غرفه نوم": "bedroom",
    "اوضه نوم": "bedroom",
    "اوض نوم": "bedrooms",
    "غرف معيشه": "living rooms",
    "غرفه معيشه": "living room",
    "غرف جلوس": "living rooms",
    "غرفه جلوس": "living room",
    "دوره مياه": "bathroom",
    "دورات مياه": "bathrooms",
    
    # Creation/Edit verbs
    "اضافه": "add",
    "اضف": "add",
    "ضيف": "add",
    "زود": "add",
    "حط": "add",
    "احذف": "remove",
    "امسح": "remove",
    "ازاله": "remove",
    "ازيل": "remove",
    "حذف": "remove",
    "مسح": "remove",
    "الغ": "remove",
    "شيل": "remove",
    "كبر": "make bigger",
    "وسع": "make bigger",
    "زياده": "make bigger",
    "توسيع": "make bigger",
    "صغر": "make smaller",
    "قلل": "make smaller",
    "تضييق": "make smaller",
    "بدل": "swap",
    "تبديل": "swap",
    "غير": "swap",
    "تغيير": "swap",

    # Prepositions & Adjectives
    "بجانب": "adjacent to",
    "جنب": "adjacent to",
    "بجوار": "adjacent to",
    "بين": "between",

    # Singular Rooms
    "حمام": "bathroom",
    "حمامات": "bathrooms",
    "مطبخ": "kitchen",
    "مطابخ": "kitchens",
    "ريسبشن": "living room",
    "صاله": "living room",
    "صالون": "living room",
    "سفره": "dining room",
    "ممر": "corridor",
    "طرقه": "corridor",
    "سلم": "stairs",
    "غرف": "bedrooms",
    "غرفه": "bedroom",
    "اوضه": "bedroom",
    "اوض": "bedrooms",
    
    # Numbers
    "واحد": "1",
    "واحده": "1",
    "اثنين": "2",
    "اثنان": "2",
    "اتنين": "2",
    "ثلاثه": "3",
    "ثلاث": "3",
    "تلاته": "3",
    "تلات": "3",
    "اربعه": "4",
    "اربع": "4",
    "خمسه": "5",
    "خمس": "5",
    "سته": "6",
    "ست": "6",
    "سبعه": "7",
    "سبع": "7",
    "ثمانيه": "8",
    "ثماني": "8",
    "تمانيه": "8",
    "تماني": "8",
    "تسعه": "9",
    "تسع": "9",
    "عشره": "10",
    "عشر": "10",
    
    # Dimensions & Units
    "متر مربع": "sqm",
    "متر مربعا": "sqm",
    "م٢": "sqm",
    "م2": "sqm",
    "متر": "meters",
    "امتار": "meters",
    "م": "meters",
    "في": " x ",
    "بـ": " x ",
    "ضرب": " x ",
    "عرض": "width",
    "عرضه": "width",
    "طول": "height",
    "طوله": "height",
    "ارتفاع": "height",
    "مساحه": "area",
    "بمساحه": "area",
    
    # Building types
    "شقه": "apartment",
    "بيت": "house",
    "فيلا": "villa",
}


def normalize_arabic_text(text: str) -> str:
    """Normalize Arabic orthographic variations for robust key mapping."""
    # Normalize Alef variations
    text = re.sub(r"[إأآ]", "ا", text)
    # Normalize Teh Marbutah to Ha
    text = re.sub(r"ة", "ه", text)
    # Normalize Alef Maksura to Yeh
    text = re.sub(r"ى", "ي", text)
    return text


def translate_arabic_to_english(prompt: str) -> str:
    """
    Robustly translate Arabic architectural/design keywords to English
    without stripping unmatched text.
    """
    import unicodedata
    normalized_prompt = unicodedata.normalize("NFKC", str(prompt or "")).strip()
    
    # Normalize Arabic digits first
    translated = normalized_prompt
    for arabic_digit, ascii_digit in [
        ("٠", "0"), ("١", "1"), ("٢", "2"), ("٣", "3"), ("٤", "4"),
        ("٥", "5"), ("٦", "6"), ("٧", "7"), ("٨", "8"), ("٩", "9")
    ]:
        translated = translated.replace(arabic_digit, ascii_digit)
        
    translated = normalize_arabic_text(translated)
    
    # Sort keywords by length descending
    sorted_keywords = sorted(
        _ARABIC_TO_ENGLISH_MAP.items(),
        key=lambda item: len(item[0]),
        reverse=True,
    )
    
    for arabic, english in sorted_keywords:
        translated = translated.replace(arabic, f" {english} ")
        
    return re.sub(r"\s+", " ", translated).strip()

