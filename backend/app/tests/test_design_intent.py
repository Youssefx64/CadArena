from app.schemas.design_intent import DesignIntent


def main():
    intent = DesignIntent(
        boundary={
            "width": 30,
            "height": 20
        },
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
                "room_name": "Living Room",
                "wall": "bottom",
                "offset": 4.0
            }
        ]
    )

    print(intent.model_dump())


if __name__ == "__main__":
    main()
