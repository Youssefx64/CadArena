from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final

# Keep module import cheap: missing CAD deps should only fail when DXF rendering is used.
try:
    import ezdxf
except ImportError as exc:  # pragma: no cover - exercised only when CAD deps are absent
    ezdxf = None
    _EZDXF_IMPORT_ERROR: ImportError | None = exc
else:
    _EZDXF_IMPORT_ERROR = None

from app.core.file_utils import generate_dxf_filename
from app.core.logging import get_logger
from app.domain.architecture.door_geometry import DoorGeometry
from app.schemas.geometry import Point
from app.services.dxf_blocks import register_all_blocks


logger = get_logger(__name__)

# Keep the professional layer table centralized so both DXF and preview output share the same intent.
ARCHITECTURAL_LAYERS: Final[dict[str, dict[str, int]]] = {
    "WALLS": {"color": 0, "lineweight": 50},
    "DOORS": {"color": 0, "lineweight": 25},
    "WINDOWS": {"color": 0, "lineweight": 25},
    "ROOM_LABELS": {"color": 0, "lineweight": 13},
    "DIMENSIONS": {"color": 0, "lineweight": 13},
    "FURNITURE": {"color": 252, "lineweight": 13},
    "HATCH": {"color": 253, "lineweight": 9},
    "BORDER": {"color": 0, "lineweight": 70},
}
# Keep room-bound inference tolerant to the split wall segments created around doors and windows.
AXIS_TOLERANCE: Final[float] = 1e-6
ROOM_BOUND_FALLBACK_SPAN: Final[float] = 4.0
# Keep wall and annotation sizing aligned with the requested professional architectural presentation.
WALL_THICKNESS: Final[float] = 0.20
PLAN_BORDER_WIDTH: Final[float] = 0.08
TEXT_SCALE_FACTOR: Final[float] = 0.05
TEXT_HEIGHT_MIN: Final[float] = 0.12
TEXT_HEIGHT_MAX: Final[float] = 0.35
DIMENSION_OFFSET: Final[float] = 0.8
BATHROOM_HATCH_INSET: Final[float] = 0.1
# Minimum furniture clearance from walls.
WALL_CLR: Final[float] = 0.15
# Store positive extents from insertion point for bounds checking.
BLOCK_BOUNDS: Final[dict[str, tuple[float, float]]] = {
    "BED_DOUBLE": (1.60, 2.00),
    "BED_SINGLE": (1.00, 2.00),
    "WARDROBE": (1.80, 0.60),
    "TOILET_WC": (0.19, 0.70),
    "SINK_WALL": (0.30, 0.52),
    "SHOWER_TRAY": (0.90, 0.90),
    "STOVE_4BURNER": (0.60, 0.60),
    "KITCHEN_SINK_DOUBLE": (0.80, 0.52),
    "REFRIGERATOR": (0.70, 0.75),
    "SOFA_3SEAT": (2.20, 0.92),
    "COFFEE_TABLE": (1.20, 0.60),
}


# Arabic text shaping forms mapping
ARABIC_FORMS = {
    '\u0621': ('\u0621', '\u0621', '\u0621', '\u0621'),  # ء
    '\u0622': ('\ufe81', '\ufe82', '\ufe82', '\ufe81'),  # آ
    '\u0623': ('\ufe83', '\ufe84', '\ufe84', '\ufe83'),  # أ
    '\u0624': ('\ufe85', '\ufe86', '\ufe86', '\ufe85'),  # ؤ
    '\u0625': ('\ufe87', '\ufe88', '\ufe88', '\ufe87'),  # إ
    '\u0626': ('\ufe89', '\ufe8a', '\ufe8c', '\ufe8b'),  # ئ
    '\u0627': ('\ufe8d', '\ufe8e', '\ufe8e', '\ufe8d'),  # ا
    '\u0628': ('\ufe8f', '\ufe90', '\ufe92', '\ufe91'),  # ب
    '\u0629': ('\ufe93', '\ufe94', '\ufe94', '\ufe93'),  # ة
    '\u062a': ('\ufe95', '\ufe96', '\ufe98', '\ufe97'),  # ت
    '\u062b': ('\ufe99', '\ufe9a', '\ufe9c', '\ufe9b'),  # ث
    '\u062c': ('\ufe9d', '\ufe9e', '\ufea0', '\ufe9f'),  # ج
    '\u062d': ('\ufea1', '\ufea2', '\ufea4', '\ufea3'),  # ح
    '\u062e': ('\ufea5', '\ufea6', '\ufea8', '\ufea7'),  # خ
    '\u062f': ('\ufea9', '\ufeaa', '\ufeaa', '\ufea9'),  # د
    '\u0630': ('\ufeab', '\ufeac', '\ufeac', '\ufeab'),  # ذ
    '\u0631': ('\ufead', '\ufeae', '\ufeae', '\ufead'),  # ر
    '\u0632': ('\ufeaf', '\ufeb0', '\ufeb0', '\ufeaf'),  # ز
    '\u0633': ('\ufeb1', '\ufeb2', '\ufeb4', '\ufeb3'),  # س
    '\u0634': ('\ufeb5', '\ufeb6', '\ufeb8', '\ufeb7'),  # ش
    '\u0635': ('\ufeb9', '\ufeba', '\ufebc', '\ufebb'),  # ص
    '\u0636': ('\ufebd', '\ufebe', '\ufec0', '\ufebf'),  # ض
    '\u0637': ('\ufec1', '\ufec2', '\ufec4', '\ufec3'),  # ط
    '\u0638': ('\ufec5', '\ufec6', '\ufec8', '\ufec7'),  # ظ
    '\u0639': ('\ufec9', '\ufeca', '\ufecc', '\ufecb'),  # ع
    '\u063a': ('\ufecd', '\ufece', '\ufed0', '\ufecf'),  # غ
    '\u0641': ('\ufed1', '\ufed2', '\ufed4', '\ufed3'),  # ف
    '\u0642': ('\ufed5', '\ufed6', '\ufed8', '\ufed7'),  # ق
    '\u0643': ('\ufed9', '\ufeda', '\ufedc', '\ufedb'),  # ك
    '\u0644': ('\ufedd', '\ufede', '\ufee0', '\ufedf'),  # ل
    '\u0645': ('\ufee1', '\ufee2', '\ufee4', '\ufee3'),  # م
    '\u0646': ('\ufee5', '\ufee6', '\ufee8', '\ufee7'),  # ن
    '\u0647': ('\ufee9', '\ufeea', '\ufeec', '\ufeeb'),  # ه
    '\u0648': ('\ufeed', '\ufeee', '\ufeee', '\ufeed'),  # و
    '\u0649': ('\ufeef', '\ufef0', '\ufef0', '\ufeef'),  # ى
    '\u064a': ('\ufef1', '\ufef2', '\ufef4', '\ufef3'),  # ي
}

