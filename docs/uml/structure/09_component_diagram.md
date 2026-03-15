# 09_component_diagram (المكوّنات الرئيسية والاعتماديات) — CadArena

## الغرض
يوضح هذا المخطط المكوّنات الأساسية في CadArena وكيف تتبادل البيانات مع بعضها ومع الأنظمة الخارجية.

## المخطط

```mermaid
flowchart LR
    subgraph CLIENT["متصفح المستخدم"]
        FE["Frontend HTML/CSS/JS\n(frontend/)"]
    end

    subgraph API["FastAPI App (backend/app/main.py)"]
        ROUTERS["Routers (design_parser, workspace, auth, profile, contact, api/v1)"]
        SERVICES["Services (design_parser_service, auth_storage, workspace_storage, contact_email_service, dxf_exporter)"]
        PIPELINE["Pipeline (intent_to_agent, draw_pipeline)"]
        DOMAIN["Domain (planner, constraints, architecture, geometry)"]
        SCHEMAS["Schemas + Models (Pydantic)"]
        UTILS["core/ + utils/"]
    end

    subgraph STORAGE["Storage"]
        SQLITE[("workspace.db")]
        OUTPUT[("backend/output/*")]
    end

    subgraph EXTERNAL["External Systems"]
        OLLAMA["Ollama API"]
        HF["HuggingFace Transformers"]
        SMTP["SMTP Server"]
        MATPLOTLIB["matplotlib"]
        EZDXF["ezdxf"]
    end

    FE -->|HTTP| ROUTERS
    ROUTERS --> SERVICES
    ROUTERS --> PIPELINE
    ROUTERS --> SCHEMAS

    SERVICES --> DOMAIN
    SERVICES --> UTILS
    SERVICES --> SQLITE
    SERVICES --> OUTPUT
    SERVICES --> OLLAMA
    SERVICES --> HF
    SERVICES --> SMTP

    PIPELINE --> DOMAIN
    PIPELINE --> SCHEMAS
    PIPELINE --> EZDXF
    SERVICES --> MATPLOTLIB
```
<!-- VALIDATED: no <<>> inline, no Arabic outside quotes, no reserved keywords as IDs -->

## ملاحظات معمارية
- الواجهة الأمامية ثابتة وتُخدم مباشرة عبر FastAPI دون بناء، لذلك تعتمد كل الواجهات على المسارات HTTP نفسها.
- الاعتماد على `ezdxf` داخل خط الرسم يجعل توليد DXF محلياً ومحدداً بإصدارات المكتبة.
- التصدير إلى PDF/PNG يمر عبر `matplotlib` مع مسار بديل في حال غياب الاعتماديات.
