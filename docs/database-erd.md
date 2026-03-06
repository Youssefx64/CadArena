# CadArena Database ERD

```mermaid
erDiagram
    USERS {
        TEXT id PK
        TEXT name
        TEXT email "UNIQUE"
        TEXT password_hash
        TEXT created_at
    }

    USER_PROFILES {
        TEXT user_id PK, FK
        TEXT display_name
        TEXT headline
        TEXT company
        TEXT website
        TEXT timezone
        TEXT profile_image_path
        TEXT profile_image_updated_at
        TEXT created_at
        TEXT updated_at
    }

    USER_PROVIDER_API_KEYS {
        TEXT id PK
        TEXT user_id FK
        TEXT provider "UNIQUE WITH user_id"
        TEXT api_key
        TEXT created_at
        TEXT updated_at
    }

    PROJECTS {
        TEXT id PK
        TEXT user_id "Indexed"
        TEXT name
        TEXT created_at
        TEXT updated_at
    }

    MESSAGES {
        TEXT id PK
        TEXT project_id FK
        TEXT role "user|assistant|error|system"
        TEXT text
        TEXT created_at
        TEXT dxf_path
        TEXT dxf_name
        TEXT model_used
        TEXT provider_used
    }

    USERS ||--|| USER_PROFILES : has_profile
    USERS ||--o{ USER_PROVIDER_API_KEYS : stores_keys
    USERS ||--o{ PROJECTS : owns_app_level
    PROJECTS ||--o{ MESSAGES : contains
```

Notes:
- `PROJECTS.user_id` is currently an application-level ownership link (no DB-level foreign key constraint).
- `USER_PROVIDER_API_KEYS` enforces unique pairs for `(user_id, provider)`.
- Cascading delete is enforced from `USERS -> USER_PROFILES`, `USERS -> USER_PROVIDER_API_KEYS`, and `PROJECTS -> MESSAGES`.

