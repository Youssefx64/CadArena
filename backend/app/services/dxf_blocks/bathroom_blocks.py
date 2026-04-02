from __future__ import annotations

from typing import Any


_LAYER_NAME = "FURNITURE_SANITARY"
_LAYER_COLOR = 4


# Ensure the sanitary fixture layer exists before creating bathroom block geometry.
def _ensure_layer(doc: Any) -> None:
    if _LAYER_NAME not in doc.layers:
        doc.layers.new(_LAYER_NAME, dxfattribs={"color": _LAYER_COLOR})


# Register all sanitary fixture block definitions used by the renderer.
def register_bathroom_blocks(doc: Any) -> None:
    _register_toilet_wc(doc)
    _register_sink_wall(doc)
    _register_shower_tray(doc)


# Register the toilet block with cistern, bowl ellipses, hinges, and flush button.
def _register_toilet_wc(doc: Any) -> None:
    if "TOILET_WC" in doc.blocks:
        return

    _ensure_layer(doc)
    blk = doc.blocks.new(name="TOILET_WC")
    attrs = {"layer": _LAYER_NAME, "color": _LAYER_COLOR}

    blk.add_lwpolyline([(-0.19, 0.52), (0.19, 0.52), (0.19, 0.70), (-0.19, 0.70)], close=True, dxfattribs={**attrs, "const_width": 0.015})  # Draw cistern tank.
    blk.add_ellipse(center=(0.00, 0.26), major_axis=(0.0, 0.26), ratio=0.68, dxfattribs=attrs)  # Draw outer bowl ellipse.
    blk.add_ellipse(center=(0.00, 0.26), major_axis=(0.0, 0.22), ratio=0.68, dxfattribs=attrs)  # Draw seat ring ellipse.
    blk.add_circle(center=(-0.06, 0.50), radius=0.025, dxfattribs=attrs)  # Draw left hinge bump.
    blk.add_circle(center=(0.06, 0.50), radius=0.025, dxfattribs=attrs)  # Draw right hinge bump.
    blk.add_lwpolyline([(-0.04, 0.66), (0.04, 0.66), (0.04, 0.70), (-0.04, 0.70)], close=True, dxfattribs=attrs)  # Draw flush button.


# Register the wall sink block with surround, basin ellipse, drain, and tap set.
def _register_sink_wall(doc: Any) -> None:
    if "SINK_WALL" in doc.blocks:
        return

    _ensure_layer(doc)
    blk = doc.blocks.new(name="SINK_WALL")
    attrs = {"layer": _LAYER_NAME, "color": _LAYER_COLOR}

    blk.add_lwpolyline([(-0.30, 0.0), (0.30, 0.0), (0.30, 0.52), (-0.30, 0.52)], close=True, dxfattribs={**attrs, "const_width": 0.015})  # Draw sink surround.
    blk.add_ellipse(center=(0.00, 0.24), major_axis=(0.22, 0.0), ratio=0.78, dxfattribs=attrs)  # Draw rounded basin profile.
    blk.add_circle(center=(0.00, 0.22), radius=0.035, dxfattribs=attrs)  # Draw drain point.
    blk.add_circle(center=(-0.09, 0.46), radius=0.025, dxfattribs=attrs)  # Draw hot tap marker.
    blk.add_circle(center=(0.09, 0.46), radius=0.025, dxfattribs=attrs)  # Draw cold tap marker.
    blk.add_line((-0.09, 0.44), (0.09, 0.44), dxfattribs=attrs)  # Draw tap body line.


# Register the shower tray block with fixture rings, glass edge, and hatch pattern.
def _register_shower_tray(doc: Any) -> None:
    if "SHOWER_TRAY" in doc.blocks:
        return

    _ensure_layer(doc)
    blk = doc.blocks.new(name="SHOWER_TRAY")
    attrs = {"layer": _LAYER_NAME, "color": _LAYER_COLOR}
    tray_boundary = [(0.0, 0.0), (0.90, 0.0), (0.90, 0.90), (0.0, 0.90)]

    blk.add_lwpolyline(tray_boundary, close=True, dxfattribs={**attrs, "const_width": 0.02})  # Draw tray border.
    blk.add_circle(center=(0.45, 0.45), radius=0.14, dxfattribs=attrs)  # Draw shower head circle.
    blk.add_circle(center=(0.45, 0.45), radius=0.09, dxfattribs=attrs)  # Draw spray ring.
    blk.add_circle(center=(0.45, 0.45), radius=0.04, dxfattribs=attrs)  # Draw drain circle.
    blk.add_line((0.0, 0.0), (0.0, 0.90), dxfattribs=attrs)  # Draw glass door indicator line.
    blk.add_lwpolyline([(0.0, 0.0), (0.0, 0.90)], close=False, dxfattribs={**attrs, "const_width": 0.025})  # Draw thick glass edge indicator.
    tray_hatch = blk.add_hatch(dxfattribs=attrs)  # Create hatch for tray tiling pattern.
    tray_hatch.set_pattern_fill(name="LINE", scale=0.15, angle=45)  # Apply line hatch pattern settings.
    tray_hatch.paths.add_polyline_path(tray_boundary, is_closed=True)  # Attach hatch boundary to tray extents.
