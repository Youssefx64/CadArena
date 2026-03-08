# Docker

CadArena can run as a single container because the frontend is served directly by the FastAPI backend.

## Files

- [`docker/Dockerfile`](/home/mango/Coding/Projects/CadArena/docker/Dockerfile): builds the application image
- [`docker/docker-compose.yml`](/home/mango/Coding/Projects/CadArena/docker/docker-compose.yml): runs the app with persistent data and output volumes

## Prerequisites

Create the backend env file first:

```bash
cp backend/.env.example backend/.env
```

## Run

From the project root:

```bash
docker compose -f docker/docker-compose.yml up --build
```

Then open `http://localhost:8000`.

## Persistence

The compose setup keeps runtime files on the host:

- `backend/data` for local databases
- `backend/output` for generated DXF and exported assets

## Stop

```bash
docker compose -f docker/docker-compose.yml down
```
