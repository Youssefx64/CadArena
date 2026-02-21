import json
import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

os.environ.setdefault("TRANSFORMERS_NO_TF", "1")
os.environ.setdefault("USE_TF", "0")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

try:
    import torch
except ImportError:  # pragma: no cover
    torch = None

try:
    from transformers import AutoTokenizer, AutoModelForCausalLM
except ImportError:  # pragma: no cover
    AutoTokenizer = None
    AutoModelForCausalLM = None

try:
    from .system_prompt import system_prompt
    from .few_shots import few_shot_messages
except ImportError:  # support direct execution: python backend/app/llm/prompt_to_json.py
    from system_prompt import system_prompt
    from few_shots import few_shot_messages


# ══════════════════════════════════════════════════════════════════════════════
# VALIDATION LAYER  ← هنا بنمسك الأخطاء قبل ما توصل للـ API
# ══════════════════════════════════════════════════════════════════════════════
@dataclass
class ValidationError:
    field: str
    message: str

class FloorPlanValidator:
    ALLOWED_TOP_KEYS   = {"boundary", "rooms", "openings"}
    REQUIRED_TOP_KEYS  = {"boundary", "rooms", "openings"}
    ALLOWED_ROOM_KEYS  = {"name", "room_type", "width", "height", "origin"}
    REQUIRED_ROOM_KEYS = {"name", "room_type", "width", "height", "origin"}
    ALLOWED_DOOR_KEYS  = {"type", "room_name", "wall", "cut_start", "cut_end", "hinge", "swing"}
    REQUIRED_DOOR_KEYS = {"type", "room_name", "wall", "cut_start", "cut_end", "hinge", "swing"}
    ALLOWED_WIN_KEYS   = {"type", "room_name", "wall", "cut_start", "cut_end"}
    REQUIRED_WIN_KEYS  = {"type", "room_name", "wall", "cut_start", "cut_end"}
    VALID_WALLS        = {"top", "bottom", "left", "right"}

    def validate(self, data: dict) -> list[ValidationError]:
        errors: list[ValidationError] = []
        if not isinstance(data, dict):
            return [ValidationError("root", f"Output must be a JSON object, got {type(data).__name__}")]

        # ── 1. Top-level keys ─────────────────────────────────────────────
        extra_top = set(data.keys()) - self.ALLOWED_TOP_KEYS
        if extra_top:
            errors.append(ValidationError("root", f"Forbidden extra keys: {extra_top}"))
        missing_top = self.REQUIRED_TOP_KEYS - set(data.keys())
        if missing_top:
            errors.append(ValidationError("root", f"Missing required top-level keys: {sorted(missing_top)}"))

        boundary = data.get("boundary", {})
        if not isinstance(boundary, dict):
            boundary = {}
            errors.append(ValidationError("boundary", "boundary must be an object with width/height"))
        bw = boundary.get("width", 0)
        bh = boundary.get("height", 0)
        if not isinstance(bw, (int, float)) or bw <= 0:
            errors.append(ValidationError("boundary.width", f"boundary.width must be > 0, got {bw!r}"))
        if not isinstance(bh, (int, float)) or bh <= 0:
            errors.append(ValidationError("boundary.height", f"boundary.height must be > 0, got {bh!r}"))

        rooms = data.get("rooms", [])
        if not isinstance(rooms, list):
            errors.append(ValidationError("rooms", "rooms must be an array"))
            rooms = []
        if len(rooms) == 0:
            errors.append(ValidationError("rooms", "rooms array must not be empty"))
        room_names = {r["name"] for r in rooms if isinstance(r, dict) and "name" in r}

        # ── 2. Room checks ────────────────────────────────────────────────
        for i, room in enumerate(rooms):
            if not isinstance(room, dict):
                errors.append(ValidationError(f"rooms[{i}]", f"Room must be an object, got {type(room).__name__}"))
                continue
            prefix = f"rooms[{i}] '{room.get('name', '?')}'"

            extra_room = set(room.keys()) - self.ALLOWED_ROOM_KEYS
            if extra_room:
                errors.append(ValidationError(prefix, f"Forbidden extra keys: {extra_room}"))
            missing_room = self.REQUIRED_ROOM_KEYS - set(room.keys())
            if missing_room:
                errors.append(ValidationError(prefix, f"Missing required keys: {sorted(missing_room)}"))

            origin = room.get("origin", {})
            if not isinstance(origin, dict):
                origin = {}
                errors.append(ValidationError(prefix, "origin must be an object with x/y"))

            ox = origin.get("x", 0)
            oy = origin.get("y", 0)
            rw = room.get("width", 0)
            rh = room.get("height", 0)
            if not isinstance(ox, (int, float)) or not isinstance(oy, (int, float)):
                errors.append(ValidationError(prefix, f"origin.x/origin.y must be numbers, got {ox!r}, {oy!r}"))
                continue
            if not isinstance(rw, (int, float)) or rw <= 0:
                errors.append(ValidationError(prefix, f"width must be > 0, got {rw!r}"))
                continue
            if not isinstance(rh, (int, float)) or rh <= 0:
                errors.append(ValidationError(prefix, f"height must be > 0, got {rh!r}"))
                continue

            if ox + rw > bw:
                errors.append(ValidationError(
                    prefix,
                    f"Out of boundary (x): origin.x({ox}) + width({rw}) = {ox+rw} > boundary.width({bw})"
                ))
            if oy + rh > bh:
                errors.append(ValidationError(
                    prefix,
                    f"Out of boundary (y): origin.y({oy}) + height({rh}) = {oy+rh} > boundary.height({bh})"
                ))
            if ox < 0 or oy < 0:
                errors.append(ValidationError(prefix, f"origin must be non-negative, got ({ox}, {oy})"))

        # ── 3. Opening checks ─────────────────────────────────────────────
        openings = data.get("openings", [])
        if not isinstance(openings, list):
            errors.append(ValidationError("openings", "openings must be an array"))
            openings = []
        for i, op in enumerate(openings):
            if not isinstance(op, dict):
                errors.append(ValidationError(f"openings[{i}]", f"Opening must be an object, got {type(op).__name__}"))
                continue
            t     = op.get("type", "?")
            rname = op.get("room_name", "?")
            prefix = f"openings[{i}] type={t} room='{rname}'"

            # Forbidden extra keys
            allowed = self.ALLOWED_DOOR_KEYS if t == "door" else self.ALLOWED_WIN_KEYS
            extra_op = set(op.keys()) - allowed
            if extra_op:
                errors.append(ValidationError(prefix, f"Forbidden extra keys: {extra_op}"))
            required = self.REQUIRED_DOOR_KEYS if t == "door" else self.REQUIRED_WIN_KEYS
            missing_op = required - set(op.keys())
            if missing_op:
                errors.append(ValidationError(prefix, f"Missing required keys: {sorted(missing_op)}"))

            # Room must exist
            if rname not in room_names:
                errors.append(ValidationError(
                    prefix,
                    f"room_name '{rname}' not found in rooms array (available: {sorted(room_names)})"
                ))

            # Wall validity
            wall = op.get("wall", "?")
            if wall not in self.VALID_WALLS:
                errors.append(ValidationError(prefix, f"Invalid wall '{wall}'"))

            # Check cut coordinates are on the correct wall of the room
            room_obj = next((r for r in rooms if r.get("name") == rname), None)
            if room_obj and wall in self.VALID_WALLS:
                origin = room_obj.get("origin") or {}
                if not isinstance(origin, dict):
                    errors.append(ValidationError(prefix, f"room '{rname}' has malformed origin"))
                    continue

                ox = origin.get("x", 0)
                oy = origin.get("y", 0)
                rw = room_obj.get("width", 0)
                rh = room_obj.get("height", 0)

                cs = op.get("cut_start", {})
                ce = op.get("cut_end",   {})

                # Guard: model sometimes emits a number instead of {"x":…,"y":…}
                if not isinstance(cs, dict):
                    errors.append(ValidationError(prefix, f"cut_start must be an object {{x,y}}, got: {cs!r}"))
                    continue
                if not isinstance(ce, dict):
                    errors.append(ValidationError(prefix, f"cut_end must be an object {{x,y}}, got: {ce!r}"))
                    continue

                csx, csy = cs.get("x", None), cs.get("y", None)
                cex, cey = ce.get("x", None), ce.get("y", None)
                if not isinstance(csx, (int, float)) or not isinstance(csy, (int, float)):
                    errors.append(ValidationError(prefix, f"cut_start.x/y must be numbers, got {csx!r}, {csy!r}"))
                    continue
                if not isinstance(cex, (int, float)) or not isinstance(cey, (int, float)):
                    errors.append(ValidationError(prefix, f"cut_end.x/y must be numbers, got {cex!r}, {cey!r}"))
                    continue

                wall_coord = {
                    "bottom": ("y", oy),
                    "top":    ("y", oy + rh),
                    "left":   ("x", ox),
                    "right":  ("x", ox + rw),
                }
                axis, expected = wall_coord[wall]

                if axis == "y":
                    if csy != expected:
                        errors.append(ValidationError(
                            prefix,
                            f"cut_start.y={csy} must equal {expected} (wall '{wall}' of '{rname}')"
                        ))
                    if cey != expected:
                        errors.append(ValidationError(
                            prefix,
                            f"cut_end.y={cey} must equal {expected} (wall '{wall}' of '{rname}')"
                        ))
                else:
                    if csx != expected:
                        errors.append(ValidationError(
                            prefix,
                            f"cut_start.x={csx} must equal {expected} (wall '{wall}' of '{rname}')"
                        ))
                    if cex != expected:
                        errors.append(ValidationError(
                            prefix,
                            f"cut_end.x={cex} must equal {expected} (wall '{wall}' of '{rname}')"
                        ))

        return errors


