"""Unit tests for ArchChat document parsers."""
from __future__ import annotations

import io
import pytest
from app.parsers import parse_document, ParserOutput
from app.parsers.txt import parse_txt
from app.parsers.csv import parse_csv
from app.parsers.pdf import parse_pdf
from app.parsers.xlsx import parse_xlsx
from app.parsers.dxf import parse_dxf
from app.parsers.ifc import parse_ifc
from app.parsers.image import parse_image

def test_txt_parser() -> None:
    content = b"This is a structural wall and column calculation sheet."
    result = parse_txt("test.txt", content, "text/plain")
    assert isinstance(result, ParserOutput)
    assert "structural wall" in result.content
    assert result.metadata["file_type"] == "text"
    assert result.metadata["detected_domain"] == "architecture-civil"

def test_csv_parser() -> None:
    content = (
        "Item,Area,Rate,Total\n"
        "Wall,15.5,100,1550\n"
        "Column,5.0,200,1000\n"
    ).encode("utf-8")
    result = parse_csv("boq.csv", content, "text/csv")
    assert isinstance(result, ParserOutput)
    assert "Total Rows: 2" in result.content
    assert "Column 'Area' Summary" in result.content
    assert result.metadata["file_type"] == "csv"
    assert result.metadata["detected_domain"] == "architecture-civil"

def test_pdf_parser_missing_or_empty() -> None:
    # PyMuPDF fitz requires valid PDF structure. We'll verify it raises ValueError on bad data.
    with pytest.raises(ValueError):
        parse_pdf("bad.pdf", b"corrupted content", "application/pdf")

def test_xlsx_parser() -> None:
    import openpyxl
    # Create a small in-memory workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "BOQ"
    ws.append(["Item", "Quantity", "Rate", "Total"])
    ws.append(["Concrete M30", 50, 1200, "=B2*C2"])
    
    stream = io.BytesIO()
    wb.save(stream)
    excel_bytes = stream.getvalue()

    result = parse_xlsx("boq.xlsx", excel_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    assert isinstance(result, ParserOutput)
    assert "Sheet: BOQ" in result.content
    assert "[Formula: =B2*C2]" in result.content
    assert result.metadata["is_boq"] is True
    assert result.metadata["detected_domain"] == "architecture-civil"

def test_dxf_parser() -> None:
    import ezdxf
    # Create a small in-memory DXF drawing
    doc = ezdxf.new()
    doc.layers.new(name="Walls")
    doc.layers.new(name="Rooms")
    msp = doc.modelspace()
    msp.add_line((0, 0), (10, 10), dxfattribs={"layer": "Walls"})
    msp.add_text("Living Room", dxfattribs={"layer": "Rooms", "insert": (5, 5)})
    
    stream = io.StringIO()
    doc.write(stream)
    dxf_bytes = stream.getvalue().encode("utf-8")

    result = parse_dxf("layout.dxf", dxf_bytes, "application/dxf")
    assert isinstance(result, ParserOutput)
    assert "LINES: 1" in result.content
    assert "TEXTS/MTEXTS: 1" in result.content
    assert "[Rooms] Living Room" in result.content
    assert result.metadata["file_type"] == "dxf"
    assert "Walls" in result.metadata["layers"]

def test_ifc_parser_text_fallback() -> None:
    # Test the STEP fallback parser by supplying mock STEP strings
    step_content = (
        "ISO-10303-21;\n"
        "HEADER;\n"
        "ENDSEC;\n"
        "DATA;\n"
        "#1=IFCPROJECT('123',$,$,$,$,$,$,$,$);\n"
        "#2=IFCSPACE('456',$,'Living Room',$,$,$,$,$,$,$,$);\n"
        "#3=IFCWALL('789',$,$,$,$,$,$,$);\n"
        "ENDSEC;\n"
        "END-ISO-10303-21;\n"
    ).encode("utf-8")

    result = parse_ifc("model.ifc", step_content, "application/x-step")
    assert isinstance(result, ParserOutput)
    assert "BIM text parser fallback activated" in result.content
    assert "Walls: 1" in result.content
    assert "Spaces: 1" in result.content
    assert result.metadata["file_type"] == "ifc"
    assert result.metadata["native_parsed"] is False

def test_image_parser() -> None:
    from PIL import Image
    # Create a small white image
    img = Image.new("RGB", (100, 100), color="white")
    stream = io.BytesIO()
    img.save(stream, format="PNG")
    img_bytes = stream.getvalue()

    result = parse_image("floor_plan.png", img_bytes, "image/png")
    assert isinstance(result, ParserOutput)
    assert "Dimensions: 100 x 100 px" in result.content
    assert "Format: PNG" in result.content
    assert result.metadata["image_metadata"]["drawing_class"] == "Floor Plan"

def test_parse_document_routing() -> None:
    content = b"This is text content."
    result = parse_document("test.txt", content, "text/plain")
    assert result.metadata["file_type"] == "text"
