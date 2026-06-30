"""Image parser for PNG, JPG, and TIFF formats, handling dimensions, layout metadata, and OCR."""
from __future__ import annotations

import logging
from typing import Any
from app.parsers import ParserOutput, register_parser

logger = logging.getLogger(__name__)

@register_parser(
    extensions=[".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".gif"],
    mime_types=["image/png", "image/jpeg", "image/tiff", "image/bmp", "image/gif"]
)
def parse_image(filename: str, content: bytes, content_type: str) -> ParserOutput:
    """Parse image files, extracting dimensions, structural drawings classification, and performing OCR."""
    from io import BytesIO
    try:
        from PIL import Image
    except ModuleNotFoundError as e:
        logger.error("PIL (Pillow) is not installed in the RAG environment.")
        raise RuntimeError("Pillow is required to parse images.") from e

    try:
        img = Image.open(BytesIO(content))
        width, height = img.size
        img_format = img.format
    except Exception as e:
        logger.error(f"Failed to open image file: {e}")
        raise ValueError(f"Unable to read image file: {e}") from e

    # Perform OCR if tools are available
    ocr_text = ""
    ocr_tool = "none"
    
    # Try easyocr first
    try:
        import easyocr
        reader = easyocr.Reader(['en', 'ar'])
        # easyocr expects file path or bytes/numpy array
        results = reader.readtext(content)
        ocr_text = " ".join([res[1] for res in results])
        ocr_tool = "easyocr"
    except Exception:
        # Try pytesseract
        try:
            import pytesseract
            ocr_text = pytesseract.image_to_string(img)
            ocr_tool = "pytesseract"
        except Exception:
            pass

    ocr_text = ocr_text.strip()
    
    # Classify drawing type based on filename keywords or metadata
    filename_lower = filename.lower()
    drawing_class = "unknown"
    is_drawing = False
    
    if any(k in filename_lower for k in ["plan", "layout", "floor"]):
        drawing_class = "Floor Plan"
        is_drawing = True
    elif any(k in filename_lower for k in ["elevation", "facade"]):
        drawing_class = "Elevation Drawing"
        is_drawing = True
    elif any(k in filename_lower for k in ["section", "cut"]):
        drawing_class = "Sectional Drawing"
        is_drawing = True
    elif any(k in filename_lower for k in ["site", "plot"]):
        drawing_class = "Site Plan"
        is_drawing = True
    elif any(k in filename_lower for k in ["detail", "isometric", "structural"]):
        drawing_class = "Detail/Structural Drawing"
        is_drawing = True

    # Identify drawing symbols
    symbols_found = []
    if is_drawing:
        # Check OCR text for common symbols or annotations
        symbols_map = {
            "Door": ["door", "dr", "d-"],
            "Window": ["window", "wd", "w-"],
            "Column": ["column", "col", "c-"],
            "Dimension": ["mm", "cm", "dim", "dimension", "meter"],
            "Stairs": ["stair", "str", "up", "dn"],
            "Room Name": ["room", "bed", "bath", "kitchen", "living", "hall", "office"]
        }
        for symbol, kws in symbols_map.items():
            if any(kw in ocr_text.lower() for kw in kws):
                symbols_found.append(symbol)

    content_parts = [
        f"Image File: {filename}",
        f"Dimensions: {width} x {height} px",
        f"Format: {img_format}",
        f"Drawing Classification: {drawing_class}",
    ]
    if ocr_text:
        content_parts.append(f"\nOCR Extracted Text ({ocr_tool}):\n{ocr_text}")
    else:
        content_parts.append("\n[No text extracted via OCR. Image may contain only graphical elements.]")

    if symbols_found:
        content_parts.append(f"\nIdentified Symbols/Annotations: {', '.join(symbols_found)}")

    full_content = "\n".join(content_parts)

    metadata = {
        "file_type": "image",
        "page_count": 1,
        "has_drawings": is_drawing,
        "has_tables": False,
        "language": "ar" if any("\u0600" <= c <= "\u06FF" for c in ocr_text) else "en",
        "detected_domain": "architecture-civil" if is_drawing else "general",
        "confidence": 0.8 if ocr_text else 0.5,
        "filename": filename,
        "image_metadata": {
            "width": width,
            "height": height,
            "format": img_format,
            "drawing_class": drawing_class,
            "symbols": symbols_found
        }
    }

    return ParserOutput(content=full_content, metadata=metadata)
