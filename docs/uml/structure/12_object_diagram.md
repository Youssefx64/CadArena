# Object Diagram (لقطة كائنات أثناء توليد DXF) — CadArena

## الغرض
يعرض لقطة آنية لكائنات فعلية أثناء معالجة طلب توليد DXF، مع قيم نموذجية مشتقة من مسار التنفيذ الحقيقي.

## المخطط
```mermaid
classDiagram
    class Intent {
        <<DesignIntent>>
        boundary_width = 12
        boundary_height = 8
        rooms_count = 2
        openings_count = 1
    }

    class RoomIntentA {
        <<RoomIntent>>
        name = Living Room
        room_type = living
        width = 4
        height = 3
        origin = null
    }

    class RoomIntentB {
        <<RoomIntent>>
        name = Bedroom 1
        room_type = bedroom
        width = 3
        height = 3
        origin = null
    }

    class Boundary {
        <<RectangleGeometry>>
        width = 12
        height = 8
        origin = 0_0
    }

    class Planner {
        <<PlannerAgent>>
    }

    class RoomA {
        <<Room>>
        name = Living Room
        width = 4
        height = 3
        origin = 0_0
    }

    class RoomB {
        <<Room>>
        name = Bedroom 1
        width = 3
        height = 3
        origin = 4_0
    }

    class Wall0 {
        <<WallSegment>>
        start = 0_0
        end = 4_0
    }

    class DoorSpec {
        <<DoorSpec>>
        width = 1.0
        hinge = left
        swing = in
        angle = 90
    }

    class Placement {
        <<DoorPlacement>>
        offset = 1.5
    }

    class DoorGeom {
        <<DoorGeometry>>
        swing_radius = 1.0
    }

    class Renderer {
        <<DXFRoomRenderer>>
    }

    Intent --> RoomIntentA : "rooms[0]"
    Intent --> RoomIntentB : "rooms[1]"

    Planner --> Boundary : "boundary"
    Planner --> RoomA : "placed_rooms[0]"
    Planner --> RoomB : "placed_rooms[1]"

    Placement --> Wall0 : "wall"
    Placement --> DoorSpec : "door"
    DoorGeom ..> Placement : "from"
    Renderer ..> DoorGeom : "renders"
```

## ملاحظات معمارية
- `RoomIntent` تمثل المدخلات، بينما `Room` تمثل الكيانات الموضوعة بعد التخطيط داخل `PlannerAgent`.
- `DoorPlacement` يربط الباب بجدار محدد عبر `WallSegment` قبل حساب `DoorGeometry`.
- قيم الأصول في المثال تتوافق مع منطق التخطيط الشبكي في `PlannerAgent`.