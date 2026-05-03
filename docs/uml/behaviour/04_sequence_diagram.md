# 04_sequence_diagram (تسلسل توليد DXF من محادثة workspace) — CadArena

## الغرض
يوضح هذا المخطط التسلسلي التفاعل التفصيلي بين الواجهة وخدمات التحليل والتخطيط والرسم عند إنشاء DXF من داخل مساحة العمل.

## المخطط

```mermaid
sequenceDiagram
    actor User
    participant Frontend
    participant WorkspaceRouter
    participant WorkspaceStorage
    participant ParserService
    participant Orchestrator
    participant Provider
    participant OutputParser
    participant ExtractValidator
    participant LayoutPlanner
    participant OpeningPlanner
    participant IntentValidator
    participant LayoutValidator
    participant DXFPipeline
    participant DesignIntentValidator
    participant PlannerAgent
    participant WallCutManager
    participant DXFRoomRenderer
    participant FileSystem

    User->>Frontend: "إدخال وصف معماري"
    Frontend->>WorkspaceRouter: "POST /api/v1/workspace/.../generate-dxf"
    WorkspaceRouter->>WorkspaceStorage: "add_message(role=user)"
    WorkspaceRouter->>ParserService: "parse_design_prompt_with_metadata"
    ParserService->>Orchestrator: "parse"
    Orchestrator->>Provider: "generate(compiled_prompt)"
    Provider-->>Orchestrator: "raw_output"
    Orchestrator->>OutputParser: "parse(raw_output)"
    Orchestrator->>ExtractValidator: "validate(extracted_payload)"
    Orchestrator->>LayoutPlanner: "plan_with_metadata"
    Orchestrator->>OpeningPlanner: "plan"
    Orchestrator->>IntentValidator: "validate(planned_payload)"
    Orchestrator->>LayoutValidator: "validate(metrics)"
    ParserService-->>WorkspaceRouter: "result(data, metrics)"
    WorkspaceRouter->>DXFPipeline: "generate_dxf_from_intent"
    DXFPipeline->>DesignIntentValidator: "validate(intent)"
    DXFPipeline->>PlannerAgent: "place_room / place_room_with_rules"
    DXFPipeline->>WallCutManager: "add_wall_segments + process_cuts"
    DXFPipeline->>DXFRoomRenderer: "draw and save"
    DXFRoomRenderer->>FileSystem: "save -> backend/output/dxf"
    WorkspaceRouter->>WorkspaceStorage: "add_message(role=assistant, dxf_path)"
    WorkspaceRouter-->>Frontend: "200 + dxf_path + metrics + messages"
    Frontend-->>User: "عرض رابط التحميل/المعاينة"

    alt "فشل التحليل أو القواعد"
        WorkspaceRouter-->>Frontend: "ParseDesignErrorResponse"
        WorkspaceRouter->>WorkspaceStorage: "add_message(role=error)"
    else "فشل توليد DXF"
        WorkspaceRouter-->>Frontend: "422 GENERATE_DXF_FAILED"
        WorkspaceRouter->>WorkspaceStorage: "add_message(role=error)"
    end
```

## ملاحظات معمارية
- مسار workspace يضيف رسائل المستخدم والمساعد إلى قاعدة بيانات SQLite لتأمين سجل المحادثة حتى عند الإخفاق.
- التحليل يمر بعدة طبقات تحقق قبل الوصول إلى توليد DXF لمنع إدخال هندسي غير صالح إلى خط الرسم.
- توليد DXF يعمل في threadpool لتجنب حجب حلقة الحدث داخل FastAPI.
