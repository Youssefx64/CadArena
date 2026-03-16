---
# System Flow — CadArena

## Overview

CadArena is a natural-language-to-CAD platform built on FastAPI.
The system accepts architectural descriptions as text, parses them into
structured design intent, validates layout constraints, and generates
DXF files ready for professional CAD use.

Three actors interact with the system:
- **Guest** — uses the studio without authentication (local user_id)
- **Authenticated User** — full workspace persistence via JWT
- **External Services** — LLM providers, SMTP, filesystem, SQLite

---

## Flow 1: Design Parsing and Guest DXF Generation

> Parse natural language into structured intent, optionally returning a DXF path.

Endpoints:
- `GET /api/v1/parse-design-models`
- `POST /api/v1/parse-design`
- `POST /api/v1/parse-design-generate-dxf`

```mermaid
flowchart TD
    A1[User submits prompt] --> B1[POST api v1 parse design]
    A1 --> C1[POST api v1 parse design generate dxf]
    B1 --> D1[Design parse orchestrator]
    C1 --> D1
    D1 --> E1[LLM provider]
    E1 --> F1[Deterministic layout planner]
    F1 --> G1[Deterministic opening planner]
    G1 --> H1[Intent schema validation]
    H1 --> I1[Structured design intent payload]
    I1 --> J1{Generate DXF}
    J1 -->|No| K1[200 response with data and metrics]
    J1 -->|Yes| L1[DesignIntent model validation]
    L1 --> M1[DXF generation pipeline]
    M1 --> N1[DXFRoomRenderer save]
    N1 --> O1[200 response with dxf path]
```

**Key components involved:**
| Component | Location | Responsibility |
|-----------|----------|----------------|
| DesignParseOrchestrator | app/services/design_parser/orchestrator.py | Orchestrates prompt compile, provider calls, planning, and validation |
| DeterministicLayoutPlanner | app/services/design_parser/layout_planner.py | Generates room placements from extracted programs |
| DeterministicOpeningPlanner | app/services/design_parser/opening_planner.py | Derives doors and windows from planned rooms |
| LayoutValidator | app/services/design_parser/layout_validator.py | Enforces deterministic layout rules and scoring |
| IntentValidator | app/services/design_parser/intent_validator.py | Validates final parsed payload schema |
| save_parse_design_output | app/utils/parse_output_storage.py | Persists parse output for inspection and reuse |
| DesignIntentValidator | app/services/intent_validation.py | Validates DXF intent before rendering |
| PlannerAgent | app/domain/planner/planner_agent.py | Places rooms without explicit origins |
| DXFRoomRenderer | app/services/dxf_room_renderer.py | Renders DXF entities and saves the file |

---

## Flow 2: Workspace DXF Generation

> Persisted generation with project history and message logging.

Endpoints:
- `POST /api/v1/workspace/projects/{project_id}/generate-dxf` (user_id in body)
- `POST /api/v1/workspace/me/projects/{project_id}/generate-dxf` (JWT)

```mermaid
flowchart TD
    A2[User selects project] --> B2{Auth mode}
    B2 -->|JWT| C2[POST api v1 workspace me projects id generate dxf]
    B2 -->|User id| D2[POST api v1 workspace projects id generate dxf]
    C2 --> E2[workspace auth router]
    D2 --> F2[workspace router]
    E2 --> F2
    F2 --> G2[workspace storage add user message]
    G2 --> H2[Design parser service with retry]
    H2 --> I2[generate dxf from intent]
    I2 --> J2[workspace storage add assistant message]
    J2 --> K2[200 response with dxf path and message ids]
```

---

## Flow 3: Authentication

