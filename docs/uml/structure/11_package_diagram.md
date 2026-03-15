# 11_package_diagram (تقسيم الحزم داخل المشروع) — CadArena

## الغرض
يوضح هذا المخطط تقسيم الحزم الداخلية في CadArena وتدفقات الاعتماد بين الطبقات المختلفة.

## المخطط

```mermaid
flowchart TB
    subgraph BACKEND["backend/app"]
        CORE["core/"]
        ROUTERS["routers/"]
        SERVICES["services/"]
        PIPELINE["pipeline/"]
        DOMAIN["domain/"]
        SCHEMAS["schemas/"]
        MODELS["models/"]
        UTILS["utils/"]
        API_V1["api/v1/"]
    end

    subgraph FRONTEND["frontend/"]
        PAGES["HTML pages"]
        SCRIPTS["scripts/"]
        STYLES["styles/"]
    end

    SCRIPTS --> ROUTERS

    API_V1 --> PIPELINE
    ROUTERS --> SERVICES
    ROUTERS --> PIPELINE
    ROUTERS --> SCHEMAS
    ROUTERS --> MODELS

    SERVICES --> DOMAIN
    SERVICES --> UTILS
    SERVICES --> SCHEMAS

    PIPELINE --> DOMAIN
    PIPELINE --> SCHEMAS

    CORE --> ROUTERS
    CORE --> SERVICES
```
<!-- VALIDATED: no <<>> inline, no Arabic outside quotes, no reserved keywords as IDs -->

## ملاحظات معمارية
- `routers/` تبقي النقل (HTTP) منفصلاً عن المنطق وتستدعي `services/` و`pipeline/` عند الحاجة.
- `domain/` يحتوي المنطق الهندسي والقيود ويُستهلك من الخدمات وخط الرسم دون الاعتماد على FastAPI.
- الواجهة الأمامية تعتمد على المسارات التي يقدمها `routers/` وتستخدمها عبر `fetch` داخل `frontend/scripts/app.js`.
