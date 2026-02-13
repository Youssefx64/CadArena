import json
import math
from typing import Any, Dict, List, Optional, Tuple

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from .few_shots import few_shot_messages


model_id = "LiquidAI/LFM2-1.2B-Extract"


tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    device_map="auto",
)


REQUIRED_TOP_KEYS = {"boundary", "rooms", "openings"}
REQUIRED_BOUNDARY_KEYS = {"width", "height"}
REQUIRED_ROOM_KEYS = {"name", "room_type", "width", "height", "origin"}
REQUIRED_POINT_KEYS = {"x", "y"}
ALLOWED_OPENING_KEYS = {"type", "room_name", "wall", "cut_start", "cut_end", "hinge", "swing"}
REQUIRED_OPENING_COMMON_KEYS = {"type", "room_name", "wall", "cut_start", "cut_end"}
REQUIRED_DOOR_KEYS = {"type", "room_name", "wall", "cut_start", "cut_end", "hinge", "swing"}
REQUIRED_WINDOW_KEYS = {"type", "room_name", "wall", "cut_start", "cut_end"}
VALID_WALLS = {"top", "bottom", "left", "right"}
VALID_HINGES = {"left", "right"}
VALID_SWINGS = {"in", "out"}
EPS = 1e-6
MAX_VALIDATION_RETRIES = 2
MAX_NEW_TOKENS = 512


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _eq(a: float, b: float, eps: float = EPS) -> bool:
    return abs(a - b) <= eps


def _between(value: float, low: float, high: float, eps: float = EPS) -> bool:
    return (low - eps) <= value <= (high + eps)


def _truncate_errors(errors: List[str], max_items: int = 20) -> List[str]:
    if len(errors) <= max_items:
        return errors
    return errors[:max_items] + [f"... and {len(errors) - max_items} more errors."]


def _format_errors(errors: List[str]) -> str:
    return "\n".join(f"- {err}" for err in errors)


def _parse_point(point_obj: Any, path: str, errors: List[str]) -> Optional[Tuple[float, float]]:
    if not isinstance(point_obj, dict):
        errors.append(f"{path} must be an object.")
        return None

    point_keys = set(point_obj.keys())
    missing_keys = REQUIRED_POINT_KEYS - point_keys
    extra_keys = point_keys - REQUIRED_POINT_KEYS
    if missing_keys:
        errors.append(f"{path} missing keys: {sorted(missing_keys)}.")
    if extra_keys:
        errors.append(f"{path} has extra keys: {sorted(extra_keys)}.")

    x = point_obj.get("x")
    y = point_obj.get("y")

    if not _is_number(x):
        errors.append(f"{path}.x must be a finite number.")
    if not _is_number(y):
        errors.append(f"{path}.y must be a finite number.")

    if _is_number(x) and x < 0:
        errors.append(f"{path}.x must be non-negative.")
    if _is_number(y) and y < 0:
        errors.append(f"{path}.y must be non-negative.")

    if not (_is_number(x) and _is_number(y)):
        return None

    return float(x), float(y)


def _validate_opening_geometry(
    wall: str,
    room_bounds: Tuple[float, float, float, float],
    cut_start: Tuple[float, float],
    cut_end: Tuple[float, float],
    path: str,
    errors: List[str],
) -> None:
    x0, y0, x1, y1 = room_bounds
    sx, sy = cut_start
    ex, ey = cut_end

    if wall == "left":
        if not (_eq(sx, x0) and _eq(ex, x0)):
            errors.append(f"{path} points must lie on room left wall x={x0}.")
        if not (_between(sy, y0, y1) and _between(ey, y0, y1)):
            errors.append(f"{path} y-values must be within [{y0}, {y1}].")
        if not _eq(sx, ex):
            errors.append(f"{path} must be vertical for left wall.")
        if _eq(sy, ey):
            errors.append(f"{path} must have non-zero length.")

    elif wall == "right":
        if not (_eq(sx, x1) and _eq(ex, x1)):
            errors.append(f"{path} points must lie on room right wall x={x1}.")
        if not (_between(sy, y0, y1) and _between(ey, y0, y1)):
            errors.append(f"{path} y-values must be within [{y0}, {y1}].")
        if not _eq(sx, ex):
            errors.append(f"{path} must be vertical for right wall.")
        if _eq(sy, ey):
            errors.append(f"{path} must have non-zero length.")

    elif wall == "bottom":
        if not (_eq(sy, y0) and _eq(ey, y0)):
            errors.append(f"{path} points must lie on room bottom wall y={y0}.")
        if not (_between(sx, x0, x1) and _between(ex, x0, x1)):
            errors.append(f"{path} x-values must be within [{x0}, {x1}].")
        if not _eq(sy, ey):
            errors.append(f"{path} must be horizontal for bottom wall.")
        if _eq(sx, ex):
            errors.append(f"{path} must have non-zero length.")

    elif wall == "top":
        if not (_eq(sy, y1) and _eq(ey, y1)):
            errors.append(f"{path} points must lie on room top wall y={y1}.")
        if not (_between(sx, x0, x1) and _between(ex, x0, x1)):
            errors.append(f"{path} x-values must be within [{x0}, {x1}].")
        if not _eq(sy, ey):
            errors.append(f"{path} must be horizontal for top wall.")
        if _eq(sx, ex):
            errors.append(f"{path} must have non-zero length.")


