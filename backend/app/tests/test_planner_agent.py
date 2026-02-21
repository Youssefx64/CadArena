from app.domain.entities import Point2D, RectangleGeometry, Room
from app.domain.planner.planner_agent import PlannerAgent


def test_planner_agent_places_rooms_without_overlap() -> None:
    boundary = RectangleGeometry(width=30.0, height=20.0, origin=Point2D(x=0.0, y=0.0), type="rectangle")
    agent = PlannerAgent(boundary)

    rooms = [
        Room(name="Living", room_type="living", width=10.0, height=8.0),
        Room(name="Bedroom 1", room_type="bedroom", width=5.0, height=5.0),
        Room(name="Bedroom 2", room_type="bedroom", width=5.0, height=5.0),
        Room(name="Kitchen", room_type="kitchen", width=4.0, height=4.0),
    ]

    for room in rooms:
        placed = agent.place_room(room)
        assert placed.origin is not None

    assert len(agent.placed_rooms) == 4
    names = {room.name for room in agent.placed_rooms}
    assert names == {"Living", "Bedroom 1", "Bedroom 2", "Kitchen"}
