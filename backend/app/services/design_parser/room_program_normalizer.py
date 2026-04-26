"""Deterministic normalization for extracted architectural room programs."""

from __future__ import annotations

import re
import unicodedata
from typing import Any


ALLOWED_ROOM_TYPES = {"bedroom", "bathroom", "kitchen", "living", "corridor", "stairs"}
PUBLIC_ROOM_TYPES = {"living"}

_EPSILON = 1e-6
_TARGET_COVERAGE = 0.85
_LOW_COVERAGE = 0.80
_HIGH_COVERAGE = 0.95
_MAX_ROOM_RATIO = 0.35
_MAX_LIVING_RATIO = 0.28

_DIMENSION_PATTERN = re.compile(
    r"(?P<w>\d+(?:\.\d+)?)\s*(?:m|meter|meters)?\s*[x×]\s*"
    r"(?P<h>\d+(?:\.\d+)?)\s*(?:m|meter|meters)?",
    re.I,
)
_NUMBER_WORDS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
}
_COUNT_TOKEN = r"(?P<count>\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)"

_ROOM_COUNT_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(rf"\b{_COUNT_TOKEN}\s*[- ]*(?:master|primary|children|child|kids?)?\s*bedrooms?\b", re.I), "bedroom"),
    (
        re.compile(
            rf"\b{_COUNT_TOKEN}\s*[- ]*(?:(?:private|en[- ]?suite|shared|guest|master)\s+)?"
            r"(?:bathrooms?|baths?|toilets?|wc|restrooms?)\b",
            re.I,
        ),
        "bathroom",
    ),
    (re.compile(rf"\b{_COUNT_TOKEN}\s*[- ]*laundr(?:y|ies)\b", re.I), "bathroom"),
    (re.compile(rf"\b{_COUNT_TOKEN}\s*[- ]*(?:kitchens?|cooking\s+areas?)\b", re.I), "kitchen"),
    (
        re.compile(
            rf"\b{_COUNT_TOKEN}\s*[- ]*(?:living\s+rooms?|lounges?|salons?|receptions?|dining\s+rooms?|dining\s+areas?)\b",
            re.I,
        ),
        "living",
    ),
    (re.compile(rf"\b{_COUNT_TOKEN}\s*[- ]*(?:corridors?|hallways?|passages?)\b", re.I), "corridor"),
    (re.compile(rf"\b{_COUNT_TOKEN}\s*[- ]*storage(?:\s+rooms?)?\b", re.I), "corridor"),
    (re.compile(rf"\b{_COUNT_TOKEN}\s*[- ]*(?:stairs?|staircases?)\b", re.I), "stairs"),
]
_ROOM_IMPLICIT_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b(?:a|an|the)\s+bedroom\b|\bbedroom\b", re.I), "bedroom"),
    (re.compile(r"\b(?:a|an|the)\s+(?:bathroom|bath|toilet|restroom)\b|\b(?:bathroom|bath|toilet|wc|restroom)\b", re.I), "bathroom"),
    (re.compile(r"\b(?:a|an|the)\s+(?:kitchen|cooking\s+area)\b|\b(?:kitchen|cooking\s+area)\b", re.I), "kitchen"),
    (
        re.compile(
            r"\b(?:a|an|the)\s+(?:living\s+room|lounge|salon|reception|dining\s+room|dining\s+area)\b|"
            r"\b(?:living\s+room|lounge|salon|reception|dining\s+room|dining\s+area)\b",
            re.I,
        ),
        "living",
    ),
    (re.compile(r"\b(?:corridor|hallway|passage)\b", re.I), "corridor"),
    (re.compile(r"\b(?:stairs?|staircase)\b", re.I), "stairs"),
]

