# CadArena Backend

The backend is a FastAPI application that owns the API, persistence, DXF workflow, and production serving of the frontend build.

## What Lives Here

- auth and profile APIs
- workspace projects and project messages
- community questions, answers, and voting
- design parsing and DXF generation
- export endpoints for preview images and PDFs
- startup tasks for local databases and cleanup jobs

## Directory Layout

```text
backend/
├── app/
│   ├── api/        DXF and lower-level API routes
│   ├── core/       settings, auth helpers, env loading, logging
│   ├── models/     request and response models
│   ├── routers/    auth, profile, workspace, community, parsing
│   ├── services/   storage, exporters, parsers, integrations
│   ├── tests/      backend tests
│   └── utils/      shared helpers
├── data/           local SQLite databases and runtime data
├── output/         generated DXF and exported files
├── requirements.txt
└── .env.example
```

## Setup

```bash
cd backend
cp .env.example .env
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Useful URLs:

- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/docs` when docs are enabled

## Environment

Use `backend/.env.example` as the source of truth. The most important values are:

- `HF_TOKEN`
- `OLLAMA_API_KEY`
- `CADARENA_OLLAMA_URL`
- `CADARENA_JWT_SECRET`
- `PROVIDER_KEY_SECRET`
- `CADARENA_WORKSPACE_DB_PATH`

## Main Route Groups

- `/api/v1/auth/*`
- `/api/v1/profile/*`
- `/api/v1/workspace/*`
- `/api/v1/community/*`
- `/api/v1/parse-design*`
- `/api/v1/generate-dxf`
- `/api/v1/dxf/*`

## Frontend Integration

The app entry point is `backend/app/main.py`.

When `frontend/build/` exists, the backend serves:

- the React app on `/`
- React routes such as `/community` and `/generate`
- legacy studio assets on `/studio-app/*`

## Tests

Run the backend test suite from `backend/`:

```bash
pytest app/tests
```

For focused checks:

```bash
pytest app/tests/test_community_storage.py
```

## Runtime Notes

- local databases are initialized on startup
- community and workspace data are stored in `backend/data/`
- generated files are cleaned up periodically by the lifespan task
