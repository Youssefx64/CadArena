# 01_activity_diagram (تدفق تحويل الوصف إلى DXF) — CadArena

## الغرض
يوضح هذا المخطط النشاطي المسار التشغيلي الكامل لتحويل وصف المستخدم النصي إلى ملف DXF عبر خدمات التحليل والتخطيط والرسم في CadArena.

## المخطط

```mermaid
flowchart TD
    BEGIN_NODE(["بدء الطلب"]) --> PROMPT_NODE["Frontend: إدخال وصف معماري"]
    PROMPT_NODE --> API_NODE["POST /api/v1/parse-design-generate-dxf"]
    API_NODE --> ROUTER_NODE["design_parser.parse_design_generate_dxf"]
    ROUTER_NODE --> PARSE_SVC_NODE["design_parser_service.parse_design_prompt_with_metadata"]
    PARSE_SVC_NODE --> ORCH_NODE["DesignParseOrchestrator.parse"]
    ORCH_NODE --> COMPILE_NODE["PromptCompiler.compile"]
    COMPILE_NODE --> PROVIDER_NODE{"المزوّد المختار؟"}
    PROVIDER_NODE -->|Ollama| OLLAMA_NODE["OllamaProviderClient.generate"]
    PROVIDER_NODE -->|HuggingFace| HF_NODE["HuggingFaceProviderClient.generate"]
    OLLAMA_NODE --> RAW_NODE["raw_output"]
    HF_NODE --> RAW_NODE
    RAW_NODE --> OUTPUT_PARSE_NODE["OutputParser.parse"]
    OUTPUT_PARSE_NODE --> EXTRACT_VALIDATE_NODE["ExtractedIntentValidator.validate"]
    EXTRACT_VALIDATE_NODE --> LAYOUT_PLAN_NODE["DeterministicLayoutPlanner.plan_with_metadata"]
    LAYOUT_PLAN_NODE --> OPENING_PLAN_NODE["DeterministicOpeningPlanner.plan"]
    OPENING_PLAN_NODE --> INTENT_VALIDATE_NODE["IntentValidator.validate"]
    INTENT_VALIDATE_NODE --> LAYOUT_VALIDATE_NODE["LayoutValidator.validate"]
    LAYOUT_VALIDATE_NODE --> INTENT_MODEL_NODE["DesignIntent.model_validate"]
    INTENT_MODEL_NODE --> DXF_PIPELINE_NODE["generate_dxf_from_intent"]
    DXF_PIPELINE_NODE --> DXF_VALIDATE_NODE["DesignIntentValidator.validate"]
    DXF_VALIDATE_NODE --> PLACE_ROOMS_NODE["PlannerAgent.place_room/with_rules"]
    PLACE_ROOMS_NODE --> WALLS_NODE["generate_wall_segments + WallCutManager.process_cuts"]
    WALLS_NODE --> RENDER_NODE["DXFRoomRenderer.draw_*"]
    RENDER_NODE --> SAVE_NODE["DXFRoomRenderer.save -> backend/output/dxf"]
    SAVE_NODE --> RESPONSE_NODE["200 + dxf_path"]

    OUTPUT_PARSE_NODE -->|"JSON غير صالح"| ERROR_NODE["ParseDesignErrorResponse"]
    EXTRACT_VALIDATE_NODE -->|ValidationError| ERROR_NODE
    LAYOUT_PLAN_NODE -->|LayoutPlanningError| ERROR_NODE
    OPENING_PLAN_NODE -->|RuleViolationError| ERROR_NODE
    INTENT_VALIDATE_NODE -->|ValidationError| ERROR_NODE
    LAYOUT_VALIDATE_NODE -->|RuleViolationError| ERROR_NODE
    DXF_PIPELINE_NODE -->|RuntimeError/ValueError| ERROR_NODE
```
<!-- VALIDATED: no <<>> inline, no Arabic outside quotes, no reserved keywords as IDs -->

## ملاحظات معمارية
- فصل مسار التحليل (DesignParseOrchestrator) عن مسار الرسم (generate_dxf_from_intent) يقلل التداخل ويبسّط الاختبار.
- التحقق المتكرر (IntentValidator وLayoutValidator وDesignIntentValidator) يحمي خط الرسم من المدخلات غير الصالحة.
- التخطيط الحتمي للأبواب والجدران يعتمد على نفس هندسة الغرف لضمان اتساق القطع قبل الرسم.
