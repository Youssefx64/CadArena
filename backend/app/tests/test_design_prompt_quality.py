from app.utils.design_prompt import build_design_parser_prompt


def test_design_prompt_starts_with_critical_extraction_rules() -> None:
    prompt = build_design_parser_prompt("Create a 20x12 house with 2 bedrooms.")
    assert prompt.startswith("CRITICAL EXTRACTION RULES — violating any rule = invalid output:")
    assert 'For master bedroom: room_type="bedroom", name="Master Bedroom"' in prompt
    assert "Use ONLY: bedroom, bathroom, kitchen, living, corridor, stairs" in prompt
