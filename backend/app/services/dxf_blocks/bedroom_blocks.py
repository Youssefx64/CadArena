from __future__ import annotations

from typing import Any


_LAYER_NAME = "FURNITURE_BEDROOM"
_LAYER_COLOR = 5


# Ensure the bedroom furniture layer exists before creating any bedroom block geometry.
def _ensure_layer(doc: Any) -> None:
    if _LAYER_NAME not in doc.layers:
        doc.layers.new(_LAYER_NAME, dxfattribs={"color": _LAYER_COLOR})


# Register all bedroom-related reusable CAD blocks.
def register_bedroom_blocks(doc: Any) -> None:
    _register_bed_double(doc)
    _register_bed_single(doc)
    _register_wardrobe(doc)


# Register the 1.60x2.00 double-bed symbol with hatch and bedding detail.
def _register_bed_double(doc: Any) -> None:
    if "BED_DOUBLE" in doc.blocks:
        return

    _ensure_layer(doc)
    blk = doc.blocks.new(name="BED_DOUBLE")
    attrs = {"layer": _LAYER_NAME, "color": _LAYER_COLOR}

    blk.add_lwpolyline([(0.0, 0.0), (1.60, 0.0), (1.60, 2.00), (0.0, 2.00)], close=True, dxfattribs={**attrs, "const_width": 0.02})  # Draw mattress outline.
    blk.add_lwpolyline([(0.04, 1.74), (1.56, 1.74), (1.56, 1.98), (0.04, 1.98)], close=True, dxfattribs=attrs)  # Draw headboard boundary.
    headboard_hatch = blk.add_hatch(dxfattribs=attrs)  # Create solid hatch for the headboard fill.
    headboard_hatch.set_solid_fill(color=_LAYER_COLOR)  # Use solid pattern for professional CAD look.
    headboard_hatch.paths.add_polyline_path([(0.04, 1.74), (1.56, 1.74), (1.56, 1.98), (0.04, 1.98)], is_closed=True)  # Apply hatch boundary.
    blk.add_lwpolyline([(0.08, 1.42), (0.68, 1.42), (0.68, 1.70), (0.08, 1.70)], close=True, dxfattribs=attrs)  # Draw left pillow.
    blk.add_lwpolyline([(0.92, 1.42), (1.52, 1.42), (1.52, 1.70), (0.92, 1.70)], close=True, dxfattribs=attrs)  # Draw right pillow.
    blk.add_lwpolyline([(0.04, 1.28), (1.56, 1.28)], close=False, dxfattribs=attrs)  # Draw blanket fold line.
    blk.add_line((0.80, 0.04), (0.80, 1.26), dxfattribs=attrs)  # Draw mattress center seam.


# Register the 1.00x2.00 single-bed symbol with one centered pillow.
def _register_bed_single(doc: Any) -> None:
    if "BED_SINGLE" in doc.blocks:
        return

    _ensure_layer(doc)
    blk = doc.blocks.new(name="BED_SINGLE")
    attrs = {"layer": _LAYER_NAME, "color": _LAYER_COLOR}

    blk.add_lwpolyline([(0.0, 0.0), (1.00, 0.0), (1.00, 2.00), (0.0, 2.00)], close=True, dxfattribs={**attrs, "const_width": 0.02})  # Draw mattress outline.
    blk.add_lwpolyline([(0.04, 1.74), (0.96, 1.74), (0.96, 1.98), (0.04, 1.98)], close=True, dxfattribs=attrs)  # Draw headboard boundary.
    headboard_hatch = blk.add_hatch(dxfattribs=attrs)  # Create solid hatch for the headboard fill.
    headboard_hatch.set_solid_fill(color=_LAYER_COLOR)  # Use solid pattern for professional CAD look.
    headboard_hatch.paths.add_polyline_path([(0.04, 1.74), (0.96, 1.74), (0.96, 1.98), (0.04, 1.98)], is_closed=True)  # Apply hatch boundary.
    blk.add_lwpolyline([(0.12, 1.42), (0.88, 1.42), (0.88, 1.70), (0.12, 1.70)], close=True, dxfattribs=attrs)  # Draw centered pillow.
    blk.add_lwpolyline([(0.04, 1.28), (0.96, 1.28)], close=False, dxfattribs=attrs)  # Draw blanket fold line.


# Register a 1.80x0.60 wardrobe symbol with doors, handles, and swing arcs.
def _register_wardrobe(doc: Any) -> None:
    if "WARDROBE" in doc.blocks:
        return

    _ensure_layer(doc)
    blk = doc.blocks.new(name="WARDROBE")
    attrs = {"layer": _LAYER_NAME, "color": _LAYER_COLOR}

    blk.add_lwpolyline([(0.0, 0.0), (1.80, 0.0), (1.80, 0.60), (0.0, 0.60)], close=True, dxfattribs={**attrs, "const_width": 0.02})  # Draw wardrobe outer body.
    blk.add_line((0.90, 0.0), (0.90, 0.60), dxfattribs=attrs)  # Draw door split line.
    blk.add_circle((0.82, 0.30), radius=0.03, dxfattribs=attrs)  # Draw left handle.
    blk.add_circle((0.98, 0.30), radius=0.03, dxfattribs=attrs)  # Draw right handle.
    blk.add_arc(center=(0.0, 0.60), radius=0.90, start_angle=-90, end_angle=0, dxfattribs=attrs)  # Draw left door swing arc.
    blk.add_arc(center=(1.80, 0.60), radius=0.90, start_angle=180, end_angle=270, dxfattribs=attrs)  # Draw right door swing arc.
