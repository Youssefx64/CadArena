"""Rule-based design suggestions for generated floor plans.

Called after successful DXF generation to provide alternatives.
No LLM call — purely deterministic for speed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class DesignSuggestion:
    id: str
    title: str
    description: str
    prompt_modifier: str
    category: str


def generate_suggestions(
    parsed_layout: dict[str, Any],
    original_prompt: str,
) -> list[dict[str, str]]:
    """Generate up to 3 actionable design suggestions based on the current layout."""
    suggestions: list[DesignSuggestion] = []
    rooms = parsed_layout.get("room_program", parsed_layout.get("rooms", []))
    room_types = {r.get("room_type") for r in rooms}
    boundary = parsed_layout.get("boundary", {})
    total_area = boundary.get("width", 10) * boundary.get("height", 8)

    bedroom_count = sum(
        r.get("count", 1) for r in rooms if r.get("room_type") == "bedroom"
    )

    # Size suggestion
    if total_area < 100:
        suggestions.append(DesignSuggestion(
            id="size_upgrade",
            title="Spacious Version",
            description=f"Expand to a larger footprint (current: {total_area:.0f} m2) for more comfort and storage space.",
            prompt_modifier="Increase total floor area by 30%, keeping the same room program.",
            category="size",
        ))
    elif bedroom_count >= 3:
        suggestions.append(DesignSuggestion(
            id="size_compact",
            title="Compact Version",
            description="A more efficient layout with tighter room sizes — ideal for urban settings.",
            prompt_modifier="Make a compact version of the same plan, reducing total area by 20%.",
            category="size",
        ))
    else:
        suggestions.append(DesignSuggestion(
            id="size_optimize",
            title="Optimized Proportions",
            description="Rebalance room sizes for better flow — larger living area, more efficient bedrooms.",
            prompt_modifier="Optimize room proportions: larger living room (30%), smaller bedrooms (15% each).",
            category="size",
        ))

    # Amenity suggestion
    if bedroom_count >= 2 and "bathroom" in room_types:
        suggestions.append(DesignSuggestion(
            id="add_ensuite",
            title="Add En-Suite Bathroom",
            description="Attach a private bathroom to the master bedroom for luxury and privacy.",
            prompt_modifier="Add an en-suite bathroom attached to the master bedroom.",
            category="amenity",
        ))
    elif "stairs" not in room_types and total_area > 120:
        suggestions.append(DesignSuggestion(
            id="add_floor",
            title="Add Second Floor",
            description="Extend vertically with a second floor — double the usable area on the same footprint.",
            prompt_modifier="Design as a 2-floor house with stairs, distribute bedrooms on the upper floor.",
            category="amenity",
        ))
    else:
        suggestions.append(DesignSuggestion(
            id="add_balcony",
            title="Add Balcony",
            description="A private outdoor balcony connected to the living room — adds natural light and ventilation.",
            prompt_modifier="Add a balcony (minimum 6 m2) connected to the living room.",
            category="amenity",
        ))

    # Layout alternative
    suggestions.append(DesignSuggestion(
        id="open_plan",
        title="Open-Plan Layout",
        description="Remove the wall between kitchen and living room for a modern open-concept feel.",
        prompt_modifier="Use an open-plan layout where kitchen and living room share one open space.",
        category="layout",
    ))

    return [
        {
            "id": s.id,
            "title": s.title,
            "description": s.description,
            "apply_prompt": f"{original_prompt}. {s.prompt_modifier}",
            "category": s.category,
        }
        for s in suggestions[:3]
    ]
