import pytest
from pydantic import ValidationError

from app.schemas.design_intent import DesignIntent


def test_design_intent_model_accepts_valid_payload() -> None:
    intent = DesignIntent(
        boundary={"width": 30, "height": 20},
        rooms=[
            {"name": "Living Room", "room_type": "living", "width": 10, "height": 8},
            {"name": "Bedroom", "room_type": "bedroom", "width": 5, "height": 5},
        ],
        openings=[
            {"type": "door", "width": 1.0, "room_name": "Living Room", "wall": "bottom", "offset": 4.0}
        ],
    )

    assert intent.boundary.width == 30
    assert len(intent.rooms) == 2
    assert intent.openings[0].type == "door"


def test_design_intent_model_rejects_invalid_room_type() -> None:
    with pytest.raises(ValidationError):
        DesignIntent(
            boundary={"width": 30, "height": 20},
            rooms=[
                {"name": "Bad", "room_type": "garage", "width": 5, "height": 5},
            ],
            openings=[],
        )
