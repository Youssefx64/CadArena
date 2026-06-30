"""PDF Parser using PyMuPDF (fitz) with Table/Drawing heuristics."""
from __future__ import annotations

import logging
from typing import Any
from app.parsers import ParserOutput, register_parser

logger = logging.getLogger(__name__)

@register_parser(extensions=[".pdf"], mime_types=["application/pdf"])
def parse_pdf(filename: str, content: bytes, content_type: str) -> ParserOutput:
    """Parse PDF documents, extracting text, pages, tables, and vector graphic indicators."""
    try:
        import fitz
    except ModuleNotFoundError as e:
        logger.error("PyMuPDF (fitz) is not installed in the RAG environment.")
        raise RuntimeError("PyMuPDF is required to ingest PDF files.") from e

    try:
        doc = fitz.open(stream=content, filetype="pdf")
    except Exception as e:
        logger.error(f"Failed to open PDF file: {e}")
        raise ValueError(f"Unable to read PDF file: {e}") from e

    pages_text = []
    has_tables = False
    has_drawings = False
    total_pages = len(doc)

    for page_idx, page in enumerate(doc):
        # Extract text
        text = page.get_text("text").strip()
        pages_text.append(text)

        # Detect drawings using vector elements
        try:
            drawings = page.get_drawings()
            if len(drawings) > 10:  # heuristic threshold for schematics or drawings
                has_drawings = True
        except Exception:
            pass

        # Detect tables using text formatting heuristics
        if not has_tables:
            # Check for grid-like patterns or markdown-like table symbols
            lines = text.split("\n")
            pipe_lines = [l for l in lines if "|" in l or "\t" in l]
            if len(pipe_lines) > 2:
                has_tables = True
            
            # Check if fitz find_tables is available
            try:
                if hasattr(page, "find_tables"):
                    tbls = page.find_tables()
                    if tbls and len(tbls.tables) > 0:
                        has_tables = True
            except Exception:
                pass

    full_text = "\n\n--- PAGE --- \n\n".join(pages_text).strip()

    # If the PDF is completely empty or image-only, set up a warning/tag
    confidence = 1.0
    if not full_text:
        full_text = "[Image-only PDF detected. Requires OCR.]"
        confidence = 0.5

    # Simple language check
    language = "en"
    arabic_chars = sum(1 for c in full_text if "\u0600" <= c <= "\u06FF")
    if arabic_chars > len(full_text) * 0.1:
        language = "ar"

    # Auto-correct AutoCAD visual Arabic garbled encoding if detected
    if language == "ar" and full_text.count("حُ") > 5:
        full_text = _clean_autocad_arabic(full_text)

    metadata = {
        "file_type": "pdf",
        "page_count": total_pages,
        "has_drawings": has_drawings,
        "has_tables": has_tables,
        "language": language,
        "detected_domain": "architecture-civil" if (has_drawings or "building" in full_text.lower() or "structural" in full_text.lower()) else "general",
        "confidence": confidence,
        "filename": filename,
    }

    return ParserOutput(content=full_text, metadata=metadata)


def _clean_autocad_arabic(text: str) -> str:
    """Decodes visual AutoCAD Arabic fonts to standard logical Unicode Arabic."""
    mapping = {
        0x062d: 0x0627, # ح -> ا
        0x064f: 0x0644, # ُ -> ل
        0x062e: 0x0627, # خ -> ا
        0x064e: 0x0631, # َ -> ر
        0x0654: 0x0645, # ٔ -> م
        0x0664: 0x064a, # ٤ -> ي
        0x0634: 0x0629, # ش -> ة
        0x065d: 0x0648, # ٝ -> و
        0x065e: 0x0628, # ٞ -> ب
        0x064a: 0x062f, # ي -> د
        0x0657: 0x0646, # ٗ -> ن
        0x0638: 0x0641, # ظ -> ف
        0x0637: 0x062a, # ط -> ت
        0x0650: 0x0643, # ِ -> ك
        0x0663: 0x0623, # ٣ -> أ
        0x0648: 0x062e, # و -> خ
        0x0643: 0x0647, # ك -> ه
        0x0662: 0x0644, # ٢ -> ل
        0x064c: 0x062d, # ٌ -> ح
        0x0632: 0x0628, # ز -> ب
        0x063b: 0x0639, # ػ -> ع
        0x064d: 0x0635, # ٍ -> ص
        0x0627: 0x0630, # ا -> ذ
        0x063c: 0x063a, # ؼ -> غ
        0x065c: 0x0647, # ٜ -> ه
        0x0656: 0x0621, # ٖ -> ء
        0x064b: 0x0636, # ً -> ض
        0x0645: 0x0637, # م -> ط
        0x065b: 0x0638, # ٛ -> ظ
        0x0635: 0x062a, # ص -> ت
        0x0652: 0x0645, # ْ -> م
        0x063f: 0x062e, # ؿ -> خ
    }
    
    res = []
    for i, c in enumerate(text):
        code = ord(c)
        if code == 0x0653: # ٓ
            # Check if part of "الخرسانية" or similar (preceded by U+064e and followed by U+062e)
            prev_char = text[i-1] if i > 0 else ''
            next_char = text[i+1] if i < len(text) - 1 else ''
            if ord(prev_char) == 0x064e and ord(next_char) == 0x062e:
                res.append(chr(0x0633)) # -> س
            else:
                res.append(chr(0x0645)) # -> م
        elif code == 0x0658: # ٘
            # Check if followed by آ (U+0622) -> ش, otherwise ن
            next_char = text[i+1] if i < len(text) - 1 else ''
            if ord(next_char) == 0x0622:
                res.append(chr(0x0634)) # -> ش
            else:
                res.append(chr(0x0646)) # -> ن
        else:
            res.append(chr(mapping.get(code, code)))
            
    return "".join(res)
