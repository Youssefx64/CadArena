from __future__ import annotations

from typing import Any


_LAYER_NAME = "FURNITURE_LIVING"
_LAYER_COLOR = 6


# Ensure the living furniture layer exists before creating living block geometry.
def _ensure_layer(doc: Any) -> None:
    if _LAYER_NAME not in doc.layers:
        doc.layers.new(_LAYER_NAME, dxfattribs={"color": _LAYER_COLOR})


# Register all living room furniture blocks used by DXF insertion.
def register_living_blocks(doc: Any) -> None:
    _register_sofa_3seat(doc)
    _register_coffee_table(doc)


# Register the 3-seat sofa with hatched back/arms and cushion detailing.
def _register_sofa_3seat(doc: Any) -> None:
    if "SOFA_3SEAT" in doc.blocks:
        return

    _ensure_layer(doc)
    blk = doc.blocks.new(name="SOFA_3SEAT")
    attrs = {"layer": _LAYER_NAME, "color": _LAYER_COLOR}

    blk.add_lwpolyline([(0.0, 0.0), (2.20, 0.0), (2.20, 0.24), (0.0, 0.24)], close=True, dxfattribs=attrs)  # Draw sofa back rest outline.
    back_hatch = blk.add_hatch(dxfattribs=attrs)  # Create solid hatch for the back rest mass.
    back_hatch.set_solid_fill(color=_LAYER_COLOR)  # Fill back rest with solid hatch.
    back_hatch.paths.add_polyline_path([(0.0, 0.0), (2.20, 0.0), (2.20, 0.24), (0.0, 0.24)], is_closed=True)  # Set back rest hatch boundary.
    blk.add_lwpolyline([(0.0, 0.24), (0.24, 0.24), (0.24, 0.92), (0.0, 0.92)], close=True, dxfattribs=attrs)  # Draw left armrest outline.
    left_arm_hatch = blk.add_hatch(dxfattribs=attrs)  # Create solid hatch for left armrest.
    left_arm_hatch.set_solid_fill(color=_LAYER_COLOR)  # Fill left armrest with solid hatch.
    left_arm_hatch.paths.add_polyline_path([(0.0, 0.24), (0.24, 0.24), (0.24, 0.92), (0.0, 0.92)], is_closed=True)  # Set left armrest hatch boundary.
    blk.add_lwpolyline([(1.96, 0.24), (2.20, 0.24), (2.20, 0.92), (1.96, 0.92)], close=True, dxfattribs=attrs)  # Draw right armrest outline.
    right_arm_hatch = blk.add_hatch(dxfattribs=attrs)  # Create solid hatch for right armrest.
    right_arm_hatch.set_solid_fill(color=_LAYER_COLOR)  # Fill right armrest with solid hatch.
    right_arm_hatch.paths.add_polyline_path([(1.96, 0.24), (2.20, 0.24), (2.20, 0.92), (1.96, 0.92)], is_closed=True)  # Set right armrest hatch boundary.
    blk.add_lwpolyline([(0.26, 0.26), (0.80, 0.26), (0.80, 0.90), (0.26, 0.90)], close=True, dxfattribs=attrs)  # Draw cushion 1.
    blk.add_lwpolyline([(0.83, 0.26), (1.37, 0.26), (1.37, 0.90), (0.83, 0.90)], close=True, dxfattribs=attrs)  # Draw cushion 2.
    blk.add_lwpolyline([(1.40, 0.26), (1.94, 0.26), (1.94, 0.90), (1.40, 0.90)], close=True, dxfattribs=attrs)  # Draw cushion 3.
    blk.add_line((0.26, 0.28), (1.94, 0.28), dxfattribs=attrs)  # Draw lower tuck line.
    blk.add_line((0.26, 0.88), (1.94, 0.88), dxfattribs=attrs)  # Draw upper tuck line.


# Register the coffee table with frame, inset glass, legs, and reflection lines.
def _register_coffee_table(doc: Any) -> None:
    if "COFFEE_TABLE" in doc.blocks:
        return

    _ensure_layer(doc)
    blk = doc.blocks.new(name="COFFEE_TABLE")
    attrs = {"layer": _LAYER_NAME, "color": _LAYER_COLOR}

    blk.add_lwpolyline([(0.0, 0.0), (1.20, 0.0), (1.20, 0.60), (0.0, 0.60)], close=True, dxfattribs={**attrs, "const_width": 0.015})  # Draw outer table frame.
    blk.add_lwpolyline([(0.06, 0.06), (1.14, 0.06), (1.14, 0.54), (0.06, 0.54)], close=True, dxfattribs=attrs)  # Draw glass inset.
    blk.add_circle(center=(0.06, 0.06), radius=0.04, dxfattribs=attrs)  # Draw leg marker at front-left.
    blk.add_circle(center=(1.14, 0.06), radius=0.04, dxfattribs=attrs)  # Draw leg marker at front-right.
    blk.add_circle(center=(0.06, 0.54), radius=0.04, dxfattribs=attrs)  # Draw leg marker at back-left.
    blk.add_circle(center=(1.14, 0.54), radius=0.04, dxfattribs=attrs)  # Draw leg marker at back-right.
    blk.add_line((0.08, 0.08), (0.18, 0.18), dxfattribs=attrs)  # Draw glass reflection line 1.
    blk.add_line((0.10, 0.08), (0.20, 0.18), dxfattribs=attrs)  # Draw glass reflection line 2.