def _validate_layout(layout: Any) -> List[str]:
    errors: List[str] = []

    if not isinstance(layout, dict):
        return ["Top-level JSON must be an object."]

    top_keys = set(layout.keys())
    missing_top = REQUIRED_TOP_KEYS - top_keys
    extra_top = top_keys - REQUIRED_TOP_KEYS
    if missing_top:
        errors.append(f"Top-level missing keys: {sorted(missing_top)}.")
    if extra_top:
        errors.append(f"Top-level extra keys: {sorted(extra_top)}.")

    boundary_width: Optional[float] = None
    boundary_height: Optional[float] = None

    boundary = layout.get("boundary")
    if not isinstance(boundary, dict):
        errors.append("boundary must be an object.")
    else:
        boundary_keys = set(boundary.keys())
        missing_boundary = REQUIRED_BOUNDARY_KEYS - boundary_keys
        extra_boundary = boundary_keys - REQUIRED_BOUNDARY_KEYS
        if missing_boundary:
            errors.append(f"boundary missing keys: {sorted(missing_boundary)}.")
        if extra_boundary:
            errors.append(f"boundary extra keys: {sorted(extra_boundary)}.")

        width = boundary.get("width")
        height = boundary.get("height")
        if not _is_number(width):
            errors.append("boundary.width must be a finite number.")
        if not _is_number(height):
            errors.append("boundary.height must be a finite number.")

        if _is_number(width):
            boundary_width = float(width)
            if boundary_width <= 0:
                errors.append("boundary.width must be > 0.")
        if _is_number(height):
            boundary_height = float(height)
            if boundary_height <= 0:
                errors.append("boundary.height must be > 0.")

    rooms = layout.get("rooms")
    room_bounds_by_name: Dict[str, Tuple[float, float, float, float]] = {}
    room_rects: List[Tuple[str, float, float, float, float]] = []

    if not isinstance(rooms, list):
        errors.append("rooms must be an array.")
    else:
        for idx, room in enumerate(rooms):
            path = f"rooms[{idx}]"
            if not isinstance(room, dict):
                errors.append(f"{path} must be an object.")
                continue

            room_keys = set(room.keys())
            missing_room = REQUIRED_ROOM_KEYS - room_keys
            extra_room = room_keys - REQUIRED_ROOM_KEYS
            if missing_room:
                errors.append(f"{path} missing keys: {sorted(missing_room)}.")
            if extra_room:
                errors.append(f"{path} extra keys: {sorted(extra_room)}.")

            name = room.get("name")
            room_type = room.get("room_type")
            width = room.get("width")
            height = room.get("height")
            origin = room.get("origin")

            valid_name = isinstance(name, str) and bool(name.strip())
            if not valid_name:
                errors.append(f"{path}.name must be a non-empty string.")
            elif name in room_bounds_by_name:
                errors.append(f"Duplicate room name: {name}.")

            if not (isinstance(room_type, str) and bool(room_type.strip())):
                errors.append(f"{path}.room_type must be a non-empty string.")

            if not _is_number(width):
                errors.append(f"{path}.width must be a finite number.")
            if not _is_number(height):
                errors.append(f"{path}.height must be a finite number.")

            valid_size = _is_number(width) and _is_number(height)
            if valid_size:
                width = float(width)
                height = float(height)
                if width <= 0:
                    errors.append(f"{path}.width must be > 0.")
                if height <= 0:
                    errors.append(f"{path}.height must be > 0.")

            if not isinstance(origin, dict):
                errors.append(f"{path}.origin must be an object.")
                continue

            origin_keys = set(origin.keys())
            missing_origin = REQUIRED_POINT_KEYS - origin_keys
            extra_origin = origin_keys - REQUIRED_POINT_KEYS
            if missing_origin:
                errors.append(f"{path}.origin missing keys: {sorted(missing_origin)}.")
            if extra_origin:
                errors.append(f"{path}.origin extra keys: {sorted(extra_origin)}.")

            ox = origin.get("x")
            oy = origin.get("y")
            if not _is_number(ox):
                errors.append(f"{path}.origin.x must be a finite number.")
            if not _is_number(oy):
                errors.append(f"{path}.origin.y must be a finite number.")

            valid_origin = _is_number(ox) and _is_number(oy)
            if valid_origin:
                ox = float(ox)
                oy = float(oy)
                if ox < 0:
                    errors.append(f"{path}.origin.x must be non-negative.")
                if oy < 0:
                    errors.append(f"{path}.origin.y must be non-negative.")

            if not (valid_name and valid_size and valid_origin):
                continue

            if width <= 0 or height <= 0:
                continue

            x0 = ox
            y0 = oy
            x1 = ox + width
            y1 = oy + height

            if boundary_width is not None and boundary_height is not None:
                if x1 > boundary_width + EPS or y1 > boundary_height + EPS:
                    errors.append(f"{path} exceeds boundary limits.")

            room_rects.append((str(name), x0, y0, x1, y1))
            room_bounds_by_name[str(name)] = (x0, y0, x1, y1)

        for i in range(len(room_rects)):
            name_a, ax0, ay0, ax1, ay1 = room_rects[i]
            for j in range(i + 1, len(room_rects)):
                name_b, bx0, by0, bx1, by1 = room_rects[j]
                overlap_w = min(ax1, bx1) - max(ax0, bx0)
                overlap_h = min(ay1, by1) - max(ay0, by0)
                if overlap_w > EPS and overlap_h > EPS:
                    errors.append(f"Rooms overlap: {name_a} and {name_b}.")

    openings = layout.get("openings")
    if not isinstance(openings, list):
        errors.append("openings must be an array.")
    else:
        for idx, opening in enumerate(openings):
            path = f"openings[{idx}]"
            if not isinstance(opening, dict):
                errors.append(f"{path} must be an object.")
                continue

            opening_keys = set(opening.keys())
            missing_common = REQUIRED_OPENING_COMMON_KEYS - opening_keys
            extra_opening = opening_keys - ALLOWED_OPENING_KEYS
            if missing_common:
                errors.append(f"{path} missing keys: {sorted(missing_common)}.")
            if extra_opening:
                errors.append(f"{path} extra keys: {sorted(extra_opening)}.")

            opening_type = opening.get("type")
            if opening_type not in {"door", "window"}:
                errors.append(f"{path}.type must be 'door' or 'window'.")

            if opening_type == "door":
                missing_door = REQUIRED_DOOR_KEYS - opening_keys
                if missing_door:
                    errors.append(f"{path} missing door keys: {sorted(missing_door)}.")
                hinge = opening.get("hinge")
                swing = opening.get("swing")
                if hinge not in VALID_HINGES:
                    errors.append(f"{path}.hinge must be one of {sorted(VALID_HINGES)}.")
                if swing not in VALID_SWINGS:
                    errors.append(f"{path}.swing must be one of {sorted(VALID_SWINGS)}.")

            if opening_type == "window":
                missing_window = REQUIRED_WINDOW_KEYS - opening_keys
                if missing_window:
                    errors.append(f"{path} missing window keys: {sorted(missing_window)}.")
                forbidden_window_keys = {"hinge", "swing"} & opening_keys
                if forbidden_window_keys:
                    errors.append(f"{path} window has forbidden keys: {sorted(forbidden_window_keys)}.")

            room_name = opening.get("room_name")
            if not (isinstance(room_name, str) and bool(room_name.strip())):
                errors.append(f"{path}.room_name must be a non-empty string.")
                room_name = None
            elif room_name not in room_bounds_by_name:
                errors.append(f"{path}.room_name must match an existing room.")

            wall = opening.get("wall")
            if wall not in VALID_WALLS:
                errors.append(f"{path}.wall must be one of {sorted(VALID_WALLS)}.")
                wall = None

            cut_start = _parse_point(opening.get("cut_start"), f"{path}.cut_start", errors)
            cut_end = _parse_point(opening.get("cut_end"), f"{path}.cut_end", errors)

            if room_name and wall and cut_start and cut_end:
                _validate_opening_geometry(
                    wall=wall,
                    room_bounds=room_bounds_by_name[room_name],
                    cut_start=cut_start,
                    cut_end=cut_end,
                    path=path,
                    errors=errors,
                )

    return _truncate_errors(errors)


