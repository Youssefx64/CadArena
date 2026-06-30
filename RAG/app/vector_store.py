"""
Vector store abstraction for the integration-ready RAG service.

Qdrant is the safe default because it can run as an isolated local file-backed
store under RAG/data. PGVector remains documented as an opt-in legacy backend
for deployments that intentionally provide a separate PostgreSQL database.
"""
from __future__ import annotations

from dataclasses import dataclass
import logging
from pathlib import Path
from typing import Any

from .config import RAGSettings

logger = logging.getLogger(__name__)


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

    def search_hybrid(
        self,
        *,
        collection: str,
        query_text: str,
        embedding: list[float],
        top_k: int,
        filters: dict[str, Any] | None = None,
    ) -> list[RetrievedSource]:
        """Search using a combination of vector similarity and BM25 text rank."""
        raise NotImplementedError

    def clear_collection(self, collection: str) -> None:
        """Delete a vector collection."""
        raise NotImplementedError

    def delete_document(self, collection: str, document_id: str) -> str | None:
        """Delete all documents/chunks matching a specific document_id in the collection, returning the filename if found."""
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

    def search_hybrid(
        self,
        *,
        collection: str,
        query_text: str,
        embedding: list[float],
        top_k: int,
        filters: dict[str, Any] | None = None,
    ) -> list[RetrievedSource]:
        """Search using a combination of vector similarity and BM25 text rank."""
        if not self.client.collection_exists(collection_name=collection):
            return []

        # Get larger pool of candidates semantically
        candidates = self.search(
            collection=collection,
            embedding=embedding,
            top_k=max(top_k * 3, 20),
            filters=filters
        )

        if not candidates:
            return []

        # Simple Python BM25 implementation for candidate ranking
        import math
        corpus = [doc.text.lower().split() for doc in candidates]
        query_tokens = query_text.lower().split()

        # BM25 parameters
        k1 = 1.5
        b = 0.75
        corpus_size = len(corpus)
        avgdl = sum(len(x) for x in corpus) / corpus_size if corpus_size > 0 else 0

        # Compute document frequencies
        doc_freqs = []
        doc_lengths = []
        nd = {}
        for doc in corpus:
            doc_lengths.append(len(doc))
            freqs = {}
            for word in doc:
                freqs[word] = freqs.get(word, 0) + 1
            doc_freqs.append(freqs)
            for word in freqs:
                nd[word] = nd.get(word, 0) + 1

        # Compute IDF
        idf = {}
        for word, freq in nd.items():
            idf[word] = math.log(1 + (corpus_size - freq + 0.5) / (freq + 0.5))

        # Score documents
        bm25_scores = []
        for index, freqs in enumerate(doc_freqs):
            score = 0.0
            doc_len = doc_lengths[index]
            for word in query_tokens:
                if word not in freqs:
                    continue
                freq = freqs[word]
                numerator = idf.get(word, 0.0) * freq * (k1 + 1)
                denominator = freq + k1 * (1 - b + b * doc_len / avgdl) if avgdl > 0 else 1
                score += numerator / denominator
            bm25_scores.append(score)

        # Sort candidates by BM25 score
        bm25_ranked = [
            doc for _, doc in sorted(zip(bm25_scores, candidates), key=lambda pair: pair[0], reverse=True)
        ]

        # Apply Reciprocal Rank Fusion (RRF)
        rrf_scores = {}
        k_constant = 60
        for rank, doc in enumerate(candidates):
            rrf_scores[doc.text] = rrf_scores.get(doc.text, 0.0) + 1.0 / (rank + 1 + k_constant)

        for rank, doc in enumerate(bm25_ranked):
            if doc.text not in rrf_scores:
                rrf_scores[doc.text] = 0.0
            rrf_scores[doc.text] += 1.0 / (rank + 1 + k_constant)

        # Build final merged result list
        doc_map = {doc.text: doc for doc in candidates}
        sorted_texts = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
        
        merged_results = []
        for text in sorted_texts[:top_k]:
            orig_doc = doc_map[text]
            merged_results.append(
                RetrievedSource(
                    text=orig_doc.text,
                    metadata=orig_doc.metadata,
                    score=rrf_scores[text]
                )
            )
        return merged_results

    def clear_collection(self, collection: str) -> None:
        if not self.client.collection_exists(collection_name=collection):
            return

        from qdrant_client import models

        # Clear all points while preserving the collection configuration
        self.client.delete(
            collection_name=collection,
            points_selector=models.Filter(must=[]),
        )

    def delete_document(self, collection: str, document_id: str) -> str | None:
        if not self.client.collection_exists(collection_name=collection):
            return None

        from qdrant_client import models

        query_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="metadata.document_id",
                    match=models.MatchValue(value=document_id),
                )
            ]
        )

        filename = None
        try:
            records, _ = self.client.scroll(
                collection_name=collection,
                scroll_filter=query_filter,
                limit=1,
                with_payload=True,
            )
            if records and records[0].payload:
                filename = records[0].payload.get("metadata", {}).get("filename")
        except Exception as e:
            logger.error(f"Error scrolling for document_id {document_id}: {e}")

        self.client.delete(
            collection_name=collection,
            points_selector=query_filter,
        )
        return filename

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

    def search_hybrid(
        self,
        *,
        collection: str,
        query_text: str,
        embedding: list[float],
        top_k: int,
        filters: dict[str, Any] | None = None,
    ) -> list[RetrievedSource]:
        self._unsupported()
        return []

    def clear_collection(self, collection: str) -> None:
        self._unsupported()

    def delete_document(self, collection: str, document_id: str) -> str | None:
        self._unsupported()
        return None


def create_vector_store(settings: RAGSettings) -> VectorStore:
    """Create the configured vector store adapter."""
    if settings.RAG_VECTOR_STORE == "QDRANT":
        return QdrantVectorStore(settings)
    if settings.RAG_VECTOR_STORE == "PGVECTOR":
        return PGVectorStore(settings)
    raise ValueError(f"Unsupported RAG vector store: {settings.RAG_VECTOR_STORE}")