def validate_floor_plan(data: dict) -> tuple[bool, list[str]]:
    """Returns (is_valid, list_of_error_messages)."""
    v = FloorPlanValidator()
    errors = v.validate(data)
    return (len(errors) == 0), [f"[{e.field}] {e.message}" for e in errors]


# ══════════════════════════════════════════════════════════════════════════════
# CLEANER  ← بيشيل الـ keys الزيادة اللي الموديل بيضيفها
# ══════════════════════════════════════════════════════════════════════════════

def clean_output(data: dict) -> dict:
    """Remove any forbidden extra top-level keys the model hallucinated."""
    if not isinstance(data, dict):
        raise ValueError(f"Model output must be a JSON object, got {type(data).__name__}")

    allowed_top = {"boundary", "rooms", "openings"}
    cleaned = {k: v for k, v in data.items() if k in allowed_top}

    # Clean room keys
    allowed_room = {"name", "room_type", "width", "height", "origin"}
    rooms = cleaned.get("rooms", [])
    if not isinstance(rooms, list):
        rooms = []
    cleaned["rooms"] = [
        {k: v for k, v in room.items() if k in allowed_room}
        for room in rooms
        if isinstance(room, dict)
    ]

    # Clean opening keys
    allowed_door   = {"type", "room_name", "wall", "cut_start", "cut_end", "hinge", "swing"}
    allowed_window = {"type", "room_name", "wall", "cut_start", "cut_end"}
    cleaned_openings = []
    openings = cleaned.get("openings", [])
    if not isinstance(openings, list):
        openings = []

    for op in openings:
        if not isinstance(op, dict):
            continue
        allowed = allowed_door if op.get("type") == "door" else allowed_window
        clean_op = {k: v for k, v in op.items() if k in allowed}
        # Guard: drop openings where cut_start/cut_end are not dicts
        if not isinstance(clean_op.get("cut_start"), dict) or \
           not isinstance(clean_op.get("cut_end"), dict):
            print(f"  WARNING: Dropping opening with malformed cut_start/cut_end: {clean_op}")
            continue
        cleaned_openings.append(clean_op)
    cleaned["openings"] = cleaned_openings

    return cleaned


