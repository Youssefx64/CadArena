# Backend

The backend is the core of CadArena.
It handles prompt parsing, layout validation, DXF generation, file export, authentication, profile management, and workspace persistence.

## Responsibilities

- Expose the HTTP API through FastAPI
- Convert natural-language prompts into structured architectural intent
- Generate DXF files and export previews
- Manage auth, cookies, profiles, and provider keys
- Store workspace projects and project messages
- Serve the frontend pages through the main application

## Stack

- FastAPI
- Pydantic v2
- Uvicorn
- `ezdxf`
- `matplotlib`
- `transformers`, `torch`, `accelerate`
- Pytest

## Layout

```text
backend/
├── app/
│   ├── api/         # DXF and API v1 routes
│   ├── core/        # settings, env loading, auth helpers, logging
│   ├── domain/      # planning, geometry, constraints, architecture rules
│   ├── models/      # API models and response contracts
│   ├── pipeline/    # intent-to-agent and drawing pipelines
│   ├── routers/     # auth, profile, workspace, design parsing, contact
│   ├── schemas/     # validated design schemas
│   ├── services/    # storage, exporters, parser orchestration, integrations
│   ├── tests/       # backend test suite
│   └── utils/       # prompt and parsing utilities
├── data/            # local application data
├── output/          # generated DXF/export files
└── .env.example     # environment template
```

## Run Locally

### 1. Setup

```bash
cd backend
cp .env.example .env
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Start the server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The app entry point is [`backend/app/main.py`](/home/mango/Coding/Projects/CadArena/backend/app/main.py).

## Environment Variables

Use [`backend/.env.example`](/home/mango/Coding/Projects/CadArena/backend/.env.example) as the source of truth.

### AI providers

- `HF_TOKEN`
- `OLLAMA_API_KEY`

### Contact email

- `CONTACT_INBOX_EMAIL`
- `CONTACT_SENDER_EMAIL`
- `CONTACT_SENDER_NAME`
- `CONTACT_SMTP_HOST`
- `CONTACT_SMTP_PORT`
- `CONTACT_SMTP_USERNAME`
- `CONTACT_SMTP_PASSWORD`
- `CONTACT_SMTP_USE_TLS`
- `CONTACT_SMTP_USE_SSL`

### Authentication

- `CADARENA_JWT_SECRET`
- `CADARENA_AUTH_TOKEN_TTL_SECONDS`
- `CADARENA_AUTH_COOKIE_NAME`
- `CADARENA_AUTH_COOKIE_SECURE`
- `CADARENA_GOOGLE_CLIENT_ID`

### Runtime behavior

- `CADARENA_ENV`
- `CADARENA_API_VERSION`
- `CADARENA_APP_NAME`

## API Surface

### CAD and exports

- `POST /api/v1/generate-dxf`
- `POST /api/v1/dxf/upload`
- `GET /api/v1/dxf/download`
- `GET /api/v1/dxf/preview`
- `GET /api/v1/dxf/export`

### Design parsing

- `GET /api/v1/parse-design-models`
- `POST /api/v1/parse-design`
- `POST /api/v1/parse-design-generate-dxf`

### Authentication

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/google`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`

### Profile

- `GET /api/v1/profile/me`
- `PATCH /api/v1/profile/me`
- `POST /api/v1/profile/me/avatar`
- `DELETE /api/v1/profile/me/avatar`
- `PUT /api/v1/profile/me/providers/{provider}`

### Workspace

- `GET /api/v1/workspace/projects`
- `POST /api/v1/workspace/projects`
- `PATCH /api/v1/workspace/projects/{project_id}`
- `DELETE /api/v1/workspace/projects/{project_id}`
- `GET /api/v1/workspace/projects/{project_id}/messages`
- `POST /api/v1/workspace/projects/{project_id}/generate-dxf`

## Architecture Notes

- `domain/` contains the deterministic geometry, planning, and constraint logic
- `services/` contains orchestration, storage, exporters, and provider integrations
- `pipeline/` connects validated design intent to DXF generation
- `routers/` keep transport concerns separate from business logic

## Testing

Run the test suite from `backend/`:

```bash
pytest app/tests
```

## Output and Persistence

- Generated files are written under `backend/output`
- Local data stores are initialized on application startup
- Workspace and auth storage are bootstrapped during FastAPI lifespan startup
