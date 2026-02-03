from app.schemas.design_intent import DesignIntent
from app.schemas.geometry import RectangleGeometry, Point
from app.schemas.room import Room
from app.domain.planner.planner_agent import PlannerAgent
from app.services.dxf_room_renderer import DXFRoomRenderer
from app.domain.architecture.wall_generator import (
    generate_wall_segments,
    generate_boundary_segments,
)
from app.domain.architecture.door_wall_placement import (
    auto_place_door_on_room,
    place_door_on_wall,
)
from app.domain.architecture.wall_cut_manager import WallCutManager
from app.domain.architecture.door_geometry import compute_door_geometry
from app.domain.architecture.opening import DoorPlacement
from app.domain.architecture.wall import WallSegment


def _opening_points_from_placement(placement: DoorPlacement) -> tuple[Point, Point]:
    wall = placement.wall
    length = wall.length()
    if length < 0.001:
        raise ValueError("Wall segment too short for door placement")

    dx = wall.end.x - wall.start.x
    dy = wall.end.y - wall.start.y
    ux = dx / length
    uy = dy / length

    cut_start = Point(
        x=wall.start.x + ux * placement.offset,
        y=wall.start.y + uy * placement.offset
    )

    cut_end = Point(
        x=cut_start.x + ux * placement.door.width,
        y=cut_start.y + uy * placement.door.width
    )

    return cut_start, cut_end


def _point_on_axis_segment(segment: WallSegment, point: Point, tol: float = 1e-6) -> bool:
    if abs(segment.start.x - segment.end.x) < tol:
        if abs(point.x - segment.start.x) > tol:
            return False
        return (
            min(segment.start.y, segment.end.y) - tol
            <= point.y
            <= max(segment.start.y, segment.end.y) + tol
        )
    if abs(segment.start.y - segment.end.y) < tol:
        if abs(point.y - segment.start.y) > tol:
            return False
        return (
            min(segment.start.x, segment.end.x) - tol
            <= point.x
            <= max(segment.start.x, segment.end.x) + tol
        )
    return False


def _boundary_door_placements(
    boundary_segments: list[WallSegment],
    door_placements: list[DoorPlacement]
) -> list[DoorPlacement]:
    boundary_placements: list[DoorPlacement] = []

    for placement in door_placements:
        cut_start, cut_end = _opening_points_from_placement(placement)

        for boundary in boundary_segments:
            if not (
                _point_on_axis_segment(boundary, cut_start)
                and _point_on_axis_segment(boundary, cut_end)
            ):
                continue

            length = boundary.length()
            if length < 0.001:
                continue

            dx = boundary.end.x - boundary.start.x
            dy = boundary.end.y - boundary.start.y
            ux = dx / length
            uy = dy / length

            proj_start = (
                (cut_start.x - boundary.start.x) * ux
                + (cut_start.y - boundary.start.y) * uy
            )
            proj_end = (
                (cut_end.x - boundary.start.x) * ux
                + (cut_end.y - boundary.start.y) * uy
            )

            offset = min(proj_start, proj_end)
            offset = max(0.0, min(offset, length))

            boundary_placements.append(
                DoorPlacement(
                    wall=boundary,
                    offset=offset,
                    door=placement.door
                )
            )
            break

    return boundary_placements


def generate_dxf_from_intent(intent: DesignIntent):
    # 1) Build boundary
    boundary = RectangleGeometry(
        type="rectangle",
        width=intent.boundary.width,
        height=intent.boundary.height,
        origin=Point(x=0, y=0),
    )

    # 2) Initialize planner agent
    agent = PlannerAgent(boundary)

    # 3) Create and place rooms
    for r in intent.rooms:
        room = Room(name=r.name, room_type=r.room_type, width=r.width, height=r.height)
        agent.place_room(room)

    # 4) Generate wall segments + door placements
    wall_manager = WallCutManager()
    door_placements = []
    door_intents = [o for o in intent.openings if o.type == "door"]

    wall_index = {
        "bottom": 0,
        "right": 1,
        "top": 2,
        "left": 3,
    }

    for idx, room in enumerate(agent.placed_rooms):
        segments = generate_wall_segments(room)
        wall_manager.add_wall_segments(segments)

        if door_intents:
            door_intent = door_intents[min(idx, len(door_intents) - 1)]
            wall_segment = segments[wall_index[door_intent.wall]]
            placement = place_door_on_wall(
                wall=wall_segment,
                offset=door_intent.offset,
                door_width=door_intent.width
            )
        else:
            placement = auto_place_door_on_room(room, segments)

        door_placements.append(placement)
        wall_manager.add_door_placement(placement)

    # 5) Cut walls for doors
    final_wall_segments = wall_manager.process_cuts()

    # 5b) Cut boundary for doors that touch the outer perimeter
    boundary_segments = generate_boundary_segments(boundary)
    boundary_manager = WallCutManager()
    boundary_manager.add_wall_segments(boundary_segments)
    for placement in _boundary_door_placements(boundary_segments, door_placements):
        boundary_manager.add_door_placement(placement)
    final_boundary_segments = boundary_manager.process_cuts()

    # 6) Compute door geometry
    door_geometries = [compute_door_geometry(p) for p in door_placements]

    # 7) Render DXF
    renderer = DXFRoomRenderer()
    renderer.draw_boundary_segments(final_boundary_segments)
    renderer.draw_wall_segments(final_wall_segments)

    for geom in door_geometries:
        renderer.draw_door_geometry(geom)

    for room in agent.placed_rooms:
        renderer.draw_room_label(room)
        renderer.draw_room_dimensions(room)

    # 8) Save DXF
    return renderer.save()
