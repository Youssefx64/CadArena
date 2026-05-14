# 12 Object Diagram - Runtime Snapshot During DXF Generation - CadArena

## Purpose
This object diagram shows a representative runtime snapshot after the parser has produced a validated layout and before the backend returns a workspace generation response.

## Diagram

```mermaid
classDiagram
    class WorkspaceRequest {
        <<WorkspaceGenerateDxfRequest>>
        user_id = guest_or_authenticated_user
        project_id = project_abc123
        model = ollama_cloud
        recovery_mode = repair
    }

    class Project {
        <<ProjectRecord>>
        id = project_abc123
        name = Apartment Concept
        message_count = 4
    }

    class ParsedIntent {
        <<ParsedDesignIntent>>
        boundary = 12m by 8m
        rooms_count = 4
        walls_count = 16
        openings_count = 5
    }

    class Metrics {
        <<LayoutMetrics>>
        selected_topology = horizontal_public_private
        total_score = 0.86
        efficiency = 0.82
    }

    class LivingRoom {
        <<RoomIntent>>
        name = Living Room
        room_type = living
        width = 4.8
        height = 3.2
        origin = 0_0
    }

    class Kitchen {
        <<RoomIntent>>
        name = Kitchen
        room_type = kitchen
        width = 2.8
        height = 3.2
        origin = 4.8_0
    }

    class Bedroom {
        <<RoomIntent>>
        name = Bedroom 1
        room_type = bedroom
        width = 4.0
        height = 3.0
        origin = 0_3.2
    }

    class Bathroom {
        <<RoomIntent>>
        name = Bathroom
        room_type = bathroom
        width = 2.4
        height = 2.2
        origin = 4.0_3.2
    }

    class MainDoor {
        <<OpeningIntent>>
        type = door
        room_name = Living Room
        wall = bottom
        hinge = left
        swing = in
    }

    class DesignIntentObject {
        <<DesignIntent>>
        boundary = BoundaryIntent
        rooms = 4
        openings = 5
    }

    class Planner {
        <<PlannerAgent>>
        boundary = 12m by 8m
        placed_rooms = 4
    }

    class WallManager {
        <<WallCutManager>>
        wall_segments = 16
        cut_segments = 5
    }

    class Renderer {
        <<DXFRoomRenderer>>
        layers = WALLS, DOORS, WINDOWS, ROOM_LABELS, DIMENSIONS, FURNITURE
    }

    class DxfFile {
        <<Path>>
        location = backend/output/dxf/generated_file.dxf
    }

    class FileToken {
        <<Workspace file token>>
        token = opaque_browser_token
        owner = guest_or_authenticated_user
    }

    class AssistantMessage {
        <<ChatMessageRecord>>
        role = assistant
        dxf_name = apartment_concept_timestamp.dxf
        file_token = opaque_browser_token
    }

    WorkspaceRequest --> Project : "targets"
    Project --> AssistantMessage : "stores"
    ParsedIntent --> Metrics : "quality"
    ParsedIntent --> LivingRoom : "rooms[0]"
    ParsedIntent --> Kitchen : "rooms[1]"
    ParsedIntent --> Bedroom : "rooms[2]"
    ParsedIntent --> Bathroom : "rooms[3]"
    ParsedIntent --> MainDoor : "openings[0]"
    ParsedIntent --> DesignIntentObject : "converted for DXF"
    DesignIntentObject --> Planner : "validated and placed"
    Planner --> WallManager : "room and boundary walls"
    WallManager --> Renderer : "final wall segments"
    Renderer --> DxfFile : "save"
    DxfFile --> FileToken : "registered"
    FileToken --> AssistantMessage : "returned to UI"
```

## Architectural Notes
- The parser-facing `ParsedDesignIntent` includes explicit walls and metrics; the renderer-facing `DesignIntent` uses only boundary, rooms, and openings.
- `PlannerAgent` still validates placement even when the parser has already produced explicit room origins.
- `WallCutManager` owns the final wall gaps for doors and windows before `DXFRoomRenderer` writes CAD layers.
- The stored assistant message keeps user-facing file metadata and a token, not the raw absolute path.
