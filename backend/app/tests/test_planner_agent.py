from app.domain.planner.planner_agent import PlannerAgent
from app.schemas.geometry import RectangleGeometry, Point
from app.schemas.room import Room


def main():
    boundary = RectangleGeometry(
        type="rectangle",
        width=30,
        height=20,
        origin=Point(x=0, y=0)
    )

    agent = PlannerAgent(boundary)

    rooms = [
        Room(name="Living", room_type="living", width=10, height=8),
        Room(name="Bedroom 1", room_type="bedroom", width=5, height=5),
        Room(name="Bedroom 2", room_type="bedroom", width=5, height=5),
        Room(name="Kitchen", room_type="kitchen", width=4, height=4),
    ]

    for room in rooms:
        agent.place_room(room)

    print("\nFinal layout:")
    for r in agent.placed_rooms:
        print(
            f"{r.name} at ({r.origin.x}, {r.origin.y}) "
            f"size={r.width}x{r.height}"
        )


if __name__ == "__main__":
    main()
