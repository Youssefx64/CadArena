"""
Egyptian Building Code (EBC) 2023 dimensional standards.
الكود المصري للمباني - الأبعاد والاشتراطات القياسية

Sources:
  - EBC 2023 (الكود المصري للاشتراطات الإنشائية)
  - Egyptian Housing Standards (معايير وزارة الإسكان)
  - Law 119/2008 (قانون البناء الموحد) — Unified Building Law
  - Egyptian National Authority for Tunnels spatial standards

All dimensions in METERS unless specified.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final


# ══════════════════════════════════════════════════════════════════════════════
# MINIMUM CLEAR DIMENSIONS — EBC Chapter 7 (الأبعاد الدنيا الصافية)
# ══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class RoomStandard:
    """Dimensional standard for a single room type per EBC 2023."""
    min_area: float            # m² — absolute minimum (EBC hard limit)
    recommended_area: float    # m² — good practice
    min_dimension: float       # m — smallest side (clear dimension)
    max_area_ratio: float      # fraction of total floor area (0.0–1.0)
    min_ceiling: float = 2.70  # m — EBC min clear height


EBC_ROOM_STANDARDS: Final[dict[str, RoomStandard]] = {

    # ── BEDROOMS (غرف النوم) ─────────────────────────────────────────────────
    # EBC: غرفة النوم لا تقل مساحتها عن 9 م² وأقل بُعد 2.75 م
    "bedroom": RoomStandard(
        min_area=9.0,
        recommended_area=14.0,
        min_dimension=2.75,
        max_area_ratio=0.25,
        min_ceiling=2.70,
    ),

    # Master bedroom (غرفة النوم الرئيسية)
    # EBC: لا تقل عن 12 م² للغرفة الرئيسية
    "master_bedroom": RoomStandard(
        min_area=12.0,
        recommended_area=18.0,
        min_dimension=3.00,
        max_area_ratio=0.28,
        min_ceiling=2.70,
    ),

    # ── BATHROOMS (الحمامات / دورات المياه) ─────────────────────────────────
    # EBC: الحمام لا يقل عن 2.5 م² بأقل بُعد 1.20 م
    "bathroom": RoomStandard(
        min_area=2.5,
        recommended_area=4.5,
        min_dimension=1.20,
        max_area_ratio=0.08,
        min_ceiling=2.40,   # EBC: يُسمح بسقف أدنى للخدمات
    ),

    # Full bathroom with tub (حمام كامل)
    "bathroom_full": RoomStandard(
        min_area=4.0,
        recommended_area=6.0,
        min_dimension=1.60,
        max_area_ratio=0.10,
        min_ceiling=2.40,
    ),

    # ── KITCHEN (المطبخ) ─────────────────────────────────────────────────────
    # EBC: المطبخ لا يقل عن 4 م² بأقل بُعد 1.50 م
    "kitchen": RoomStandard(
        min_area=4.0,
        recommended_area=9.0,
        min_dimension=1.80,
        max_area_ratio=0.14,
        min_ceiling=2.70,
    ),

    # ── LIVING ROOM (غرفة المعيشة / الصالة) ─────────────────────────────────
    # EBC: غرفة المعيشة لا تقل عن 12 م² بأقل بُعد 3.0 م
    "living": RoomStandard(
        min_area=12.0,
        recommended_area=22.0,
        min_dimension=3.00,
        max_area_ratio=0.30,
        min_ceiling=2.70,
    ),

    # ── DINING ROOM (غرفة السفرة) ────────────────────────────────────────────
    "dining": RoomStandard(
        min_area=8.0,
        recommended_area=12.0,
        min_dimension=2.50,
        max_area_ratio=0.12,
        min_ceiling=2.70,
    ),

    # ── CORRIDOR / HALLWAY (الممر / الردهة) ──────────────────────────────────
    # EBC: عرض الممرات لا يقل عن 1.20 م (Law 119/2008 Article 74)
    "corridor": RoomStandard(
        min_area=3.6,           # 1.2m × 3.0m minimum
        recommended_area=6.0,
        min_dimension=1.20,     # EBC HARD MINIMUM — strict, never smaller
        max_area_ratio=0.08,
        min_ceiling=2.40,
    ),

    # ── ENTRANCE HALL (بهو المدخل / الريسبشن) ────────────────────────────────
    "entrance": RoomStandard(
        min_area=3.0,
        recommended_area=5.0,
        min_dimension=1.50,
        max_area_ratio=0.07,
        min_ceiling=2.70,
    ),

    # ── MAID'S ROOM (غرفة الخادمة) ──────────────────────────────────────────
    "service_room": RoomStandard(
        min_area=6.0,
        recommended_area=8.0,
        min_dimension=2.25,
        max_area_ratio=0.10,
        min_ceiling=2.40,
    ),

    # ── STORAGE (مخزن / مخدع) ───────────────────────────────────────────────
    "storage": RoomStandard(
        min_area=1.5,
        recommended_area=3.0,
        min_dimension=0.90,
        max_area_ratio=0.05,
        min_ceiling=2.20,
    ),

    # ── BALCONY (شرفة) ──────────────────────────────────────────────────────
    # EBC: الشرفة لا تقل عن 1.20 م عمقاً
    "balcony": RoomStandard(
        min_area=3.0,
        recommended_area=6.0,
        min_dimension=1.20,     # depth minimum
        max_area_ratio=0.08,
        min_ceiling=2.40,
    ),

    # ── LAUNDRY (غرفة الغسيل) ───────────────────────────────────────────────
    "laundry": RoomStandard(
        min_area=2.0,
        recommended_area=4.0,
        min_dimension=1.20,
        max_area_ratio=0.05,
        min_ceiling=2.40,
    ),

    # ── OFFICE / STUDY (مكتب / غرفة الدراسة) ────────────────────────────────
    "office": RoomStandard(
        min_area=8.0,
        recommended_area=12.0,
        min_dimension=2.50,
        max_area_ratio=0.15,
        min_ceiling=2.70,
    ),
}


# ══════════════════════════════════════════════════════════════════════════════
# APARTMENT TYPE STANDARDS (فئات الشقق)
# Based on Egyptian Social Housing and Ministry of Housing classifications
# ══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class ApartmentStandard:
    """Reference standard for a complete apartment type."""
    label_ar: str
    label_en: str
    min_total_area: float      # m²
    recommended_area: float    # m²
    min_bedrooms: int
    typical_bedrooms: int
    requires_corridor: bool
    min_bathrooms: int
    # Typical room program
    room_program: list[str] = field(default_factory=list)


EBC_APARTMENT_STANDARDS: Final[dict[str, ApartmentStandard]] = {
    "studio": ApartmentStandard(
        label_ar="استوديو",
        label_en="Studio",
        min_total_area=25.0,
        recommended_area=40.0,
        min_bedrooms=0,
        typical_bedrooms=0,
        requires_corridor=False,
        min_bathrooms=1,
        room_program=["living", "bathroom", "kitchen"],
    ),
    "1br": ApartmentStandard(
        label_ar="شقة غرفة نوم واحدة",
        label_en="1-Bedroom Apartment",
        min_total_area=45.0,
        recommended_area=65.0,
        min_bedrooms=1,
        typical_bedrooms=1,
        requires_corridor=False,
        min_bathrooms=1,
        room_program=["bedroom", "living", "bathroom", "kitchen"],
    ),
    "2br": ApartmentStandard(
        label_ar="شقة غرفتي نوم",
        label_en="2-Bedroom Apartment",
        min_total_area=75.0,
        recommended_area=100.0,
        min_bedrooms=2,
        typical_bedrooms=2,
        requires_corridor=True,
        min_bathrooms=1,
        room_program=["bedroom", "bedroom", "living", "bathroom", "kitchen", "corridor"],
    ),
    "3br": ApartmentStandard(
        label_ar="شقة ثلاث غرف نوم",
        label_en="3-Bedroom Apartment",
        min_total_area=100.0,
        recommended_area=140.0,
        min_bedrooms=3,
        typical_bedrooms=3,
        requires_corridor=True,
        min_bathrooms=2,
        room_program=["bedroom", "bedroom", "bedroom", "living", "bathroom",
                      "bathroom", "kitchen", "corridor"],
    ),
    "4br": ApartmentStandard(
        label_ar="شقة أربع غرف نوم",
        label_en="4-Bedroom Apartment",
        min_total_area=140.0,
        recommended_area=200.0,
        min_bedrooms=4,
        typical_bedrooms=4,
        requires_corridor=True,
        min_bathrooms=2,
        room_program=["bedroom", "bedroom", "bedroom", "bedroom", "living",
                      "bathroom", "bathroom", "kitchen", "corridor", "entrance"],
    ),
    "villa": ApartmentStandard(
        label_ar="فيلا",
        label_en="Villa",
        min_total_area=200.0,
        recommended_area=350.0,
        min_bedrooms=3,
        typical_bedrooms=4,
        requires_corridor=True,
        min_bathrooms=3,
        room_program=["bedroom", "bedroom", "bedroom", "bedroom", "living",
                      "dining", "bathroom", "bathroom", "bathroom",
                      "kitchen", "corridor", "entrance", "service_room"],
    ),
}


# ══════════════════════════════════════════════════════════════════════════════
# DOOR & WINDOW STANDARDS (الأبواب والنوافذ)
# EBC Chapter 9
# ══════════════════════════════════════════════════════════════════════════════

# Door widths (clear opening) — EBC minimums
# EBC-FIX: These ensure doors can be placed while respecting room-type constraints
EBC_DOOR_WIDTHS: Final[dict[str, float]] = {
    "main_entry":   1.00,   # m — الباب الرئيسي لا يقل عن 1.0 م
    "bedroom":      0.90,   # m — غرفة النوم
    "bathroom":     0.70,   # m — الحمام (compact) or 0.80m if accessible
    "kitchen":      0.80,   # m — المطبخ
    "service":      0.80,   # m — باب الخدمة
    "corridor":     0.90,   # m — الممر
    "balcony":      0.90,   # m — الشرفة
    "default":      0.90,   # m — الافتراضي
}

# Window requirements — EBC: window area ≥ 10% of room floor area
EBC_WINDOW_MIN_RATIO: Final[float] = 0.10   # 10% of floor area

# Wall thickness — standard Egyptian construction
EBC_WALL_THICKNESS: Final[float] = 0.20     # m (20 cm — طوب أحمر مزدوج)
EBC_PARTITION_THICKNESS: Final[float] = 0.12  # m (12 cm — حوائط تقسيم)


# ══════════════════════════════════════════════════════════════════════════════
# ADJACENCY RULES (قواعد التجاور المعمارية)
# ══════════════════════════════════════════════════════════════════════════════

# Rooms that must NEVER be directly adjacent (no shared door)
# EBC-FIX: These are FORBIDDEN_ADJACENCIES — hard violations per validator
FORBIDDEN_ADJACENCIES: Final[dict[tuple[str, str], str]] = {
    ("bathroom", "kitchen"):  "hard",   # EBC prohibition — reject layout
    ("bedroom", "kitchen"):   "soft",   # Prefer separation, don't reject
    ("bathroom", "dining"):   "hard",   # Health/sanitation rule
}

# Rooms that are PREFERRED adjacent (soft constraints, validator scores)
REQUIRED_ADJACENCIES: Final[list[tuple[str, str, str]]] = [
    ("bedroom", "bathroom", "soft"),    # Nice to have — penalize if separated
    ("kitchen", "dining", "soft"),      # Prefer adjacency for convenience
    ("corridor", "bedroom", "soft"),    # Natural flow through bedrooms
    ("entrance", "living", "soft"),     # Entry to main space
]


# ══════════════════════════════════════════════════════════════════════════════
# LAYOUT PROPORTION TARGETS
# ══════════════════════════════════════════════════════════════════════════════

# Target area ratios for a balanced layout (soft guidelines, not hard constraints)
AREA_RATIO_TARGETS: Final[dict[str, tuple[float, float]]] = {
    # room_type: (min_ratio, max_ratio) of total apartment area
    "bedroom":   (0.14, 0.25),
    "bathroom":  (0.05, 0.10),
    "kitchen":   (0.08, 0.14),
    "living":    (0.18, 0.30),
    "corridor":  (0.04, 0.09),
    "dining":    (0.07, 0.13),
    "entrance":  (0.03, 0.07),
    "balcony":   (0.03, 0.08),
    "storage":   (0.02, 0.05),
}

# Maximum any single room can be (regardless of type)
ABSOLUTE_MAX_SINGLE_ROOM_RATIO: Final[float] = 0.35


# ══════════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def get_room_standard(room_type: str) -> RoomStandard:
    """
    Get EBC standard for a room type, with fallback to bedroom standard.

    Normalizes various room type spellings/synonyms to canonical EBC standards.
    """
    # Normalize room type
    rt = room_type.strip().lower()
    if rt in EBC_ROOM_STANDARDS:
        return EBC_ROOM_STANDARDS[rt]

    # Fallbacks by keyword matching
    if "bath" in rt or "toilet" in rt or "wc" in rt or "loo" in rt:
        return EBC_ROOM_STANDARDS["bathroom"]
    if "bed" in rt or "room" in rt or "chamber" in rt:
        return EBC_ROOM_STANDARDS["bedroom"]
    if "corridor" in rt or "hall" in rt or "passage" in rt or "hallway" in rt:
        return EBC_ROOM_STANDARDS["corridor"]
    if "kitchen" in rt or "cook" in rt or "kitchenette" in rt:
        return EBC_ROOM_STANDARDS["kitchen"]
    if "living" in rt or "salon" in rt or "lounge" in rt or "sitting" in rt:
        return EBC_ROOM_STANDARDS["living"]
    if "dining" in rt or "dine" in rt:
        return EBC_ROOM_STANDARDS["dining"]
    if "entrance" in rt or "reception" in rt or "foyer" in rt or "entry" in rt:
        return EBC_ROOM_STANDARDS["entrance"]
    if "storage" in rt or "store" in rt or "closet" in rt or "cupboard" in rt:
        return EBC_ROOM_STANDARDS["storage"]
    if "balcony" in rt or "terrace" in rt or "deck" in rt or "porch" in rt:
        return EBC_ROOM_STANDARDS["balcony"]
    if "office" in rt or "study" in rt or "desk" in rt:
        return EBC_ROOM_STANDARDS["office"]
    if "laundry" in rt or "wash" in rt:
        return EBC_ROOM_STANDARDS["laundry"]

    # Default fallback
    return EBC_ROOM_STANDARDS["bedroom"]


def validate_room_dimensions(
    room_type: str, width: float, height: float
) -> list[str]:
    """
    Validate room dimensions against EBC standards.

    Returns list of violation messages (empty = compliant).
    Violations indicate which EBC constraint was violated and by how much.
    """
    std = get_room_standard(room_type)
    area = width * height
    min_dim = min(width, height)
    violations = []

    if area < std.min_area - 0.01:  # Small tolerance for rounding
        violations.append(
            f"{room_type}: area {area:.1f}m² < EBC minimum {std.min_area}m²"
        )
    if min_dim < std.min_dimension - 0.01:
        violations.append(
            f"{room_type}: smallest side {min_dim:.2f}m < EBC minimum {std.min_dimension}m"
        )
    return violations


def get_door_width(room_type: str) -> float:
    """
    Get EBC-compliant door width for a room type.

    Returns width in meters. Used by opening planner for bilateral door logic:
    actual_door_width = min(get_door_width(room_a), get_door_width(room_b))
    """
    rt = room_type.strip().lower()

    if "bath" in rt or "toilet" in rt or "wc" in rt or "loo" in rt:
        return EBC_DOOR_WIDTHS["bathroom"]
    if "kitchen" in rt or "cook" in rt:
        return EBC_DOOR_WIDTHS["kitchen"]
    if "bed" in rt or "master" in rt:
        return EBC_DOOR_WIDTHS["bedroom"]
    if "corridor" in rt or "hall" in rt or "passage" in rt:
        return EBC_DOOR_WIDTHS["corridor"]
    if "balcony" in rt or "terrace" in rt:
        return EBC_DOOR_WIDTHS["balcony"]
    if "service" in rt or "maid" in rt:
        return EBC_DOOR_WIDTHS["service"]
    if "entrance" in rt or "entry" in rt or "main" in rt:
        return EBC_DOOR_WIDTHS["main_entry"]

    return EBC_DOOR_WIDTHS["default"]
