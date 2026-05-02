# CadArena

AI-powered architectural design platform that transforms natural language prompts into professional CAD floor plans.

## Architecture

- **Frontend**: React 18 app (Create React App / react-scripts) running on port 5000
- **Backend**: FastAPI (Python 3.12) running on port 8000 (dev) / port 5000 (production)
- **Database**: SQLite (stored in `backend/data/`)
- **AI**: HuggingFace transformers, Ollama LLM integration, LangChain

## Project Structure

```
frontend/          React frontend app
  src/             Application source
  public/          Static assets
  studio-source/   Studio app source (copied to public/studio-app on start)
  scripts/         Build helper scripts (copy-studio.js)

backend/           FastAPI backend
  app/
    api/           API v1 routes (DXF endpoints)
    core/          Settings, logging, env loading
    models/        Pydantic models
    routers/       Route handlers (auth, community, workspace, etc.)
    services/      Business logic (design parser, DXF, auth, community)
    domain/        Domain logic
  data/            SQLite database files (runtime, gitignored)
  .env             Runtime environment variables (not in git)
  .env.example     Template for env vars
```

## Key Features

- AI-powered floor plan generation from natural language
- DXF export (AutoCAD/Revit compatible)
- EBC 2023 compliance checking
- Community Q&A hub
- Multi-language (Arabic & English)
- JWT authentication with optional Google OAuth
- Workspace with project management

## Workflows

- **Start application** — Frontend dev server: `cd frontend && HOST=0.0.0.0 PORT=5000 DANGEROUSLY_DISABLE_HOST_CHECK=true REACT_APP_API_URL='' npm start`
- **Backend API** — Backend server: `cd backend && python -m uvicorn app.main:app --host localhost --port 8000`

## Deployment

- Build: `cd frontend && npm run build` (React build served by FastAPI)
- Run: `cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 5000`
- Target: autoscale

## Environment Variables

Stored in `backend/.env` (see `backend/.env.example` for template). Key vars:
- `CADARENA_JWT_SECRET` — JWT signing secret
- `PROVIDER_KEY_SECRET` — Fernet key for encrypting provider API keys
- `HF_TOKEN` — HuggingFace token (optional, enables higher rate limits)
- `CADARENA_WORKSPACE_DB_PATH` — SQLite DB path (default: `./data/workspace.db`)

## Dependencies

- Python: FastAPI, uvicorn, ezdxf, matplotlib, torch (CPU), transformers, accelerate, langchain, langchain-ollama, bcrypt, cryptography
- Node: React, react-router-dom, axios, framer-motion, tailwindcss, recharts, lucide-react
