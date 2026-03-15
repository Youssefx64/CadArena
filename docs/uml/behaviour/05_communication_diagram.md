# 05_communication_diagram (تبادل الرسائل بين مكوّنات التوليد) — CadArena

## الغرض
يبرز هذا المخطط عناصر التفاعل الأساسية والرسائل المتبادلة بينها عند تنفيذ توليد DXF في مسار workspace.

## المخطط

```mermaid
flowchart LR
    Frontend["Frontend app.js"]
    WorkspaceRouter["workspace router"]
    WorkspaceStorage[("workspace.db")]
    Parser["DesignParseOrchestrator"]
    Provider["ProviderClient (Ollama/HF)"]
    OutputParser["OutputParser"]
    LayoutPlanner["DeterministicLayoutPlanner"]
    OpeningPlanner["DeterministicOpeningPlanner"]
    IntentValidator["IntentValidator"]
    LayoutValidator["LayoutValidator"]
    DXFPipeline["generate_dxf_from_intent"]
    RoomRenderer["DXFRoomRenderer"]
    Files[("backend/output")]

    Frontend -->|"1: POST /workspace/.../generate-dxf"| WorkspaceRouter
    WorkspaceRouter -->|"2: add_message(user)"| WorkspaceStorage
    WorkspaceRouter -->|"3: parse_design_prompt_with_metadata"| Parser
    Parser -->|"3.1: generate"| Provider
    Parser -->|"3.2: parse"| OutputParser
    Parser -->|"3.3: plan"| LayoutPlanner
    Parser -->|"3.4: openings"| OpeningPlanner
    Parser -->|"3.5: validate"| IntentValidator
    Parser -->|"3.6: metrics"| LayoutValidator
    WorkspaceRouter -->|"4: generate_dxf_from_intent"| DXFPipeline
    DXFPipeline -->|"4.1: render"| RoomRenderer
    RoomRenderer -->|"4.2: save"| Files
    WorkspaceRouter -->|"5: add_message(assistant)"| WorkspaceStorage
    WorkspaceRouter -->|"6: response"| Frontend
```
<!-- VALIDATED: no <<>> inline, no Arabic outside quotes, no reserved keywords as IDs -->

## ملاحظات معمارية
- التواصل مركزي عبر `workspace_generate_dxf` الذي ينسق كل المكونات دون أن يكشف تفاصيل داخلية للواجهة.
- DesignParseOrchestrator يجمع التخطيط والتحقق ضمن نقطة واحدة لتقليل التشتت بين الخدمات.
- تخزين الملفات منفصل عن التخزين النصي للمحادثات لتبسيط التحكم في الأمان والمسارات.
