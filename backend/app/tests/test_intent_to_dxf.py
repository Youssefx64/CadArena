from pathlib import Path

import pytest

pytest.importorskip("ezdxf")

from app.pipeline.intent_to_agent import generate_dxf_from_intent
from app.schemas.design_intent import DesignIntent


def test_generate_dxf_from_intent_creates_file() -> None:
    intent = DesignIntent(
        boundary={"width": 12.0, "height": 8.0},
        rooms=[
            {
                "name": "Living Room",
                "room_type": "living",
                "width": 12.0,
                "height": 8.0,
                "origin": {"x": 0.0, "y": 0.0},
            }
        ],
        openings=[],
    )

    dxf_path = generate_dxf_from_intent(intent)

    assert isinstance(dxf_path, Path)
    assert dxf_path.suffix.lower() == ".dxf"
    assert dxf_path.exists()