_ROOM_TYPE_SYNONYMS = {
    "living": "living",
    "living room": "living",
    "living_room": "living",
    "lounge": "living",
    "salon": "living",
    "reception": "living",
    "dining": "living",
    "dining room": "living",
    "dining_room": "living",
    "dining area": "living",
    "family room": "living",
    "bedroom": "bedroom",
    "bed room": "bedroom",
    "bed_room": "bedroom",
    "master bedroom": "bedroom",
    "master_bedroom": "bedroom",
    "primary bedroom": "bedroom",
    "children bedroom": "bedroom",
    "kids bedroom": "bedroom",
    "guest room": "bedroom",
    "study": "bedroom",
    "office": "bedroom",
    "room": "bedroom",
    "chamber": "bedroom",
    "bathroom": "bathroom",
    "bath": "bathroom",
    "toilet": "bathroom",
    "wc": "bathroom",
    "restroom": "bathroom",
    "laundry": "bathroom",
    "kitchen": "kitchen",
    "cooking area": "kitchen",
    "cooking_area": "kitchen",
    "corridor": "corridor",
    "hallway": "corridor",
    "passage": "corridor",
    "storage": "corridor",
    "stairs": "stairs",
    "stair": "stairs",
    "staircase": "stairs",
}
_DEFAULT_NAMES = {
    "bedroom": "Bedroom",
    "bathroom": "Bathroom",
    "kitchen": "Kitchen",
    "living": "Living Room",
    "corridor": "Main Corridor",
    "stairs": "Stairs",
}
_AREA_RATIOS = {
    "bedroom": 0.18,
    "bathroom": 0.08,
    "kitchen": 0.12,
    "living": 0.20,
    "corridor": 0.08,
    "stairs": 0.08,
}
_MANDATORY_MIN_AREAS = {
    "bedroom": 9.0,
    "bathroom": 3.5,
    "kitchen": 6.0,
    "living": 12.0,
    "corridor": 6.0,
    "stairs": 6.0,
}
_FORBIDDEN_ADJACENCIES = {
    frozenset(("bedroom", "kitchen")),
    frozenset(("bathroom", "kitchen")),
}


def normalize_extracted_room_program(payload: dict[str, Any], *, prompt: str | None = None) -> dict[str, Any]:
    """Return a schema-safe, architecturally bounded extraction payload."""

    prompt_text = unicodedata.normalize("NFKC", str(prompt or "")).strip()
    raw_entries = _coerce_room_entries(payload.get("room_program"))
    requested_counts = extract_requested_room_counts(prompt_text)
    boundary_count = _boundary_room_count(raw_entries=raw_entries, requested_counts=requested_counts)
    explicit_boundary = extract_prompt_boundary(prompt_text) if prompt_text else None
    boundary = _resolve_boundary(
        raw_boundary=payload.get("boundary"),
        explicit_boundary=explicit_boundary,
        boundary_count=boundary_count,
        has_prompt=bool(prompt_text),
    )

    room_units = _expand_room_entries(raw_entries)
    room_units = _apply_requested_counts(room_units, requested_counts)
    room_units = _apply_structural_defaults(room_units)
    if not room_units:
        room_units = [{"name": "Living Room", "room_type": "living", "count": 1}]

    room_units = _dedupe_room_names(room_units)
    room_units = _apply_area_distribution(room_units, boundary)
    constraints = _normalize_constraints(payload.get("constraints"), room_units)

    return {
        "boundary": boundary,
        "room_program": room_units,
        "constraints": constraints,
    }


def extract_prompt_boundary(prompt: str) -> tuple[float, float] | None:
    """Extract explicit prompt dimensions and return them in landscape orientation."""

    match = _DIMENSION_PATTERN.search(prompt)
    if match is None:
        return None
    width = _positive_float(match.group("w"))
    height = _positive_float(match.group("h"))
    if width is None or height is None:
        return None
    return (max(width, height), min(width, height))


def extract_requested_room_counts(prompt: str) -> dict[str, int]:
    """Extract explicit or singular-implied room counts from prompt text."""

    normalized = _normalize_number_words(prompt)
    counts: dict[str, int] = {}

    for pattern, room_type in _ROOM_COUNT_PATTERNS:
        total = 0
        for match in pattern.finditer(normalized):
            parsed = _parse_count(match.group("count"))
            if parsed is not None:
                total += parsed
        if total > 0:
            counts[room_type] = counts.get(room_type, 0) + total

    for pattern, room_type in _ROOM_IMPLICIT_PATTERNS:
        if room_type in counts:
            continue
        if pattern.search(normalized):
            counts[room_type] = 1

    return counts


