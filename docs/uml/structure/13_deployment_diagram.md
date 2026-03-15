# 13_deployment_diagram (نشر المكوّنات وبيئات التشغيل) — CadArena

## الغرض
يوضح هذا المخطط مواقع تشغيل المكونات الأساسية في CadArena وعلاقات الاتصال بينها أثناء التشغيل الفعلي.

## المخطط

```mermaid
flowchart LR
    subgraph CLIENT["Client Device"]
        BROWSER["Browser + Frontend HTML/JS"]
    end

    subgraph SERVER["Backend Host"]
        FASTAPI["FastAPI app (app.main)"]
        PARSER_SVC["Design Parser Service (DesignParseOrchestrator)"]
        DXF_PIPELINE["DXF Pipeline (intent_to_agent)"]
        OUTPUT_FS[("backend/output/")]
        DB[("SQLite workspace.db")]
        HF_LOCAL["HuggingFace model (local transformers)"]
    end

    subgraph EXTERNAL["External Services"]
        OLLAMA_API["Ollama API http://localhost:11434"]
        SMTP_SERVER["SMTP Server"]
    end

    BROWSER -->|HTTP| FASTAPI
    FASTAPI --> PARSER_SVC
    FASTAPI --> DXF_PIPELINE
    FASTAPI --> DB
    FASTAPI --> OUTPUT_FS

    PARSER_SVC --> HF_LOCAL
    PARSER_SVC --> OLLAMA_API

    FASTAPI --> SMTP_SERVER
    DXF_PIPELINE --> OUTPUT_FS
```
<!-- VALIDATED: no <<>> inline, no Arabic outside quotes, no reserved keywords as IDs -->

## ملاحظات معمارية
- مزود Ollama يُستدعى عبر HTTP بينما مزود HuggingFace يعمل محلياً داخل نفس المضيف عبر مكتبات Python.
- الملفات الناتجة تحفظ على نظام الملفات المحلي وتُخدم لاحقاً عبر مسارات `/api/v1/dxf/*`.
- قاعدة بيانات SQLite مدمجة ضمن نفس المضيف وتستخدمها وحدات `auth_storage` و`workspace_storage`.
