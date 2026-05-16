# CadArena Engineering RAG

The RAG service is a standalone FastAPI application for Retrieval-Augmented Generation over civil and architectural reference documents. The integration-ready runtime lives in `RAG/app` and exposes all public routes under `/rag`.

## Runtime Services

| Service | Location | Responsibility |
| --- | --- | --- |
| RAG FastAPI app | `app/main.py` | Creates the standalone app, applies CORS, mounts the RAG router, and exposes `/rag/ping`. |
| RAG router | `app/router.py` | Model listing, health, text ingestion, file ingestion, querying, and collection clearing. |
| RAG engine | `app/rag_engine.py` | Coordinates ingestion, retrieval, generation, chunking, and provider selection. |
| Document loader | `app/document_loader.py` | Extracts text from uploaded PDF, TXT, Markdown, CSV, and JSON files. |
| Vector store | `app/vector_store.py` | Stores and retrieves document chunks through the configured vector backend. |
| Embeddings | `app/embeddings.py` | Creates embeddings for indexed document chunks. |
| Configuration | `app/config.py` | Reads `RAG_*` environment variables. |
| Legacy RAG app | `src/` | Older project-oriented upload, processing, vector indexing, and NLP API. |

## Public URLs

Default local URLs:

- RAG API root prefix: `http://127.0.0.1:8001/rag`
- RAG docs: `http://127.0.0.1:8001/rag/docs`
- Frontend RAG chat page: `http://127.0.0.1:3000/rag-chat`

## Main Endpoints

| Endpoint | Method | Description |
| --- | --- | --- |
| `/rag/ping` | GET | Minimal liveness check. |
| `/rag/models` | GET | Lists available local Ollama models and configured cloud provider defaults. |
| `/rag/health` | GET | Returns vector store, embedding model, and document count. |
| `/rag/query` | POST | Answers a question with retrieved context and optional provider or model override. |
| `/rag/ingest` | POST | Ingests raw text documents. |
| `/rag/ingest/files` | POST | Extracts and ingests uploaded reference files. |
| `/rag/collection/{collection_name}` | DELETE | Clears a vector collection. |

## Supported Uploads

- PDF
- TXT
- Markdown
- CSV
- JSON

Uploaded files are archived under `RAG/src/assets/files` by the current file-ingestion route before text extraction.

## Environment

Copy the example file:

```bash
cp RAG/.env.example RAG/.env
```

Common values:

```bash
RAG_HOST=0.0.0.0
RAG_PORT=8001
RAG_PREFIX=/rag
RAG_CORS_ORIGINS=*
RAG_VECTOR_STORE=QDRANT
RAG_VECTOR_STORE_PATH=./data/qdrant_db
RAG_COLLECTION_NAME=default
RAG_LLM_PROVIDER=COHERE
RAG_EMBEDDING_PROVIDER=COHERE
RAG_LLM_MODEL=command-a-03-2025
RAG_EMBEDDING_MODEL=embed-multilingual-v3.0
RAG_COHERE_API_KEY=<key>
```

OpenAI can be used instead:

```bash
RAG_LLM_PROVIDER=OPENAI
RAG_EMBEDDING_PROVIDER=OPENAI
RAG_OPENAI_API_KEY=<key>
RAG_OPENAI_API_URL=<optional-compatible-base-url>
```

## Install

From the repository root:

```bash
conda create -n rag-app python=3.12 -y
conda run -n rag-app pip install -r RAG/requirements.txt
```

The repository also includes a unified `cad` environment through `environment.yml`, which installs backend and RAG requirements together.

## Run

Run only the RAG service:

```bash
cd RAG
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

Run backend, RAG, and frontend together from the repository root:

```bash
BACKEND_ENV_NAME=cad RAG_ENV_NAME=cad bash scripts/run-backend-rag.sh
```

The runner reuses services that are already listening on their configured ports.

## Local Vector Data

Default Qdrant storage:

```text
RAG/data/qdrant_db
```

After ingestion, Qdrant stores collection data under its local storage directory. This directory is runtime data and should be managed according to the project's backup and retention policy.

## Example Requests

Health:

```bash
curl http://127.0.0.1:8001/rag/health
```

Query:

```bash
curl -X POST http://127.0.0.1:8001/rag/query \
  -H "Content-Type: application/json" \
  -d '{"question":"What are the key constraints for brick quality inspection?","top_k":5,"collection":"default"}'
```

Clear a collection:

```bash
curl -X DELETE http://127.0.0.1:8001/rag/collection/default
```

## Legacy `RAG/src`

`RAG/src` contains an older project-oriented RAG application with these route groups:

- `/api/v1/` for application metadata
- `/api/v1/data/upload/{project_id}` for file upload
- `/api/v1/data/process/{project_id}` for chunk creation
- `/api/v1/nlp/index/push/{project_id}` for vector indexing
- `/api/v1/nlp/index/info/{project_id}` for collection information
- `/api/v1/nlp/index/search/{project_id}` for vector search
- `/api/v1/nlp/index/answer/{project_id}` for RAG answers

The integration path used by the current frontend and backend is `RAG/app`.

## Tests

```bash
cd RAG
pytest tests
```
