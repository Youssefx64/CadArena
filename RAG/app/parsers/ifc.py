"""IFC parser using ifcopenshell with a text-based STEP fallback."""
from __future__ import annotations

import logging
import re
from typing import Any
from app.parsers import ParserOutput, register_parser

logger = logging.getLogger(__name__)

@register_parser(extensions=[".ifc"], mime_types=["application/x-step", "text/plain"])
def parse_ifc(filename: str, content: bytes, content_type: str) -> ParserOutput:
    """Parse IFC BIM files, extracting spaces, structural components, properties, and relationships."""
    has_ifcopenshell = False
    elements_summary = {}
    relationships = []
    text_content = ""
    
    try:
        import ifcopenshell
        has_ifcopenshell = True
    except ModuleNotFoundError:
        logger.warning("ifcopenshell is not installed. Using STEP plain-text parser fallback.")

    if has_ifcopenshell:
        try:
            # We must write to a temp file or use a temporary mechanism because ifcopenshell.open
            # sometimes doesn't take raw byte stream in older versions. Let's do it safely:
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(suffix=".ifc", delete=False) as tmp:
                tmp.write(content)
                tmp_path = tmp.name

            try:
                model = ifcopenshell.open(tmp_path)
                
                # Count core BIM elements
                spaces = model.by_type("IfcSpace")
                walls = model.by_type("IfcWall") + model.by_type("IfcWallStandardCase")
                slabs = model.by_type("IfcSlab")
                columns = model.by_type("IfcColumn")
                doors = model.by_type("IfcDoor")
                windows = model.by_type("IfcWindow")
                beams = model.by_type("IfcBeam")
                
                elements_summary = {
                    "spaces": len(spaces),
                    "walls": len(walls),
                    "slabs": len(slabs),
                    "columns": len(columns),
                    "doors": len(doors),
                    "windows": len(windows),
                    "beams": len(beams)
                }

                # Try to extract relations (e.g., spatial structure)
                rel_aggregates = model.by_type("IfcRelAggregates")
                for rel in rel_aggregates[:10]: # limit to avoid bloat
                    source = rel.RelatingObject.Name if rel.RelatingObject else None
                    targets = [obj.Name for obj in rel.RelatedObjects if obj.Name]
                    if source and targets:
                        relationships.append(f"{source} contains: {', '.join(targets)}")

                # Build readable content
                parts = [
                    f"IFC Building Model: {filename}",
                    f"Native IFC parser (ifcopenshell) activated.",
                    f"Spaces Count: {len(spaces)}",
                    f"Structural Elements Count:",
                    f"  - Walls: {len(walls)}",
                    f"  - Slabs: {len(slabs)}",
                    f"  - Columns: {len(columns)}",
                    f"  - Beams: {len(beams)}",
                    f"  - Doors: {len(doors)}",
                    f"  - Windows: {len(windows)}"
                ]
                if relationships:
                    parts.append("\nSpatial Relationships (Aggregates):\n" + "\n".join(relationships))
                text_content = "\n".join(parts)
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
        except Exception as e:
            logger.error(f"Native IFC parsing failed: {e}. Falling back to text parser.")
            has_ifcopenshell = False

    if not has_ifcopenshell:
        # STEP text-based parsing fallback
        try:
            raw_text = content.decode("utf-8", errors="replace")
        except Exception:
            raw_text = ""

        # Use regex to find element counts
        entity_patterns = {
            "spaces": r"\bIFCSPACE\b",
            "walls": r"\bIFCWALL(STANDARDCASE)?\b",
            "slabs": r"\bIFCSLAB\b",
            "columns": r"\bIFCCOLUMN\b",
            "doors": r"\bIFCDOOR\b",
            "windows": r"\bIFCWINDOW\b",
            "beams": r"\bIFCBEAM\b",
            "projects": r"\bIFCPROJECT\b"
        }

        elements_summary = {}
        for key, pattern in entity_patterns.items():
            matches = re.findall(pattern, raw_text, re.IGNORECASE)
            elements_summary[key] = len(matches)

        parts = [
            f"IFC Building Model: {filename}",
            f"BIM text parser fallback activated.",
            f"Detected Element Counts (Keyword matching):",
            f"  - Spaces: {elements_summary.get('spaces', 0)}",
            f"  - Walls: {elements_summary.get('walls', 0)}",
            f"  - Slabs: {elements_summary.get('slabs', 0)}",
            f"  - Columns: {elements_summary.get('columns', 0)}",
            f"  - Beams: {elements_summary.get('beams', 0)}",
            f"  - Doors: {elements_summary.get('doors', 0)}",
            f"  - Windows: {elements_summary.get('windows', 0)}"
        ]
        text_content = "\n".join(parts)

    metadata = {
        "file_type": "ifc",
        "page_count": 1,
        "has_drawings": True,
        "has_tables": True,
        "language": "en",
        "detected_domain": "architecture-civil",
        "confidence": 1.0 if has_ifcopenshell else 0.7,
        "filename": filename,
        "elements_count": elements_summary,
        "native_parsed": has_ifcopenshell
    }

    return ParserOutput(content=text_content, metadata=metadata)
