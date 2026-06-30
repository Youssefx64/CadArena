"""Deterministic prompt-side program derivation for extraction hardening."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


_DIMENSION_PATTERN = re.compile(r"(?P<w>\d+(?:\.\d+)?)\s*[x×]\s*(?P<h>\d+(?:\.\d+)?)")
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


@dataclass(frozen=True)
class _ProgramToken:
    pattern: re.Pattern[str]
    name: str
    room_type: str


_PROGRAM_TOKENS: list[_ProgramToken] = [
    _ProgramToken(
        pattern=re.compile(r"\b(?P<count>\d+)?\s*(?:master|primary)\s*bedrooms?\b"),
        name="Master Bedroom",
        room_type="bedroom",
    ),
    _ProgramToken(
        pattern=re.compile(r"\b(?P<count>\d+)?\s*(?:children|child|kids?)\s*bedrooms?\b"),
        name="Children Bedroom",
        room_type="bedroom",
    ),
    _ProgramToken(
        pattern=re.compile(r"\b(?P<count>\d+)?\s*(?:private|en[- ]?suite)\s*bathrooms?\b"),
        name="Private Bathroom",
        room_type="bathroom",
    ),
    _ProgramToken(
        pattern=re.compile(r"\b(?P<count>\d+)?\s*shared\s*bathrooms?\b"),
        name="Shared Bathroom",
        room_type="bathroom",
    ),
    _ProgramToken(
        pattern=re.compile(r"\b(?P<count>\d+)?\s*guest\s*bathrooms?\b"),
        name="Guest Bathroom",
        room_type="bathroom",
    ),
    _ProgramToken(
        pattern=re.compile(r"\b(?P<count>\d+)?\s*living\s*rooms?\b"),
        name="Living Room",
        room_type="living",
    ),
    _ProgramToken(
        pattern=re.compile(r"\b(?P<count>\d+)?\s*salons?\b"),
        name="Salon",
        room_type="living",
    ),
    _ProgramToken(
        pattern=re.compile(r"\b(?P<count>\d+)?\s*receptions?\b"),
        name="Reception",
        room_type="living",
    ),
    _ProgramToken(
        pattern=re.compile(r"\b(?P<count>\d+)?\s*lounges?\b"),
        name="Lounge",
        room_type="living",
    ),
    _ProgramToken(
        pattern=re.compile(r"\b(?P<count>\d+)?\s*dining\s*rooms?\b"),
        name="Dining Room",
        room_type="living",
    ),
    _ProgramToken(
        pattern=re.compile(r"\b(?P<count>\d+)?\s*kitchens?\b"),
        name="Kitchen",
        room_type="kitchen",
    ),
    _ProgramToken(
        pattern=re.compile(r"\b(?P<count>\d+)?\s*laundr(?:y|ies)\b"),
        name="Laundry",
        room_type="bathroom",
    ),
    _ProgramToken(
        pattern=re.compile(r"\b(?P<count>\d+)?\s*storage(?:\s*rooms?)?\b"),
        name="Storage",
        room_type="corridor",
    ),
]


class PromptProgramDeriver:
    """Builds deterministic room programs from the raw user prompt."""

    def derive(self, *, prompt: str, extracted_payload: dict[str, Any]) -> dict[str, Any]:
        prompt_program = self._parse_prompt_program(prompt)
        if not prompt_program:
            return extracted_payload

        output = dict(extracted_payload)
        output["room_program"] = prompt_program

        boundary = dict(output.get("boundary") or {})
        parsed_boundary = self._parse_boundary(prompt)
        if parsed_boundary is not None:
            boundary["width"], boundary["height"] = parsed_boundary
        if boundary:
            output["boundary"] = boundary

        constraints = output.get("constraints")
        if not isinstance(constraints, dict):
            output["constraints"] = {"notes": [], "adjacency_preferences": []}
        return output

    def _parse_prompt_program(self, prompt: str) -> list[dict[str, Any]]:
        normalized = self._normalize_numbers(prompt.lower())
        working = normalized
        extracted: list[dict[str, Any]] = []

        for token in _PROGRAM_TOKENS:
            matches = list(token.pattern.finditer(working))
            if not matches:
                continue
            total = 0
            for match in matches:
                val = match.group("count")
                total += int(val) if val is not None else 1
            if total > 0:
                extracted.append(
                    {
                        "name": token.name,
                        "room_type": token.room_type,
                        "count": total,
                    }
                )
            working = token.pattern.sub(" ", working)

        archetype_program = self._parse_apartment_archetype(normalized)
        if archetype_program:
            self._merge_minimum_program(extracted, archetype_program)
        self._append_keyword_singletons(extracted=extracted, normalized_text=normalized)
        self._append_generic_counts(extracted=extracted, residual_text=working)
        return extracted

    @staticmethod
    def _parse_apartment_archetype(normalized_text: str) -> list[dict[str, Any]]:
        bedroom_count: int | None = None
        br_match = re.search(r"\b(?P<count>\d+)\s*(?:br|bdr|bed)\b", normalized_text)
        if br_match is not None:
            bedroom_count = int(br_match.group("count"))
        apartment_match = re.search(r"\b(?P<count>\d+)\s*[- ]*bedroom\s+(?:apartment|flat|unit|house)\b", normalized_text)
        if apartment_match is not None:
            bedroom_count = int(apartment_match.group("count"))

        if bedroom_count is None:
            if re.search(r"\bstudio\b", normalized_text):
                bedroom_count = 0
            else:
                return []

        bedroom_count = max(0, min(6, bedroom_count))
        bathroom_count = 1 if bedroom_count <= 2 else 2
        program: list[dict[str, Any]] = [
            {"name": "Living Room", "room_type": "living", "count": 1},
            {"name": "Kitchen", "room_type": "kitchen", "count": 1},
            {"name": "Bathroom", "room_type": "bathroom", "count": bathroom_count},
        ]
        if bedroom_count > 0:
            program.insert(0, {"name": "Bedroom", "room_type": "bedroom", "count": bedroom_count})
        if bedroom_count >= 2:
            program.append({"name": "Main Corridor", "room_type": "corridor", "count": 1})
        return program

    @staticmethod
    def _merge_minimum_program(
        extracted: list[dict[str, Any]],
        minimum_program: list[dict[str, Any]],
    ) -> None:
        by_type = {str(item.get("room_type")): item for item in extracted}
        for item in minimum_program:
            room_type = str(item.get("room_type"))
            current = by_type.get(room_type)
            if current is None:
                copied = dict(item)
                extracted.append(copied)
                by_type[room_type] = copied
                continue
            current["count"] = max(int(current.get("count", 1)), int(item.get("count", 1)))

    @staticmethod
    def _normalize_numbers(text: str) -> str:
        output = text
        for word, value in _NUMBER_WORDS.items():
            output = re.sub(rf"\b{word}\b", str(value), output)
        return output

    @staticmethod
    def _append_keyword_singletons(*, extracted: list[dict[str, Any]], normalized_text: str) -> None:
        existing_names = {item["name"] for item in extracted}
        existing_types = {item["room_type"] for item in extracted}
        if "Living Room" not in existing_names and "living room" in normalized_text:
            extracted.append({"name": "Living Room", "room_type": "living", "count": 1})
        if "Salon" not in existing_names and "salon" in normalized_text:
            extracted.append({"name": "Salon", "room_type": "living", "count": 1})
        if "Reception" not in existing_names and "reception" in normalized_text:
            extracted.append({"name": "Reception", "room_type": "living", "count": 1})
        if "Lounge" not in existing_names and "lounge" in normalized_text:
            extracted.append({"name": "Lounge", "room_type": "living", "count": 1})
        if "Dining Room" not in existing_names and "dining room" in normalized_text:
            extracted.append({"name": "Dining Room", "room_type": "living", "count": 1})
        if "Kitchen" not in existing_names and "kitchen" in normalized_text:
            extracted.append({"name": "Kitchen", "room_type": "kitchen", "count": 1})
        if "bathroom" not in existing_types and "bathroom" in normalized_text:
            extracted.append({"name": "Bathroom", "room_type": "bathroom", "count": 1})
        if "Laundry" not in existing_names and "laundry" in normalized_text:
            extracted.append({"name": "Laundry", "room_type": "bathroom", "count": 1})
        if "Storage" not in existing_names and "storage" in normalized_text:
            extracted.append({"name": "Storage", "room_type": "corridor", "count": 1})

    @staticmethod
    def _append_generic_counts(*, extracted: list[dict[str, Any]], residual_text: str) -> None:
        bedroom_count = 0
        for match in re.finditer(r"(?P<count>\d+)\s*bedrooms?\b", residual_text):
            bedroom_count += max(0, int(match.group("count")))
        if bedroom_count > 0:
            extracted.append({"name": "Bedroom", "room_type": "bedroom", "count": bedroom_count})

        bathroom_count = 0
        for match in re.finditer(r"(?P<count>\d+)\s*bathrooms?\b", residual_text):
            bathroom_count += max(0, int(match.group("count")))
        if bathroom_count > 0:
            extracted.append({"name": "Bathroom", "room_type": "bathroom", "count": bathroom_count})

    @staticmethod
    def _parse_boundary(prompt: str) -> tuple[float, float] | None:
        match = _DIMENSION_PATTERN.search(prompt.lower())
        if match is None:
            return None
        width = float(match.group("w"))
        height = float(match.group("h"))
        if width <= 0 or height <= 0:
            return None
        return (max(width, height), min(width, height))
