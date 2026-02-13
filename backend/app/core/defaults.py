"""
Default values for intent resolution and planning.
"""

# Boundary defaults (meters)
DEFAULT_BOUNDARY_WIDTH = 20.0
DEFAULT_BOUNDARY_HEIGHT = 20.0

# Room defaults (meters)
DEFAULT_ROOM_TYPE = "living"
DEFAULT_ROOM_SIZES: dict[str, tuple[float, float]] = {
    "living": (6.0, 5.0),
    "bedroom": (4.0, 4.0),
    "kitchen": (4.0, 3.5),
    "bathroom": (3.0, 2.5),
    "corridor": (2.0, 6.0),
    "stairs": (3.0, 3.0),
}

# Opening defaults (meters)
DEFAULT_OPENING_WIDTH = 1.0
DEFAULT_OPENING_WALL = "bottom"

# Planning defaults
DEFAULT_RULES_ENABLED = True
DEFAULT_ENABLE_ROOM_TYPE_HEURISTICS = True
DEFAULT_ENABLE_BOUNDARY_EXPANSION = True
DEFAULT_PRIORITIZE_ROOM_TYPES = True

DEFAULT_ROOM_TYPE_PRIORITY: dict[str, int] = {
    "corridor": 0,
    "stairs": 1,
    "living": 2,
    "kitchen": 3,
    "bathroom": 4,
    "bedroom": 5,
}