def _coerce_room_entries(raw_program: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_program, list):
        return []

    entries: list[dict[str, Any]] = []
    for raw in raw_program:
        if not isinstance(raw, dict):
            continue
        room_type = _canonical_room_type(raw.get("room_type"))
        if room_type not in ALLOWED_ROOM_TYPES:
            room_type = str(raw.get("room_type", "")).strip().lower()
        count = _positive_int(raw.get("count")) or 1
        name = _clean_name(raw.get("name")) or _DEFAULT_NAMES.get(room_type, "Room")
        entries.append({"name": name, "room_type": room_type, "count": count})
    return entries


def _expand_room_entries(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    expanded: list[dict[str, Any]] = []
    for entry in entries:
        count = _positive_int(entry.get("count")) or 1
        base_name = _clean_name(entry.get("name")) or _DEFAULT_NAMES.get(str(entry.get("room_type")), "Room")
        for index in range(count):
            name = base_name if count == 1 else f"{base_name} {index + 1}"
            expanded.append({"name": name, "room_type": entry["room_type"], "count": 1})
    return expanded


def _apply_requested_counts(
    units: list[dict[str, Any]],
    requested_counts: dict[str, int],
) -> list[dict[str, Any]]:
    if not requested_counts:
        return units

    output = list(units)
    for room_type, expected_count in requested_counts.items():
        if room_type not in ALLOWED_ROOM_TYPES:
            continue
        indices = [index for index, unit in enumerate(output) if unit.get("room_type") == room_type]
        if len(indices) > expected_count:
            remove = set(indices[expected_count:])
            output = [unit for index, unit in enumerate(output) if index not in remove]
        elif len(indices) < expected_count:
            missing = expected_count - len(indices)
            for offset in range(missing):
                if not indices and expected_count > 1:
                    name = f"{_DEFAULT_NAMES[room_type]} {offset + 1}"
                else:
                    name = _DEFAULT_NAMES[room_type]
                output.append({"name": name, "room_type": room_type, "count": 1})
    return output


def _apply_structural_defaults(units: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = list(units)
    has_public_room = any(unit.get("room_type") in PUBLIC_ROOM_TYPES for unit in output)
    if output and not has_public_room:
        output.append({"name": "Living Room", "room_type": "living", "count": 1})

    bedroom_count = sum(1 for unit in output if unit.get("room_type") == "bedroom")
    has_corridor = any(unit.get("room_type") == "corridor" for unit in output)
    if bedroom_count >= 2 and not has_corridor:
        output.append({"name": "Main Corridor", "room_type": "corridor", "count": 1})
    return output


def _apply_area_distribution(
    units: list[dict[str, Any]],
    boundary: dict[str, float],
) -> list[dict[str, Any]]:
    total_area = boundary["width"] * boundary["height"]
    target_area = total_area * _TARGET_COVERAGE
    floors = [_preferred_floor(str(unit["room_type"]), total_area) for unit in units]
    caps = [_preferred_cap(str(unit["room_type"]), total_area) for unit in units]
    preferred = [
        min(max(total_area * _AREA_RATIOS.get(str(unit["room_type"]), 0.08), floors[index]), caps[index])
        for index, unit in enumerate(units)
    ]

    preferred = _grow_to_target(preferred=preferred, caps=caps, target=target_area)
    preferred = _shrink_to_target(preferred=preferred, floors=floors, target=target_area)
    rounded = _round_and_adjust(preferred=preferred, floors=floors, caps=caps, target=target_area)

    output: list[dict[str, Any]] = []
    for unit, preferred_area in zip(units, rounded, strict=False):
        preferred_area = max(preferred_area, 0.01)
        output.append(
            {
                "name": str(unit["name"]),
                "room_type": str(unit["room_type"]),
                "count": 1,
                "preferred_area": preferred_area,
                "min_area": round(preferred_area * 0.85, 2),
                "max_area": round(preferred_area * 1.15, 2),
            }
        )
    return output


def _normalize_constraints(raw_constraints: Any, units: list[dict[str, Any]]) -> dict[str, Any]:
    notes: list[str] = []
    raw_preferences: Any = None
    if isinstance(raw_constraints, dict):
        raw_notes = raw_constraints.get("notes")
        if isinstance(raw_notes, list):
            notes = [str(note).strip() for note in raw_notes if str(note).strip()]
        raw_preferences = raw_constraints.get("adjacency_preferences")

    room_types = {str(unit.get("room_type", "")).strip().lower() for unit in units}
    preferences: list[list[str]] = []
    seen_pairs: set[tuple[str, str]] = set()

    if isinstance(raw_preferences, list):
        for pair in raw_preferences:
            if not isinstance(pair, list) or len(pair) != 2:
                continue
            first = _canonical_room_type(pair[0])
            second = _canonical_room_type(pair[1])
            _append_adjacency(preferences, seen_pairs, first, second, room_types)

    if "bedroom" in room_types and "bathroom" in room_types:
        _append_adjacency(preferences, seen_pairs, "bedroom", "bathroom", room_types)
    if "kitchen" in room_types and "living" in room_types:
        _append_adjacency(preferences, seen_pairs, "kitchen", "living", room_types)
    if "corridor" in room_types and "bedroom" in room_types:
        _append_adjacency(preferences, seen_pairs, "corridor", "bedroom", room_types)
    if "corridor" in room_types and "bathroom" in room_types:
        _append_adjacency(preferences, seen_pairs, "corridor", "bathroom", room_types)

    default_notes = [
        "bedrooms in private zone",
        "kitchen near living",
    ]
    for note in default_notes:
        if note not in notes:
            notes.append(note)
    return {"notes": notes, "adjacency_preferences": preferences}


def _append_adjacency(
    preferences: list[list[str]],
    seen_pairs: set[tuple[str, str]],
    first: str,
    second: str,
    room_types: set[str],
) -> None:
    if first not in room_types or second not in room_types:
        return
    if frozenset((first, second)) in _FORBIDDEN_ADJACENCIES:
        return
    key = tuple(sorted((first, second)))
    if key in seen_pairs:
        return
    seen_pairs.add(key)
    preferences.append([first, second])


def _resolve_boundary(
    *,
    raw_boundary: Any,
    explicit_boundary: tuple[float, float] | None,
    boundary_count: int,
    has_prompt: bool,
) -> dict[str, float]:
    if explicit_boundary is not None:
        width, height = explicit_boundary
    elif has_prompt:
        width, height = _boundary_for_count(boundary_count)
    else:
        width, height = _coerce_boundary(raw_boundary) or _boundary_for_count(boundary_count)
    width, height = max(width, height), min(width, height)
    return {"width": round(width, 2), "height": round(height, 2)}


def _boundary_for_count(room_count: int) -> tuple[float, float]:
    if room_count <= 2:
        return (8.0, 6.0)
    if room_count <= 4:
        return (12.0, 9.0)
    if room_count <= 6:
        return (16.0, 10.0)
    return (20.0, 12.0)


def _boundary_room_count(
    *,
    raw_entries: list[dict[str, Any]],
    requested_counts: dict[str, int],
) -> int:
    if requested_counts:
        return max(1, sum(max(0, value) for value in requested_counts.values()))
    return max(1, sum(_positive_int(entry.get("count")) or 1 for entry in raw_entries))


def _coerce_boundary(raw_boundary: Any) -> tuple[float, float] | None:
    if not isinstance(raw_boundary, dict):
        return None
    width = _positive_float(raw_boundary.get("width"))
    height = _positive_float(raw_boundary.get("height"))
    if width is None or height is None:
        return None
    return (width, height)


def _preferred_floor(room_type: str, total_area: float) -> float:
    mandatory_min = _MANDATORY_MIN_AREAS.get(room_type, 3.5)
    cap = _preferred_cap(room_type, total_area)
    return min(mandatory_min / 0.85, cap)


def _preferred_cap(room_type: str, total_area: float) -> float:
    ratio = _MAX_LIVING_RATIO if room_type == "living" else _MAX_ROOM_RATIO
    return max(0.01, total_area * ratio)


def _grow_to_target(
    *,
    preferred: list[float],
    caps: list[float],
    target: float,
) -> list[float]:
    output = list(preferred)
    for _ in range(12):
        deficit = target - sum(output)
        if deficit <= _EPSILON:
            break
        candidates = [index for index, value in enumerate(output) if caps[index] - value > _EPSILON]
        if not candidates:
            break
        total_weight = sum(max(output[index], 1.0) for index in candidates)
        progress = 0.0
        for index in candidates:
            share = deficit * (max(output[index], 1.0) / total_weight)
            delta = min(share, caps[index] - output[index])
            output[index] += delta
            progress += delta
        if progress <= _EPSILON:
            break
    return output


def _shrink_to_target(
    *,
    preferred: list[float],
    floors: list[float],
    target: float,
) -> list[float]:
    output = list(preferred)
    for _ in range(12):
        surplus = sum(output) - target
        if surplus <= _EPSILON:
            break
        candidates = [index for index, value in enumerate(output) if value - floors[index] > _EPSILON]
        if not candidates:
            break
        total_weight = sum(output[index] - floors[index] for index in candidates)
        progress = 0.0
        for index in candidates:
            share = surplus * ((output[index] - floors[index]) / total_weight)
            delta = min(share, output[index] - floors[index])
            output[index] -= delta
            progress += delta
        if progress <= _EPSILON:
            break
    return output


def _round_and_adjust(
    *,
    preferred: list[float],
    floors: list[float],
    caps: list[float],
    target: float,
) -> list[float]:
    rounded = [round(value, 2) for value in preferred]
    lower = target / _TARGET_COVERAGE * _LOW_COVERAGE
    upper = target / _TARGET_COVERAGE * _HIGH_COVERAGE
    if lower - _EPSILON <= sum(rounded) <= upper + _EPSILON:
        delta = round(target - sum(rounded), 2)
        if abs(delta) <= 0.01:
            return rounded
        adjusted = _apply_rounding_delta(rounded, floors=floors, caps=caps, delta=delta)
        if adjusted is not None:
            return adjusted
    return rounded


def _apply_rounding_delta(
    rounded: list[float],
    *,
    floors: list[float],
    caps: list[float],
    delta: float,
) -> list[float] | None:
    output = list(rounded)
    if delta > 0:
        candidates = sorted(range(len(output)), key=lambda index: output[index], reverse=True)
        for index in candidates:
            if output[index] + delta <= caps[index] + _EPSILON:
                output[index] = round(output[index] + delta, 2)
                return output
    if delta < 0:
        candidates = sorted(range(len(output)), key=lambda index: output[index], reverse=True)
        for index in candidates:
            if output[index] + delta >= floors[index] - _EPSILON:
                output[index] = round(output[index] + delta, 2)
                return output
    return None


def _dedupe_room_names(units: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    output: list[dict[str, Any]] = []
    for unit in units:
        room_type = str(unit.get("room_type", "")).strip().lower()
        base_name = _clean_name(unit.get("name")) or _DEFAULT_NAMES.get(room_type, "Room")
        candidate = base_name
        suffix = 2
        while candidate in seen:
            candidate = f"{base_name} {suffix}"
            suffix += 1
        seen.add(candidate)
        output.append({"name": candidate, "room_type": room_type, "count": 1})
    return output


def _canonical_room_type(value: Any) -> str:
    cleaned = str(value or "").strip().lower()
    cleaned = re.sub(r"\s+", " ", cleaned)
    if cleaned in ALLOWED_ROOM_TYPES:
        return cleaned
    if cleaned in _ROOM_TYPE_SYNONYMS:
        return _ROOM_TYPE_SYNONYMS[cleaned]
    spaced = cleaned.replace("_", " ").replace("-", " ")
    if spaced in _ROOM_TYPE_SYNONYMS:
        return _ROOM_TYPE_SYNONYMS[spaced]
    for token, canonical in _ROOM_TYPE_SYNONYMS.items():
        if token and token.replace("_", " ") in spaced:
            return canonical
    return cleaned


def _clean_name(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _normalize_number_words(text: str) -> str:
    output = unicodedata.normalize("NFKC", str(text or "")).lower()
    for word, value in _NUMBER_WORDS.items():
        output = re.sub(rf"\b{word}\b", str(value), output)
    return output


def _parse_count(value: str) -> int | None:
    cleaned = str(value).strip().lower()
    if cleaned.isdigit():
        parsed = int(cleaned)
        return parsed if parsed > 0 else None
    return _NUMBER_WORDS.get(cleaned)


def _positive_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int) and value > 0:
        return value
    return None


def _positive_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if parsed <= 0:
        return None
    return parsed
