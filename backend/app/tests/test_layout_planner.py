from app.domain.planner.layout_planner import LayoutPlanner
from app.schemas.room import Room

def main():
    planner = LayoutPlanner(30, 50)

    rooms = [
        Room(name="Living", room_type="living", width=10, height=8),
        Room(name="Bedroom 1", room_type="bedroom", width=5, height=5),
        Room(name="Bedroom 2", room_type="bedroom", width=5, height=5),
    ]

    placed = [planner.place_room(r) for r in rooms]

    for room in placed:
        print(
            f"{room.name} → origin=({room.origin.x}, {room.origin.y}) "
            f"size={room.width}x{room.height}"
        )

if __name__ == "__main__":
    main()