def _parse_json_strict(text: str) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    stripped = text.strip()
    if not stripped:
        return None, ["Model output is empty."]

    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError as exc:
        return None, [f"Invalid JSON: {exc.msg} at line {exc.lineno}, column {exc.colno}."]

    if not isinstance(parsed, dict):
        return None, ["Top-level JSON must be an object."]

    return parsed, []


def _prepare_model_inputs(messages: List[Dict[str, str]]) -> Dict[str, torch.Tensor]:
    templated = tokenizer.apply_chat_template(
        messages,
        tokenize=True,
        add_generation_prompt=True,
        return_dict=True,
        return_tensors="pt",
    )

    if isinstance(templated, torch.Tensor):
        model_inputs = {
            "input_ids": templated,
            "attention_mask": torch.ones_like(templated),
        }
    elif hasattr(templated, "keys"):
        model_inputs = {key: templated[key] for key in templated.keys()}
    else:
        raise TypeError("Unexpected chat template return type.")

    return {key: value.to(model.device) for key, value in model_inputs.items()}


def _generate_text(messages: List[Dict[str, str]]) -> str:
    model_inputs = _prepare_model_inputs(messages)

    if "input_ids" not in model_inputs:
        raise ValueError("Model inputs missing input_ids.")

    prompt_len = model_inputs["input_ids"].shape[-1]

    eos_token_id = tokenizer.eos_token_id
    if eos_token_id is None:
        eos_token_id = model.config.eos_token_id
    if eos_token_id is None:
        raise ValueError("Missing eos_token_id in tokenizer/model config.")

    pad_token_id = tokenizer.pad_token_id
    if pad_token_id is None:
        pad_token_id = eos_token_id

    outputs = model.generate(
        **model_inputs,
        max_new_tokens=MAX_NEW_TOKENS,
        temperature=0.0,
        do_sample=False,
        eos_token_id=eos_token_id,
        pad_token_id=pad_token_id,
    )

    if outputs.ndim != 2:
        raise ValueError("Unexpected generation output shape.")

    generated_tokens = outputs[0, prompt_len:]
    return tokenizer.decode(generated_tokens, skip_special_tokens=True).strip()


