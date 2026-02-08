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
    """
    Calculate the start and end points of an opening on a wall.
    
    Args:
        placement: Door placement containing wall, offset, and door width.
    
    Returns:
        Tuple of (cut_start, cut_end) points along the wall.
    
    Raises:
        ValueError: If wall segment is too short.
    """
    wall = placement.wall
    length = wall.length()
    if length < 0.001:
        raise ValueError("Wall segment too short for opening placement")

    # Calculate unit vector along wall direction
    dx = wall.end.x - wall.start.x
    dy = wall.end.y - wall.start.y
    ux = dx / length
    uy = dy / length

    # Calculate opening start point
    cut_start = Point(
        x=wall.start.x + ux * placement.offset,
        y=wall.start.y + uy * placement.offset
    )
    # Calculate opening end point
    cut_end = Point(
        x=cut_start.x + ux * placement.door.width,
        y=cut_start.y + uy * placement.door.width
    )
    return cut_start, cut_end


def _point_on_axis_segment(segment: WallSegment, point: Point, tol: float = 1e-6) -> bool:
    """
    Check if a point lies on an axis-aligned wall segment.
    
    Args:
        segment: Wall segment (must be horizontal or vertical).
        point: Point to check.
        tol: Tolerance for floating-point comparison.
    
    Returns:
        True if point lies on the segment, False otherwise.
    """
    # Check vertical wall (x constant)
    if abs(segment.start.x - segment.end.x) < tol:
        if abs(point.x - segment.start.x) > tol:
            return False
        return (
            min(segment.start.y, segment.end.y) - tol
            <= point.y
            <= max(segment.start.y, segment.end.y) + tol
        )
    # Check horizontal wall (y constant)
    if abs(segment.start.y - segment.end.y) < tol:
        if abs(point.y - segment.start.y) > tol:
            return False
        return (
            min(segment.start.x, segment.end.x) - tol
            <= point.x
            <= max(segment.start.x, segment.end.x) + tol
        )
    return False


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
    if not (_point_on_axis_segment(wall, cut_start) and _point_on_axis_segment(wall, cut_end)):
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


def _boundary_opening_placements(
    boundary_segments: list[WallSegment],
    opening_placements: list[DoorPlacement]
) -> list[DoorPlacement]:
    """
    Map room opening placements to boundary wall segments.
    
    Finds which boundary segments align with room openings and creates
    corresponding placements on the boundary walls.
    
    Args:
        boundary_segments: List of boundary wall segments.
        opening_placements: List of door placements from room walls.
    
    Returns:
        List of door placements on boundary walls.
    """
    boundary_placements: list[DoorPlacement] = []

    for placement in opening_placements:
        cut_start, cut_end = _opening_points_from_placement(placement)

        # Find matching boundary segment
        for boundary in boundary_segments:
            if not (
                _point_on_axis_segment(boundary, cut_start)
                and _point_on_axis_segment(boundary, cut_end)
            ):
                continue

            length = boundary.length()
            if length < 0.001:
                continue

            # Calculate offset along boundary wall
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


def _wall_object_key(wall: WallSegment) -> tuple[int, int]:
    """
    Generate a unique key for a wall segment based on endpoint object IDs.
    
    Args:
        wall: Wall segment.
    
    Returns:
        Tuple of (start_id, end_id) for use as dictionary key.
    """
    return (id(wall.start), id(wall.end))


def _opening_segment_key(cut_start: Point, cut_end: Point) -> tuple[float, float, float, float]:
    """
    Generate a normalized key for an opening segment.
    
    Normalizes point order and rounds coordinates to avoid duplicate openings.
    
    Args:
        cut_start: Opening start point.
        cut_end: Opening end point.
    
    Returns:
        Tuple of (x1, y1, x2, y2) with normalized order.
    """
    p1 = (round(cut_start.x, 4), round(cut_start.y, 4))
    p2 = (round(cut_end.x, 4), round(cut_end.y, 4))
    # Normalize order (smaller point first)
    if p2 < p1:
        p1, p2 = p2, p1
    return (p1[0], p1[1], p2[0], p2[1])


def _door_render_key(placement: DoorPlacement) -> tuple[float, float, float, float]:
    """
    Generate a key for door rendering deduplication.
    
    Args:
        placement: Door placement.
    
    Returns:
        Normalized opening segment key.
    """
    cut_start, cut_end = _opening_points_from_placement(placement)
    return _opening_segment_key(cut_start, cut_end)


def _find_mirror_wall_candidates(
    source_wall: WallSegment,
    cut_start: Point,
    cut_end: Point,
    all_walls: list[WallSegment],
) -> list[WallSegment]:
    """
    Find wall segments that align with the same opening points.
    
    Used to find opposite walls that should have mirrored door openings
    (e.g., internal doors between adjacent rooms).
    
    Args:
        source_wall: Original wall with the opening.
        cut_start: Opening start point.
        cut_end: Opening end point.
        all_walls: All wall segments to search.
    
    Returns:
        List of candidate walls that align with the opening points.
    """
    candidates: list[WallSegment] = []
    source_key = _wall_object_key(source_wall)

    for wall in all_walls:
        # Skip the source wall itself
        if _wall_object_key(wall) == source_key:
            continue
        # Check if opening points lie on this wall
        if _point_on_axis_segment(wall, cut_start) and _point_on_axis_segment(wall, cut_end):
            candidates.append(wall)

    return candidates


