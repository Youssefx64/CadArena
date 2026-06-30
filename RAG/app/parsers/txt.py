"""Text and Markdown parser for direct ingestion."""
from __future__ import annotations

import logging
from typing import Any
from app.parsers import ParserOutput, register_parser

logger = logging.getLogger(__name__)

@register_parser(extensions=[".txt", ".md"], mime_types=["text/plain", "text/markdown"])
def parse_txt(filename: str, content: bytes, content_type: str) -> ParserOutput:
    """Parse text and markdown documents, detecting structure and metadata."""
    # Attempt UTF-8 decode
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        # Fallback to Latin-1/CP1256 which is common for legacy encoding
        try:
            text = content.decode("cp1256")
        except UnicodeDecodeError:
            text = content.decode("utf-8", errors="replace")

    # Clean text
    text = text.strip()

    # Detect language
    language = "en"
    arabic_chars = sum(1 for c in text if "\u0600" <= c <= "\u06FF")
    if arabic_chars > len(text) * 0.1:
        language = "ar"

    # Heuristic domain check
    keywords = {"wall", "slab", "beam", "column", "foundation", "dxf", "ifc", "layout", "building code", "boq", "concrete"}
    has_keywords = any(kw in text.lower() for kw in keywords)

    metadata = {
        "file_type": "text",
        "page_count": 1,
        "has_drawings": False,
        "has_tables": "|" in text and "-" in text, # simple md table check
        "language": language,
        "detected_domain": "architecture-civil" if has_keywords else "general",
        "confidence": 1.0,
        "filename": filename,
    }

    return ParserOutput(content=text, metadata=metadata)