def remove_invalid_openings(data: dict) -> dict:
    """Drop openings that reference rooms not in the rooms array."""
    room_names = {r["name"] for r in data.get("rooms", []) if isinstance(r, dict) and "name" in r}
    openings = data.get("openings", [])
    if not isinstance(openings, list):
        openings = []
    data["openings"] = [
        op for op in openings
        if isinstance(op, dict)
        if op.get("room_name") in room_names
    ]
    return data


def _to_float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _clip(value: float, low: float, high: float) -> float:
    if low > high:
        return low
    return max(low, min(value, high))


def _normalize_room_type(name: str, room_type: Optional[str]) -> str:
    allowed = {"living", "bedroom", "kitchen", "bathroom", "corridor", "stairs"}
    if isinstance(room_type, str) and room_type in allowed:
        return room_type

    lowered = (name or "").lower()
    if "bed" in lowered:
        return "bedroom"
    if "kitchen" in lowered:
        return "kitchen"
    if "bath" in lowered or "wc" in lowered or "toilet" in lowered:
        return "bathroom"
    if "corridor" in lowered or "hall" in lowered or "passage" in lowered:
        return "corridor"
    if "stair" in lowered:
        return "stairs"
    return "living"


def _parse_rooms_from_prompt(user_prompt: str, boundary_w: float, boundary_h: float) -> list[dict]:
    rooms: list[dict] = []
    line_re = re.compile(r"^\s*-\s*([^:]+):\s*(.*)$")
    dim_re = re.compile(
        r"(\d+(?:\.\d+)?)\s*(?:wide)?\s*x\s*(\d+(?:\.\d+)?)\s*(?:high)?",
        re.IGNORECASE,
    )
    origin_re = re.compile(
        r"origin\s*\(\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\)",
        re.IGNORECASE,
    )

    for raw_line in user_prompt.splitlines():
        line_match = line_re.match(raw_line)
        if line_match is None:
            continue
        room_name = line_match.group(1).strip()
        body = line_match.group(2)

        dim_match = dim_re.search(body)
        if dim_match is None:
            continue

        width = _to_float(dim_match.group(1), 0.0)
        height = _to_float(dim_match.group(2), 0.0)
        if width <= 0 or height <= 0:
            continue

        origin_match = origin_re.search(body)
        if origin_match is not None:
            ox = _to_float(origin_match.group(1), 0.0)
            oy = _to_float(origin_match.group(2), 0.0)
            origin = {"x": ox, "y": oy}
        else:
            origin = None

        rooms.append({
            "name": room_name,
            "room_type": _normalize_room_type(room_name, None),
            "width": width,
            "height": height,
            "origin": origin,
        })

    if not rooms:
        return rooms

    # Auto-place rooms with missing origins in a simple row-wrap strategy.
    cursor_x = 0.0
    cursor_y = 0.0
    row_height = 0.0
    for room in rooms:
        if room["origin"] is not None:
            continue
        rw = room["width"]
        rh = room["height"]
        if cursor_x + rw > boundary_w and cursor_x > 0:
            cursor_x = 0.0
            cursor_y += row_height
            row_height = 0.0

        if cursor_y + rh > boundary_h:
            cursor_y = max(0.0, boundary_h - rh)
        room["origin"] = {"x": cursor_x, "y": cursor_y}

        cursor_x += rw
        row_height = max(row_height, rh)

    return rooms


