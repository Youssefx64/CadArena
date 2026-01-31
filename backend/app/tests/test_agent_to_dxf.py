from app.domain.planner.planner_agent import PlannerAgent
from app.schemas.geometry import RectangleGeometry, Point
from app.schemas.room import Room
from app.services.dxf_room_renderer import DXFRoomRenderer
from app.schemas.opening import Opening
from app.domain.openings.door_placement import place_door_inside_room


def main():
    # Define the apartment / villa boundary
    boundary = RectangleGeometry(
        type="rectangle",
        width=30,
        height=20,
        origin=Point(x=0, y=0)
    )

    # Initialize the planner agent
    agent = PlannerAgent(boundary)

    # Define rooms requested by the user
    rooms = [
        Room(name="Living Room", room_type="living", width=10, height=8),
        Room(name="Bedroom", room_type="bedroom", width=5, height=5),
        Room(name="Kitchen", room_type="kitchen", width=4, height=4),
    ]

    # Place rooms using the agent
    for room in rooms:
        agent.place_room(room)

    # Initialize DXF renderer
    renderer = DXFRoomRenderer()

    # Draw the boundary
    renderer.draw_boundary(boundary)

    # Draw rooms, labels, and dimensions
    for room in agent.placed_rooms:
        renderer.draw_room_walls(room)
        renderer.draw_room_label(room)
        renderer.draw_room_dimensions(room)

        door = place_door_inside_room(room)
        renderer.draw_door(door)

    # Save DXF file
    file_path = renderer.save()
    print("DXF generated at:", file_path)


if __name__ == "__main__":
    main()
