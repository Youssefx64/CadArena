# CadArena

CadArena turns architectural intent into workable CAD output.
It combines a FastAPI backend, a static frontend studio, and a design-parsing pipeline that converts natural language into structured layout data and DXF exports.

## What It Does

- Parses architectural prompts into structured room, boundary, and opening data
- Generates DXF files from validated design intent
- Exports previews and derived files such as PNG and PDF
- Supports authentication, profile management, and project-based workspace flows
- Serves the marketing pages and the studio UI from the same application

## Project Structure

```text
CadArena/
├── backend/   # FastAPI app, domain logic, services, tests, local data/output
├── frontend/  # Static HTML, CSS, JS pages used by the app
├── docker/    # Container orchestration assets
└── docs/      # Supporting documentation
```

## Stack

- Backend: FastAPI, Pydantic, Uvicorn
- CAD and rendering: `ezdxf`, `matplotlib`
- AI/parsing integrations: Hugging Face, Ollama, Transformers
- Frontend: Vanilla HTML, CSS, JavaScript
- Testing: Pytest

## Quick Start

### 1. Prepare environment

```bash
cd backend
cp .env.example .env
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Run the app

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open:

- `http://localhost:8000/` for the landing page
- `http://localhost:8000/app/` for the studio
- `http://localhost:8000/docs` for API docs in non-production mode

## Configuration

The backend loads configuration from [`backend/.env.example`](/home/mango/Coding/Projects/CadArena/backend/.env.example).
Main groups:

- Model provider keys for Hugging Face and Ollama
- SMTP settings for the contact form
- Auth settings for JWT, cookies, and Google sign-in

## Main Flows

### Prompt to DXF

1. Submit a natural-language design prompt
2. Parse it into structured architectural intent
3. Validate layout constraints
4. Generate DXF output
5. Download or export the result

### Workspace Flow

1. Create or load a project
2. Store prompt history and generated messages
3. Generate DXF files per project context

## Key Routes

- `/` landing page
- `/app/` studio frontend
- `/api/v1/parse-design`
- `/api/v1/parse-design-generate-dxf`
- `/api/v1/generate-dxf`
- `/api/v1/dxf/upload`
- `/api/v1/dxf/export`
- `/api/v1/auth/*`
- `/api/v1/profile/*`
- `/api/v1/workspace/*`

## Documentation

- Backend setup and architecture: [`backend/README.md`](/home/mango/Coding/Projects/CadArena/backend/README.md)
- Frontend structure and page organization: [`frontend/README.md`](/home/mango/Coding/Projects/CadArena/frontend/README.md)
- Docker assets: [`docker/README.md`](/home/mango/Coding/Projects/CadArena/docker/README.md)

## Development Notes

- Frontend files are served directly by the backend
- API docs are disabled automatically when `CADARENA_ENV=prod`
- Generated files and local runtime artifacts live under `backend/output` and `backend/data`
