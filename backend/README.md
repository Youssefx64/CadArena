# CadArena Backend

The backend is a FastAPI application that owns the HTTP API, authentication, workspace persistence, design parsing, DXF generation, community data, ArchChat integration, contact email delivery, health checks, and production serving of frontend assets.

## Runtime Services

| Service area | Main files | Responsibility |
| --- | --- | --- |
| Application entry point | `app/main.py` | FastAPI setup, middleware, route registration, startup initialization, static asset serving, health, and metrics. |
| Authentication | `app/routers/auth.py`, `app/core/auth.py`, `app/services/auth_storage.py`, `app/services/auth_security.py` | Email/password auth, JWT cookies, Google login, user records, and password hashing. |
| Profile | `app/routers/profile.py`, `app/services/auth_storage.py` | Profile fields, avatar upload/delete, and encrypted provider API keys. |
| Workspace | `app/routers/workspace.py`, `app/routers/workspace_auth.py`, `app/services/workspace_storage.py` | Guest and authenticated projects, messages, prompt generation, iteration, and persisted DXF metadata. |
| Design parser | `app/routers/design_parser.py`, `app/services/design_parser_service.py`, `app/services/design_parser/` | Prompt compilation, model provider calls, output repair, intent validation, layout planning, opening planning, and metrics. |
| DXF and exports | `app/api/v1/routes.py`, `app/pipeline/`, `app/domain/`, `app/services/dxf_exporter.py`, `app/services/dxf_room_renderer.py` | Structured DXF generation, upload, tokenized preview, download, PNG export, and PDF export. |
| Community | `app/routers/community.py`, `app/services/community_storage.py` | Questions, answers, voting, search, filtering, and sorting. |
| ArchChat | `app/routers/archchat.py`, `app/services/archchat_storage.py`, `app/services/archchat_title.py` | Authenticated chat threads that call the standalone RAG service. |
| Contact | `app/routers/contact.py`, `app/services/contact_email_service.py` | SMTP-backed contact form delivery. |
| File tokens | `app/services/file_token_registry.py` | Session and workspace file-token issuance and resolution. |
| Cleanup | `app/services/output_cleanup.py` | Periodic cleanup of generated output files. |

## Storage

The current backend storage layer requires PostgreSQL through:

```bash
CADARENA_DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/cadarena
```

The compatibility layer is implemented in `app/services/postgres_compat.py`. It converts legacy SQLite-style `?` placeholders into PostgreSQL parameters and executes statements through `psycopg2`.

ArchChat uses SQLAlchemy async sessions and resolves its database URL in this order:

1. `CADARENA_DATABASE_URL`
2. `CADARENA_ARCHCHAT_DATABASE_URL`

Generated artifacts are stored outside the database:

- DXF, PNG, and PDF files: `backend/output/dxf`
- Profile images: `backend/output/profile_images`
- Parse snapshots: `backend/output/parse_design_json`

## Setup

```bash
cd backend
cp .env.example .env
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Required environment values for a functional backend:

```bash
CADARENA_DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/cadarena
PROVIDER_KEY_SECRET=<fernet-key>
CADARENA_JWT_SECRET=<secret>
```

Common optional values:

```bash
CADARENA_RAG_API_URL=http://localhost:8001
CADARENA_OLLAMA_URL=http://localhost:11434/api/generate
CADARENA_OLLAMA_CLOUD_URL=https://cloud.ollama.com
CONTACT_SMTP_HOST=<smtp-host>
CADARENA_GOOGLE_CLIENT_ID=<google-client-id>
```

## Run

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Useful URLs:

- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/metrics`

## Main Route Groups

| Route group | Description |
| --- | --- |
| `/api/v1/auth/*` | Register, login, logout, current user, Google config, and Google login. |
| `/api/v1/profile/*` | Current profile, avatar, and provider API-key management. |
| `/api/v1/workspace/*` | Guest workspace projects, messages, generation, and iteration. |
| `/api/v1/workspace/me/*` | Authenticated workspace project and generation routes. |
| `/api/v1/parse-design-models` | Available parser provider and model options. |
| `/api/v1/parse-design` | Prompt-to-structured-layout parsing. |
| `/api/v1/parse-design-generate-dxf` | Parse prompt and generate DXF in one request. |
| `/api/v1/generate-dxf` | Generate a DXF from structured design intent. |
| `/api/v1/dxf/download` | Download a tokenized DXF file. |
| `/api/v1/dxf/preview` | Render a tokenized DXF preview as PNG. |
| `/api/v1/dxf/export` | Export a tokenized DXF as PNG, PDF, or DXF. |
| `/api/v1/dxf/upload` | Upload an existing DXF and receive a file token. |
| `/api/v1/community/*` | Questions, answers, votes, and community listing. |
| `/api/v1/contact/send-email` | Contact form email delivery. |
| `/api/v1/archchat/*` | Authenticated RAG chat threads and messages. |
| `/health` | Database, RAG, and model-provider health checks. |
| `/metrics` | Process memory, active requests, PID, and uptime. |

## Frontend Serving

When `frontend/build/index.html` exists, the backend serves the React build and routes such as:

- `/`
- `/studio`
- `/community`
- `/generate`
- `/rag-chat`
- `/models`
- `/metrics`
- `/about`
- `/developers`

When only `frontend/public/assets` exists, the backend serves public assets and the copied Studio app if present.

## Tests

Run all backend tests:

```bash
pytest app/tests
```

Run focused tests:

```bash
pytest app/tests/test_parse_design_api.py
pytest app/tests/test_workspace_generate_dxf_response.py
pytest app/tests/test_rag_enterprise.py
```

## Notes for Maintainers

- `ezdxf` is guarded at import time; if it is missing, DXF routes are disabled without blocking the whole application.
- DXF generation is executed in a threadpool from async routes to avoid blocking the event loop.
- Parser model providers are selected through `app/services/design_parser/config.py`.
- File tokens are the security boundary between browser clients and server-side output paths.
