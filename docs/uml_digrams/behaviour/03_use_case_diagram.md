# 03 Use Case Diagram - CadArena User Capabilities

## Purpose
This use case diagram summarizes the current capabilities exposed by CadArena to guests, authenticated users, administrators of local services, and external integrations.

## Diagram

```mermaid
flowchart LR
    Guest[Guest user]
    User[Authenticated user]
    Operator[Local operator]
    ModelProvider[Model provider]
    EmbeddingProvider[Embedding provider]
    RAGService[RAG service]
    VectorStore[RAG vector store]
    SMTP[SMTP server]
    Google[Google OAuth]
    Files[File storage]

    subgraph System[CadArena system]
        Browse[Browse public pages]
        Register[Register and sign in]
        GoogleLogin[Sign in with Google]
        Profile[Manage profile and avatar]
        ProviderKeys[Manage provider API keys]
        Workspace[Manage workspace projects]
        Chat[Use workspace chat]
        Generate[Generate floor plan from prompt]
        Iterate[Refine an existing layout]
        Preview[Preview generated DXF]
        Upload[Upload existing DXF]
        Download[Download DXF]
        Export[Export PNG or PDF]
        Community[Use engineering community]
        Contact[Send contact message]
        ModelCatalog[Read parser model catalog]
        ArchChat[Use RAG-backed architecture chat]
        RagQuery[Query indexed engineering references]
        RagIngestFiles[Upload and ingest RAG files]
        RagIngestText[Ingest raw text documents]
        RagModels[List RAG models]
        RagCollection[Clear RAG collection]
        RagHealth[Check RAG health]
        Health[Check health and metrics]
        DockerRun[Run containerized service]
    end

    Guest --> Browse
    Guest --> Workspace
    Guest --> Chat
    Guest --> Generate
    Guest --> Iterate
    Guest --> Preview
    Guest --> Upload
    Guest --> Download
    Guest --> Export
    Guest --> Community
    Guest --> Contact
    Guest --> ModelCatalog

    User --> Browse
    User --> Register
    User --> GoogleLogin
    User --> Profile
    User --> ProviderKeys
    User --> Workspace
    User --> Chat
    User --> Generate
    User --> Iterate
    User --> Preview
    User --> Upload
    User --> Download
    User --> Export
    User --> Community
    User --> ArchChat
    User --> RagQuery
    User --> RagIngestFiles
    User --> ModelCatalog

    Operator --> Health
    Operator --> RagHealth
    Operator --> RagModels
    Operator --> RagIngestText
    Operator --> RagCollection
    Operator --> DockerRun

    Generate --> ModelCatalog
    Generate --> Preview
    Iterate --> Preview
    Preview --> Export
    Upload --> Preview
    ArchChat --> RAGService
    ArchChat --> RagQuery
    RagQuery --> RAGService
    RagIngestFiles --> RAGService
    RagIngestText --> RAGService
    RagModels --> RAGService
    RagCollection --> RAGService
    RagHealth --> RAGService

    ModelProvider -.-> Generate
    ModelProvider -.-> Iterate
    ModelProvider -.-> RagQuery
    EmbeddingProvider -.-> RagQuery
    EmbeddingProvider -.-> RagIngestFiles
    EmbeddingProvider -.-> RagIngestText
    VectorStore -.-> RagQuery
    VectorStore -.-> RagIngestFiles
    VectorStore -.-> RagIngestText
    VectorStore -.-> RagCollection
    VectorStore -.-> RagHealth
    SMTP -.-> Contact
    Google -.-> GoogleLogin
    Files -.-> Preview
    Files -.-> Download
    Files -.-> Export
```

## Architectural Notes
- Guests use cookie-bound workspace identity; authenticated users use the JWT-backed `/workspace/me` route set.
- The design parser can call local Ollama, Ollama Cloud compatible endpoints, Qwen-compatible cloud endpoints, or a local HuggingFace model.
- ArchChat is authenticated and delegates retrieval requests to the standalone RAG API.
- The standalone RAG API supports reference querying, text ingestion, file ingestion, model listing, collection clearing, and health checks.
- RAG ingestion uses the configured embedding provider and stores vectors in the configured vector store, Qdrant by default.
- DXF preview, download, upload, and export are token-mediated file operations.