def _build_retry_messages(
    base_messages: List[Dict[str, str]],
    previous_output: str,
    errors: List[str],
) -> List[Dict[str, str]]:
    repair_request = (
        "Your previous response is invalid. "
        "Return exactly one corrected JSON object and no other text.\n"
        "Fix these errors:\n"
        f"{_format_errors(_truncate_errors(errors, max_items=12))}"
    )

    return base_messages + [
        {"role": "assistant", "content": previous_output},
        {"role": "user", "content": repair_request},
    ]


def prompt_to_json(user_prompt: str) -> Dict[str, Any]:
    base_messages: List[Dict[str, str]] = list(few_shot_messages) + [
        {"role": "user", "content": user_prompt}
    ]

    messages = base_messages
    last_errors: List[str] = ["Unknown validation error."]

    for attempt in range(MAX_VALIDATION_RETRIES + 1):
        raw_output = _generate_text(messages)

        parsed, parse_errors = _parse_json_strict(raw_output)
        if parse_errors:
            last_errors = parse_errors
        else:
            validation_errors = _validate_layout(parsed)
            if not validation_errors:
                return parsed
            last_errors = validation_errors

        if attempt < MAX_VALIDATION_RETRIES:
            messages = _build_retry_messages(base_messages, raw_output, last_errors)

    raise ValueError(
        "Failed to produce valid layout JSON after retries: "
        + " | ".join(_truncate_errors(last_errors, max_items=5))
    )