def _make_default_opening(room: dict, wall: str) -> tuple[dict, dict]:
    ox = _to_float((room.get("origin") or {}).get("x"), 0.0)
    oy = _to_float((room.get("origin") or {}).get("y"), 0.0)
    rw = _to_float(room.get("width"), 0.0)
    rh = _to_float(room.get("height"), 0.0)

    if wall in {"top", "bottom"}:
        span = max(0.8, min(1.2, rw * 0.25))
        start_x = ox + max(0.0, (rw - span) / 2.0)
        end_x = min(ox + rw, start_x + span)
        fixed_y = oy if wall == "bottom" else oy + rh
        return {"x": start_x, "y": fixed_y}, {"x": end_x, "y": fixed_y}

    span = max(0.8, min(1.2, rh * 0.25))
    start_y = oy + max(0.0, (rh - span) / 2.0)
    end_y = min(oy + rh, start_y + span)
    fixed_x = ox if wall == "left" else ox + rw
    return {"x": fixed_x, "y": start_y}, {"x": fixed_x, "y": end_y}


def _repair_opening(opening: dict, room_map: dict[str, dict]) -> Optional[dict]:
    if not isinstance(opening, dict):
        return None

    opening_type = opening.get("type")
    if opening_type not in {"door", "window"}:
        return None

    room_name = opening.get("room_name")
    if not isinstance(room_name, str) or room_name not in room_map:
        return None
    room = room_map[room_name]

    wall = opening.get("wall")
    if wall not in {"top", "bottom", "left", "right"}:
        wall = "bottom"

    raw_cs = opening.get("cut_start")
    raw_ce = opening.get("cut_end")
    if not isinstance(raw_cs, dict) or not isinstance(raw_ce, dict):
        cs, ce = _make_default_opening(room, wall)
    else:
        cs = {"x": _to_float(raw_cs.get("x"), 0.0), "y": _to_float(raw_cs.get("y"), 0.0)}
        ce = {"x": _to_float(raw_ce.get("x"), 0.0), "y": _to_float(raw_ce.get("y"), 0.0)}

        ox = _to_float((room.get("origin") or {}).get("x"), 0.0)
        oy = _to_float((room.get("origin") or {}).get("y"), 0.0)
        rw = _to_float(room.get("width"), 0.0)
        rh = _to_float(room.get("height"), 0.0)
        min_x = ox
        max_x = ox + rw
        min_y = oy
        max_y = oy + rh

        if wall in {"top", "bottom"}:
            fixed_y = oy if wall == "bottom" else oy + rh
            x1 = _clip(cs["x"], min_x, max_x)
            x2 = _clip(ce["x"], min_x, max_x)
            if abs(x2 - x1) < 0.01:
                cs, ce = _make_default_opening(room, wall)
            else:
                x_start, x_end = sorted((x1, x2))
                cs = {"x": x_start, "y": fixed_y}
                ce = {"x": x_end, "y": fixed_y}
        else:
            fixed_x = ox if wall == "left" else ox + rw
            y1 = _clip(cs["y"], min_y, max_y)
            y2 = _clip(ce["y"], min_y, max_y)
            if abs(y2 - y1) < 0.01:
                cs, ce = _make_default_opening(room, wall)
            else:
                y_start, y_end = sorted((y1, y2))
                cs = {"x": fixed_x, "y": y_start}
                ce = {"x": fixed_x, "y": y_end}

    repaired = {
        "type": opening_type,
        "room_name": room_name,
        "wall": wall,
        "cut_start": cs,
        "cut_end": ce,
    }
    if opening_type == "door":
        hinge = opening.get("hinge")
        swing = opening.get("swing")
        repaired["hinge"] = hinge if hinge in {"left", "right"} else "left"
        repaired["swing"] = swing if swing in {"in", "out"} else "in"
    return repaired


