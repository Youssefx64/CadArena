# CadArena Engineering RAG

Standalone Retrieval-Augmented Generation service for CadArena's civil and architectural engineering workspace.

## What It Is For

- Query project specifications, code notes, reports, BOQs, and design references.
- Retrieve source-backed chunks for architectural planning, structural coordination, MEP interfaces, and construction constraints.
- Keep RAG runtime state isolated under `RAG/data` so it does not touch the main CadArena backend database.

## Supported Uploads

- PDF
- TXT
- Markdown
- CSV
- JSON

## Local URLs

- Frontend page: `http://127.0.0.1:3000/rag-chat`
- RAG API: `http://127.0.0.1:8001/rag`
- API docs: `http://127.0.0.1:8001/rag/docs`

## Install

```bash
# from the repository root
conda env create -f environment.yml
# or update the existing shared env
conda env update -n cad -f environment.yml --prune
cp RAG/.env.example RAG/.env
```

Add one provider key in `.env`:

```bash
RAG_COHERE_API_KEY=...
# or
RAG_OPENAI_API_KEY=...
```

## Run

```bash
./scripts/run-backend-rag.sh
```

The script starts the backend on `http://127.0.0.1:8000` and RAG on `http://127.0.0.1:8001/rag`. If either service is already running on its configured port, it reuses it and starts only the missing service.

## Local Vector Database

Default Qdrant storage:

```text
RAG/data/qdrant_db
```

After documents are ingested, Qdrant creates collection storage under:

```text
RAG/data/qdrant_db/collection/<collection-name>/storage.sqlite
```

## Health Check

```bash
curl http://127.0.0.1:8001/rag/health
```

## Clear A Collection

```bash
curl -X DELETE http://127.0.0.1:8001/rag/collection/default
```
