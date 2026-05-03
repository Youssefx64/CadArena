# 13 Deployment Diagram - Runtime Topology - CadArena

## Purpose
This deployment diagram shows where CadArena components run in local or containerized development, including browser assets, FastAPI, local databases, generated files, model providers, and optional external services.

## Diagram

```mermaid
flowchart LR
    subgraph CLIENT_DEVICE["Client Device"]
        BROWSER["Web browser"]
        REACT_RUNTIME["React SPA runtime"]
        STUDIO_RUNTIME["Studio iframe runtime"]
        VIEWER_RUNTIME["DXF viewer runtime"]
    end

    subgraph BACKEND_HOST["Backend Host or Docker Container"]
        FASTAPI["FastAPI app\nbackend/app/main.py"]
        STATIC_ASSETS["frontend/build or frontend/public assets"]
        PARSER_SERVICE["Design parser service singleton"]
        DXF_PIPELINE["DXF pipeline and renderer"]
        CLEANUP_TASK["Output cleanup lifespan task"]
        SQLITE_AUTH[("auth/community/profile SQLite")]
        SQLITE_WORKSPACE[("workspace SQLite")]
        OUTPUT_DIR[("backend/output")]
        DXF_DIR[("backend/output/dxf")]
        HF_MODEL["HuggingFace local model bundle"]
    end

    subgraph LOCAL_MODEL_HOST["Optional Local Model Host"]
        OLLAMA_LOCAL["Ollama local API\nCADARENA_OLLAMA_URL"]
    end

    subgraph EXTERNAL_SERVICES["External Services"]
        OLLAMA_CLOUD["Ollama Cloud or Qwen-compatible API"]
        SMTP_SERVER["SMTP server"]
        GOOGLE_OAUTH["Google OAuth verification"]
    end

    BROWSER --> REACT_RUNTIME
    REACT_RUNTIME --> STUDIO_RUNTIME
    REACT_RUNTIME --> VIEWER_RUNTIME
    BROWSER -->|"HTTP / and /api/v1/*"| FASTAPI

    FASTAPI --> STATIC_ASSETS
    FASTAPI --> PARSER_SERVICE
    FASTAPI --> DXF_PIPELINE
    FASTAPI --> SQLITE_AUTH
    FASTAPI --> SQLITE_WORKSPACE
    FASTAPI --> OUTPUT_DIR
    FASTAPI --> CLEANUP_TASK

    PARSER_SERVICE --> HF_MODEL
    PARSER_SERVICE --> OLLAMA_LOCAL
    PARSER_SERVICE --> OLLAMA_CLOUD
    FASTAPI --> SMTP_SERVER
    FASTAPI --> GOOGLE_OAUTH

    DXF_PIPELINE --> DXF_DIR
    OUTPUT_DIR --> DXF_DIR
    CLEANUP_TASK --> OUTPUT_DIR
```

## Architectural Notes
- The backend serves both API routes and frontend assets when the build or public asset folders exist.
- Local SQLite databases and generated files are colocated with the backend process; Docker deployment preserves the same logical topology.
- HuggingFace runs in-process through Python dependencies, while Ollama can be a local server or cloud-compatible endpoint.
- Contact email and Google sign-in are optional external integrations controlled by environment configuration.