def repair_floor_plan(data: dict, user_prompt: str) -> dict:
    """
    Repair model output into a strict, drawable JSON contract.
    """
    if not isinstance(data, dict):
        data = {}

    parsed_bw, parsed_bh = _extract_boundary_from_prompt(user_prompt)
    boundary = data.get("boundary")
    if not isinstance(boundary, dict):
        boundary = {}

    bw = _to_float(boundary.get("width"), 0.0)
    bh = _to_float(boundary.get("height"), 0.0)
    if bw <= 0 and parsed_bw is not None:
        bw = parsed_bw
    if bh <= 0 and parsed_bh is not None:
        bh = parsed_bh

    if bw <= 0:
        bw = 20.0
    if bh <= 0:
        bh = 12.0

    raw_rooms = data.get("rooms")
    if not isinstance(raw_rooms, list):
        raw_rooms = []
    if not raw_rooms:
        raw_rooms = _parse_rooms_from_prompt(user_prompt, bw, bh)

    repaired_rooms: list[dict] = []
    seen_names: dict[str, int] = {}
    for idx, room in enumerate(raw_rooms):
        if not isinstance(room, dict):
            continue

        base_name = str(room.get("name") or f"Room {idx + 1}").strip()
        if not base_name:
            base_name = f"Room {idx + 1}"
        count = seen_names.get(base_name, 0) + 1
        seen_names[base_name] = count
        room_name = base_name if count == 1 else f"{base_name} ({count})"

        rw = _to_float(room.get("width"), 0.0)
        rh = _to_float(room.get("height"), 0.0)
        if rw <= 0 or rh <= 0:
            continue
        rw = min(rw, bw)
        rh = min(rh, bh)

        origin = room.get("origin")
        ox = 0.0
        oy = 0.0
        if isinstance(origin, dict):
            ox = _to_float(origin.get("x"), 0.0)
            oy = _to_float(origin.get("y"), 0.0)
        ox = _clip(ox, 0.0, max(0.0, bw - rw))
        oy = _clip(oy, 0.0, max(0.0, bh - rh))

        repaired_rooms.append({
            "name": room_name,
            "room_type": _normalize_room_type(room_name, room.get("room_type")),
            "width": rw,
            "height": rh,
            "origin": {"x": ox, "y": oy},
        })

    if not repaired_rooms:
        repaired_rooms = [{
            "name": "Room 1",
            "room_type": "living",
            "width": bw,
            "height": bh,
            "origin": {"x": 0.0, "y": 0.0},
        }]

    room_map = {r["name"]: r for r in repaired_rooms}
    raw_openings = data.get("openings")
    if not isinstance(raw_openings, list):
        raw_openings = []

    repaired_openings: list[dict] = []
    for opening in raw_openings:
        repaired = _repair_opening(opening, room_map)
        if repaired is not None:
            repaired_openings.append(repaired)

    return {
        "boundary": {"width": bw, "height": bh},
        "rooms": repaired_rooms,
        "openings": repaired_openings,
    }


