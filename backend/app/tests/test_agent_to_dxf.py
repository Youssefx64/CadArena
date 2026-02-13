from app.services.intent_processing import generate_dxf_from_payload


def main():
    payload = {
        "boundary": {"width": 18, "height": 12},
        "rooms": [
            {"name": "Living", "room_type": "living", "width": 7, "height": 5},
            {"name": "Kitchen", "room_type": "kitchen", "width": 5, "height": 4},
            {"name": "Bath", "room_type": "bathroom"},
            {"name": "Bedroom", "room_type": "bedroom", "width": 4, "height": 4},
        ],
        "openings": [
            {"type": "door", "room_name": "Living", "wall": "bottom"},
            {"type": "door", "room_name": "Kitchen", "wall": "left", "width": 0.9},
            {"type": "window", "room_name": "Bedroom", "wall": "top"},
        ],
        "planning": {"mode": "rules", "corridor_first": False},
    }

    dxf_path = generate_dxf_from_payload(payload)
    print("DXF generated at:", dxf_path)


if __name__ == "__main__":
    main()
