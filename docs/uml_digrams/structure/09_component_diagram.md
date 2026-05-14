# 09 Component Diagram - Main Components and Dependencies - CadArena

## Purpose
This component diagram shows the major deployable and logical components in the current CadArena repository and how they depend on each other.

## Diagram

```mermaid
flowchart LR
    subgraph CLIENT["Client Browser"]
        SPA["React SPA\nfrontend/src"]
        STUDIO["Embedded Studio\nfrontend/public/studio-app"]
        VIEWER["DXF Viewer\nfrontend/src/pages/ViewerPage.js"]
    end

    subgraph FASTAPI["FastAPI Backend\nbackend/app/main.py"]
        ROUTERS["Routers\nauth, profile, workspace, workspace_auth, design_parser, community, contact, dxf"]
        CORE["Core\nsettings, auth, env loading, logging, file utils"]
        MODELS["API Models\nPydantic request and response models"]
        SCHEMAS["Schemas\ndesign intent, geometry, room, opening, export"]
        SERVICES["Services\nstorage, parser facade, DXF exporter, chat assistant, suggestions, tokens"]
        PARSER["Design Parser Services\norchestrator, providers, planners, validators, patcher"]
        PIPELINE["DXF Pipeline\nintent_to_agent, draw_pipeline"]
        DOMAIN["Domain\nplanner, constraints, architecture, geometry, openings"]
    end

    subgraph STORAGE["Local Storage"]
        SQLITE_AUTH[("auth/profile/community SQLite")]
        SQLITE_WORKSPACE[("workspace SQLite")]
        OUTPUT[("backend/output and backend/output/dxf")]
    end

    subgraph EXTERNAL["External or Optional Systems"]
        OLLAMA_LOCAL["Ollama local API"]
        OLLAMA_CLOUD["Ollama Cloud or Qwen-compatible API"]
        HF_LOCAL["HuggingFace transformers"]
        SMTP["SMTP server"]
        GOOGLE["Google OAuth"]
        EZDXF["ezdxf"]
        MATPLOTLIB["matplotlib"]
    end

    SPA -->|"routes and iframe"| STUDIO
    SPA -->|"viewer route"| VIEWER
    STUDIO -->|"HTTP fetch"| ROUTERS
    VIEWER -->|"HTTP fetch"| ROUTERS
    SPA -->|"auth/profile/community HTTP"| ROUTERS

    ROUTERS --> CORE
    ROUTERS --> MODELS
    ROUTERS --> SCHEMAS
    ROUTERS --> SERVICES
    ROUTERS --> PIPELINE

    SERVICES --> PARSER
    SERVICES --> SQLITE_AUTH
    SERVICES --> SQLITE_WORKSPACE
    SERVICES --> OUTPUT
    SERVICES --> SMTP
    SERVICES --> GOOGLE

    PARSER --> OLLAMA_LOCAL
    PARSER --> OLLAMA_CLOUD
    PARSER --> HF_LOCAL
    PARSER --> MODELS

    PIPELINE --> DOMAIN
    PIPELINE --> SCHEMAS
    PIPELINE --> EZDXF
    PIPELINE --> OUTPUT

    SERVICES --> MATPLOTLIB
    SERVICES --> EZDXF
    DOMAIN --> SCHEMAS
```

## Architectural Notes
- `backend/app/main.py` mounts frontend assets when available and registers all `/api/v1` routers.
- The Studio workspace is a legacy static app embedded by the React `/studio` route, but it uses the same backend APIs as the rest of the React application.
- Parser providers are optional at runtime; missing CAD dependencies disable DXF routes rather than preventing the whole app from importing.
- SQLite databases and generated files live on the backend host and are initialized or cleaned up through startup tasks.
