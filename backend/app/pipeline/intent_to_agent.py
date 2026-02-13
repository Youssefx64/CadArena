"""
Design intent to DXF generation pipeline.

This module orchestrates the complete process of converting a design intent
into a DXF file, including room placement, wall generation, door/window
placement, and rendering.
"""

from app.schemas.design_intent import DesignIntent, OpeningIntent
from app.schemas.geometry import RectangleGeometry, Point
from app.schemas.room import Room
from app.domain.planner.planner_agent import PlannerAgent
from app.domain.planner.planning_context import PlanningContext
from app.services.dxf_room_renderer import DXFRoomRenderer
from app.services.intent_validation import DesignIntentValidator
from app.domain.architecture.wall_generator import (
    generate_wall_segments,
    generate_boundary_segments,
)
from app.domain.architecture.door_wall_placement import (
    auto_place_door_on_room,
    place_door_on_wall,
)
from app.domain.architecture.wall_cut_manager import WallCutManager
from app.domain.architecture.opening_geometry import (
    opening_points_from_placement,
    opening_segment_key,
    point_on_axis_segment,
)
from app.domain.architecture.door_geometry import compute_door_geometry
from app.domain.architecture.opening import DoorPlacement
from app.domain.architecture.wall import WallSegment
from app.domain.architecture.render_geometry import (
    build_thick_wall_lines,
    build_room_labels,
    build_room_dimensions,
    build_stair_lines,
)


def _placement_from_cut_points(
    wall: WallSegment,
    cut_start: Point,
    cut_end: Point
) -> DoorPlacement:
    """
    Create a door placement from explicit cut points on a wall.
    
    Converts cut points to offset and width, then creates a DoorPlacement.
    
    Args:
        wall: Wall segment where the opening will be placed.
        cut_start: Start point of the opening.
        cut_end: End point of the opening.
    
    Returns:
        DoorPlacement with calculated offset and door width.
    
    Raises:
        RuntimeError: If points don't lie on wall, wall is too short, or opening too small.
    """
    if not (point_on_axis_segment(wall, cut_start) and point_on_axis_segment(wall, cut_end)):
        raise RuntimeError("cut_start/cut_end must lie on the selected wall")

    length = wall.length()
    if length < 0.001:
        raise RuntimeError("Wall segment too short for opening placement")

    # Calculate unit vector along wall
    dx = wall.end.x - wall.start.x
    dy = wall.end.y - wall.start.y
    ux = dx / length
    uy = dy / length

    # Project points onto wall axis to get offset and width
    proj_start = (cut_start.x - wall.start.x) * ux + (cut_start.y - wall.start.y) * uy
    proj_end = (cut_end.x - wall.start.x) * ux + (cut_end.y - wall.start.y) * uy

    offset = min(proj_start, proj_end)
    opening_width = abs(proj_end - proj_start)

    if opening_width < 0.01:
        raise RuntimeError("Opening width too small")

    # Clamp offset to ensure opening fits on wall
    offset = max(0.0, min(offset, length - opening_width))
    return place_door_on_wall(wall=wall, offset=offset, door_width=opening_width)


def _apply_opening_style(placement: DoorPlacement, opening: OpeningIntent):
    """
    Apply door style attributes (hinge, swing) from opening intent.
    
    Args:
        placement: Door placement to modify.
        opening: Opening intent containing style preferences.
    """
    if opening.hinge is not None:
        placement.door.hinge = opening.hinge
    if opening.swing is not None:
        placement.door.swing = opening.swing


def _place_room_with_origin(agent: PlannerAgent, room: Room, origin: Point):
    """
    Place a room at a specific origin point with constraint validation.
    
    Args:
        agent: Planner agent managing room placement.
        room: Room to place.
        origin: Desired origin point for the room.
    
    Raises:
        RuntimeError: If room violates boundary or overlap constraints.
    """
    room.origin = origin

    if not agent.boundary_constraint.is_valid(room, agent.boundary):
        raise RuntimeError(f"Room {room.name} is out of boundary")
    if not agent.overlap_constraint.is_valid(room, agent.placed_rooms):
        raise RuntimeError(f"Room {room.name} overlaps with another room")

    agent.placed_rooms.append(room)


def _door_render_key(placement: DoorPlacement) -> tuple[float, float, float, float]:
    """
    Generate a key for door rendering deduplication.
    
    Args:
        placement: Door placement.
    
    Returns:
        Normalized opening segment key.
    """
    cut_start, cut_end = opening_points_from_placement(placement)
    return opening_segment_key(cut_start, cut_end)


