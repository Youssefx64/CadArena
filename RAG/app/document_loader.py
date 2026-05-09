"""Document text extraction helpers for uploaded RAG files."""
from __future__ import annotations

import csv
import io
import json
from pathlib import Path


class UnsupportedDocumentError(ValueError):
    """Raised when an uploaded document type is not supported."""


def extract_uploaded_document_text(
    *,
    filename: str,
    content: bytes,
    content_type: str | None = None,
) -> str:
    """Extract text from a supported uploaded document."""
    suffix = Path(filename or "").suffix.lower()
    normalized_type = (content_type or "").split(";", 1)[0].strip().lower()

    if suffix == ".pdf" or normalized_type == "application/pdf":
        return _extract_pdf_text(content)

    if suffix in {".txt", ".md"} or normalized_type in {
        "text/plain",
        "text/markdown",
        "application/x-empty",
    }:
        return _extract_text_file(content)

    if suffix == ".csv" or normalized_type == "text/csv":
        return _extract_csv_file(content)

    if suffix == ".json" or normalized_type == "application/json":
        return _extract_json_file(content)

    raise UnsupportedDocumentError("Only PDF, TXT, Markdown, CSV, and JSON files are supported.")


def _extract_text_file(content: bytes) -> str:
    """Decode a text file with a forgiving fallback."""
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError:
        return content.decode("utf-8", errors="replace")


def _extract_csv_file(content: bytes) -> str:
    """Extract readable rows from a CSV file."""
    text = _extract_text_file(content)
    rows = csv.reader(io.StringIO(text))
    return "\n".join(" | ".join(cell.strip() for cell in row if cell.strip()) for row in rows)


def _extract_json_file(content: bytes) -> str:
    """Extract readable text from a JSON file."""
    text = _extract_text_file(content)
    try:
        return json.dumps(json.loads(text), ensure_ascii=False, indent=2)
    except json.JSONDecodeError:
        return text


def _extract_pdf_text(content: bytes) -> str:
    """Extract page text from a PDF using PyMuPDF."""
    try:
        import fitz
    except ModuleNotFoundError as exc:  # pragma: no cover - dependency guard.
        raise RuntimeError("PyMuPDF is required to ingest PDF files.") from exc

    try:
        with fitz.open(stream=content, filetype="pdf") as document:
            pages = [
                page.get_text("text").strip()
                for page in document
            ]
    except Exception as exc:
        raise ValueError("Unable to read the uploaded PDF file.") from exc

    return "\n\n".join(page for page in pages if page)