DUAL_CONNECTING = {
    '\u0628', '\u062a', '\u062b', '\u062c', '\u062d', '\u062e',
    '\u0633', '\u0634', '\u0635', '\u0636', '\u0637', '\u0638',
    '\u0639', '\u063a', '\u0641', '\u0642', '\u0643', '\u0644',
    '\u0645', '\u0646', '\u0647', '\u064a', '\u0626'
}

RIGHT_CONNECTING = {
    '\u0622', '\u0623', '\u0624', '\u0625', '\u0627', '\u0629',
    '\u062f', '\u0630', '\u0631', '\u0632', '\u0648', '\u0649',
    '\u0621'
}

def is_arabic_char(c: str) -> bool:
    if not c:
        return False
    val = ord(c)
    return (
        (0x0600 <= val <= 0x06FF) or
        (0x0750 <= val <= 0x077F) or
        (0xFB50 <= val <= 0xFDFF) or
        (0xFE70 <= val <= 0xFEFF)
    )

def shape_arabic_string(text: str) -> str:
    n = len(text)
    shaped = []
    for i, c in enumerate(text):
        if c not in ARABIC_FORMS:
            shaped.append(c)
            continue
        
        connect_right = False
        if i > 0:
            prev_c = text[i-1]
            if prev_c in DUAL_CONNECTING and (c in DUAL_CONNECTING or c in RIGHT_CONNECTING):
                connect_right = True
                
        connect_left = False
        if i < n - 1:
            next_c = text[i+1]
            if c in DUAL_CONNECTING and (next_c in DUAL_CONNECTING or next_c in RIGHT_CONNECTING):
                connect_left = True
                
        forms = ARABIC_FORMS[c]
        if connect_right and connect_left:
            shaped.append(forms[2])  # Medial
        elif connect_right:
            shaped.append(forms[1])  # Final
        elif connect_left:
            shaped.append(forms[3])  # Initial
        else:
            shaped.append(forms[0])  # Isolated
            
    return "".join(shaped)

def reshape_and_reverse_bidi(text: str) -> str:
    if not text:
        return text
        
    arabic_indices = [i for i, c in enumerate(text) if is_arabic_char(c)]
    if not arabic_indices:
        return text
        
    blocks = []
    current_start = arabic_indices[0]
    current_end = arabic_indices[0]
    
    for idx in arabic_indices[1:]:
        in_between = text[current_end + 1 : idx]
        all_ok = True
        for char in in_between:
            if not (is_arabic_char(char) or char.isspace() or char in "—-_()[]{}.,;:!?/\\*+=&%#@$<>\"'"):
                all_ok = False
                break
        if all_ok:
            current_end = idx
        else:
            blocks.append((current_start, current_end))
            current_start = idx
            current_end = idx
    blocks.append((current_start, current_end))
    
    result_parts = []
    last_idx = 0
    for start, end in blocks:
        result_parts.append(text[last_idx:start])
        block_text = text[start : end + 1]
        shaped = shape_arabic_string(block_text)
        reversed_shaped = shaped[::-1]
        result_parts.append(reversed_shaped)
        last_idx = end + 1
    result_parts.append(text[last_idx:])
    
    return "".join(result_parts)



# Keep the lightweight room view so furniture placement can run without changing external schemas.
@dataclass(frozen=True)
class _RenderableFurnitureRoom:
    name: str
    room_type: str
    width: float
    height: float


# Keep insertion metadata together for consistent pre-insert validation.
@dataclass(frozen=True)
class _BlockPlacement:
    block_name: str
    x: float
    y: float
    piece_w: float
    piece_h: float
    rotation: float = 0.0
    scale: float = 1.0


# Raise a clear runtime error at the point of DXF use instead of crashing app imports.
def _require_ezdxf():
    if ezdxf is None:
        raise RuntimeError(
            "DXF rendering requires 'ezdxf'. Install CAD dependencies to enable DXF generation."
        ) from _EZDXF_IMPORT_ERROR
    return ezdxf


# Ensure a named layer exists with the requested color and lineweight.
def _ensure_layer(doc, name: str, color: int, lineweight: int | None = None) -> None:
    if name in doc.layers:
        layer = doc.layers.get(name)
    else:
        layer = doc.layers.new(name)
    layer.color = color
    if lineweight is not None:
        layer.lineweight = lineweight


# Compute the professional room-name height from the shorter room dimension with the requested floor and ceiling.
def compute_text_height(
    room_w: float,
    room_h: float,
    room_name: str = "",
    dims_text: str = "",
    boundary_w: float | None = None,
    boundary_h: float | None = None,
) -> float:
    shorter = min(room_w, room_h)
    
    if boundary_w is not None and boundary_h is not None and boundary_w > 0 and boundary_h > 0:
        diag = (boundary_w**2 + boundary_h**2) ** 0.5
        layout_scale = max(0.45, min(1.25, diag / 20.0))
    else:
        layout_scale = 1.0

    h_min = TEXT_HEIGHT_MIN * layout_scale
    h_max = TEXT_HEIGHT_MAX * layout_scale
    scale_factor = TEXT_SCALE_FACTOR * layout_scale

    h = shorter * scale_factor
    h = max(h_min, min(h_max, h))
    
    # Dynamic adjustment based on text lengths to prevent wall overlap
    if room_name:
        max_allowed_w = room_w * 0.85
        # Standard character width in standard DXF font is roughly 0.75 * height
        height_limit_w = max_allowed_w / (len(room_name) * 0.75)
        h = min(h, height_limit_w)
        
    if dims_text:
        max_allowed_w = room_w * 0.85
        # Since dims_text is rendered at height h * 0.65, its width is len(dims_text) * (h * 0.65) * 0.7
        height_limit_dims = max_allowed_w / (len(dims_text) * 0.65 * 0.7)
        h = min(h, height_limit_dims)
        
    # Vertical space limit (total block height is approx 1.8 * h)
    max_allowed_h = room_h * 0.75
    height_limit_h = max_allowed_h / 1.8
    h = min(h, height_limit_h)
    
    # Legibility floor
    return max(0.06 * layout_scale, h)


