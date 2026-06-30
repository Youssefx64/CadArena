"""Document extraction and format-specific analyst agents for ArchChat."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional
from app.agents.base import Agent, AgentOutput
from app.parsers import parse_document

logger = logging.getLogger(__name__)

class OCRAgent(Agent):
    """Coordinates image OCR operations on drawings and scans."""

    def run(self, input_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> AgentOutput:
        filename = input_data.get("filename", "")
        content = input_data.get("content", b"")
        mime = input_data.get("mime", "")

        try:
            parsed = parse_document(filename, content, mime)
            return AgentOutput(
                output={"text": parsed.content, "metadata": parsed.metadata},
                confidence=parsed.metadata.get("confidence", 0.8),
                metadata={"ocr_method": "Pillow+Fallback"}
            )
        except Exception as e:
            logger.error(f"OCR agent failed on {filename}: {e}")
            return AgentOutput(output={"text": ""}, confidence=0.0, metadata={"error": str(e)})


class VisionAgent(Agent):
    """Analyzes drawing schemas, sheet bounds, and architectural symbols from images."""

    def run(self, input_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> AgentOutput:
        filename = input_data.get("filename", "")
        content = input_data.get("content", b"")
        mime = input_data.get("mime", "")

        try:
            parsed = parse_document(filename, content, mime)
            img_meta = parsed.metadata.get("image_metadata", {})
            return AgentOutput(
                output={
                    "drawing_class": img_meta.get("drawing_class", "unknown"),
                    "symbols": img_meta.get("symbols", []),
                    "dimensions": f"{img_meta.get('width')}x{img_meta.get('height')}"
                },
                confidence=0.85,
                metadata={"dimensions": img_meta}
            )
        except Exception as e:
            return AgentOutput(output={"drawing_class": "unknown", "symbols": []}, confidence=0.0, metadata={"error": str(e)})


class DocumentAnalyst(Agent):
    """Extracts specification values, material lists, and structural constraints from files."""

    def run(self, input_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> AgentOutput:
        filename = input_data.get("filename", "")
        content = input_data.get("content", b"")
        mime = input_data.get("mime", "")

        try:
            parsed = parse_document(filename, content, mime)
            text = parsed.content
            # Basic key extraction heuristics
            found_materials = []
            for mat in ["concrete", "steel", "brick", "masonry", "timber", "wood", "glass"]:
                if mat in text.lower():
                    found_materials.append(mat)

            return AgentOutput(
                output={"content_text": text, "materials_detected": found_materials},
                confidence=1.0,
                metadata={"char_count": len(text)}
            )
        except Exception as e:
            return AgentOutput(output={"content_text": ""}, confidence=0.0, metadata={"error": str(e)})


class TableExtractionAgent(Agent):
    """Extracts tabular schedules, load spreadsheets, and BOQ line items."""

    def run(self, input_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> AgentOutput:
        filename = input_data.get("filename", "")
        content = input_data.get("content", b"")
        mime = input_data.get("mime", "")

        try:
            parsed = parse_document(filename, content, mime)
            # Detect tables or sheet segments
            rows = []
            for line in parsed.content.split("\n"):
                if "|" in line:
                    parts = [p.strip() for p in line.split("|")]
                    rows.append(parts)

            return AgentOutput(
                output={"table_rows": rows, "is_boq": parsed.metadata.get("is_boq", False)},
                confidence=0.95,
                metadata={"row_count": len(rows)}
            )
        except Exception as e:
            return AgentOutput(output={"table_rows": []}, confidence=0.0, metadata={"error": str(e)})


class DXFAnalyst(Agent):
    """Performs layer audits and extracts wall/room metadata from DXF vector formats."""

    def run(self, input_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> AgentOutput:
        filename = input_data.get("filename", "")
        content = input_data.get("content", b"")
        mime = input_data.get("mime", "")

        try:
            parsed = parse_document(filename, content, mime)
            meta = parsed.metadata
            return AgentOutput(
                output={
                    "layers": meta.get("layers", []),
                    "blocks": meta.get("blocks", []),
                    "entities_count": meta.get("entities_count", {}),
                    "summary_text": parsed.content
                },
                confidence=1.0,
                metadata={"layers_found": len(meta.get("layers", []))}
            )
        except Exception as e:
            return AgentOutput(output={"layers": [], "blocks": []}, confidence=0.0, metadata={"error": str(e)})


class IFCAnalyst(Agent):
    """Audits spaces and structural relationships within openBIM IFC formats."""

    def run(self, input_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> AgentOutput:
        filename = input_data.get("filename", "")
        content = input_data.get("content", b"")
        mime = input_data.get("mime", "")

        try:
            parsed = parse_document(filename, content, mime)
            meta = parsed.metadata
            return AgentOutput(
                output={
                    "elements_count": meta.get("elements_count", {}),
                    "native_parsed": meta.get("native_parsed", False),
                    "details": parsed.content
                },
                confidence=meta.get("confidence", 0.8),
                metadata={"native_parsed": meta.get("native_parsed")}
            )
        except Exception as e:
            return AgentOutput(output={"elements_count": {}}, confidence=0.0, metadata={"error": str(e)})
