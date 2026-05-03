# 06_interaction_overview_diagram (نظرة شاملة لتفاعلات المسارات الأساسية) — CadArena

## الغرض
يقدم هذا المخطط نظرة عالية المستوى لمسارات التفاعل المختلفة في CadArena، مع ربط كل مسار بتفاعل تفصيلي محدد.

## المخطط

```mermaid
flowchart TD
    START["طلب من الواجهة"] --> CHOICE{"ما نوع المسار؟"}

    CHOICE -->|"تحليل فقط"| PARSE_ONLY["/api/v1/parse-design"]
    CHOICE -->|"تحليل + DXF"| PARSE_DXF["/api/v1/parse-design-generate-dxf"]
    CHOICE -->|"Workspace"| WORKSPACE["/api/v1/workspace/.../generate-dxf"]
    CHOICE -->|"تصدير/معاينة"| EXPORT["/api/v1/dxf/*"]
    CHOICE -->|"تواصل"| CONTACT["/api/v1/contact/send-email"]

    PARSE_ONLY --> PARSE_CORE["PromptCompiler → Provider → OutputParser"]
    PARSE_CORE --> PARSE_VALIDATE["ExtractedIntentValidator → IntentValidator"]
    PARSE_VALIDATE --> PARSE_ONLY_RETURN["JSON Intent"]

    PARSE_DXF --> PARSE_CORE_2["PromptCompiler → Provider → OutputParser"]
    PARSE_CORE_2 --> PLAN_2["DeterministicLayoutPlanner → OpeningPlanner"]
    PLAN_2 --> DXF_2["generate_dxf_from_intent"]
    DXF_2 --> PARSE_DXF_RETURN["JSON + dxf_path"]

    WORKSPACE --> PERSIST["workspace_storage.add_message"]
    PERSIST --> PLAN_3["parse_design_prompt_with_metadata"]
    PLAN_3 --> DXF_3["generate_dxf_from_intent"]
    DXF_3 --> WORKSPACE_RETURN["JSON + messages"]

    EXPORT --> EXPORTER["dxf_exporter.export_dxf_file"]
    EXPORTER --> FILE_RESPONSE["DXF/PNG/PDF"]

    CONTACT --> SMTP["contact_email_service.send_contact_email"]
```

## ملاحظات معمارية
- تفاعل parse-only يعيد JSON منظم بدون توليد DXF، ما يسمح باستعماله في أدوات خارجية.
- مسار workspace يضيف طبقة حفظ الرسائل والمشاريع قبل وبعد التحليل لضمان الاستمرارية.
- مسار التصدير يستخدم dxf_exporter مع `resolve_output_path` لضمان الوصول الآمن للملفات.