# ══════════════════════════════════════════════════════════════════════════════
# MODEL
# ══════════════════════════════════════════════════════════════════════════════

model_id = "LiquidAI/LFM2-1.2B-Extract"

def load_model():
    if AutoTokenizer is None or AutoModelForCausalLM is None or torch is None:
        raise RuntimeError(
            "Missing dependencies. Install with: pip install transformers torch"
        )

    print(f"Loading {model_id} ...")
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        device_map="auto",
    )
    model.eval()
    print("Done.")
    return tokenizer, model


def _score_candidate_json(obj: dict) -> tuple[int, int, int]:
    """Higher score is better: prefers complete floor-plan shape and richer content."""
    has_boundary = isinstance(obj.get("boundary"), dict)
    has_rooms = isinstance(obj.get("rooms"), list)
    has_openings = isinstance(obj.get("openings"), list)
    top_bonus = 3 if has_boundary and has_rooms and has_openings else 0
    room_count = len(obj.get("rooms", [])) if has_rooms else 0
    opening_count = len(obj.get("openings", [])) if has_openings else 0
    return (top_bonus, room_count, opening_count)


def _extract_boundary_from_prompt(user_prompt: str) -> tuple[Optional[float], Optional[float]]:
    """
    Best-effort boundary extraction from plain-English prompt.
    Supports patterns like: "20 meters wide by 12 meters high".
    """
    pattern = re.compile(
        r"(\d+(?:\.\d+)?)\s*meters?\s*wide\s*by\s*(\d+(?:\.\d+)?)\s*meters?\s*high",
        re.IGNORECASE,
    )
    match = pattern.search(user_prompt)
    if not match:
        return None, None
    return float(match.group(1)), float(match.group(2))


