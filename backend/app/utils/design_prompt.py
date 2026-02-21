"""Prompt templates for strict architectural design parsing."""

from __future__ import annotations

import json


_SCHEMA_EXAMPLE = {
    "boundary": {"width": 24.0, "height": 14.0},
    "rooms": [
        {
            "name": "Living Room",
            "room_type": "living",
            "width": 10.0,
            "height": 8.0,
            "origin": {"x": 0.0, "y": 0.0},
        },
        {
            "name": "Corridor",
            "room_type": "corridor",
            "width": 2.0,
            "height": 14.0,
            "origin": {"x": 10.0, "y": 0.0},
        },
    ],
    "walls": [
        {
            "room_name": "Living Room",
            "wall": "bottom",
            "start": {"x": 0.0, "y": 0.0},
            "end": {"x": 10.0, "y": 0.0},
            "thickness": 0.2,
        },
        {
            "room_name": "Living Room",
            "wall": "right",
            "start": {"x": 10.0, "y": 0.0},
            "end": {"x": 10.0, "y": 8.0},
            "thickness": 0.2,
        },
    ],
    "openings": [
        {
            "type": "door",
            "room_name": "Living Room",
            "wall": "right",
            "cut_start": {"x": 10.0, "y": 2.0},
            "cut_end": {"x": 10.0, "y": 3.0},
            "hinge": "left",
            "swing": "in",
        },
        {
            "type": "window",
            "room_name": "Living Room",
            "wall": "bottom",
            "cut_start": {"x": 3.0, "y": 0.0},
            "cut_end": {"x": 4.5, "y": 0.0},
        },
    ],
}


def build_design_parser_prompt(user_prompt: str) -> str:
    """Build a strict single-turn prompt that enforces JSON-only output."""

    schema_example = json.dumps(_SCHEMA_EXAMPLE, ensure_ascii=False, separators=(",", ":"))

    return (
        "You are an architectural intent compiler for CAD generation.\n"
        "Input is English only.\n"
        "All output text values MUST be English only.\n"
        "Convert the user request into EXACTLY one valid JSON object.\n"
        "Do not output markdown, code fences, comments, or explanatory text.\n"
        "Top-level keys must be exactly: boundary, rooms, walls, openings.\n"
        "All coordinates are absolute meters from origin (0,0).\n"
        "Rules:\n"
        "1) boundary.width > 0 and boundary.height > 0.\n"
        "2) rooms: non-overlapping axis-aligned rectangles inside boundary.\n"
        "3) walls: each wall belongs to a room and lies exactly on that room perimeter.\n"
        "4) openings: each opening belongs to a room wall and cut points lie exactly on the declared wall.\n"
        "5) door requires hinge and swing; window must not include hinge/swing.\n"
        "6) room_type must be one of: living, bedroom, kitchen, bathroom, corridor, stairs.\n"
        "7) wall must be one of: top, bottom, left, right.\n"
        "8) No extra keys anywhere.\n"
        "9) Return JSON only.\n"
        "JSON schema example:\n"
        f"{schema_example}\n"
        "User request:\n"
        f"{user_prompt.strip()}\n"
    )
