# Legacy RAG SQL Schema

This schema belongs to the older `RAG/src` application. The current integration-ready RAG service in `RAG/app` uses Qdrant by default, so use these tables only when running or maintaining the legacy API.

## Tables

| ORM class | Table | Purpose |
| --- | --- | --- |
| `Project` | `projects` | Legacy RAG project record. |
| `Asset` | `assets` | Uploaded file metadata for a project. |
| `DataChunk` | `chunks` | Processed text chunks linked to a project and asset. |

## ERD

```mermaid
erDiagram
    projects {
        INTEGER id PK
        UUID project_uuid "unique"
        TIMESTAMP created_at "not null"
        TIMESTAMP updated_at
    }

    assets {
        INTEGER asset_id PK
        UUID asset_uuid "unique"
        VARCHAR asset_type "not null"
        VARCHAR asset_name "not null"
        INTEGER asset_size "not null"
        JSON asset_config
        INTEGER asset_project_id FK
        TIMESTAMP created_at "not null"
        TIMESTAMP updated_at
    }

    chunks {
        INTEGER chunk_id PK
        UUID chunk_uuid "unique"
        VARCHAR chunk_content "not null"
        JSON chunk_metadata
        INTEGER chunk_order "not null"
        INTEGER chunk_project_id FK
        INTEGER chunk_asset_id FK
        TIMESTAMP created_at "not null"
        TIMESTAMP updated_at
    }

    projects ||--o{ assets : owns_assets
    projects ||--o{ chunks : owns_chunks
    assets ||--o{ chunks : contains_chunks
```

## Notes

- `RAG/src/main.py` can create missing tables on startup.
- Alembic files live in `alembic/`; see `alembic/README` for migration commands.
- These tables use generic names such as `projects`, so avoid sharing the same database with other CadArena schemas unless the deployment is reviewed.