def _extract_json_object(raw: str) -> dict:
    """Parse the best JSON object found in model output."""
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    decoder = json.JSONDecoder()
    candidates: list[dict] = []
    for idx, ch in enumerate(raw):
        if ch != "{":
            continue
        try:
            parsed, _end = decoder.raw_decode(raw[idx:])
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            candidates.append(parsed)

    if candidates:
        candidates.sort(key=_score_candidate_json, reverse=True)
        return candidates[0]

    raise ValueError(f"No JSON object found in model output:\n{raw}")


def save_floor_plan_output(
    data: dict,
    output_dir: Optional[Path] = None,
    file_name: Optional[str] = None,
) -> Path:
    """Persist output JSON under backend/app/llm/json_output."""
    target_dir = output_dir or (Path(__file__).resolve().parent / "json_output")
    target_dir.mkdir(parents=True, exist_ok=True)

    if file_name is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"floor_plan_output_{timestamp}.json"

    output_path = target_dir / file_name
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return output_path


def generate_floor_plan_json(
    user_prompt: str,
    tokenizer,
    model,
    max_new_tokens: int = 2048,
    temperature: float = 0.0,          # 0 = greedy, most deterministic
    validate: bool = True,
    auto_clean: bool = True,
    strict: bool = True,
    max_attempts: int = 2,
    retry_temperature: float = 0.2,
    use_few_shots: bool = False,
) -> dict:
    if torch is None:
        raise RuntimeError("torch is not installed. Install with: pip install torch")

    base_messages: list[dict] = [{"role": "system", "content": system_prompt}]
    if use_few_shots:
        base_messages.extend(few_shot_messages)
        if base_messages and isinstance(base_messages[1], dict) and base_messages[1].get("role") == "system":
            # Keep one system message only.
            base_messages = [base_messages[0]] + base_messages[2:]
    base_messages.append({"role": "user", "content": user_prompt})
    boundary_w, boundary_h = _extract_boundary_from_prompt(user_prompt)

    attempt_messages = list(base_messages)
    final_data: Optional[dict] = None
    final_errors: list[str] = []
    parse_errors: list[str] = []

    for attempt in range(1, max(1, max_attempts) + 1):
        attempt_temp = temperature if attempt == 1 else max(temperature, retry_temperature)
        attempt_do_sample = attempt_temp > 0
        generation_kwargs = {
            "max_new_tokens": max_new_tokens,
            "do_sample": attempt_do_sample,
            "pad_token_id": tokenizer.eos_token_id,
        }
        if attempt_do_sample:
            generation_kwargs["temperature"] = attempt_temp
            generation_kwargs["top_p"] = 0.95

        prompt_text = tokenizer.apply_chat_template(
            attempt_messages, tokenize=False, add_generation_prompt=True
        )
        inputs = tokenizer(prompt_text, return_tensors="pt").to(model.device)

        with torch.no_grad():
            output_ids = model.generate(**inputs, **generation_kwargs)

        generated_ids = output_ids[0][inputs["input_ids"].shape[-1]:]
        raw = tokenizer.decode(generated_ids, skip_special_tokens=True).strip()

        try:
            data = _extract_json_object(raw)
        except ValueError as exc:
            parse_errors.append(f"Attempt {attempt}: {exc}")
            if attempt == max_attempts:
                if strict:
                    raise
                return {"boundary": {}, "rooms": [], "openings": []}

            attempt_messages = list(base_messages)
            attempt_messages.append({
                "role": "user",
                "content": (
                    "Your previous answer was not parseable JSON. "
                    "Return ONLY one valid JSON object with exactly keys: "
                    "boundary, rooms, openings. No markdown, no explanation."
                ),
            })
            continue

        if auto_clean:
            data = clean_output(data)
            data = remove_invalid_openings(data)
        data = repair_floor_plan(data, user_prompt)

        if not validate:
            return data

        is_valid, errors = validate_floor_plan(data)
        if is_valid:
            print("✅ Validation passed — safe to send to API.")
            return data

        final_data = data
        final_errors = errors
        if attempt == max_attempts:
            break

        boundary_hint = ""
        if boundary_w is not None and boundary_h is not None:
            boundary_hint = (
                f"\nBoundary MUST stay exactly: width={boundary_w}, height={boundary_h}."
            )

        correction_prompt = (
            "Your previous JSON failed validation. "
            "Fix all issues and return ONLY corrected JSON with keys boundary/rooms/openings.\n"
            "Keep all rooms inside boundary and ensure opening cut points lie on the selected wall."
            + boundary_hint +
            "\n"
            "Validation errors:\n"
            + "\n".join(f"- {e}" for e in errors)
        )
        attempt_messages = list(base_messages)
        attempt_messages.append({"role": "assistant", "content": raw})
        attempt_messages.append({"role": "user", "content": correction_prompt})

    if strict:
        fallback_data = repair_floor_plan({}, user_prompt)
        fallback_ok, fallback_errors = validate_floor_plan(fallback_data)
        if fallback_ok:
            print("✅ Fallback from prompt generated a valid JSON.")
            return fallback_data

        detail_lines = []
        if parse_errors:
            detail_lines.extend(parse_errors)
        if final_errors:
            detail_lines.extend(f"Validation: {e}" for e in final_errors)
        if fallback_errors:
            detail_lines.extend(f"Fallback: {e}" for e in fallback_errors)
        raise ValueError("Invalid floor plan JSON after retries:\n" + "\n".join(f" - {e}" for e in detail_lines))

    if final_data is not None:
        print("\n⚠️  Validation errors found BEFORE sending to API:")
        for e in final_errors:
            print(f"   • {e}")
        print()
        return final_data

    return {"boundary": {}, "rooms": [], "openings": []}


