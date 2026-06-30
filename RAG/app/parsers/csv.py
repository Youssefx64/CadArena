"""CSV parser for structured engineering data, calculating statistical summaries."""
from __future__ import annotations

import csv
import io
import logging
from typing import Any
from app.parsers import ParserOutput, register_parser

logger = logging.getLogger(__name__)

@register_parser(extensions=[".csv"], mime_types=["text/csv"])
def parse_csv(filename: str, content: bytes, content_type: str) -> ParserOutput:
    """Parse CSV rows, scan for engineering headers, and compute summaries."""
    try:
        raw_text = content.decode("utf-8")
    except UnicodeDecodeError:
        try:
            raw_text = content.decode("cp1256")
        except UnicodeDecodeError:
            raw_text = content.decode("utf-8", errors="replace")

    reader = csv.reader(io.StringIO(raw_text))
    rows = list(reader)

    if not rows:
        return ParserOutput(
            content="[Empty CSV]",
            metadata={
                "file_type": "csv",
                "page_count": 1,
                "has_drawings": False,
                "has_tables": True,
                "language": "en",
                "detected_domain": "general",
                "confidence": 1.0,
                "filename": filename,
            }
        )

    header = [col.strip().lower() for col in rows[0]]
    num_rows = len(rows) - 1

    # Detect engineering or structural columns
    eng_keywords = {"area", "volume", "length", "width", "height", "thickness", "weight", "concrete", "steel", "reinforcement", "cost", "price", "rate", "quantity", "qnty", "load", "force", "stress", "moment"}
    detected_eng_cols = []
    
    for idx, col_name in enumerate(header):
        if any(kw in col_name for kw in eng_keywords):
            detected_eng_cols.append((idx, col_name))

    # Calculate summaries for numeric columns
    summaries = []
    for idx, col_name in detected_eng_cols:
        values = []
        for row in rows[1:]:
            if idx < len(row):
                val_str = row[idx].strip()
                # strip currency or unit marks
                val_str = val_str.replace("$", "").replace("L.E", "").replace("m2", "").replace("m3", "").replace("mm", "").replace("m", "")
                try:
                    values.append(float(val_str))
                except ValueError:
                    pass
        if values:
            col_sum = sum(values)
            col_avg = col_sum / len(values)
            col_min = min(values)
            col_max = max(values)
            summaries.append(
                f"Column '{rows[0][idx]}' Summary: Count={len(values)}, Sum={col_sum:.2f}, Avg={col_avg:.2f}, Min={col_min:.2f}, Max={col_max:.2f}"
            )

    # Format the CSV output into a readable text format
    output_parts = [f"CSV File: {filename}", f"Total Rows: {num_rows}", f"Headers: {', '.join(rows[0])}"]
    if summaries:
        output_parts.append("\nEngineering Statistics:\n" + "\n".join(summaries))
    
    output_parts.append("\nData Rows:")
    for idx, row in enumerate(rows):
        output_parts.append(f"Row {idx}: " + " | ".join(row))

    full_content = "\n".join(output_parts)

    metadata = {
        "file_type": "csv",
        "page_count": 1,
        "has_drawings": False,
        "has_tables": True,
        "language": "en",
        "detected_domain": "architecture-civil" if detected_eng_cols else "general",
        "confidence": 1.0,
        "filename": filename,
        "engineering_columns": [name for _, name in detected_eng_cols],
    }

    return ParserOutput(content=full_content, metadata=metadata)
