from app.schemas.design_intent import DesignIntent
from app.schemas.geometry import RectangleGeometry, Point
from app.schemas.room import Room
from app.domain.planner.planner_agent import PlannerAgent
from app.services.dxf_room_renderer import DXFRoomRenderer

from app.domain.openings.door_placement import (
    place_door_with_user_preference,
    place_door_inside_room,
)
from app.domain.openings.auto_windows import auto_place_windows


def generate_dxf_from_intent(intent: DesignIntent):
    # 1) Build boundary
    boundary = RectangleGeometry(
        type="rectangle",
        width=intent.boundary.width,
        height=intent.boundary.height,
        origin=Point(x=0, y=0)
    )

    # 2) Initialize planner agent
    agent = PlannerAgent(boundary)

    # 3) Create and place rooms
    for r in intent.rooms:
        room = Room(
            name=r.name,
            room_type=r.room_type,
            width=r.width,
            height=r.height
        )
        agent.place_room(room)

    # 4) Initialize renderer
    renderer = DXFRoomRenderer()
    renderer.draw_boundary(boundary)

    # 5) Draw rooms + labels + dimensions
    for room in agent.placed_rooms:
        renderer.draw_room_walls(room)
        renderer.draw_room_label(room)
        renderer.draw_room_dimensions(room)

    # 6) Draw doors (ONE door per room)
    door_intents = [o for o in intent.openings if o.type == "door"]

    for idx, room in enumerate(agent.placed_rooms):
        if door_intents:
            # use corresponding intent if exists, else fallback
            door_intent = door_intents[min(idx, len(door_intents) - 1)]
            door = place_door_with_user_preference(room, door_intent)
        else:
            door = place_door_inside_room(room)

        renderer.draw_door(door)

    # 7) Draw windows (always auto for now)
    for room in agent.placed_rooms:
        windows = auto_place_windows(room, boundary)
        for window in windows:
            renderer.draw_window(window)

    # 8) Save DXF
    return renderer.save()
