from app.utils.design_prompt import build_design_parser_prompt


def test_design_prompt_starts_with_critical_extraction_rules() -> None:
    prompt = build_design_parser_prompt("Create a 20x12 house with 2 bedrooms.")
    assert "REQUEST_SEED:" in prompt
    assert "CRITICAL EXTRACTION RULES" in prompt
    assert "1-2 rooms -> 8x6 m" in prompt
    assert "5-6 rooms -> 16x10 m" in prompt
    assert "If no public-zone room exists, silently add exactly 1 Living Room." in prompt
    assert "If bedroom_count >= 2, silently add exactly 1 Main Corridor." in prompt
    assert "Use ONLY: bedroom, bathroom, kitchen, living, corridor, stairs" in prompt
    assert "Every room entry must include preferred_area, min_area, and max_area." in prompt
    assert "Sum(preferred_area * count) must be 80%-95% of boundary area." in prompt
    assert "NEVER include bedroom-kitchen or bathroom-kitchen adjacency." in prompt
    assert "BEDROOM COUNT FROM PROMPT: 2 bedrooms" in prompt
    assert "BOUNDARY FROM PROMPT: 20x12" in prompt
