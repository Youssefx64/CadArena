"""
Tests for Egyptian Building Code compliance in layout generation.
All generated rooms must meet EBC 2023 minimum standards where feasible.
"""
import pytest
from app.services.design_parser.egyptian_building_code import (
    validate_room_dimensions,
    get_room_standard,
    get_door_width,
    EBC_ROOM_STANDARDS,
    EBC_DOOR_WIDTHS,
    EBC_APARTMENT_STANDARDS,
)
from app.services.design_parser.layout_planner import normalize_layout


class TestEBCRoomStandards:
    """Test EBC minimum dimension lookups."""

    def test_bedroom_ebc_minimum(self):
        std = get_room_standard("bedroom")
        assert std.min_area == 9.0, "Bedroom min area per EBC"
        assert std.min_dimension == 2.75, "Bedroom min side per EBC"

    def test_bathroom_ebc_minimum(self):
        std = get_room_standard("bathroom")
        assert std.min_area == 2.5, "Bathroom min area per EBC"
        assert std.min_dimension == 1.20, "Bathroom min side per EBC"

    def test_kitchen_ebc_minimum(self):
        std = get_room_standard("kitchen")
        assert std.min_area == 4.0, "Kitchen min area per EBC"
        assert std.min_dimension == 1.80, "Kitchen min side per EBC"

    def test_living_ebc_minimum(self):
        std = get_room_standard("living")
        assert std.min_area == 12.0, "Living room min area per EBC"
        assert std.min_dimension == 3.00, "Living room min side per EBC"

    def test_corridor_ebc_minimum(self):
        """Corridor width is an absolute EBC HARD LIMIT (Law 119/2008 Article 74)."""
        std = get_room_standard("corridor")
        assert std.min_dimension == 1.20, "Corridor 1.20m HARD LIMIT per EBC"

    def test_entrance_ebc_minimum(self):
        std = get_room_standard("entrance")
        assert std.min_area == 3.0, "Entrance min area per EBC"
        assert std.min_dimension == 1.50, "Entrance min side per EBC"

    def test_unknown_type_fallback(self):
        """Unknown room types should fallback to bedroom standard safely."""
        std = get_room_standard("unknown_room_xyz")
        assert std is not None
        assert std.min_area > 0


class TestEBCRoomTypeNormalization:
    """Test room type string normalization."""

    def test_bathroom_synonyms(self):
        """'loo', 'toilet', 'wc' should map to bathroom."""
        assert get_room_standard("loo").min_dimension == get_room_standard("bathroom").min_dimension
        assert get_room_standard("toilet").min_area == get_room_standard("bathroom").min_area
        assert get_room_standard("WC").min_area == get_room_standard("bathroom").min_area

    def test_bedroom_synonyms(self):
        """'bed', 'chamber' should map to bedroom."""
        assert get_room_standard("bed").min_area == get_room_standard("bedroom").min_area
        assert get_room_standard("chamber").min_dimension == get_room_standard("bedroom").min_dimension

    def test_corridor_synonyms(self):
        """'hall', 'passage', 'hallway' should map to corridor."""
        assert get_room_standard("hall").min_dimension == get_room_standard("corridor").min_dimension
        assert get_room_standard("passage").min_area == get_room_standard("corridor").min_area


