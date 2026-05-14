# 06 Interaction Overview Diagram - Main Runtime Flows - CadArena

## Purpose
This interaction overview links the main user-visible routes to the backend workflows that implement them.

## Diagram

```mermaid
flowchart TD
    START["Browser or Studio request"] --> ROUTE_CHOICE{"Route group"}

    ROUTE_CHOICE -->|"Public React route"| REACT_ROUTE["/, /studio, /viewer, /community, /generate, /models, /metrics, /about, /developers, /docs"]
    REACT_ROUTE --> STATIC_SERVING["FastAPI serves frontend/build or frontend/public assets"]
    STATIC_SERVING --> REACT_DONE["Page rendered in browser"]

    ROUTE_CHOICE -->|"Auth and profile"| AUTH_FLOW["/api/v1/auth/* and /api/v1/profile/*"]
    AUTH_FLOW --> AUTH_STORAGE["auth_storage: users, JWT cookies, profiles, provider keys, avatars"]
    AUTH_STORAGE --> AUTH_DONE["Current user or profile response"]

    ROUTE_CHOICE -->|"Community"| COMMUNITY_FLOW["/api/v1/community/questions and answers"]
    COMMUNITY_FLOW --> COMMUNITY_STORAGE["community_storage: questions, answers, votes, views"]
    COMMUNITY_STORAGE --> COMMUNITY_DONE["Q&A response"]

    ROUTE_CHOICE -->|"Parse only"| PARSE_ONLY["POST /api/v1/parse-design"]
    PARSE_ONLY --> PARSE_CORE["PromptCompiler, ProviderClient, OutputParser"]
    PARSE_CORE --> PARSE_PLAN["ExtractedIntentValidator, LayoutPlanner, OpeningPlanner, LayoutValidator"]
    PARSE_PLAN --> PARSE_DONE["ParsedDesignIntent and LayoutMetrics"]

    ROUTE_CHOICE -->|"Parse and generate"| PARSE_DXF["POST /api/v1/parse-design-generate-dxf"]
    PARSE_DXF --> PARSE_CORE_2["Parser service"]
    PARSE_CORE_2 --> DXF_CORE_2["generate_dxf_from_intent"]
    DXF_CORE_2 --> PARSE_DXF_DONE["Parsed layout and dxf_path"]

    ROUTE_CHOICE -->|"Workspace generate"| WORKSPACE_GENERATE["POST /api/v1/workspace/.../generate-dxf or /workspace/me/.../generate-dxf"]
    WORKSPACE_GENERATE --> WORKSPACE_PERSIST["Persist user message and resolve model"]
    WORKSPACE_PERSIST --> WORKSPACE_PARSE["Parser service with layout retry"]
    WORKSPACE_PARSE --> WORKSPACE_DXF["DXF pipeline and workspace file token"]
    WORKSPACE_DXF --> WORKSPACE_DONE["Layout, suggestions, metrics, messages, file_token"]

    ROUTE_CHOICE -->|"Workspace iterate"| WORKSPACE_ITERATE["POST /api/v1/workspace/{project_id}/iterate or /workspace/me/projects/{project_id}/iterate"]
    WORKSPACE_ITERATE --> ITERATIVE_CORE["run_iterative_design with LayoutPatcher or full parse fallback"]
    ITERATIVE_CORE --> ITERATIVE_DXF["Optional DXF preview token"]
    ITERATIVE_DXF --> ITERATIVE_DONE["Updated layout, changed rooms, suggestions"]

    ROUTE_CHOICE -->|"DXF file operations"| DXF_ROUTES["/api/v1/generate-dxf and /api/v1/dxf/*"]
    DXF_ROUTES --> TOKEN_CHECK["Resolve or issue file token"]
    TOKEN_CHECK --> EXPORTER["dxf_exporter: DXF, PNG, PDF, preview"]
    EXPORTER --> DXF_DONE["FileResponse or token payload"]

    ROUTE_CHOICE -->|"Contact"| CONTACT_FLOW["POST /api/v1/contact/send-email"]
    CONTACT_FLOW --> SMTP_FLOW["contact_email_service sends SMTP email"]
    SMTP_FLOW --> CONTACT_DONE["Contact success or 503 error"]

    REACT_DONE --> END["End"]
    AUTH_DONE --> END
    COMMUNITY_DONE --> END
    PARSE_DONE --> END
    PARSE_DXF_DONE --> END
    WORKSPACE_DONE --> END
    ITERATIVE_DONE --> END
    DXF_DONE --> END
    CONTACT_DONE --> END
```

## Architectural Notes
- The same parser core powers the standalone parse routes, workspace generation, and iterative full-parse fallback.
- Workspace generation adds project/message persistence and tokenized file access around the parser and DXF pipeline.
- DXF file operations are isolated under `/api/v1/dxf/*`, which keeps upload, preview, download, and export behavior consistent across Studio and Viewer.
- The backend also serves the frontend when a production build exists, while still supporting public assets and the embedded Studio app in development.