# ══════════════════════════════════════════════════════════════════════════════
# EXAMPLE
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    user_prompt = """Generate a precise 2D floor plan with a total footprint of 20 meters wide by 12 meters high.

1. Left Wing (x: 0 to 8):
- Living Room: Bottom-left corner. Dimensions: 8 wide x 7 high. origin (0,0).
- Kitchen: Directly above Living Room. Dimensions: 8 wide x 5 high. origin (0,7).

2. Central Circulation (x: 8 to 10):
- Corridor: Full-height vertical hallway. Dimensions: 2 wide x 12 high. origin (8,0).

3. Right Wing (x: 10 to 20):
- Bedroom 1: Bottom-right. Dimensions: 10 wide x 6 high. origin (10,0).
- Bedroom 2: Top-right. Dimensions: 10 wide x 6 high. origin (10,6).

4. Openings:
- Main entrance door at bottom of Corridor.
- Internal doors connecting Corridor to Living Room, Kitchen, Bedroom 1, Bedroom 2.
- Exterior windows for all rooms."""

    tokenizer, model = load_model()
    try:
        result = generate_floor_plan_json(user_prompt, tokenizer, model)
    except ValueError as exc:
        print("\n❌ Failed to generate a valid floor-plan JSON.")
        print(str(exc))
        raise SystemExit(1)

    print(json.dumps(result, indent=2))
    output_path = save_floor_plan_output(result)
    print(f"\nSaved → {output_path}")