def _validate_opening(opening: OpeningIntent):
    """
    Validate opening intent parameters.
    
    Args:
        opening: Opening intent to validate.
    
    Raises:
        RuntimeError: If opening parameters are invalid or inconsistent.
    """
    if opening.width <= 0:
        raise RuntimeError("Opening.width must be > 0")
    if opening.wall is None:
        raise RuntimeError("Opening.wall is required")
    if opening.room_name is None:
        raise RuntimeError("Opening.room_name is required for deterministic placement")
    if opening.offset is not None and opening.offset < 0:
        raise RuntimeError("Opening.offset must be >= 0")
    if (opening.cut_start is None) != (opening.cut_end is None):
        raise RuntimeError("Opening.cut_start and Opening.cut_end must be provided together")
    if opening.cut_start is not None and opening.offset is not None:
        raise RuntimeError("Use either cut_start/cut_end or offset, not both")


def generate_dxf_from_intent(intent: DesignIntent):
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
    # Create boundary geometry
    boundary = RectangleGeometry(
        type="rectangle",
        width=intent.boundary.width,
        height=intent.boundary.height,
        origin=Point(x=0, y=0),
    )

    # Initialize planner agent with boundary
    agent = PlannerAgent(boundary)

    # Place all rooms (manual origin or automatic placement)
    for r in intent.rooms:
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
            agent.place_room(room)

    # Generate wall segments for all rooms
    wall_manager = WallCutManager()
    room_segments: dict[str, list[WallSegment]] = {}
    all_room_walls: list[WallSegment] = []

    for room in agent.placed_rooms:
        segments = generate_wall_segments(room)
        room_segments[room.name] = segments
        all_room_walls.extend(segments)
        wall_manager.add_wall_segments(segments)

    # Map wall names to segment indices (order: bottom, right, top, left)
    wall_index = {
        "bottom": 0,
        "right": 1,
        "top": 2,
        "left": 3,
    }

    # Track openings for rendering and wall cutting
    all_opening_placements: list[DoorPlacement] = []
    door_placements_for_render: list[DoorPlacement] = []
    window_segments_for_render: list[tuple[Point, Point]] = []
    door_render_keys: set[tuple[float, float, float, float]] = set()
    wall_cut_keys: set[tuple[tuple[int, int], tuple[float, float, float, float]]] = set()

    def register_wall_cut(placement: DoorPlacement):
        """
        Register a door placement for wall cutting, avoiding duplicates.
        
        Uses composite key (wall_id, opening_segment) to prevent duplicate cuts.
        """
        cut_start, cut_end = _opening_points_from_placement(placement)
        segment_key = _opening_segment_key(cut_start, cut_end)
        key = (_wall_object_key(placement.wall), segment_key)
        if key in wall_cut_keys:
            return
        wall_cut_keys.add(key)
        all_opening_placements.append(placement)
        wall_manager.add_door_placement(placement)

    # Process explicit openings or auto-place doors
    if intent.openings:
        # Process user-specified openings
        for opening in intent.openings:
            _validate_opening(opening)

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
            register_wall_cut(placement)

            cut_start, cut_end = _opening_points_from_placement(placement)

            if opening.type == "door":
                # Deduplicate door renderings
                render_key = _door_render_key(placement)
                if render_key not in door_render_keys:
                    door_render_keys.add(render_key)
                    door_placements_for_render.append(placement)

                # Auto-mirror internal doors so opposite wall gets the same gap
                for mirror_wall in _find_mirror_wall_candidates(
                    source_wall=target_wall,
                    cut_start=cut_start,
                    cut_end=cut_end,
                    all_walls=all_room_walls,
                ):
                    mirrored = _placement_from_cut_points(mirror_wall, cut_start, cut_end)
                    register_wall_cut(mirrored)
            else:
                # Window: just store segment for rendering
                window_segments_for_render.append((cut_start, cut_end))
    else:
        # No explicit openings: auto-place doors on bottom wall of each room
        for room in agent.placed_rooms:
            segments = room_segments[room.name]
            placement = auto_place_door_on_room(room, segments)
            register_wall_cut(placement)
            door_placements_for_render.append(placement)

    # Process wall cuts to create gaps for doors
    final_wall_segments = wall_manager.process_cuts()

    # Process boundary walls with openings
    boundary_segments = generate_boundary_segments(boundary)
    boundary_manager = WallCutManager()
    boundary_manager.add_wall_segments(boundary_segments)
    for placement in _boundary_opening_placements(boundary_segments, all_opening_placements):
        boundary_manager.add_door_placement(placement)
    final_boundary_segments = boundary_manager.process_cuts()

    # Compute door geometries for rendering
    door_geometries = [compute_door_geometry(p) for p in door_placements_for_render]

    # Render all elements to DXF
    renderer = DXFRoomRenderer()
    renderer.draw_boundary_segments(final_boundary_segments)
    renderer.draw_wall_segments(final_wall_segments)

    for start, end in window_segments_for_render:
        renderer.draw_window_segment(start, end)

    for geom in door_geometries:
        renderer.draw_door_geometry(geom)

    # Add room labels, dimensions, and special features
    for room in agent.placed_rooms:
        renderer.draw_room_label(room)
        renderer.draw_room_dimensions(room)
        if room.room_type == "stairs" and room.origin is not None:
            renderer.draw_stairs(room.origin, room.width, room.height)

    return renderer.save()
