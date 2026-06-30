"""DXF parser using ezdxf to read geometric entities, layers, blocks, rooms, walls, doors, windows, and text annotations."""
from __future__ import annotations

import io
import logging
from typing import Any
from app.parsers import ParserOutput, register_parser

logger = logging.getLogger(__name__)

@register_parser(extensions=[".dxf"], mime_types=["image/vnd.dxf", "application/dxf", "model/vnd.dxf"])
def parse_dxf(filename: str, content: bytes, content_type: str) -> ParserOutput:
    """Parse AutoCAD DXF files, extracting structural layers, text descriptions, blocks, coordinates, dimensions, doors, and walls."""
    try:
        import ezdxf
    except ModuleNotFoundError as e:
        logger.error("ezdxf is not installed in the RAG environment.")
        raise RuntimeError("ezdxf is required to parse DXF files.") from e

    try:
        raw_text = content.decode("utf-8", errors="ignore")
        doc = ezdxf.read(io.StringIO(raw_text))
    except Exception as e:
        logger.error(f"Failed to load DXF file: {e}")
        raise ValueError(f"Unable to read DXF file: {e}") from e

    msp = doc.modelspace()
    
    # Layer and block audits
    layers = [layer.dxf.name for layer in doc.layers]
    blocks = [block.name for block in doc.blocks if not block.name.startswith("*")]

    # Query entities
    lines = msp.query("LINE")
    polylines = msp.query("LWPOLYLINE POLYLINE")
    texts = msp.query("TEXT MTEXT")
    dimensions = msp.query("DIMENSION")
    inserts = msp.query("INSERT")
    hatches = msp.query("HATCH")

    # Group texts by layer for contextual room or parameter matching
    text_data = []
    for t in texts:
        t_type = t.dxftype()
        val = t.dxf.text if t_type == "TEXT" else t.text
        val = (val or "").strip()
        if val:
            text_data.append(f"[{t.dxf.layer}] {val} at ({t.dxf.insert[0]:.2f}, {t.dxf.insert[1]:.2f})")

    # Heuristically classify doors/windows and rooms
    detected_rooms = []
    detected_walls_count = 0
    detected_doors_count = 0
    detected_windows_count = 0

    for l in layers:
        layer_lower = l.lower()
        if "room" in layer_lower or "space" in layer_lower:
            detected_rooms.append(l)
        if "wall" in layer_lower:
            detected_walls_count += 1
        if "door" in layer_lower:
            detected_doors_count += 1
        if "win" in layer_lower:
            detected_windows_count += 1

    # Extract dimension values
    dim_values = []
    for d in dimensions:
        try:
            # Try to read raw value or measurement
            measurement = d.dxf.actual_measurement
            if measurement is not None and measurement > 0:
                dim_values.append(f"Dimension: {measurement:.2f} on Layer '{d.dxf.layer}'")
        except AttributeError:
            pass

    # Build detailed text representation
    output_parts = [
        f"DXF Drawing File: {filename}",
        f"Layers Count: {len(layers)} ({', '.join(layers[:15])}{'...' if len(layers) > 15 else ''})",
        f"User Blocks Count: {len(blocks)} ({', '.join(blocks[:15])}{'...' if len(blocks) > 15 else ''})",
        f"Geometrical Counts:",
        f"  - LINES: {len(lines)}",
        f"  - POLYLINES: {len(polylines)}",
        f"  - TEXTS/MTEXTS: {len(texts)}",
        f"  - DIMENSIONS: {len(dimensions)}",
        f"  - BLOCK INSERTIONS: {len(inserts)}",
        f"  - HATCH PATTERNS: {len(hatches)}"
    ]

    if text_data:
        output_parts.append("\nText Annotations found in Drawing:\n" + "\n".join(text_data[:50]))
    if dim_values:
        output_parts.append("\nDimension Measurements:\n" + "\n".join(dim_values[:20]))

    full_content = "\n".join(output_parts)

    metadata = {
        "file_type": "dxf",
        "page_count": 1,
        "has_drawings": True,
        "has_tables": False,
        "language": "en",
        "detected_domain": "architecture-civil",
        "confidence": 1.0,
        "filename": filename,
        "layers": layers,
        "blocks": blocks,
        "entities_count": {
            "lines": len(lines),
            "polylines": len(polylines),
            "texts": len(texts),
            "dimensions": len(dimensions),
            "inserts": len(inserts)
        }
    }

    return ParserOutput(content=full_content, metadata=metadata)