def generate_dxf_from_intent(
    intent: DesignIntent,
    planning_context: PlanningContext | None = None,
):
    """
    Generate a DXF file from a complete design intent.
    
    Main pipeline function that orchestrates:
    1. Room placement (manual or automatic)
    2. Wall segment generation
    3. Door/window opening placement
    4. Wall cutting for openings
    5. DXF rendering with all elements
    
    Args:
        intent: Complete design specification.
    
    Returns:
        Path to the generated DXF file.
    
    Raises:
        RuntimeError: If room placement fails, opening validation fails, or processing errors occur.
        ValueError: If geometry calculations fail.
    """
    # Validate intent before planning
    DesignIntentValidator().validate(intent)

    # Create boundary geometry
    boundary = RectangleGeometry(
        type="rectangle",
        width=intent.boundary.width,
        height=intent.boundary.height,
        origin=Point(x=0, y=0),
    )

    # Initialize planner agent with boundary
    agent = PlannerAgent(boundary)

    # Determine room order for placement
    rooms_to_place = (
        planning_context.order_rooms(intent.rooms)
        if planning_context is not None
        else list(intent.rooms)
    )

    # Place all rooms (manual origin or automatic placement)
    for r in rooms_to_place:
        room = Room(
            name=r.name,
            room_type=r.room_type,
            width=r.width,
            height=r.height,
            origin=r.origin,
        )
        if r.origin is not None:
            # Manual placement with validation
            _place_room_with_origin(agent, room, r.origin)
        else:
            # Automatic placement by planner
            if planning_context is not None and planning_context.has_rules():
                rules = planning_context.rules_for_room(room, agent.placed_rooms)
                agent.place_room_with_rules(room, rules)
            else:
                agent.place_room(room)

    # Generate wall segments for all rooms
    wall_manager = WallCutManager()
    room_segments: dict[str, list[WallSegment]] = {}

    for room in agent.placed_rooms:
        segments = generate_wall_segments(room)
        room_segments[room.name] = segments
        wall_manager.add_wall_segments(segments)

    # Map wall names to segment indices (order: bottom, right, top, left)
    wall_index = {
        "bottom": 0,
        "right": 1,
        "top": 2,
        "left": 3,
    }

    # Track openings for rendering and wall cutting
    all_cut_segments: list[tuple[Point, Point]] = []
    door_placements_for_render: list[DoorPlacement] = []
    window_segments_for_render: list[tuple[Point, Point]] = []
    door_render_keys: set[tuple[float, float, float, float]] = set()
    cut_segment_keys: set[tuple[float, float, float, float]] = set()

    def register_wall_cut_segment(
        cut_start: Point,
        cut_end: Point,
        wall: WallSegment,
        allow_shared: bool,
    ):
        segment_key = opening_segment_key(cut_start, cut_end)
        if segment_key in cut_segment_keys:
            return
        cut_segment_keys.add(segment_key)
        all_cut_segments.append((cut_start, cut_end))
        wall_manager.add_cut_segment(cut_start, cut_end, wall=wall, allow_shared=allow_shared)

    # Process explicit openings or auto-place doors
    if intent.openings:
        # Process user-specified openings
        for opening in intent.openings:

            if opening.room_name not in room_segments:
                raise RuntimeError(f"Opening room not found: {opening.room_name}")

            target_wall = room_segments[opening.room_name][wall_index[opening.wall]]

            try:
                # Create placement from cut points or offset
                if opening.cut_start is not None and opening.cut_end is not None:
                    placement = _placement_from_cut_points(
                        wall=target_wall,
                        cut_start=opening.cut_start,
                        cut_end=opening.cut_end,
                    )
                else:
                    placement = place_door_on_wall(
                        wall=target_wall,
                        offset=opening.offset,
                        door_width=opening.width,
                    )
            except ValueError as exc:
                raise RuntimeError(str(exc)) from exc

            _apply_opening_style(placement, opening)
            cut_start, cut_end = opening_points_from_placement(placement)
            register_wall_cut_segment(
                cut_start,
                cut_end,
                wall=placement.wall,
                allow_shared=opening.type == "door",
            )

            if opening.type == "door":
                # Deduplicate door renderings
                render_key = _door_render_key(placement)
                if render_key not in door_render_keys:
                    door_render_keys.add(render_key)
                    door_placements_for_render.append(placement)

            else:
                # Window: just store segment for rendering
                window_segments_for_render.append((cut_start, cut_end))
    else:
        # No explicit openings: auto-place doors on bottom wall of each room
        for room in agent.placed_rooms:
            segments = room_segments[room.name]
            placement = auto_place_door_on_room(room, segments)
            cut_start, cut_end = opening_points_from_placement(placement)
            register_wall_cut_segment(
                cut_start,
                cut_end,
                wall=placement.wall,
                allow_shared=True,
            )
            door_placements_for_render.append(placement)

    # Process wall cuts to create gaps for doors
    final_wall_segments = wall_manager.process_cuts()

    # Process boundary walls with openings
    boundary_segments = generate_boundary_segments(boundary)
    boundary_manager = WallCutManager()
    boundary_manager.add_wall_segments(boundary_segments)
    for cut_start, cut_end in all_cut_segments:
        boundary_manager.add_cut_segment(cut_start, cut_end, allow_shared=True)
    final_boundary_segments = boundary_manager.process_cuts()

    # Compute door geometries for rendering
    door_geometries = [compute_door_geometry(p) for p in door_placements_for_render]

    wall_lines = build_thick_wall_lines(final_wall_segments)
    boundary_lines = build_thick_wall_lines(final_boundary_segments)
    room_labels = build_room_labels(agent.placed_rooms)
    room_dimensions = build_room_dimensions(agent.placed_rooms)
    stair_lines: list[tuple[Point, Point]] = []
    for room in agent.placed_rooms:
        if room.room_type == "stairs" and room.origin is not None:
            stair_lines.extend(build_stair_lines(room.origin, room.width, room.height))

    # Render all elements to DXF
    renderer = DXFRoomRenderer()
    renderer.draw_boundary_segments(boundary_lines)
    renderer.draw_wall_segments(wall_lines)

    for start, end in window_segments_for_render:
        renderer.draw_window_segment(start, end)

    for geom in door_geometries:
        renderer.draw_door_geometry(geom)

    # Add room labels, dimensions, and special features
    for text, position in room_labels:
        renderer.draw_room_label(text, position)
    for text, position in room_dimensions:
        renderer.draw_room_dimensions(text, position)
    if stair_lines:
        renderer.draw_stair_lines(stair_lines)

    return renderer.save()
