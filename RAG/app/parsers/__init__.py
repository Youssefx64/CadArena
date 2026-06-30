"""Document parsers registry for ArchChat.

All parsers return a ParserOutput containing content text and a metadata dict.
"""
from __future__ import annotations

import logging
from typing import Any, Callable, Dict
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class ParserOutput(BaseModel):
    """Normalized output from any document parser."""
    content: str
    metadata: Dict[str, Any]

# Type signature of a parser function
ParserFunc = Callable[[str, bytes, str], ParserOutput]

_PARSER_REGISTRY: Dict[str, ParserFunc] = {}

def register_parser(extensions: list[str], mime_types: list[str]) -> Callable[[ParserFunc], ParserFunc]:
    """Decorator to register a parser function for extensions and mime types."""
    def decorator(func: ParserFunc) -> ParserFunc:
        for ext in extensions:
            _PARSER_REGISTRY[ext.lower()] = func
        for mime in mime_types:
            _PARSER_REGISTRY[mime.lower()] = func
        return func
    return decorator

def parse_document(filename: str, content: bytes, content_type: str | None = None) -> ParserOutput:
    """Parse a document and return unified content and metadata."""
    import os
    from .txt import parse_txt
    from .pdf import parse_pdf
    from .csv import parse_csv
    from .xlsx import parse_xlsx
    from .dxf import parse_dxf
    from .ifc import parse_ifc
    from .image import parse_image

    _, ext = os.path.splitext(filename)
    ext = ext.lower().strip()
    mime = (content_type or "").split(";", 1)[0].strip().lower()

    # Route based on registry
    parser = _PARSER_REGISTRY.get(ext) or _PARSER_REGISTRY.get(mime)
    if parser is not None:
        try:
            return parser(filename, content, mime)
        except Exception as e:
            logger.error(f"Error parsing {filename} with registered parser: {e}", exc_info=True)
            raise ValueError(f"Failed to parse {filename}: {e}") from e

    # Fallbacks based on common file patterns
    if ext in {".txt", ".md", ".py", ".json", ".ini", ".yaml", ".yml"}:
        return parse_txt(filename, content, mime)
    elif ext == ".pdf":
        return parse_pdf(filename, content, mime)
    elif ext == ".csv":
        return parse_csv(filename, content, mime)
    elif ext in {".xlsx", ".xls"}:
        return parse_xlsx(filename, content, mime)
    elif ext == ".dxf":
        return parse_dxf(filename, content, mime)
    elif ext in {".ifc", ".ifcxml", ".ifczip"}:
        return parse_ifc(filename, content, mime)
    elif ext in {".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".gif"}:
        return parse_image(filename, content, mime)

    raise ValueError("Only PDF, TXT, Markdown, CSV, and JSON files are supported.")