Endpoints:
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`
- `GET /api/v1/auth/google/config`
- `POST /api/v1/auth/google`

```mermaid
flowchart TD
    subgraph Register
        R1[POST api v1 auth register] --> R2[auth storage create user]
        R2 --> R3[auth storage create profile]
        R3 --> R4[JWT cookie set]
        R4 --> R5[201 response with user]
    end

    subgraph Login
        L1[POST api v1 auth login] --> L2[auth storage get user by email]
        L2 --> L3{Password valid}
        L3 -->|No| L4[401 invalid credentials]
        L3 -->|Yes| L5[JWT cookie set]
        L5 --> L6[200 response with user]
    end

    subgraph GoogleOAuth
        G1[GET api v1 auth google config] --> G2[Google client id or disabled]
        G3[POST api v1 auth google] --> G4[Verify Google id token]
        G4 --> G5{User exists}
        G5 -->|No| G6[auth storage create user]
        G5 -->|Yes| G7[Load existing user]
        G6 --> G8[JWT cookie set]
        G7 --> G8
        G8 --> G9[200 response with user]
    end

    subgraph Session
        S1[POST api v1 auth logout] --> S2[Clear auth cookie]
        S3[GET api v1 auth me] --> S4[JWT decode access token]
        S4 --> S5[200 response with user]
    end
```

---

## Flow 4: Profile Management

Endpoints:
- `GET /api/v1/profile/me`
- `PATCH /api/v1/profile/me`
- `POST /api/v1/profile/me/avatar`
- `DELETE /api/v1/profile/me/avatar`
- `PUT /api/v1/profile/me/providers/{provider}`
- `DELETE /api/v1/profile/me/providers/{provider}`

```mermaid
flowchart TD
    subgraph Profile
        P1[GET api v1 profile me] --> P2[auth storage ensure user profile]
        P2 --> P3[200 response with profile and providers]
        P4[PATCH api v1 profile me] --> P5[auth storage update user profile]
        P5 --> P6[200 response with updated profile]
    end

    subgraph Avatar
        A1[POST api v1 profile me avatar] --> A2[Validate image and size]
        A2 --> A3[Save file to output profile images]
        A3 --> A4[auth storage update profile image]
        A4 --> A5[200 response with profile]
        A6[DELETE api v1 profile me avatar] --> A7[auth storage update profile image]
        A7 --> A8[Delete previous image file]
        A8 --> A9[200 response with profile]
    end

    subgraph ProviderKeys
        K1[PUT api v1 profile me providers provider] --> K2[auth storage upsert provider key]
        K2 --> K3[200 response with profile]
        K4[DELETE api v1 profile me providers provider] --> K5[auth storage delete provider key]
        K5 --> K6[200 response with profile]
    end
```

---

## Flow 5: Workspace Project Management

Endpoints:
- `GET /api/v1/workspace/projects`
- `POST /api/v1/workspace/projects`
- `PATCH /api/v1/workspace/projects/{project_id}`
- `DELETE /api/v1/workspace/projects/{project_id}`
- `GET /api/v1/workspace/projects/{project_id}/messages`
- `GET /api/v1/workspace/me/projects`
- `POST /api/v1/workspace/me/projects`
- `PATCH /api/v1/workspace/me/projects/{project_id}`
- `DELETE /api/v1/workspace/me/projects/{project_id}`
- `GET /api/v1/workspace/me/projects/{project_id}/messages`

```mermaid
flowchart TD
    A5[Project list request] --> B5{Auth mode}
    B5 -->|JWT| C5[GET api v1 workspace me projects]
    B5 -->|User id| D5[GET api v1 workspace projects]
    C5 --> E5[workspace storage list projects]
    D5 --> E5
    E5 --> F5[200 response with projects]

    G5[Create project] --> H5{Auth mode}
    H5 -->|JWT| I5[POST api v1 workspace me projects]
    H5 -->|User id| J5[POST api v1 workspace projects]
    I5 --> K5[workspace storage create project]
    J5 --> K5
    K5 --> L5[201 response with project]

    M5[Rename project] --> N5{Auth mode}
    N5 -->|JWT| O5[PATCH api v1 workspace me projects id]
    N5 -->|User id| P5[PATCH api v1 workspace projects id]
    O5 --> Q5[workspace storage rename project]
    P5 --> Q5
    Q5 --> R5[200 response with project or 404]

    S5[Delete project] --> T5{Auth mode}
    T5 -->|JWT| U5[DELETE api v1 workspace me projects id]
    T5 -->|User id| V5[DELETE api v1 workspace projects id]
    U5 --> W5[workspace storage delete project]
    V5 --> W5
    W5 --> X5[200 response success]

    Y5[Fetch messages] --> Z5{Auth mode}
    Z5 -->|JWT| AA5[GET api v1 workspace me projects id messages]
    Z5 -->|User id| AB5[GET api v1 workspace projects id messages]
    AA5 --> AC5[workspace storage list project messages]
    AB5 --> AC5
    AC5 --> AD5[200 response with messages]
