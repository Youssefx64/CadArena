# 11 Package Diagram - Repository Package Structure - CadArena

## Purpose
This package diagram shows the current package layout across the backend, React frontend, embedded Studio source, tests, documentation, and Docker setup.

## Diagram

```mermaid
flowchart TB
    subgraph REPO["CadArena repository"]
        BACKEND["backend/"]
        FRONTEND["frontend/"]
        DOCS["docs/"]
        DOCKER["docker/"]
    end

    subgraph BACKEND_APP["backend/app"]
        MAIN["main.py"]
        API_V1["api/v1/"]
        ROUTERS["routers/"]
        CORE["core/"]
        MODELS["models/"]
        SCHEMAS["schemas/"]
        SERVICES["services/"]
        DESIGN_PARSER["services/design_parser/"]
        ADAPTERS["services/adapters/"]
        PORTS["services/ports/"]
        PIPELINE["pipeline/"]
        DOMAIN["domain/"]
        UTILS["utils/"]
        TESTS["tests/"]
    end

    subgraph DOMAIN_PACKAGES["backend/app/domain"]
        DOMAIN_PLANNER["planner/"]
        DOMAIN_ARCH["architecture/"]
        DOMAIN_CONSTRAINTS["constraints/"]
        DOMAIN_OPENINGS["openings/"]
        DOMAIN_GEOMETRY["geometry/"]
    end

    subgraph FRONTEND_PACKAGES["frontend"]
        SRC["src/"]
        PUBLIC["public/"]
        STUDIO_SOURCE["studio-source/"]
        FRONTEND_SCRIPTS["scripts/"]
        CONFIG["package and config files"]
    end

    subgraph REACT_SRC["frontend/src"]
        PAGES["pages/"]
        COMPONENTS["components/"]
        CONTEXTS["contexts/"]
        HOOKS["hooks/"]
        FRONTEND_SERVICES["services/"]
        CONSTANTS["constants/"]
        FRONTEND_UTILS["utils/"]
        APP["App.js"]
    end

    subgraph STUDIO_STATIC["Studio static app"]
        STUDIO_PUBLIC["public/studio-app/"]
        STUDIO_HTML["index.html and profile.html"]
        STUDIO_JS["scripts/app.js and helpers"]
        STUDIO_CSS["styles/*.css"]
    end

    BACKEND --> BACKEND_APP
    FRONTEND --> FRONTEND_PACKAGES
    DOCS --> UML["docs/uml/"]
    DOCKER --> COMPOSE["Dockerfile and docker-compose.yml"]

    MAIN --> ROUTERS
    MAIN --> API_V1
    MAIN --> CORE
    MAIN --> SERVICES

    API_V1 --> PIPELINE
    API_V1 --> SCHEMAS
    ROUTERS --> MODELS
    ROUTERS --> SERVICES
    ROUTERS --> PIPELINE
    ROUTERS --> CORE
    ROUTERS --> SCHEMAS

    SERVICES --> DESIGN_PARSER
    SERVICES --> ADAPTERS
    SERVICES --> PORTS
    SERVICES --> DOMAIN
    SERVICES --> UTILS
    SERVICES --> SCHEMAS

    DESIGN_PARSER --> MODELS
    DESIGN_PARSER --> UTILS
    PIPELINE --> DOMAIN
    PIPELINE --> SCHEMAS
    ADAPTERS --> PORTS
    ADAPTERS --> PIPELINE

    DOMAIN --> DOMAIN_PLANNER
    DOMAIN --> DOMAIN_ARCH
    DOMAIN --> DOMAIN_CONSTRAINTS
    DOMAIN --> DOMAIN_OPENINGS
    DOMAIN --> DOMAIN_GEOMETRY

    SRC --> REACT_SRC
    PUBLIC --> STUDIO_PUBLIC
    STUDIO_SOURCE --> STUDIO_PUBLIC
    FRONTEND_SCRIPTS --> STUDIO_PUBLIC

    APP --> PAGES
    APP --> COMPONENTS
    APP --> CONTEXTS
    PAGES --> COMPONENTS
    PAGES --> FRONTEND_SERVICES
    COMPONENTS --> HOOKS
    COMPONENTS --> FRONTEND_UTILS
    FRONTEND_SERVICES --> ROUTERS

    STUDIO_PUBLIC --> STUDIO_HTML
    STUDIO_PUBLIC --> STUDIO_JS
    STUDIO_PUBLIC --> STUDIO_CSS
    STUDIO_JS --> ROUTERS
    STUDIO_JS --> API_V1
```

## Architectural Notes
- Backend transport concerns live in `routers/` and `api/v1/`; domain geometry and planner rules stay under `domain/`.
- `services/design_parser/` contains the high-level LLM extraction and deterministic planning pipeline, while `pipeline/intent_to_agent.py` converts validated intent into DXF geometry.
- The React app owns routing, authentication context, page shells, and the Viewer; the full Studio workspace is currently served as static HTML/CSS/JS.
- `frontend/scripts/copy-studio.js` keeps `studio-source/` and `public/studio-app/` aligned for the embedded workspace.
