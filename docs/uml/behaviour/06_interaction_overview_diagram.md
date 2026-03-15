# 06_interaction_overview_diagram (نظرة شاملة لتفاعلات المسارات الأساسية) — CadArena

## الغرض
يقدم هذا المخطط نظرة عالية المستوى لمسارات التفاعل المختلفة في CadArena، مع ربط كل مسار بتفاعل تفصيلي محدد.

## المخطط

```mermaid
flowchart TD
    BEGIN_NODE(["طلب من الواجهة"]) --> CHOICE_NODE{"ما نوع المسار؟"}

    CHOICE_NODE -->|"تحليل فقط"| PARSE_ONLY_NODE[["Interaction: /api/v1/parse-design"]]
    CHOICE_NODE -->|"تحليل + DXF"| PARSE_DXF_NODE[["Interaction: /api/v1/parse-design-generate-dxf"]]
    CHOICE_NODE -->|"Workspace"| WORKSPACE_NODE[["Interaction: /api/v1/workspace/.../generate-dxf"]]
    CHOICE_NODE -->|"تصدير/معاينة"| EXPORT_NODE[["Interaction: /api/v1/dxf/*"]]
    CHOICE_NODE -->|"تواصل"| CONTACT_NODE[["Interaction: /api/v1/contact/send-email"]]

    PARSE_ONLY_NODE --> PARSE_CORE_NODE["PromptCompiler → Provider → OutputParser"]
    PARSE_CORE_NODE --> PARSE_VALIDATE_NODE["ExtractedIntentValidator → IntentValidator"]
    PARSE_VALIDATE_NODE --> PARSE_ONLY_RETURN_NODE["JSON Intent"]

    PARSE_DXF_NODE --> PARSE_CORE_NODE2["PromptCompiler → Provider → OutputParser"]
    PARSE_CORE_NODE2 --> PLAN_NODE2["DeterministicLayoutPlanner → OpeningPlanner"]
    PLAN_NODE2 --> DXF_NODE2["generate_dxf_from_intent"]
    DXF_NODE2 --> PARSE_DXF_RETURN_NODE["JSON + dxf_path"]

    WORKSPACE_NODE --> PERSIST_NODE["workspace_storage.add_message"]
    PERSIST_NODE --> PLAN_NODE3["parse_design_prompt_with_metadata"]
    PLAN_NODE3 --> DXF_NODE3["generate_dxf_from_intent"]
    DXF_NODE3 --> WORKSPACE_RETURN_NODE["JSON + messages"]

    EXPORT_NODE --> EXPORTER_NODE["dxf_exporter.export_dxf_file"]
    EXPORTER_NODE --> FILE_RESPONSE_NODE["DXF/PNG/PDF"]

    CONTACT_NODE --> SMTP_NODE["contact_email_service.send_contact_email"]
```
<!-- VALIDATED: no <<>> inline, no Arabic outside quotes, no reserved keywords as IDs -->

## ملاحظات معمارية
- تفاعل parse-only يعيد JSON منظم بدون توليد DXF، ما يسمح باستعماله في أدوات خارجية.
- مسار workspace يضيف طبقة حفظ الرسائل والمشاريع قبل وبعد التحليل لضمان الاستمرارية.
- مسار التصدير يستخدم dxf_exporter مع `resolve_output_path` لضمان الوصول الآمن للملفات.
