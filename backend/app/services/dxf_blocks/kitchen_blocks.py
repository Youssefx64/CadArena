from __future__ import annotations

from typing import Any


_LAYER_NAME = "FURNITURE_KITCHEN"
_LAYER_COLOR = 1


# Ensure the kitchen furniture layer exists before creating kitchen block geometry.
def _ensure_layer(doc: Any) -> None:
    if _LAYER_NAME not in doc.layers:
        doc.layers.new(_LAYER_NAME, dxfattribs={"color": _LAYER_COLOR})


# Register all kitchen furniture and appliance block definitions.
def register_kitchen_blocks(doc: Any) -> None:
    _register_stove_4burner(doc)
    _register_kitchen_sink_double(doc)
    _register_refrigerator(doc)


# Register the 4-burner stove with control strip, burners, and knob circles.
def _register_stove_4burner(doc: Any) -> None:
    if "STOVE_4BURNER" in doc.blocks:
        return

    _ensure_layer(doc)
    blk = doc.blocks.new(name="STOVE_4BURNER")
    attrs = {"layer": _LAYER_NAME, "color": _LAYER_COLOR}

    blk.add_lwpolyline([(0.0, 0.0), (0.60, 0.0), (0.60, 0.60), (0.0, 0.60)], close=True, dxfattribs={**attrs, "const_width": 0.02})  # Draw stove body.
    blk.add_lwpolyline([(0.02, 0.54), (0.58, 0.54), (0.58, 0.58), (0.02, 0.58)], close=True, dxfattribs=attrs)  # Draw control strip.
    blk.add_circle(center=(0.17, 0.40), radius=0.10, dxfattribs=attrs)  # Draw back-left outer burner ring.
    blk.add_circle(center=(0.17, 0.40), radius=0.06, dxfattribs=attrs)  # Draw back-left middle burner ring.
    blk.add_circle(center=(0.17, 0.40), radius=0.03, dxfattribs=attrs)  # Draw back-left inner burner ring.
    blk.add_circle(center=(0.43, 0.40), radius=0.10, dxfattribs=attrs)  # Draw back-right outer burner ring.
    blk.add_circle(center=(0.43, 0.40), radius=0.06, dxfattribs=attrs)  # Draw back-right middle burner ring.
    blk.add_circle(center=(0.43, 0.40), radius=0.03, dxfattribs=attrs)  # Draw back-right inner burner ring.
    blk.add_circle(center=(0.17, 0.18), radius=0.10, dxfattribs=attrs)  # Draw front-left outer burner ring.
    blk.add_circle(center=(0.17, 0.18), radius=0.06, dxfattribs=attrs)  # Draw front-left middle burner ring.
    blk.add_circle(center=(0.17, 0.18), radius=0.03, dxfattribs=attrs)  # Draw front-left inner burner ring.
    blk.add_circle(center=(0.43, 0.18), radius=0.10, dxfattribs=attrs)  # Draw front-right outer burner ring.
    blk.add_circle(center=(0.43, 0.18), radius=0.06, dxfattribs=attrs)  # Draw front-right middle burner ring.
    blk.add_circle(center=(0.43, 0.18), radius=0.03, dxfattribs=attrs)  # Draw front-right inner burner ring.
    for knob_index in range(5):
        knob_x = 0.07 + (knob_index * 0.12)
        blk.add_circle(center=(knob_x, 0.56), radius=0.025, dxfattribs=attrs)  # Draw control knob marker.


# Register the 0.80x0.52 double sink with two basins and tap details.
def _register_kitchen_sink_double(doc: Any) -> None:
    if "KITCHEN_SINK_DOUBLE" in doc.blocks:
        return

    _ensure_layer(doc)
    blk = doc.blocks.new(name="KITCHEN_SINK_DOUBLE")
    attrs = {"layer": _LAYER_NAME, "color": _LAYER_COLOR}

    blk.add_lwpolyline([(0.0, 0.0), (0.80, 0.0), (0.80, 0.52), (0.0, 0.52)], close=True, dxfattribs={**attrs, "const_width": 0.02})  # Draw sink surround.
    blk.add_lwpolyline([(0.04, 0.05), (0.36, 0.05), (0.36, 0.47), (0.04, 0.47)], close=True, dxfattribs=attrs)  # Draw left basin.
    blk.add_lwpolyline([(0.44, 0.05), (0.76, 0.05), (0.76, 0.47), (0.44, 0.47)], close=True, dxfattribs=attrs)  # Draw right basin.
    blk.add_circle(center=(0.20, 0.26), radius=0.04, dxfattribs=attrs)  # Draw left drain.
    blk.add_circle(center=(0.60, 0.26), radius=0.04, dxfattribs=attrs)  # Draw right drain.
    blk.add_line((0.36, 0.48), (0.44, 0.48), dxfattribs=attrs)  # Draw tap body line.
    blk.add_circle(center=(0.40, 0.49), radius=0.03, dxfattribs=attrs)  # Draw tap head circle.


# Register the refrigerator with compartment outlines, handles, and hinge dots.
def _register_refrigerator(doc: Any) -> None:
    if "REFRIGERATOR" in doc.blocks:
        return

    _ensure_layer(doc)
    blk = doc.blocks.new(name="REFRIGERATOR")
    attrs = {"layer": _LAYER_NAME, "color": _LAYER_COLOR}

    blk.add_lwpolyline([(0.0, 0.0), (0.70, 0.0), (0.70, 0.75), (0.0, 0.75)], close=True, dxfattribs={**attrs, "const_width": 0.02})  # Draw fridge body.
    blk.add_line((0.0, 0.28), (0.70, 0.28), dxfattribs=attrs)  # Draw freezer/fridge split.
    blk.add_lwpolyline([(0.04, 0.30), (0.66, 0.30), (0.66, 0.73), (0.04, 0.73)], close=True, dxfattribs=attrs)  # Draw freezer section area.
    blk.add_lwpolyline([(0.04, 0.02), (0.66, 0.02), (0.66, 0.26), (0.04, 0.26)], close=True, dxfattribs=attrs)  # Draw fridge section area.
    blk.add_line((0.28, 0.70), (0.42, 0.70), dxfattribs=attrs)  # Draw freezer handle.
    blk.add_line((0.28, 0.24), (0.42, 0.24), dxfattribs=attrs)  # Draw fridge handle.
    blk.add_circle(center=(0.04, 0.72), radius=0.02, dxfattribs=attrs)  # Draw upper hinge dot.
    blk.add_circle(center=(0.04, 0.02), radius=0.02, dxfattribs=attrs)  # Draw lower hinge dot.