class TestEBCDimensionValidation:
    """Test room dimension validation against EBC."""

    def test_valid_bedroom(self):
        """3.5×3.5m = 12.25m² should pass (≥ 9m², side ≥ 2.75m)."""
        violations = validate_room_dimensions("bedroom", 3.5, 3.5)
        assert violations == [], f"Expected no violations, got: {violations}"

    def test_undersized_bedroom_area(self):
        """2.0×3.0m = 6m² violates 9m² minimum."""
        violations = validate_room_dimensions("bedroom", 2.0, 3.0)
        assert len(violations) > 0, "Should have area violation"
        assert any("9.0" in v for v in violations), "Should cite EBC 9m² minimum"

    def test_narrow_bedroom_dimension(self):
        """2.0×5.0m has side 2.0m < 2.75m EBC minimum."""
        violations = validate_room_dimensions("bedroom", 2.0, 5.0)
        assert len(violations) > 0, "Should have dimension violation"
        assert any("2.75" in v for v in violations), "Should cite EBC 2.75m minimum"

    def test_valid_bathroom(self):
        """1.5×2.0m = 3.0m² should pass (≥ 2.5m², side ≥ 1.20m)."""
        violations = validate_room_dimensions("bathroom", 1.5, 2.0)
        assert violations == [], f"Expected no violations, got: {violations}"

    def test_too_narrow_bathroom(self):
        """1.0×2.0m has side 1.0m < 1.20m — violates EBC."""
        violations = validate_room_dimensions("bathroom", 1.0, 2.0)
        assert len(violations) > 0, "Should have dimension violation for 1.0m < 1.20m"

    def test_undersized_bathroom_area(self):
        """1.5×1.5m = 2.25m² < 2.5m² EBC minimum."""
        violations = validate_room_dimensions("bathroom", 1.5, 1.5)
        assert len(violations) > 0, "Should have area violation"

    def test_valid_corridor(self):
        """1.2×4.0m should pass (≥ 3.6m², side ≥ 1.20m)."""
        violations = validate_room_dimensions("corridor", 1.2, 4.0)
        assert violations == [], f"Expected no violations for valid corridor, got: {violations}"

    def test_narrow_corridor_violation(self):
        """1.0×4.0m violates 1.20m EBC hard limit."""
        violations = validate_room_dimensions("corridor", 1.0, 4.0)
        assert len(violations) > 0, "Should violate EBC 1.20m corridor minimum"
        assert any("1.2" in v for v in violations), f"Should cite EBC 1.2m hard minimum, got: {violations}"

    def test_valid_kitchen(self):
        """2.0×2.5m = 5.0m² should pass (≥ 4.0m², side ≥ 1.80m)."""
        violations = validate_room_dimensions("kitchen", 2.0, 2.5)
        assert violations == [], f"Expected no violations, got: {violations}"

    def test_undersized_kitchen(self):
        """1.5×2.0m = 3.0m² < 4.0m² EBC minimum."""
        violations = validate_room_dimensions("kitchen", 1.5, 2.0)
        assert len(violations) > 0, "Should violate kitchen min area"

    def test_valid_living_room(self):
        """4.0×4.0m = 16.0m² should pass (≥ 12.0m², side ≥ 3.0m)."""
        violations = validate_room_dimensions("living", 4.0, 4.0)
        assert violations == [], f"Expected no violations for valid living room, got: {violations}"

    def test_undersized_living_room(self):
        """3.0×3.0m = 9.0m² < 12.0m² EBC minimum."""
        violations = validate_room_dimensions("living", 3.0, 3.0)
        assert len(violations) > 0, "Should violate living room min area"


class TestEBCDoorWidths:
    """Test EBC door width standards."""

    def test_bathroom_door_ebc(self):
        assert get_door_width("bathroom") == 0.70, "Bathroom door 0.70m per EBC"

    def test_bedroom_door_ebc(self):
        assert get_door_width("bedroom") == 0.90, "Bedroom door 0.90m per EBC"

    def test_kitchen_door_ebc(self):
        assert get_door_width("kitchen") == 0.80, "Kitchen door 0.80m per EBC"

    def test_main_entry_door_ebc(self):
        assert get_door_width("main_entry") == 1.00, "Main entry 1.00m per EBC"
        assert get_door_width("entrance") == 1.00, "Entrance synonymous with main_entry"

    def test_corridor_door_ebc(self):
        assert get_door_width("corridor") == 0.90, "Corridor door 0.90m per EBC"

    def test_unknown_type_default_door(self):
        assert get_door_width("unknown") == EBC_DOOR_WIDTHS["default"], "Unknown types use default"


