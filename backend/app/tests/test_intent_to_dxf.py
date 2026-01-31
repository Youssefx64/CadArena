from app.schemas.design_intent import DesignIntent
from app.pipeline.intent_to_agent import generate_dxf_from_intent


def main():
    intent = DesignIntent(
        boundary={"width": 30, "height": 20},
        rooms=[
            {
                "name": "Living Room",
                "room_type": "living",
                "width": 10,
                "height": 8
            },
            {
                "name": "Bedroom",
                "room_type": "bedroom",
                "width": 5,
                "height": 5
            },
            {
                "name": "Kitchen",
                "room_type": "kitchen",
                "width": 4,
                "height": 4
            }
        ],
        openings=[
            {
                "type": "door",
                "width": 1.0,
                "wall": "bottom",
                "offset": 4.0
            }
        ]
    )

    dxf_path = generate_dxf_from_intent(intent)
    print("DXF generated at:", dxf_path)


if __name__ == "__main__":
    main()