```

---

## Flow 6: DXF Utilities

Endpoints:
- `POST /api/v1/generate-dxf`
- `GET /api/v1/dxf/download`
- `GET /api/v1/dxf/preview`
- `GET /api/v1/dxf/export`
- `POST /api/v1/dxf/upload`

```mermaid
flowchart TD
    subgraph Generate
        G61[POST api v1 generate dxf] --> G62[generate dxf from intent]
        G62 --> G63[200 response with dxf path]
    end

    subgraph Export
        E61[GET api v1 dxf download] --> E62[resolve output path]
        E62 --> E63[FileResponse dxf]
        E64[GET api v1 dxf preview] --> E65[dxf exporter render image]
        E65 --> E66[FileResponse png]
        E67[GET api v1 dxf export] --> E68[dxf exporter render pdf or png]
        E68 --> E69[FileResponse file]
    end

    subgraph Upload
        U61[POST api v1 dxf upload] --> U62[Validate and store dxf]
        U62 --> U63[200 response with dxf path]
    end
```

---

## Flow 7: Contact Form

Endpoint:
- `POST /api/v1/contact/send-email`

```mermaid
flowchart TD
    A7[POST api v1 contact send email] --> B7[Validate request payload]
    B7 --> C7[contact email service send contact email]
    C7 --> D7{SMTP send success}
    D7 -->|Yes| E7[200 response success]
    D7 -->|No| F7[503 response]
```

---

## Layer Architecture

```mermaid
flowchart TD
    subgraph Transport
        R1[api v1 routes]
        R2[auth router]
        R3[workspace router]
        R4[workspace auth router]
        R5[design parser router]
        R6[profile router]
        R7[contact router]
    end

    subgraph Orchestration
        S1[design parser service]
        S2[auth storage]
        S3[workspace storage]
        S4[dxf exporter]
        S5[contact email service]
        S6[intent processing]
    end

    subgraph Domain
        D1[planner agent]
        D2[architecture and geometry]
        D3[constraints]
    end

    subgraph Pipeline
        P1[intent to agent]
        P2[draw pipeline]
    end

    subgraph External
        E1[ezdxf]
        E2[matplotlib]
        E3[ollama]
        E4[huggingface]
        E5[sqlite]
        E6[smtp]
    end

    Transport --> Orchestration
    Orchestration --> Domain
    Orchestration --> Pipeline
    Pipeline --> External
    Domain --> Pipeline
    Orchestration --> External
```

**Design principle:** Routers handle HTTP only.
Business logic lives exclusively in domain and services.
Pipeline connects validated intent to DXF output.

---

## Data Flow Summary

```mermaid
flowchart LR
    NL[Natural language prompt]
    DS[Structured design intent]
    DXF[DXF generation pipeline]
    DOC[DXF document]
    OUT[backend output folder]

    NL --> DS
    DS --> DXF
    DXF --> DOC
    DOC --> OUT
```

---

## Mermaid Rules Applied
- No parentheses or special chars inside node labels
- No single quote or double quote inside node labels
- No reserved keywords used as node IDs
- All subgraph names are single words
- All flowchart directions explicit
