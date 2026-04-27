# CadArena

CadArena is an AI-assisted platform for civil and architectural workflows.
The project currently has three main surfaces:

- a React website for the public pages
- a `/community` page for engineering Q&A
- a legacy Studio workspace at `/studio` for chat-driven DXF generation

## Repository Layout

```text
CadArena/
├── backend/   FastAPI app, API routes, storage, DXF generation, tests
├── frontend/  React app, shared assets, and legacy studio source
├── docker/    Dockerfile and compose setup
└── docs/      supporting design notes and diagrams
```

## Main Features

- project-based studio workflow
- prompt-to-layout and DXF generation endpoints
- DXF preview and export
- auth, profile, and workspace APIs
- community questions, answers, and voting

## Local Development

### 1. Run the backend

```bash
cd backend
cp .env.example .env
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Run the frontend

```bash
cd frontend
npm install
npm start
```

### 3. Open the app

- `http://localhost:3000/` React site
- `http://localhost:3000/studio` Studio
- `http://localhost:3000/community` Community
- `http://127.0.0.1:8000/docs` FastAPI docs when enabled

## Production-Style Local Run

If you want the backend to serve the frontend build directly:

```bash
cd frontend
npm run build

cd ../backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

With `frontend/build` present, the backend serves:

- `/` and the React routes
- `/studio-app/*` for the copied legacy studio assets

## Important Notes

- Edit legacy studio files in `frontend/studio-source/`, not in `frontend/public/studio-app/`
- `frontend/scripts/copy-studio.js` copies `studio-source` into `public/studio-app`
- runtime data is stored under `backend/data/`
- generated DXF and export files are written under `backend/output/`

## Verification

Backend:

```bash
cd backend
pytest app/tests
```

Frontend:

```bash
cd frontend
npm run build
```

## Project Docs

- [backend/README.md](backend/README.md)
- [frontend/README.md](frontend/README.md)
- [docker/README.md](docker/README.md)
