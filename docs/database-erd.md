# Database ERD - CadArena

## Purpose
This document defines the relational data model used by CadArena's backend services. It is written for academic documentation and uses valid Mermaid ER diagram syntax.

## Database Scope
CadArena currently uses a PostgreSQL-compatible persistence layer for the main backend. The connection is resolved from `CADARENA_DATABASE_URL` by `backend/app/services/postgres_compat.py`. Storage modules still use a compatibility API with `?` placeholders, but requests are executed through `psycopg2`.

The backend initializes these data areas during FastAPI startup:

- Workspace storage: `projects` and `messages`
- Authentication and profile storage: `users`, `user_profiles`, and `user_provider_api_keys`
- Community storage: `community_questions`, `community_answers`, and `community_votes`
- ArchChat storage: `archchat_threads` and `archchat_messages` when `CADARENA_DATABASE_URL` or `CADARENA_ARCHCHAT_DATABASE_URL` is configured

The standalone RAG API under `RAG/app` uses local Qdrant storage by default and does not create relational tables. The older RAG application under `RAG/src` defines a separate SQLAlchemy schema with tables named `projects`, `assets`, and `chunks`; they are shown below with a `rag_` prefix only to distinguish them from the backend workspace tables in this documentation diagram.

## Relationship Diagram

```mermaid
erDiagram
    users {
        TEXT id PK
        TEXT name "not null"
        TEXT email "not null unique"
        TEXT password_hash "not null"
        TEXT created_at "not null"
    }

    user_profiles {
        TEXT user_id PK
        TEXT display_name
        TEXT headline
        TEXT company
        TEXT website
        TEXT timezone
        TEXT profile_image_path
        TEXT profile_image_updated_at
        TEXT created_at "not null"
        TEXT updated_at "not null"
    }

    user_provider_api_keys {
        TEXT id PK
        TEXT user_id FK
        TEXT provider "not null"
        TEXT api_key "encrypted value"
        TEXT created_at "not null"
        TEXT updated_at "not null"
    }

    projects {
        TEXT id PK
        TEXT user_id "application owner"
        TEXT name "not null"
        TEXT created_at "not null"
        TEXT updated_at "not null"
    }

    messages {
        TEXT id PK
        TEXT project_id FK
        TEXT role "user assistant error system"
        TEXT text "not null"
        TEXT created_at "not null"
        TEXT dxf_path
        TEXT dxf_name
        TEXT model_used
        TEXT provider_used
    }

    community_questions {
        TEXT id PK
        TEXT author_id "application user id"
        TEXT author_name "not null"
        TEXT discipline "not null"
        TEXT title "not null"
        TEXT body "not null"
        TEXT tags_json "json array"
        INTEGER score "bounded aggregate"
        INTEGER view_count "not null"
        TEXT accepted_answer_id
        TEXT created_at "not null"
        TEXT updated_at "not null"
        TEXT last_activity_at "not null"
    }

    community_answers {
        TEXT id PK
        TEXT question_id FK
        TEXT author_id "application user id"
        TEXT author_name "not null"
        TEXT body "not null"
        INTEGER score "bounded aggregate"
        INTEGER accepted "boolean integer"
        TEXT created_at "not null"
        TEXT updated_at "not null"
    }

    community_votes {
        TEXT id PK
        TEXT user_id FK
        TEXT question_id FK
        TEXT answer_id FK
        INTEGER value "minus one zero one"
        TEXT created_at "not null"
        TEXT updated_at "not null"
    }

    archchat_threads {
        VARCHAR id PK
        VARCHAR user_id "application user id"
        VARCHAR title "not null"
        TIMESTAMP created_at "not null"
        TIMESTAMP updated_at "not null"
        TIMESTAMP last_message_at
    }

    archchat_messages {
        VARCHAR id PK
        VARCHAR thread_id FK
        VARCHAR role "user assistant system error"
        TEXT content "not null"
        TIMESTAMP created_at "not null"
        JSON rag_sources
    }

    rag_projects {
        INTEGER id PK
        UUID project_uuid "unique"
        TIMESTAMP created_at "not null"
        TIMESTAMP updated_at
    }

    rag_assets {
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

    rag_chunks {
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

    users ||--|| user_profiles : owns_profile
    users ||--o{ user_provider_api_keys : stores_keys
    users ||--o{ projects : owns_projects
    projects ||--o{ messages : contains_messages
    users ||--o{ community_questions : authors_questions
    users ||--o{ community_answers : authors_answers
    users ||--o{ community_votes : casts_votes
    community_questions ||--o{ community_answers : has_answers
    community_questions ||--o{ community_votes : receives_question_votes
    community_answers ||--o{ community_votes : receives_answer_votes
    users ||--o{ archchat_threads : owns_threads
    archchat_threads ||--o{ archchat_messages : contains_messages
    rag_projects ||--o{ rag_assets : owns_assets
    rag_projects ||--o{ rag_chunks : owns_chunks
    rag_assets ||--o{ rag_chunks : contains_chunks
```

## Main Backend Tables

| Table | Service owner | Notes |
| --- | --- | --- |
| `users` | Authentication | Stores account identity and password hash. |
| `user_profiles` | Profile | Stores display profile, website, timezone, and avatar metadata. |
| `user_provider_api_keys` | Profile | Stores encrypted provider API keys with `UNIQUE(user_id, provider)`. |
| `projects` | Workspace | Stores user-scoped workspace projects. Ownership is enforced by service queries. |
| `messages` | Workspace | Stores chat history and generated DXF metadata for a project. |
| `community_questions` | Community | Stores engineering questions with tags, discipline, score, views, and activity timestamps. |
| `community_answers` | Community | Stores answers for questions with accepted and score fields. |
| `community_votes` | Community | Stores the intended per-user voting model for question and answer votes. |
| `archchat_threads` | ArchChat | Stores authenticated RAG chat threads. |
| `archchat_messages` | ArchChat | Stores thread messages and optional RAG source metadata. |

## Integrity Rules

- `user_profiles.user_id` and `user_provider_api_keys.user_id` reference `users.id` with cascade deletion.
- `messages.project_id` references `projects.id` with cascade deletion.
- `community_answers.question_id` references `community_questions.id` with cascade deletion.
- `community_votes.user_id`, `community_votes.question_id`, and `community_votes.answer_id` reference their parent tables with cascade deletion.
- `archchat_messages.thread_id` references `archchat_threads.id` with cascade deletion through SQLAlchemy relationships.
- `projects.user_id`, `community_questions.author_id`, `community_answers.author_id`, and `archchat_threads.user_id` are application-level user links resolved by service queries.

## Persistence Notes

- Generated DXF, PNG, PDF, and avatar files are stored on disk under `backend/output`; database rows store metadata and paths rather than binary content.
- File access is mediated by session or workspace file tokens from `file_token_registry`.
- Provider API keys are encrypted with Fernet using `PROVIDER_KEY_SECRET`.
- ArchChat can use the unified backend database URL or its own `CADARENA_ARCHCHAT_DATABASE_URL`.
- The RAG service stores vectors under `RAG/data/qdrant_db` when `RAG_VECTOR_STORE=QDRANT`.
