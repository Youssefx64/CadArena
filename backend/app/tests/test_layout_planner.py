from app.domain.entities import Room
from app.domain.planner.layout_planner import LayoutPlanner


def test_layout_planner_places_rooms_left_to_right() -> None:
    planner = LayoutPlanner(boundary_width=30.0, boundary_height=50.0)
    rooms = [
        Room(name="Living", room_type="living", width=10.0, height=8.0),
        Room(name="Bedroom 1", room_type="bedroom", width=5.0, height=5.0),
        Room(name="Bedroom 2", room_type="bedroom", width=5.0, height=5.0),
    ]

    placed = [planner.place_room(room) for room in rooms]

    assert (placed[0].origin.x, placed[0].origin.y) == (0.0, 0.0)
    assert (placed[1].origin.x, placed[1].origin.y) == (10.0, 0.0)
    assert (placed[2].origin.x, placed[2].origin.y) == (15.0, 0.0)
