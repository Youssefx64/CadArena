"""
Vector store abstraction for the integration-ready RAG service.

Qdrant is the safe default because it can run as an isolated local file-backed
store under RAG/data. PGVector remains documented as an opt-in legacy backend
for deployments that intentionally provide a separate PostgreSQL database.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import RAGSettings


@dataclass(frozen=True)
class RetrievedSource:
    """Retrieved source document returned by vector stores."""

    text: str
    metadata: dict[str, Any]
    score: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize the source for API responses."""
        return {
            "text": self.text,
            "metadata": self.metadata,
            "score": self.score,
        }


class VectorStore:
    """Interface implemented by concrete vector store adapters."""

    def count_documents(self, collection: str) -> int | None:
        """Return document count for a collection."""
        raise NotImplementedError

    def add_documents(
        self,
        *,
        collection: str,
        ids: list[str],
        texts: list[str],
        embeddings: list[list[float]],
        metadata: list[dict[str, Any]],
        embedding_size: int,
    ) -> None:
        """Insert embedded documents into a collection."""
        raise NotImplementedError

    def search(
        self,
        *,
        collection: str,
        embedding: list[float],
        top_k: int,
        filters: dict[str, Any] | None = None,
    ) -> list[RetrievedSource]:
        """Search for sources by vector similarity."""
        raise NotImplementedError

    def clear_collection(self, collection: str) -> None:
        """Delete a vector collection."""
        raise NotImplementedError


class QdrantVectorStore(VectorStore):
    """File-backed Qdrant vector store adapter."""

    def __init__(self, settings: RAGSettings) -> None:
        self.settings = settings
        self._client = None

    @property
    def client(self):
        """Create the Qdrant client lazily."""
        if self._client is None:
            from qdrant_client import QdrantClient

            path = Path(self.settings.RAG_VECTOR_STORE_PATH)
            path.mkdir(parents=True, exist_ok=True)
            self._client = QdrantClient(path=str(path))
        return self._client

    def count_documents(self, collection: str) -> int | None:
        if not self.client.collection_exists(collection_name=collection):
            return 0
        info = self.client.get_collection(collection_name=collection)
        return int(getattr(info, "points_count", 0) or 0)

    def add_documents(
        self,
        *,
        collection: str,
        ids: list[str],
        texts: list[str],
        embeddings: list[list[float]],
        metadata: list[dict[str, Any]],
        embedding_size: int,
    ) -> None:
        self._ensure_collection(collection=collection, embedding_size=embedding_size)

        from qdrant_client import models

        points = [
            models.PointStruct(
                id=ids[index],
                vector=embeddings[index],
                payload={
                    "text": texts[index],
                    "metadata": metadata[index],
                },
            )
            for index in range(len(texts))
        ]
        self.client.upsert(collection_name=collection, points=points)

    def search(
        self,
        *,
        collection: str,
        embedding: list[float],
        top_k: int,
        filters: dict[str, Any] | None = None,
    ) -> list[RetrievedSource]:
        if not self.client.collection_exists(collection_name=collection):
            return []

        query_filter = self._build_filter(filters or {})
        if hasattr(self.client, "search"):
            results = self.client.search(
                collection_name=collection,
                query_vector=embedding,
                query_filter=query_filter,
                limit=top_k,
            )
        else:
            response = self.client.query_points(
                collection_name=collection,
                query=embedding,
                query_filter=query_filter,
                limit=top_k,
            )
            results = response.points

        sources: list[RetrievedSource] = []
        for result in results:
            payload = result.payload or {}
            sources.append(
                RetrievedSource(
                    text=str(payload.get("text", "")),
                    metadata=dict(payload.get("metadata") or {}),
                    score=getattr(result, "score", None),
                )
            )
        return sources

    def clear_collection(self, collection: str) -> None:
        if self.client.collection_exists(collection_name=collection):
            self.client.delete_collection(collection_name=collection)

    def _ensure_collection(self, *, collection: str, embedding_size: int) -> None:
        if self.client.collection_exists(collection_name=collection):
            return

        from qdrant_client import models

        distance = models.Distance.COSINE
        if self.settings.RAG_VECTOR_DISTANCE.lower() == "dot":
            distance = models.Distance.DOT
        self.client.create_collection(
            collection_name=collection,
            vectors_config=models.VectorParams(size=embedding_size, distance=distance),
        )

    @staticmethod
    def _build_filter(filters: dict[str, Any]):
        if not filters:
            return None

        from qdrant_client import models

        conditions = [
            models.FieldCondition(
                key=f"metadata.{key}",
                match=models.MatchValue(value=value),
            )
            for key, value in filters.items()
        ]
        return models.Filter(must=conditions)


class PGVectorStore(VectorStore):
    """Guarded PGVector placeholder for intentionally separate deployments."""

    def __init__(self, settings: RAGSettings) -> None:
        self.settings = settings

    def _unsupported(self) -> None:
        raise RuntimeError(
            "PGVector is preserved in legacy RAG/src and requires an approved "
            "database integration session before use through RAG/app."
        )

    def count_documents(self, collection: str) -> int | None:
        self._unsupported()
        return None

    def add_documents(
        self,
        *,
        collection: str,
        ids: list[str],
        texts: list[str],
        embeddings: list[list[float]],
        metadata: list[dict[str, Any]],
        embedding_size: int,
    ) -> None:
        self._unsupported()

    def search(
        self,
        *,
        collection: str,
        embedding: list[float],
        top_k: int,
        filters: dict[str, Any] | None = None,
    ) -> list[RetrievedSource]:
        self._unsupported()
        return []

    def clear_collection(self, collection: str) -> None:
        self._unsupported()


def create_vector_store(settings: RAGSettings) -> VectorStore:
    """Create the configured vector store adapter."""
    if settings.RAG_VECTOR_STORE == "QDRANT":
        return QdrantVectorStore(settings)
    if settings.RAG_VECTOR_STORE == "PGVECTOR":
        return PGVectorStore(settings)
    raise ValueError(f"Unsupported RAG vector store: {settings.RAG_VECTOR_STORE}")

