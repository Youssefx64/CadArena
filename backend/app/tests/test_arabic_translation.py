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
