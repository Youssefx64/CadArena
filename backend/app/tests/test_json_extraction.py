import pytest

from app.utils.json_extraction import extract_json_object


def test_extract_json_object_accepts_exact_schema_keys() -> None:
    raw = (
        '{"boundary":{"width":20,"height":12},'
        '"rooms":[{"name":"Living Room","room_type":"living","width":10,"height":6,"origin":{"x":0,"y":0}}],'
        '"walls":[{"room_name":"Living Room","wall":"bottom","start":{"x":0,"y":0},"end":{"x":10,"y":0},"thickness":0.2}],'
        '"openings":[]}'
    )
    parsed = extract_json_object(raw)
    assert set(parsed.keys()) == {"boundary", "rooms", "walls", "openings"}


def test_extract_json_object_rejects_wrapped_prose() -> None:
    raw = (
        "Here is your JSON:\n"
        '{"boundary":{"width":20,"height":12},"rooms":[],"walls":[],"openings":[]}'
    )
    with pytest.raises(ValueError):
        extract_json_object(raw)


def test_extract_json_object_rejects_multiple_json_objects() -> None:
    raw = (
        '{"boundary":{"width":20,"height":12},"rooms":[],"walls":[],"openings":[]}'
        '{"boundary":{"width":10,"height":6},"rooms":[],"walls":[],"openings":[]}'
    )
    with pytest.raises(ValueError):
        extract_json_object(raw)


def test_extract_json_object_rejects_missing_required_top_key() -> None:
    raw = '{"boundary":{"width":20,"height":12},"rooms":[],"openings":[]}'
    with pytest.raises(ValueError):
        extract_json_object(raw)

