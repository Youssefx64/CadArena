---
# System Flow — CadArena

## Overview
CadArena is a FastAPI-backed architectural CAD platform with a React shell plus a standalone studio iframe. Users can parse prompts, generate DXF, manage projects, upload DXF files, and export preview files.

Actors:
- Guest — local workspace mode without authentication
- Authenticated User — JWT-backed persistence and profile management
- External Services — Ollama, HuggingFace, SMTP, filesystem, SQLite

## Flow 1: Prompt Parsing
```mermaid
flowchart TD
    A[User prompt] --> B[POST /api/v1/parse-design]
    A --> C[POST /api/v1/parse-design-generate-dxf]
    B --> D[DesignParseOrchestrator]
    C --> D
    D --> E[Provider client]
    D --> F[Deterministic planners]
    D --> G[Intent validation]
    D --> H[JSON intent response]
    C --> I[DXF generation pipeline]
    I --> J[DXFRoomRenderer]
    J --> K[backend/output/dxf]
```

## Flow 2: Workspace Generation
```mermaid
flowchart TD
    A[Workspace message] --> B[workspace router]
    B --> C[workspace_storage.add_message]
    C --> D[parse_design_prompt_with_metadata]
    D --> E[DesignParseOrchestrator]
    E --> F[generate_dxf_from_intent]
    F --> G[workspace_storage.add_message assistant]
    G --> H[Response with dxf_path]
```

## Flow 3: Authentication
```mermaid
flowchart TD
    A[Login/Register] --> B[auth router]
    B --> C[auth_storage]
    C --> D[JWT cookie]
    D --> E[Authenticated session]
```

## Flow 4: Profile and Provider Keys
```mermaid
flowchart TD
    A[Profile request] --> B[profile router]
    B --> C[user_profiles]
    B --> D[user_provider_api_keys]
    C --> E[Updated profile]
    D --> F[Updated provider key]
```

## Flow 5: Workspace Projects
```mermaid
flowchart TD
    A[Project action] --> B[workspace routers]
    B --> C[workspace_storage]
    C --> D[projects]
    C --> E[messages]
    D --> F[Project response]
    E --> G[Message response]
```

## Flow 6: DXF Utilities
```mermaid
flowchart TD
    A[DXF action] --> B[/api/v1/dxf/upload]
    A --> C[/api/v1/dxf/preview]
    A --> D[/api/v1/dxf/export]
    B --> E[Stored DXF token]
    C --> F[PNG preview]
    D --> G[PNG or PDF export]
```

## Flow 7: Contact Form
```mermaid
flowchart TD
    A[Contact form] --> B[contact router]
    B --> C[contact_email_service]
    C --> D[SMTP]
```

## Layer Architecture
```mermaid
flowchart TD
    A[Frontend]
    B[API routers]
    C[Services]
    D[Domain]
    E[Storage]
    F[External services]

    A --> B --> C --> D
    C --> E
    C --> F
```

## Data Flow Summary
```mermaid
flowchart LR
    A[Prompt] --> B[Intent]
    B --> C[DXF]
    C --> D[Output files]
```
