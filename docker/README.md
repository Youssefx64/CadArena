# Docker Setup for CadArena

CadArena can run as a single container because the frontend is served directly by the FastAPI backend.

## Files

- [`Dockerfile`](./Dockerfile) - Multi-stage build for optimized application image
- [`docker-compose.yml`](./docker-compose.yml) - Docker Compose configuration for running the app with persistent volumes

## Prerequisites

1. Install Docker and Docker Compose:
   - [Docker Desktop](https://www.docker.com/products/docker-desktop) (includes Docker Compose)
   - Or install [Docker Engine](https://docs.docker.com/engine/install/) and [Docker Compose](https://docs.docker.com/compose/install/) separately

2. Create the backend environment file:

```bash
cp backend/.env.example backend/.env
```

## Quick Start

From the project root directory:

```bash
docker compose -f docker/docker-compose.yml up --build
```

Then open your browser and navigate to:

```text
http://localhost:8000
```

## Available Commands

### Start the application

```bash
docker compose -f docker/docker-compose.yml up
```

### Start in background (detached mode)

```bash
docker compose -f docker/docker-compose.yml up -d
```

### Rebuild the image

```bash
docker compose -f docker/docker-compose.yml up --build
```

### View logs

```bash
docker compose -f docker/docker-compose.yml logs -f
```

### Stop the application

```bash
docker compose -f docker/docker-compose.yml down
```

### Remove volumes (clean slate)

```bash
docker compose -f docker/docker-compose.yml down -v
```

## Data Persistence

The Docker Compose setup maintains runtime files on the host machine:

- `backend/data/` - Local databases and data files
- `backend/output/` - Generated DXF files and exported assets

These directories are mounted as volumes, so data persists even after stopping the container.

## Environment Configuration

The application uses environment variables from `backend/.env`. Key variables:

```bash
# Database
DATABASE_URL=sqlite:///./data/cadarena.db

# API Settings
API_HOST=0.0.0.0
API_PORT=8000

# Environment
CADARENA_ENV=dev
```

## Troubleshooting

### Port already in use

If port 8000 is already in use, modify the port mapping in `docker-compose.yml`:

```yaml
ports:
  - "8001:8000"  # Maps host port 8001 to container port 8000
```

### Permission denied errors

If you encounter permission errors with volumes, ensure the `backend/data` and `backend/output` directories exist:

```bash
mkdir -p backend/data backend/output
```

### Container won't start

Check the logs for errors:

```bash
docker compose -f docker/docker-compose.yml logs
```

### Clean rebuild

Remove all containers and images, then rebuild:

```bash
docker compose -f docker/docker-compose.yml down -v
docker system prune -a
docker compose -f docker/docker-compose.yml up --build
```

## Performance Tips

- **Use BuildKit** - Faster builds with better caching:

```bash
DOCKER_BUILDKIT=1 docker compose -f docker/docker-compose.yml up --build
```

- **Limit resources** - Add resource limits in `docker-compose.yml`:

```yaml
services:
  cadarena-app:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
```

- **Use .dockerignore** - Reduces build context size

## Security Considerations

The Docker setup includes several security best practices:

- **Non-root user** - Application runs as unprivileged user
- **Minimal base image** - Uses `python:3.12-slim` for smaller attack surface
- **Health checks** - Monitors container health
- **Network isolation** - Uses custom bridge network
- **Capability dropping** - Removes unnecessary Linux capabilities

## Development vs Production

### Development

```bash
docker compose -f docker/docker-compose.yml up
```

### Production

For production deployments:

1. Use environment-specific `.env` files
2. Set `CADARENA_ENV=production`
3. Configure proper logging
4. Use a reverse proxy (nginx, Traefik)
5. Enable HTTPS/TLS
6. Use managed databases instead of SQLite
7. Configure proper backup strategies

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Python Docker Best Practices](https://docs.docker.com/language/python/build-images/)
