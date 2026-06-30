from app.services.design_parser.orchestrator import (
    _extract_expected_room_counts,
    _normalize_prompt_for_extraction,
)


def test_arabic_bedroom_translates_correctly() -> None:
    result = _normalize_prompt_for_extraction(
        "عاوز شقة فيها غرفتين نوم ومطبخ وحمام"
    )
    assert "bedroom" in result.lower() or "room" in result.lower()
    assert "kitchen" in result.lower()
    assert "bathroom" in result.lower()


def test_arabic_indic_numerals_convert() -> None:
    result = _normalize_prompt_for_extraction("٣ غرف نوم")
    assert "3" in result


def test_english_prompt_unchanged() -> None:
    prompt = "Design a 3 bedroom house with kitchen"
    result = _normalize_prompt_for_extraction(prompt)
    assert result == prompt.strip()


def test_empty_arabic_returns_fallback() -> None:
    result = _normalize_prompt_for_extraction("هههههه")
    assert len(result) > 10
    assert "bedroom" in result.lower() or "room" in result.lower()


def test_arabic_written_numbers_translate() -> None:
    result = _normalize_prompt_for_extraction(
        "عاوز شقة فيها ثلاث غرف نوم ومطبخ وحمامين"
    )
    assert "3" in result or "three" in result.lower()
    assert "kitchen" in result.lower()
    assert "2 bathroom" in result.lower() or "bathrooms" in result.lower()


def test_arabic_single_bedroom_translates() -> None:
    result = _normalize_prompt_for_extraction(
        "أوضة نوم واحدة وصالة ومطبخ"
    )
    assert "1" in result or "bedroom" in result.lower()
    assert "living" in result.lower() or "salon" in result.lower()


def test_arabic_dialect_numbers() -> None:
    result = _normalize_prompt_for_extraction("تلات أوض نوم")
    assert "3" in result or "bedroom" in result.lower()


def test_extract_expected_room_counts_handles_bare_singular_rooms() -> None:
    counts = _extract_expected_room_counts("2 bedroom apartment with kitchen and bathroom")
    assert counts == {"bedroom": 2, "kitchen": 1, "bathroom": 1}


def test_extract_expected_room_counts_handles_normalized_arabic_prompt() -> None:
    normalized = _normalize_prompt_for_extraction("عاوز شقة فيها غرفتين نوم ومطبخ وحمام")
    counts = _extract_expected_room_counts(normalized)
    assert counts == {"bedroom": 2, "kitchen": 1, "bathroom": 1}


def test_arabic_boundary_matching() -> None:
    from app.services.design_parser.room_program_normalizer import extract_prompt_boundary
    
    # Test typical Arabic boundary phrases with different numerals/operators
    b1 = extract_prompt_boundary("شقة ١٠ في ١٢ متر")
    assert b1 == (12.0, 10.0)
    
    b2 = extract_prompt_boundary("تصميم شقة 10م في 8م")
    assert b2 == (10.0, 8.0)
    
    b3 = extract_prompt_boundary("شقة مساحتها 12 * 9")
    assert b3 == (12.0, 9.0)


def test_arabic_room_name_resolution_iterative() -> None:
    from app.services.design_parser.diff_orchestrator import _resolve_room_name
    
    room_names = ["Bathroom", "Bedroom 1", "Bedroom 2", "Kitchen", "Living Room"]
    lowered_names = {name.lower(): name for name in room_names}
    
    # Test that Arabic room names resolve to their English equivalents in layout
    assert _resolve_room_name("حمام", room_names, lowered_names) == "Bathroom"
    assert _resolve_room_name("غرفة نوم ١", room_names, lowered_names) == "Bedroom 1"
    assert _resolve_room_name("مطبخ", room_names, lowered_names) == "Kitchen"
    assert _resolve_room_name("صاله", room_names, lowered_names) == "Living Room"