# Convert metric lengths to architectural feet-inch strings for room labels.
def _to_ft_in(metres: float) -> str:
    total_inches = metres * 39.3701
    feet = int(total_inches // 12)
    inches = round(total_inches % 12)
    if inches == 12:
        feet += 1
        inches = 0
    return f"{feet}'-{inches}\""


# Keep line-pair reduction robust by aligning segment directions before averaging them into one centerline.
def _pair_centerline(
    first: tuple[Point, Point],
    second: tuple[Point, Point],
) -> tuple[tuple[float, float], tuple[float, float]]:
    first_start = (first[0].x, first[0].y)
    first_end = (first[1].x, first[1].y)
    second_start = (second[0].x, second[0].y)
    second_end = (second[1].x, second[1].y)

    direct_delta = (
        (first_start[0] - second_start[0]) ** 2
        + (first_start[1] - second_start[1]) ** 2
        + (first_end[0] - second_end[0]) ** 2
        + (first_end[1] - second_end[1]) ** 2
    )
    reversed_delta = (
        (first_start[0] - second_end[0]) ** 2
        + (first_start[1] - second_end[1]) ** 2
        + (first_end[0] - second_start[0]) ** 2
        + (first_end[1] - second_start[1]) ** 2
    )
    if reversed_delta < direct_delta:
        second_start, second_end = second_end, second_start

    start = ((first_start[0] + second_start[0]) / 2.0, (first_start[1] + second_start[1]) / 2.0)
    end = ((first_end[0] + second_end[0]) / 2.0, (first_end[1] + second_end[1]) / 2.0)
    return start, end


# Keep centered TEXT placement tolerant across ezdxf versions by isolating the alignment import.
def _set_middle_center(entity, insert: tuple[float, float]) -> None:
    try:
        from ezdxf.enums import TextEntityAlignment

        entity.set_placement(insert, align=TextEntityAlignment.MIDDLE_CENTER)
    except Exception:
        entity.dxf.insert = insert


# Insert one reusable block reference using rotation and uniform scaling.
def _insert(msp, name: str, x: float, y: float, rotation: float = 0, scale: float = 1.0) -> None:
    msp.add_blockref(
        name,
        insert=(x, y),
        dxfattribs={"rotation": rotation, "xscale": scale, "yscale": scale},
    )


# Enforce the requested right/top bounds gate before any furniture insert.
def _passes_bounds(
    *,
    insert_x: float,
    insert_y: float,
    piece_w: float,
    piece_h: float,
    rx: float,
    ry: float,
    rw: float,
    rh: float,
    rotation: float = 0.0,
    block_name: str | None = None,
) -> bool:
    # QUALITY FIX: enforce room bounds using the actual block orientation and symmetry.
    rotation = int(rotation) % 360
    is_symmetric = block_name in {"TOILET_WC", "SINK_WALL"}

    if is_symmetric:
        if rotation == 0:
            min_x = insert_x - piece_w
            max_x = insert_x + piece_w
            min_y = insert_y
            max_y = insert_y + piece_h
        elif rotation == 90:
            min_x = insert_x - piece_h
            max_x = insert_x
            min_y = insert_y - piece_w
            max_y = insert_y + piece_w
        elif rotation == 180:
            min_x = insert_x - piece_w
            max_x = insert_x + piece_w
            min_y = insert_y - piece_h
            max_y = insert_y
        else:  # rotation == 270
            min_x = insert_x
            max_x = insert_x + piece_h
            min_y = insert_y - piece_w
            max_y = insert_y + piece_w
    else:
        if rotation == 0:
            min_x = insert_x
            max_x = insert_x + piece_w
            min_y = insert_y
            max_y = insert_y + piece_h
        elif rotation == 90:
            min_x = insert_x - piece_h
            max_x = insert_x
            min_y = insert_y
            max_y = insert_y + piece_w
        elif rotation == 180:
            min_x = insert_x - piece_w
            max_x = insert_x
            min_y = insert_y - piece_h
            max_y = insert_y
        else:  # rotation == 270
            min_x = insert_x
            max_x = insert_x + piece_h
            min_y = insert_y - piece_w
            max_y = insert_y

    if min_x < rx + WALL_CLR - AXIS_TOLERANCE:
        return False
    if min_y < ry + WALL_CLR - AXIS_TOLERANCE:
        return False
    if max_x > rx + rw - WALL_CLR + AXIS_TOLERANCE:
        return False
    if max_y > ry + rh - WALL_CLR + AXIS_TOLERANCE:
        return False
    return True


# Validate placement and insert the block when it fits inside the room envelope.
def _insert_with_bounds(msp, room_name: str, placement: _BlockPlacement, rx: float, ry: float, rw: float, rh: float) -> None:
    if not _passes_bounds(
        insert_x=placement.x,
        insert_y=placement.y,
        piece_w=placement.piece_w,
        piece_h=placement.piece_h,
        rx=rx,
        ry=ry,
        rw=rw,
        rh=rh,
        rotation=placement.rotation,
        block_name=placement.block_name,
    ):
        logger.warning(
            "Skipping furniture block=%s room=%s insert=(%.2f, %.2f) size=(%.2f, %.2f)",
            placement.block_name,
            room_name,
            placement.x,
            placement.y,
            placement.piece_w,
            placement.piece_h,
        )
        return

    _insert(
        msp,
        placement.block_name,
        placement.x,
        placement.y,
        rotation=placement.rotation,
        scale=placement.scale,
    )


# QUALITY FIX: build wall-aligned furniture placement for any of the four walls.
def _wall_aligned_block(
    *,
    block_name: str,
    wall: str,
    rx: float,
    ry: float,
    rw: float,
    rh: float,
    item_w: float,
    item_h: float,
    along_offset: float = 0.0,
    centered: bool = False,
) -> _BlockPlacement:
    normalized_wall = wall.strip().lower()
    if normalized_wall == "bottom":
        x = rx + (rw - item_w) / 2.0 if centered else rx + WALL_CLR + along_offset
        y = ry + WALL_CLR
        rotation = 0.0
        return _BlockPlacement(
            block_name=block_name,
            x=x,
            y=y,
            piece_w=item_w,
            piece_h=item_h,
            rotation=rotation,
        )

    if normalized_wall == "top":
        x = rx + (rw + item_w) / 2.0 if centered else rx + WALL_CLR + along_offset + item_w
        y = ry + rh - WALL_CLR
        rotation = 180.0
        return _BlockPlacement(
            block_name=block_name,
            x=x,
            y=y,
            piece_w=item_w,
            piece_h=item_h,
            rotation=rotation,
        )

    footprint_w = item_h
    footprint_h = item_w
    if normalized_wall == "left":
        x = rx + WALL_CLR
        if centered:
            y = ry + (rh + item_w) / 2.0
        else:
            y = ry + WALL_CLR + along_offset + item_w
        rotation = 270.0
    else:
        x = rx + rw - WALL_CLR
        if centered:
            y = ry + (rh - item_w) / 2.0
        else:
            y = ry + WALL_CLR + along_offset
        rotation = 90.0
    return _BlockPlacement(
        block_name=block_name,
        x=x,
        y=y,
        piece_w=footprint_w,
        piece_h=footprint_h,
        rotation=rotation,
    )


# QUALITY FIX: draw a simple TV unit rectangle against the opposite wall from the sofa.
def _draw_tv_unit(
    msp,
    *,
    room_name: str,
    x: float,
    y: float,
    width: float,
    height: float,
    rx: float,
    ry: float,
    rw: float,
    rh: float,
) -> None:
    if not _passes_bounds(
        insert_x=x,
        insert_y=y,
        piece_w=width,
        piece_h=height,
        rx=rx,
        ry=ry,
        rw=rw,
        rh=rh,
    ):
        logger.warning(
            "Skipping furniture block=TV_UNIT room=%s insert=(%.2f, %.2f) size=(%.2f, %.2f)",
            room_name,
            x,
            y,
            width,
            height,
        )
        return

    msp.add_lwpolyline(
        [
            (x, y),
            (x + width, y),
            (x + width, y + height),
            (x, y + height),
        ],
        close=True,
        dxfattribs={"layer": "FURNITURE_LIVING"},
    )


# QUALITY FIX: place furniture using door-aware, inward-facing room rules.
def draw_furniture(msp, room, room_origin_x, room_origin_y, *, door_wall: str | None = None):
    rx = room_origin_x
    ry = room_origin_y
    rw = room.width
    rh = room.height
    room_type = room.room_type.strip().lower()
    placements: list[_BlockPlacement] = []

    if room_type in {"bedroom", "master_bedroom"}:
        # QUALITY FIX: bed against wall opposite the door, fallback to top wall when door is unknown.
        opposite_wall = {
            "bottom": "top",
            "top": "bottom",
            "left": "right",
            "right": "left",
        }
        preferred_bed_wall = opposite_wall.get((door_wall or "").strip().lower(), "top")
        bed_block = "BED_DOUBLE" if rw >= 3.2 else "BED_SINGLE"
        bounds_w, bounds_h = BLOCK_BOUNDS[bed_block]
        bed_placement = _wall_aligned_block(
            block_name=bed_block,
            wall=preferred_bed_wall,
            rx=rx,
            ry=ry,
            rw=rw,
            rh=rh,
            item_w=bounds_w,
            item_h=bounds_h,
            centered=True,
        )
        # QUALITY FIX: keep at least 0.7m side clearance for bed circulation.
        if preferred_bed_wall in {"top", "bottom"}:
            side_clearance = (rw - bed_placement.piece_w) / 2.0
        else:
            side_clearance = (rh - bed_placement.piece_h) / 2.0
        if side_clearance + AXIS_TOLERANCE < 0.7:
            preferred_bed_wall = "top"
            bed_placement = _wall_aligned_block(
                block_name=bed_block,
                wall=preferred_bed_wall,
                rx=rx,
                ry=ry,
                rw=rw,
                rh=rh,
                item_w=bounds_w,
                item_h=bounds_h,
                centered=True,
            )
        placements.append(bed_placement)

        if room_type == "master_bedroom" and rw >= 3.0:
            # QUALITY FIX: wardrobe on a wall perpendicular to the bed wall.
            wardrobe_w, wardrobe_h = BLOCK_BOUNDS["WARDROBE"]
            if preferred_bed_wall in {"top", "bottom"}:
                wardrobe_wall = "left"
                wardrobe = _wall_aligned_block(
                    block_name="WARDROBE",
                    wall=wardrobe_wall,
                    rx=rx,
                    ry=ry,
                    rw=rw,
                    rh=rh,
                    item_w=wardrobe_w,
                    item_h=wardrobe_h,
                    centered=True,
                )
            else:
                wardrobe_wall = "top"
                wardrobe = _wall_aligned_block(
                    block_name="WARDROBE",
                    wall=wardrobe_wall,
                    rx=rx,
                    ry=ry,
                    rw=rw,
                    rh=rh,
                    item_w=wardrobe_w,
                    item_h=wardrobe_h,
                    centered=True,
                )
            placements.append(wardrobe)

    elif room_type == "bathroom":
        # QUALITY FIX: bathroom fixtures depend on room width and back-wall orientation.
        toilet_w, toilet_h = BLOCK_BOUNDS["TOILET_WC"]
        sink_w, sink_h = BLOCK_BOUNDS["SINK_WALL"]
        shower_w, shower_h = BLOCK_BOUNDS["SHOWER_TRAY"]
        opposite_wall = {
            "bottom": "top",
            "top": "bottom",
            "left": "right",
            "right": "left",
        }
        back_wall = opposite_wall.get((door_wall or "").strip().lower(), "top")

        if rw < 1.8:
            toilet = _wall_aligned_block(
                block_name="TOILET_WC",
                wall=back_wall,
                rx=rx,
                ry=ry,
                rw=rw,
                rh=rh,
                item_w=toilet_w,
                item_h=toilet_h,
                centered=True,
            )
            placements.append(toilet)

            sink = _wall_aligned_block(
                block_name="SINK_WALL",
                wall=back_wall,
                rx=rx,
                ry=ry,
                rw=rw,
                rh=rh,
                item_w=sink_w,
                item_h=sink_h,
                along_offset=0.30,
                centered=False,
            )
            placements.append(sink)
        else:
            back_right_wall = "right" if back_wall in {"top", "bottom"} else back_wall
            front_left_wall = "left" if back_wall in {"top", "bottom"} else (
                "bottom" if back_wall == "right" else "top"
            )

            placements.append(
                _wall_aligned_block(
                    block_name="TOILET_WC",
                    wall=back_right_wall,
                    rx=rx,
                    ry=ry,
                    rw=rw,
                    rh=rh,
                    item_w=toilet_w,
                    item_h=toilet_h,
                    centered=False,
                )
            )
            placements.append(
                _wall_aligned_block(
                    block_name="SINK_WALL",
                    wall=front_left_wall,
                    rx=rx,
                    ry=ry,
                    rw=rw,
                    rh=rh,
                    item_w=sink_w,
                    item_h=sink_h,
                    centered=False,
                )
            )

        if rw >= 1.8 and rh >= 1.8:
            shower_wall = "left" if back_wall in {"top", "bottom"} else back_wall
            placements.append(
                _wall_aligned_block(
                    block_name="SHOWER_TRAY",
                    wall=shower_wall,
                    rx=rx,
                    ry=ry,
                    rw=rw,
                    rh=rh,
                    item_w=shower_w,
                    item_h=shower_h,
                    centered=False,
                )
            )

    elif room_type == "kitchen":
        # QUALITY FIX: kitchen layout uses back-wall inference and switches between single-wall and L-shape.
        sink_w, sink_h = BLOCK_BOUNDS["KITCHEN_SINK_DOUBLE"]
        stove_w, stove_h = BLOCK_BOUNDS["STOVE_4BURNER"]
        fridge_w, fridge_h = BLOCK_BOUNDS["REFRIGERATOR"]
        opposite_wall = {
            "bottom": "top",
            "top": "bottom",
            "left": "right",
            "right": "left",
        }
        back_wall = opposite_wall.get((door_wall or "").strip().lower(), "top")

        sink = _wall_aligned_block(
            block_name="KITCHEN_SINK_DOUBLE",
            wall=back_wall,
            rx=rx,
            ry=ry,
            rw=rw,
            rh=rh,
            item_w=sink_w,
            item_h=sink_h,
            along_offset=0.0,
            centered=False,
        )
        placements.append(sink)
        placements.append(
            _wall_aligned_block(
                block_name="STOVE_4BURNER",
                wall=back_wall,
                rx=rx,
                ry=ry,
                rw=rw,
                rh=rh,
                item_w=stove_w,
                item_h=stove_h,
                along_offset=sink_w + 0.10,
                centered=False,
            )
        )
        placements.append(
            _wall_aligned_block(
                block_name="REFRIGERATOR",
                wall=back_wall,
                rx=rx,
                ry=ry,
                rw=rw,
                rh=rh,
                item_w=fridge_w,
                item_h=fridge_h,
                along_offset=max(0.0, (rw if back_wall in {"top", "bottom"} else rh) - fridge_w - 2 * WALL_CLR),
                centered=False,
            )
        )

        if rw >= 2.5:
            adjacent_wall = "right" if back_wall in {"top", "bottom"} else "top"
            placements.append(
                _wall_aligned_block(
                    block_name="KITCHEN_SINK_DOUBLE",
                    wall=adjacent_wall,
                    rx=rx,
                    ry=ry,
                    rw=rw,
                    rh=rh,
                    item_w=sink_w,
                    item_h=sink_h,
                    along_offset=0.0,
                    centered=False,
                )
            )

    elif room_type == "living_room":
        # QUALITY FIX: living room sofa is centered on longest wall and always faces inward.
        sofa_w, sofa_h = BLOCK_BOUNDS["SOFA_3SEAT"]
        table_w, table_h = BLOCK_BOUNDS["COFFEE_TABLE"]

        if rw >= rh:
            sofa_wall = "bottom"
            sofa = _wall_aligned_block(
                block_name="SOFA_3SEAT",
                wall=sofa_wall,
                rx=rx,
                ry=ry,
                rw=rw,
                rh=rh,
                item_w=sofa_w,
                item_h=sofa_h,
                centered=True,
            )
            placements.append(sofa)
            sofa_center_x = sofa.x + sofa.piece_w / 2.0
            sofa_center_y = sofa.y + sofa.piece_h / 2.0
            table_center_x = sofa_center_x
            table_center_y = sofa_center_y + 0.9
            tv_x = rx + (rw - 1.60) / 2.0
            tv_y = ry + rh - 0.25 - WALL_CLR
            _draw_tv_unit(
                msp,
                room_name=room.name,
                x=tv_x,
                y=tv_y,
                width=1.60,
                height=0.25,
                rx=rx,
                ry=ry,
                rw=rw,
                rh=rh,
            )
        else:
            sofa_wall = "left"
            sofa = _wall_aligned_block(
                block_name="SOFA_3SEAT",
                wall=sofa_wall,
                rx=rx,
                ry=ry,
                rw=rw,
                rh=rh,
                item_w=sofa_w,
                item_h=sofa_h,
                centered=True,
            )
            placements.append(sofa)
            sofa_center_x = sofa.x + sofa.piece_w / 2.0
            sofa_center_y = sofa.y + sofa.piece_h / 2.0
            table_center_x = sofa_center_x + 0.9
            table_center_y = sofa_center_y
            tv_x = rx + rw - 0.25 - WALL_CLR
            tv_y = ry + (rh - 1.60) / 2.0
            _draw_tv_unit(
                msp,
                room_name=room.name,
                x=tv_x,
                y=tv_y,
                width=0.25,
                height=1.60,
                rx=rx,
                ry=ry,
                rw=rw,
                rh=rh,
            )

        placements.append(
            _BlockPlacement(
                block_name="COFFEE_TABLE",
                x=table_center_x - table_w / 2.0,
                y=table_center_y - table_h / 2.0,
                piece_w=table_w,
                piece_h=table_h,
                rotation=0.0,
            )
        )

    for placement in placements:
        _insert_with_bounds(msp, room.name, placement, rx, ry, rw, rh)


class DXFRoomRenderer:
    """
    Professional CAD renderer with standard architectural door representation.

    This class provides methods to render complete floor plans including:
    - Boundary walls
    - Interior walls with thickness
    - Doors with swing arcs
    - Windows
    - Room labels and dimensions
    - Stair representations
    """

    def __init__(self):
        """
        Initialize DXF document and create standard layers.

        Creates a new DXF document (R2010 format) and sets up layers
        for different architectural elements with appropriate colors.
        """
        dxf_module = _require_ezdxf()  # Resolve the optional dependency only when rendering starts.
        self.doc = dxf_module.new(dxfversion="R2010")
        # Keep the document explicitly metric and white-background so viewers open into the requested presentation.
        self.doc.header["$INSUNITS"] = 6
        self.doc.header["$MEASUREMENT"] = 1
        try:
            # Apply the requested white model-space background when the local ezdxf build exposes that header variable.
            self.doc.header["$BACKGRNDCOLOR"] = 7
        except Exception:
            logger.debug("DXF header $BACKGRNDCOLOR is not supported by the installed ezdxf version.")

        # Keep the professional architectural layers explicit on the DXF document.
        for name, props in ARCHITECTURAL_LAYERS.items():
            _ensure_layer(self.doc, name, props["color"], props["lineweight"])
        # Keep a compatibility layer for boundary collection even though the final heavy outline is drawn on BORDER.
        _ensure_layer(self.doc, "BOUNDARY", 0, ARCHITECTURAL_LAYERS["BORDER"]["lineweight"])

        register_all_blocks(self.doc)  # Register block definitions before any room geometry is drawn.
        # Restyle the existing furniture block layers so they read lighter than the primary wall graphics.
        for furniture_layer in (
            "FURNITURE_BEDROOM",
            "FURNITURE_SANITARY",
            "FURNITURE_LIVING",
            "FURNITURE_KITCHEN",
        ):
            _ensure_layer(
                self.doc,
                furniture_layer,
                ARCHITECTURAL_LAYERS["FURNITURE"]["color"],
                ARCHITECTURAL_LAYERS["FURNITURE"]["lineweight"],
            )

        self.msp = self.doc.modelspace()
        # Track structural lines as they are drawn so label placement can infer room bounds without changing callers.
        self._structural_segments: list[tuple[float, float, float, float]] = []
        # Deduplicate furniture inserts because furniture is emitted from the existing room-label loop.
        self._furniture_drawn_names: set[str] = set()
        # Keep bathroom hatch placement idempotent because room labels can be revisited in tests.
        self._hatched_room_keys: set[str] = set()
        # QUALITY FIX: keep door geometries so furniture placement can infer door-opposite walls per room.
        self._door_geometries: list[DoorGeometry] = []
        # Keep the final decoration pass single-shot so repeated saves do not duplicate dimensions or title graphics.
        self._decorations_finalized = False
        # Track the boundary extents so exterior dimensions and border graphics can be placed late.
        self._boundary_extents: tuple[float, float, float, float] | None = None

    def draw_boundary(self, points: list[Point]):
        if len(points) < 2:
            return
        # Reconstruct boundary centerlines so the final professional border can be drawn last during save().
        boundary_points = list(points)
        if boundary_points[0] != boundary_points[-1]:
            boundary_points.append(boundary_points[0])
        for start, end in zip(boundary_points, boundary_points[1:]):
            self._record_structural_segment((start.x, start.y), (end.x, end.y), layer="BOUNDARY")

    def draw_wall_segments(self, segments: list[tuple[Point, Point]]):
        self.draw_line_segments(segments, layer="WALLS")

    def draw_boundary_segments(self, segments: list[tuple[Point, Point]]):
        self.draw_line_segments(segments, layer="BOUNDARY")

    def draw_line_segments(
        self,
        segments: list[tuple[Point, Point]],
        layer: str,
        lineweight: int | None = None,
    ):
        if layer in {"WALLS", "BOUNDARY"}:
            # Collapse paired offset lines back into one centerline so walls render as const-width CAD entities.
            self._draw_structural_pairs(segments, layer=layer)
            return

        for start, end in segments:
            dxfattribs = {"layer": layer}
            if lineweight is not None:
                dxfattribs["lineweight"] = lineweight
            self.msp.add_line(  # Draw one non-structural segment such as stairs.
                (start.x, start.y),
                (end.x, end.y),
                dxfattribs=dxfattribs,
            )

    def draw_door_geometry(self, door_geom: DoorGeometry):
        """
        Draw door leaf line and swing arc.

        Args:
            door_geom: Door geometry containing all rendering coordinates.
        """
        self.msp.add_line(  # Draw the door leaf from hinge to leaf tip.
            (door_geom.hinge_point.x, door_geom.hinge_point.y),
            (door_geom.leaf_end_point.x, door_geom.leaf_end_point.y),
            dxfattribs={
                "layer": "DOORS",
                "lineweight": ARCHITECTURAL_LAYERS["DOORS"]["lineweight"],
                "color": ARCHITECTURAL_LAYERS["DOORS"]["color"],
            },
        )

        self.msp.add_arc(  # Draw the door swing arc.
            center=(door_geom.swing_center.x, door_geom.swing_center.y),
            radius=door_geom.swing_radius,
            start_angle=door_geom.swing_start_angle,
            end_angle=door_geom.swing_end_angle,
            dxfattribs={
                "layer": "DOORS",
                "color": ARCHITECTURAL_LAYERS["DOORS"]["color"],
            },
        )
        # QUALITY FIX: store door metadata for later room-local furniture orientation.
        self._door_geometries.append(door_geom)

    def draw_window_segment(self, start: Point, end: Point):
        self.msp.add_line(  # Draw a window opening segment.
            (start.x, start.y),
            (end.x, end.y),
            dxfattribs={
                "layer": "WINDOWS",
                "lineweight": ARCHITECTURAL_LAYERS["WINDOWS"]["lineweight"],
                "color": ARCHITECTURAL_LAYERS["WINDOWS"]["color"],
            },
        )

    def draw_room_label(self, text: str, position: Point, room_type: str | None = None, room_width: float | None = None, room_height: float | None = None, room_origin: Point | None = None):
        if room_width is not None and room_height is not None and room_origin is not None:
            room_left = room_origin.x
            room_bottom = room_origin.y
            room_w = room_width
            room_h = room_height
            room_right = room_left + room_w
            room_top = room_bottom + room_h
        else:
            room_left, room_right, room_bottom, room_top = self._resolve_room_bounds(position)
            room_w = max(room_right - room_left, AXIS_TOLERANCE)
            room_h = max(room_top - room_bottom, AXIS_TOLERANCE)
        center_x = room_left + room_w / 2
        center_y = room_bottom + room_h / 2
        room_area = room_w * room_h
        metric_dims = f"{room_w:.2f} × {room_h:.2f} m"
        area_text = f"{room_area:.1f} m²"
        dims_display = f"{metric_dims}  ({area_text})"
        room_name = (text or "Room").upper()

        boundary_w = None
        boundary_h = None
        if self._boundary_extents is not None:
            left, right, bottom, top = self._boundary_extents
            boundary_w = right - left
            boundary_h = top - bottom

        text_height = compute_text_height(
            room_w,
            room_h,
            room_name,
            dims_display,
            boundary_w=boundary_w,
            boundary_h=boundary_h,
        )

        # Reuse the room-label pass as the room loop hook for bathroom hatches and furniture insertion.
        room_key = f"{text}|{room_type}" if room_type is not None else text
        is_wet_bathroom = room_type == "bathroom" and "laundry" not in text.lower()
        if is_wet_bathroom and room_key not in self._hatched_room_keys:
            # QUALITY FIX: Bathroom floor hatching is removed completely to clean up density as requested.
            # self._draw_bathroom_hatch(room_left, room_bottom, room_w, room_h)
            self._hatched_room_keys.add(room_key)
        if room_key not in self._furniture_drawn_names:
            renderable_room = self._build_renderable_furniture_room(
                text=text,
                room_type=room_type,
                room_width=room_w,
                room_height=room_h,
            )
            if renderable_room is not None:
                # QUALITY FIX: infer nearest door wall to orient furniture inward and opposite door flow.
                door_wall = self._infer_room_door_wall(
                    room_left=room_left,
                    room_right=room_right,
                    room_bottom=room_bottom,
                    room_top=room_top,
                )
                draw_furniture(
                    self.msp,
                    renderable_room,
                    room_left,
                    room_bottom,
                    door_wall=door_wall,
                )
            self._furniture_drawn_names.add(room_key)

        name_insert = (center_x, center_y + text_height * 0.5)
        dim_insert = (center_x, center_y - text_height * 0.6)
        # Use centered TEXT entities so the room name matches the requested professional plan annotation style.
        name_entity = self.msp.add_text(
            room_name,
            dxfattribs={
                "layer": "ROOM_LABELS",
                "color": ARCHITECTURAL_LAYERS["ROOM_LABELS"]["color"],
                "height": text_height,
                "style": "Standard",
                "insert": name_insert,
            },
        )
        _set_middle_center(name_entity, name_insert)

        # Draw combined dimensions and area on a single line to prevent vertical overlap/newlines in TEXT entity
        dim_entity = self.msp.add_text(
            dims_display,
            dxfattribs={
                "layer": "ROOM_LABELS",
                "color": ARCHITECTURAL_LAYERS["ROOM_LABELS"]["color"],
                "height": text_height * 0.65,
                "style": "Standard",
                "insert": dim_insert,
            },
        )
        _set_middle_center(dim_entity, dim_insert)

    def draw_room_dimensions(self, text: str, position: Point):
        _ = (text, position)  # Keep the compatibility hook inert because draw_room_label now owns room dimensions.

    def draw_stair_lines(self, segments: list[tuple[Point, Point]]):
        self.draw_line_segments(segments, layer="STAIRS")

    def save(self) -> Path:
        """
        Save DXF file with generated filename.

        Returns:
            Path to the saved DXF file.
        """
        if not self._decorations_finalized and self._boundary_extents is not None:
            # Add professional exterior dimensions, border, and title in the requested final drawing order.
            self._draw_exterior_dimensions()
            self._draw_plan_border()
            self._draw_title()
            self._decorations_finalized = True

        file_path = generate_dxf_filename(prefix="layout")
        self.doc.saveas(file_path)
        return file_path

    # Reduce each offset line pair back to a single structural centerline before rendering or storing it.
    def _draw_structural_pairs(self, segments: list[tuple[Point, Point]], *, layer: str) -> None:
        index = 0
        while index < len(segments):
            start, end = segments[index]
            if index + 1 < len(segments):
                center_start, center_end = _pair_centerline(segments[index], segments[index + 1])
                index += 2
            else:
                center_start = (start.x, start.y)
                center_end = (end.x, end.y)
                index += 1
            self._record_structural_segment(center_start, center_end, layer=layer)

    # Keep structural bounds and render-time centerlines together so room inference stays in sync with the saved DXF.
    def _record_structural_segment(
        self,
        start: tuple[float, float],
        end: tuple[float, float],
        *,
        layer: str,
    ) -> None:
        self._structural_segments.append((start[0], start[1], end[0], end[1]))
        if layer == "BOUNDARY":
            self._update_boundary_extents(start, end)
            return

        # Render room walls as const-width polylines so openings stay cut precisely by the upstream segment splitting.
        self.msp.add_lwpolyline(
            [start, end],
            dxfattribs={
                "layer": "WALLS",
                "const_width": WALL_THICKNESS,
                "color": ARCHITECTURAL_LAYERS["WALLS"]["color"],
            },
        )

    # Track the global boundary box lazily from the centerline geometry the pipeline already provides.
    def _update_boundary_extents(self, *points: tuple[float, float]) -> None:
        xs = [point[0] for point in points]
        ys = [point[1] for point in points]
        if self._boundary_extents is None:
            self._boundary_extents = (min(xs), max(xs), min(ys), max(ys))
            return

        min_x, max_x, min_y, max_y = self._boundary_extents
        self._boundary_extents = (
            min(min_x, *xs),
            max(max_x, *xs),
            min(min_y, *ys),
            max(max_y, *ys),
        )

    # Add the requested tiled hatch to bathrooms so wet rooms read differently from dry rooms in plan.
    def _draw_bathroom_hatch(self, room_left: float, room_bottom: float, room_w: float, room_h: float) -> None:
        if room_w <= BATHROOM_HATCH_INSET * 2 or room_h <= BATHROOM_HATCH_INSET * 2:
            return
        hatch = self.msp.add_hatch(
            color=ARCHITECTURAL_LAYERS["HATCH"]["color"],
            dxfattribs={"layer": "HATCH"},
        )
        hatch.set_pattern_fill("NET", scale=0.25, angle=0.0)
        hatch.paths.add_polyline_path(
            [
                (room_left + BATHROOM_HATCH_INSET, room_bottom + BATHROOM_HATCH_INSET),
                (room_left + room_w - BATHROOM_HATCH_INSET, room_bottom + BATHROOM_HATCH_INSET),
                (room_left + room_w - BATHROOM_HATCH_INSET, room_bottom + room_h - BATHROOM_HATCH_INSET),
                (room_left + BATHROOM_HATCH_INSET, room_bottom + room_h - BATHROOM_HATCH_INSET),
            ],
            is_closed=True,
        )

    # Place overall width and height dimensions outside the plan extents to match architectural drafting conventions.
    def _draw_exterior_dimensions(self) -> None:
        if self._boundary_extents is None:
            return
        left, right, bottom, top = self._boundary_extents
        center_x = left + (right - left) / 2.0
        center_y = bottom + (top - bottom) / 2.0

        self.msp.add_linear_dim(
            base=(center_x, top + DIMENSION_OFFSET),
            p1=(left, top),
            p2=(right, top),
            dimstyle="Standard",
            dxfattribs={"layer": "DIMENSIONS", "color": 5},
        ).render()
        self.msp.add_linear_dim(
            base=(left - DIMENSION_OFFSET, center_y),
            p1=(left, bottom),
            p2=(left, top),
            angle=90,
            dimstyle="Standard",
            dxfattribs={"layer": "DIMENSIONS", "color": 5},
        ).render()

    # Draw the heavy outer border last so the plan reads as one clean architectural sheet graphic.
    def _draw_plan_border(self) -> None:
        if self._boundary_extents is None:
            return
        left, right, bottom, top = self._boundary_extents
        self.msp.add_lwpolyline(
            [
                (left, bottom),
                (right, bottom),
                (right, top),
                (left, top),
                (left, bottom),
            ],
            close=True,
            dxfattribs={
                "layer": "BORDER",
                "const_width": PLAN_BORDER_WIDTH,
                "color": ARCHITECTURAL_LAYERS["BORDER"]["color"],
            },
        )

    # Add the requested title block treatment beneath the floor plan once the geometry extents are known.
    def _draw_title(self) -> None:
        if self._boundary_extents is None:
            return
        left, right, bottom, _top = self._boundary_extents
        center_x = left + (right - left) / 2.0
        # Scale title text height dynamically based on boundary width
        title_height = max(0.15, min(0.6, (right - left) * 0.025))
        title_y = bottom - (title_height * 2.0)

        total_area = (right - left) * (_top - bottom)
        title_text = f"FLOOR PLAN — مسقط أفقي  ({total_area:.1f} m²)"
        processed_title = reshape_and_reverse_bidi(title_text)

        title_entity = self.msp.add_text(
            processed_title,
            dxfattribs={
                "layer": "ROOM_LABELS",
                "color": ARCHITECTURAL_LAYERS["ROOM_LABELS"]["color"],
                "height": title_height,
                "style": "Standard",
                "insert": (center_x, title_y),
            },
        )
        _set_middle_center(title_entity, (center_x, title_y))
        
        underline_half_len = max(1.5, min(4.0, (right - left) * 0.1))
        underline_offset = title_height * 0.5
        self.msp.add_line(
            (center_x - underline_half_len, title_y - underline_offset),
            (center_x + underline_half_len, title_y - underline_offset),
            dxfattribs={"layer": "ROOM_LABELS", "color": 0, "lineweight": 35},
        )

    # Use nearby vertical and horizontal structural lines to recover room bounds from the upstream room label anchor.
    def _resolve_room_bounds(self, position: Point) -> tuple[float, float, float, float]:
        strict_bounds = self._find_room_bounds(position.x, position.y, relaxed=False)
        if strict_bounds is not None:
            return strict_bounds

        relaxed_bounds = self._find_room_bounds(position.x, position.y, relaxed=True)
        if relaxed_bounds is not None:
            return relaxed_bounds

        # Fall back to a conservative synthetic box so labels still render when geometry is incomplete.
        half_span = ROOM_BOUND_FALLBACK_SPAN / 2
        return (
            position.x - half_span,
            position.x + half_span,
            position.y - half_span,
            position.y + half_span,
        )

    # Strict mode requires spans crossing the seed point; relaxed mode tolerates door/window gaps in walls.
    def _find_room_bounds(
        self,
        seed_x: float,
        seed_y: float,
        *,
        relaxed: bool,
    ) -> tuple[float, float, float, float] | None:
        left_candidates: list[float] = []
        right_candidates: list[float] = []
        bottom_candidates: list[float] = []
        top_candidates: list[float] = []
        gap_tolerance = 1.5 if relaxed else 0.0

        for x1, y1, x2, y2 in self._structural_segments:
            if abs(x1 - x2) <= AXIS_TOLERANCE:
                x = (x1 + x2) / 2
                segment_bottom = min(y1, y2)
                segment_top = max(y1, y2)
                if segment_bottom - gap_tolerance <= seed_y <= segment_top + gap_tolerance:
                    if x < seed_x - AXIS_TOLERANCE:
                        left_candidates.append(x)
                    elif x > seed_x + AXIS_TOLERANCE:
                        right_candidates.append(x)
            elif abs(y1 - y2) <= AXIS_TOLERANCE:
                y = (y1 + y2) / 2
                segment_left = min(x1, x2)
                segment_right = max(x1, x2)
                if segment_left - gap_tolerance <= seed_x <= segment_right + gap_tolerance:
                    if y < seed_y - AXIS_TOLERANCE:
                        bottom_candidates.append(y)
                    elif y > seed_y + AXIS_TOLERANCE:
                        top_candidates.append(y)

        if not left_candidates or not right_candidates or not bottom_candidates or not top_candidates:
            return None

        left = max(left_candidates)
        right = min(right_candidates)
        bottom = max(bottom_candidates)
        top = min(top_candidates)
        if right - left <= AXIS_TOLERANCE or top - bottom <= AXIS_TOLERANCE:
            return None
        return left, right, bottom, top

    # QUALITY FIX: infer closest door wall for a room using hinge points recorded during door rendering.
    def _infer_room_door_wall(
        self,
        *,
        room_left: float,
        room_right: float,
        room_bottom: float,
        room_top: float,
    ) -> str | None:
        if not self._door_geometries:
            return None

        tolerance = 0.35
        candidates: list[tuple[float, str]] = []

        for door in self._door_geometries:
            hinge_x = float(door.hinge_point.x)
            hinge_y = float(door.hinge_point.y)

            if (
                hinge_x < room_left - tolerance
                or hinge_x > room_right + tolerance
                or hinge_y < room_bottom - tolerance
                or hinge_y > room_top + tolerance
            ):
                continue

            if room_bottom - tolerance <= hinge_y <= room_top + tolerance:
                candidates.append((abs(hinge_x - room_left), "left"))
                candidates.append((abs(hinge_x - room_right), "right"))
            if room_left - tolerance <= hinge_x <= room_right + tolerance:
                candidates.append((abs(hinge_y - room_bottom), "bottom"))
                candidates.append((abs(hinge_y - room_top), "top"))

        if not candidates:
            return None

        distance, wall = min(candidates, key=lambda item: item[0])
        if distance > tolerance:
            return None
        return wall

    # Resolve per-room furniture preset from orchestrator hints or room-name fallbacks.
    @staticmethod
    def _build_renderable_furniture_room(
        *,
        text: str,
        room_type: str | None,
        room_width: float,
        room_height: float,
    ) -> _RenderableFurnitureRoom | None:
        preset = DXFRoomRenderer._resolve_furniture_preset(text, room_type=room_type)
        if preset is None:
            return None
        return _RenderableFurnitureRoom(
            name=text,
            room_type=preset,
            width=room_width,
            height=room_height,
        )

    # Honor request-scoped parser furniture presets while preserving fallback name heuristics.
    @staticmethod
    def _resolve_furniture_preset(room_name: str, room_type: str | None = None) -> str | None:
        if room_type == "bathroom" and "laundry" in room_name.lower():
            return None

        try:
            from app.services.design_parser.orchestrator import get_render_furniture_preset
        except Exception:
            get_render_furniture_preset = None

        if get_render_furniture_preset is not None:
            preset = get_render_furniture_preset(room_name)
            if preset == "none":
                return None
            if preset in {"bedroom", "master_bedroom", "bathroom", "kitchen", "living_room"}:
                return preset

        if room_type is not None:
            normalized = room_type.strip().lower()
            if normalized == "living":
                return "living_room"
            if normalized == "master_bedroom":
                return "master_bedroom"
            if normalized == "bedroom":
                return "bedroom"
            if normalized == "kitchen":
                return "kitchen"
            if normalized == "bathroom":
                return "bathroom"

        lowered_name = room_name.strip().lower()
        if "master" in lowered_name and "bed" in lowered_name:
            return "master_bedroom"
        if "bed" in lowered_name:
            return "bedroom"
        if "living" in lowered_name or "lounge" in lowered_name:
            return "living_room"
        if "kitchen" in lowered_name:
            return "kitchen"
        if "bath" in lowered_name or lowered_name == "wc" or "toilet" in lowered_name:
            return "bathroom"
        return None
