from pathlib import Path

import pytest

pytest.importorskip("ezdxf")

from app.services.intent_processing import generate_dxf_from_payload


def test_generate_dxf_from_payload_resolves_defaults_and_creates_file() -> None:
    payload = {
        "boundary": {"width": 18.0, "height": 12.0},
        "rooms": [
            {"name": "Living", "room_type": "living", "width": 7.0, "height": 5.0},
            {"name": "Kitchen", "room_type": "kitchen", "width": 5.0, "height": 4.0},
        ],
    }

    dxf_path = generate_dxf_from_payload(payload)

    assert isinstance(dxf_path, Path)
    assert dxf_path.suffix.lower() == ".dxf"
    assert dxf_path.exists()
