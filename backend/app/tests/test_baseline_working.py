"""
✅ BASELINE TEST - ARCHITECTURALLY CORRECT

This test follows the 6-stage pipeline EXACTLY:
1. Place rooms (PlannerAgent)
2. Generate wall segments
3. Place doors on walls
4. Cut walls for door openings
5. Compute door geometry
6. Render everything

Expected output:
✓ Clean double-line walls
✓ Real gaps in walls where doors are
✓ Proper door leaf and swing arc
✓ Professional CAD output
"""

from app.domain.planner.planner_agent import PlannerAgent
from app.schemas.geometry import RectangleGeometry, Point
from app.schemas.room import Room
from app.services.dxf_room_renderer import DXFRoomRenderer
from app.domain.architecture.wall_generator import (
    generate_wall_segments,
    generate_boundary_segments,
)
from app.domain.architecture.door_wall_placement import place_door_on_wall
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


def main():
    print("=" * 70)
    print("🏗️  CadArena Baseline Test - 6-Stage Pipeline")
    print("=" * 70)
    
    # ========================================================================
    # STAGE 1: PLACE ROOMS
    # ========================================================================
    print("\n📍 STAGE 1: Room Placement")
    print("-" * 70)
    
    boundary = RectangleGeometry(
        type="rectangle",
        width=24,
        height=14,
        origin=Point(x=0, y=0)
    )
    print(f"✓ Boundary: {boundary.width}m x {boundary.height}m")
    
    agent = PlannerAgent(boundary)

    def place_room_at(room: Room, origin: Point, enforce_spacing: bool = False):
        room.origin = origin

        if not agent.boundary_constraint.is_valid(room, agent.boundary):
            raise RuntimeError(f"{room.name} is خارج الحدود")

        if not agent.overlap_constraint.is_valid(room, agent.placed_rooms):
            raise RuntimeError(f"{room.name} متداخل مع غرفة تانية")

        if enforce_spacing and not agent.spacing_constraint.is_valid(room, agent.placed_rooms):
            raise RuntimeError(f"{room.name} قريب زيادة عن اللازم")

        agent.placed_rooms.append(room)

    rooms = []

    layout = [
        # Left wing
        (Room(name="Living Room", room_type="living", width=10, height=8), Point(x=0, y=0)),
        (Room(name="Kitchen", room_type="kitchen", width=6, height=6), Point(x=0, y=8)),
        (Room(name="Bathroom", room_type="bathroom", width=4, height=6), Point(x=6, y=8)),
        # Central corridor (circulation spine)
        (Room(name="Corridor", room_type="living", width=2, height=14), Point(x=10, y=0)),
        # Right wing
        (Room(name="Stairs", room_type="living", width=4, height=5), Point(x=12, y=0)),
        (Room(name="Bedroom 1", room_type="bedroom", width=8, height=5), Point(x=16, y=0)),
        (Room(name="Bedroom 2", room_type="bedroom", width=12, height=5), Point(x=12, y=5)),
        (Room(name="Bedroom 3", room_type="bedroom", width=12, height=4), Point(x=12, y=10)),
    ]

    for room, origin in layout:
        place_room_at(room, origin)
        rooms.append(room)
        print(f"✓ Placed: {room.name} at ({room.origin.x}, {room.origin.y})")
    
    # ========================================================================
    # STAGE 2: GENERATE WALL SEGMENTS
    # ========================================================================
    print("\n🧱 STAGE 2: Wall Generation")
    print("-" * 70)
    
    wall_manager = WallCutManager()
    room_segments = {}
    
    for room in agent.placed_rooms:
        segments = generate_wall_segments(room)
        room_segments[room.name] = segments
        wall_manager.add_wall_segments(segments)
        print(f"✓ Generated 4 wall segments for {room.name}")
        print(f"  Bottom: ({segments[0].start.x:.1f}, {segments[0].start.y:.1f}) → ({segments[0].end.x:.1f}, {segments[0].end.y:.1f})")
    
    # ========================================================================
    # STAGE 3: PLACE DOORS ON WALLS
    # ========================================================================
    print("\n🚪 STAGE 3: Door Placement")
    print("-" * 70)

    def place_between(wall: WallSegment, cut_start: Point, cut_end: Point) -> DoorPlacement:
        length = wall.length()
        if length < 0.001:
            raise ValueError("Wall segment too short")
        dx = wall.end.x - wall.start.x
        dy = wall.end.y - wall.start.y
        ux = dx / length
        uy = dy / length

        proj_start = (cut_start.x - wall.start.x) * ux + (cut_start.y - wall.start.y) * uy
        proj_end = (cut_end.x - wall.start.x) * ux + (cut_end.y - wall.start.y) * uy

        offset = min(proj_start, proj_end)
        door_width = abs(proj_end - proj_start)

        offset = max(0.0, min(offset, length - door_width))

        return place_door_on_wall(
            wall=wall,
            offset=offset,
            door_width=door_width
        )

    door_placements: list[DoorPlacement] = []
    door_geometry_placements: list[DoorPlacement] = []
    window_segments: list[tuple[Point, Point]] = []

    def add_shared_door(
        room_wall: WallSegment,
        corridor_wall: WallSegment,
        cut_start: Point,
        cut_end: Point,
        hinge: str | None = None
    ):
        room_door = place_between(room_wall, cut_start, cut_end)
        if hinge is not None:
            room_door.door.hinge = hinge
        corridor_door = place_between(corridor_wall, cut_start, cut_end)

        door_placements.append(room_door)
        door_placements.append(corridor_door)
        door_geometry_placements.append(room_door)

    def add_window(wall: WallSegment, cut_start: Point, cut_end: Point):
        window_opening = place_between(wall, cut_start, cut_end)
        door_placements.append(window_opening)
        window_segments.append((cut_start, cut_end))

    segments_by_room = room_segments

    corridor_left = segments_by_room["Corridor"][3]
    corridor_right = segments_by_room["Corridor"][1]
    corridor_bottom = segments_by_room["Corridor"][0]

    # Entrance (main door) - on corridor bottom wall (boundary)
    entrance_start = Point(x=10.4, y=0)
    entrance_end = Point(x=11.4, y=0)
    entrance_door = place_between(corridor_bottom, entrance_start, entrance_end)
    door_placements.append(entrance_door)
    door_geometry_placements.append(entrance_door)

    # Living Room ↔ Corridor
    add_shared_door(
        room_wall=segments_by_room["Living Room"][1],
        corridor_wall=corridor_left,
        cut_start=Point(x=10, y=2),
        cut_end=Point(x=10, y=3)
    )

    # Kitchen ↔ Living Room (internal)
    kitchen_bottom = segments_by_room["Kitchen"][0]
    living_top = segments_by_room["Living Room"][2]
    kitchen_start = Point(x=2, y=8)
    kitchen_end = Point(x=3.0, y=8)
    kitchen_door = place_between(kitchen_bottom, kitchen_start, kitchen_end)
    living_kitchen_door = place_between(living_top, kitchen_start, kitchen_end)
    door_placements.extend([kitchen_door, living_kitchen_door])
    door_geometry_placements.append(kitchen_door)

    # Bathroom ↔ Corridor
    add_shared_door(
        room_wall=segments_by_room["Bathroom"][1],
        corridor_wall=corridor_left,
        cut_start=Point(x=10, y=9),
        cut_end=Point(x=10, y=9.8)
    )

    # Stairs ↔ Corridor
    add_shared_door(
        room_wall=segments_by_room["Stairs"][3],
        corridor_wall=corridor_right,
        cut_start=Point(x=12, y=1.2),
        cut_end=Point(x=12, y=2.2),
        hinge="right"
    )

    # Bedroom 1 ↔ Stairs
    add_shared_door(
        room_wall=segments_by_room["Bedroom 1"][3],
        corridor_wall=segments_by_room["Stairs"][1],
        cut_start=Point(x=16, y=1.5),
        cut_end=Point(x=16, y=2.5),
        hinge="right"
    )

    # Bedrooms ↔ Corridor
    add_shared_door(
        room_wall=segments_by_room["Bedroom 2"][3],
        corridor_wall=corridor_right,
        cut_start=Point(x=12, y=6.2),
        cut_end=Point(x=12, y=7.2),
        hinge="right"
    )
    add_shared_door(
        room_wall=segments_by_room["Bedroom 3"][3],
        corridor_wall=corridor_right,
        cut_start=Point(x=12, y=11.2),
        cut_end=Point(x=12, y=12.2),
        hinge="right"
    )

    # Windows (exterior walls)
    add_window(
        wall=segments_by_room["Living Room"][3],
        cut_start=Point(x=0, y=3),
        cut_end=Point(x=0, y=4.5)
    )
    add_window(
        wall=segments_by_room["Kitchen"][2],
        cut_start=Point(x=1, y=14),
        cut_end=Point(x=2.5, y=14)
    )
    add_window(
        wall=segments_by_room["Bathroom"][2],
        cut_start=Point(x=7, y=14),
        cut_end=Point(x=8, y=14)
    )
    add_window(
        wall=segments_by_room["Bedroom 1"][0],
        cut_start=Point(x=19, y=0),
        cut_end=Point(x=20.5, y=0)
    )
    add_window(
        wall=segments_by_room["Bedroom 2"][1],
        cut_start=Point(x=24, y=6.5),
        cut_end=Point(x=24, y=8.0)
    )
    add_window(
        wall=segments_by_room["Bedroom 3"][1],
        cut_start=Point(x=24, y=11.5),
        cut_end=Point(x=24, y=12.8)
    )

    for placement in door_placements:
        wall_manager.add_door_placement(placement)

    print(f"✓ Placed {len(door_geometry_placements)} doors (geometry)")
    print(f"✓ Registered {len(door_placements)} wall cuts")
    
    # ========================================================================
    # STAGE 4: CUT WALLS
    # ========================================================================
    print("\n✂️  STAGE 4: Wall Cutting")
    print("-" * 70)
    
    final_wall_segments = wall_manager.process_cuts()
    print(f"✓ Total wall segments after cutting: {len(final_wall_segments)}")
    print(f"  (Original: {len(rooms) * 4} walls = {len(rooms)} rooms × 4 walls)")
    print(f"  (After cutting: {len(rooms) * 4} + {len(door_placements)} cuts = {len(final_wall_segments)} segments)")

    # Cut boundary for doors that touch the outer perimeter
    boundary_segments = generate_boundary_segments(boundary)
    boundary_manager = WallCutManager()
    boundary_manager.add_wall_segments(boundary_segments)
    for placement in _boundary_door_placements(boundary_segments, door_placements):
        boundary_manager.add_door_placement(placement)
    final_boundary_segments = boundary_manager.process_cuts()
    print(f"✓ Boundary segments after cutting: {len(final_boundary_segments)}")
    
    # ========================================================================
    # STAGE 5: COMPUTE DOOR GEOMETRY
    # ========================================================================
    print("\n📐 STAGE 5: Door Geometry Calculation")
    print("-" * 70)
    
    door_geometries = []
    
    for i, placement in enumerate(door_geometry_placements):
        geom = compute_door_geometry(placement)
        door_geometries.append(geom)
        print(f"✓ Door {i+1}:")
        print(f"  Hinge: ({geom.hinge_point.x:.2f}, {geom.hinge_point.y:.2f})")
        print(f"  Leaf end: ({geom.leaf_end_point.x:.2f}, {geom.leaf_end_point.y:.2f})")
        print(f"  Swing: {geom.swing_start_angle:.1f}° → {geom.swing_end_angle:.1f}°")
    
    # ========================================================================
    # STAGE 6: RENDER DXF
    # ========================================================================
    print("\n🎨 STAGE 6: DXF Rendering")
    print("-" * 70)
    
    renderer = DXFRoomRenderer()
    
    # Draw boundary (with door gaps where applicable)
    renderer.draw_boundary_segments(final_boundary_segments)
    print("✓ Drew boundary segments")

    # Draw all wall segments (gaps are natural from cutting)
    renderer.draw_wall_segments(final_wall_segments)
    print(f"✓ Drew {len(final_wall_segments)} wall segments")

    # Draw windows
    for start, end in window_segments:
        renderer.draw_window_segment(start, end)
    print(f"✓ Drew {len(window_segments)} windows")
    
    # Draw doors (leaf + arc)
    for geom in door_geometries:
        renderer.draw_door_geometry(geom)
    print(f"✓ Drew {len(door_geometries)} doors (leaf + swing arc)")
    
    # Draw labels and dimensions
    for room in agent.placed_rooms:
        renderer.draw_room_label(room)
        renderer.draw_room_dimensions(room)
    print(f"✓ Drew labels and dimensions for {len(agent.placed_rooms)} rooms")

    for room in agent.placed_rooms:
        if room.name == "Stairs" and room.origin is not None:
            renderer.draw_stairs(room.origin, room.width, room.height)
            print("✓ Drew stairs")
    
    # Save
    file_path = renderer.save()
    
    # ========================================================================
    # SUCCESS
    # ========================================================================
    print("\n" + "=" * 70)
    print("✅ SUCCESS - BASELINE TEST PASSED")
    print("=" * 70)
    print(f"\n📁 DXF file: {file_path}")
    print("\n🔍 What you should see in the DXF:")
    print(f"   ✓ {len(rooms)} rooms with clean outlines")
    print("   ✓ Each room has 4 walls with proper door gaps")
    print("   ✓ Doors connect to corridor / adjacent rooms")
    print("   ✓ Door leaf lines at each gap")
    print("   ✓ Windows placed on exterior walls")
    print("   ✓ 90° swing arcs from hinge points")
    print("   ✓ Room names and dimensions centered")
    print("\n💡 Tip: Open in AutoCAD, LibreCAD, or any DXF viewer")
    print("=" * 70)


if __name__ == "__main__":
    main()