class TestEBCApartmentStandards:
    """Test apartment type area classifications."""

    def test_studio_range(self):
        studio = EBC_APARTMENT_STANDARDS["studio"]
        assert studio.min_total_area == 25.0
        assert studio.recommended_area == 40.0
        assert studio.min_bedrooms == 0

    def test_1br_range(self):
        br1 = EBC_APARTMENT_STANDARDS["1br"]
        assert br1.min_total_area == 45.0
        assert br1.recommended_area == 65.0
        assert br1.min_bedrooms == 1

    def test_2br_range(self):
        br2 = EBC_APARTMENT_STANDARDS["2br"]
        assert br2.min_total_area == 75.0
        assert br2.recommended_area == 100.0
        assert br2.min_bedrooms == 2
        assert br2.requires_corridor

    def test_3br_range(self):
        br3 = EBC_APARTMENT_STANDARDS["3br"]
        assert br3.min_total_area == 100.0
        assert br3.min_bedrooms == 3
        assert br3.min_bathrooms == 2

    def test_villa_range(self):
        villa = EBC_APARTMENT_STANDARDS["villa"]
        assert villa.min_total_area == 200.0
        assert villa.min_bedrooms == 3


class TestLayoutEBCCompliance:
    """Test that normalize_layout respects EBC where feasible."""

    def _make_layout(self, rooms, boundary_w=12.0, boundary_h=9.0):
        """Helper to create test layouts."""
        return {
            "boundary": {"width": boundary_w, "height": boundary_h},
            "rooms": rooms,
        }

    def test_normalize_layout_preserves_compliant_bedrooms(self):
        """Compliant bedrooms should not be scaled down."""
        layout = self._make_layout([
            {"name": "Bedroom", "room_type": "bedroom",
             "width": 4.0, "height": 4.0,  # 16m² — well above 9m²
             "origin": {"x": 0, "y": 0}},
        ])
        result = normalize_layout(layout)
        bedroom = result["rooms"][0]
        # Width should be preserved or increased, not decreased
        assert float(bedroom.get("width", 0)) >= 4.0 - 0.1

    def test_corridor_minimum_respected_when_feasible(self):
        """Corridor should respect 1.20m minimum when there's space."""
        layout = self._make_layout([
            {"name": "Corridor", "room_type": "corridor",
             "width": 1.5, "height": 6.0,
             "origin": {"x": 0, "y": 0}},
            {"name": "Room", "room_type": "bedroom",
             "width": 3.0, "height": 3.0,
             "origin": {"x": 1.5, "y": 0}},
        ])
        result = normalize_layout(layout)
        corridor = result["rooms"][0]
        # Corridor width should be at least 1.20m (or clamped by position)
        narrow_side = min(corridor["width"], corridor["height"])
        assert narrow_side >= 1.10, f"Corridor {narrow_side}m should respect 1.20m EBC minimum where feasible"

    def test_living_room_meets_ebc_minimum(self):
        """Living room should be >= 12m² EBC minimum."""
        layout = self._make_layout([
            {"name": "Living", "room_type": "living",
             "width": 4.0, "height": 3.5,  # 14m²
             "origin": {"x": 0, "y": 0}},
        ])
        result = normalize_layout(layout)
        living = result["rooms"][0]
        area = living["width"] * living["height"]
        assert area >= 12.0 - 0.1, f"Living room area {area:.1f}m² should be >= EBC 12m²"

    def test_bathroom_dimension_respected_when_feasible(self):
        """Bathroom should not have side < 1.20m if there's available space."""
        layout = self._make_layout([
            {"name": "Bathroom", "room_type": "bathroom",
             "width": 1.8, "height": 2.5,
             "origin": {"x": 0, "y": 0}},
        ])
        result = normalize_layout(layout)
        bathroom = result["rooms"][0]
        min_dim = min(bathroom["width"], bathroom["height"])
        assert min_dim >= 1.15, f"Bathroom min dimension {min_dim:.2f}m should respect EBC 1.20m"

    def test_kitchen_minimum_area_respected(self):
        """Kitchen should meet 4.0m² EBC minimum when feasible."""
        layout = self._make_layout([
            {"name": "Kitchen", "room_type": "kitchen",
             "width": 2.5, "height": 2.0,  # 5m²
             "origin": {"x": 0, "y": 0}},
        ])
        result = normalize_layout(layout)
        kitchen = result["rooms"][0]
        area = kitchen["width"] * kitchen["height"]
        assert area >= 4.0 - 0.1, f"Kitchen area {area:.1f}m² should be >= EBC 4m²"
