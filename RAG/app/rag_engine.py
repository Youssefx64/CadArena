"""
RAG Engine for the integration-ready API wrapper.

The engine coordinates text chunking, embeddings, vector storage, retrieval,
and answer generation while keeping all runtime state inside the RAG project.
"""
from __future__ import annotations

from functools import lru_cache
import logging
from typing import Any
from uuid import uuid4

from .config import get_rag_settings
from .embeddings import EmbeddingClient, GenerationClient
from .vector_store import VectorStore, create_vector_store

logger = logging.getLogger(__name__)


class RAGEngine:
    """Core RAG orchestration used by the FastAPI router."""

    def __init__(self) -> None:
        self.settings = get_rag_settings()
        self.vector_store_type = self.settings.RAG_VECTOR_STORE
        self.embedding_model_name = self.settings.RAG_EMBEDDING_MODEL
        self._vector_store: VectorStore | None = None
        self._embedder: EmbeddingClient | None = None
        self._generator: GenerationClient | None = None

    @property
    def vector_store(self) -> VectorStore:
        """Return the lazy vector store adapter."""
        if self._vector_store is None:
            self._vector_store = create_vector_store(self.settings)
        return self._vector_store

    @property
    def embedder(self) -> EmbeddingClient:
        """Return the lazy embedding client."""
        if self._embedder is None:
            self._embedder = EmbeddingClient(self.settings)
        return self._embedder

    @property
    def generator(self) -> GenerationClient:
        """Return the lazy generation client."""
        if self._generator is None:
            self._generator = GenerationClient(self.settings)
        return self._generator

    def count_documents(self, collection: str | None = None) -> int | None:
        """Return total document count for a collection."""
        collection_name = collection or self.settings.RAG_COLLECTION_NAME
        return self.vector_store.count_documents(collection_name)

    def ingest(
        self,
        *,
        documents: list[str],
        metadata: list[dict[str, Any]] | None = None,
        collection: str = "default",
    ) -> dict[str, Any]:
        """Chunk, embed, and store raw text documents."""
        if not documents:
            return {"ingested": 0, "failed": 0, "collection": collection}

        chunks = self._chunk_documents(documents=documents, metadata=metadata or [])
        if not chunks:
            return {"ingested": 0, "failed": 0, "collection": collection}

        texts = [chunk["text"] for chunk in chunks]
        embeddings = self.embedder.embed_documents(texts)
        ids = [str(uuid4()) for _ in chunks]

        self.vector_store.add_documents(
            collection=collection,
            ids=ids,
            texts=texts,
            embeddings=embeddings,
            metadata=[chunk["metadata"] for chunk in chunks],
            embedding_size=len(embeddings[0]) if embeddings else self.settings.RAG_EMBEDDING_SIZE,
        )

        return {"ingested": len(chunks), "failed": 0, "collection": collection}

    def query(
        self,
        *,
        question: str,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
        collection: str | None = None,
    ) -> dict[str, Any]:
        """Retrieve relevant sources and generate a grounded answer."""
        collection_name = collection or self.settings.RAG_COLLECTION_NAME
        query_embedding = self.embedder.embed_query(question)
        sources = self.vector_store.search(
            collection=collection_name,
            embedding=query_embedding,
            top_k=top_k,
            filters=filters,
        )
        source_payload = [source.to_dict() for source in sources]
        context = "\n\n".join(
            f"[Source {index + 1}]\n{source.text}"
            for index, source in enumerate(sources)
        )
        answer = self.generator.generate(question=question, context=context)
        return {
            "answer": answer,
            "sources": source_payload,
            "confidence": None,
        }

    def clear_collection(self, collection_name: str) -> None:
        """Delete a vector collection."""
        self.vector_store.clear_collection(collection_name)

    def _chunk_documents(
        self,
        *,
        documents: list[str],
        metadata: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Split documents into overlapping word chunks."""
        chunks: list[dict[str, Any]] = []
        size = max(1, self.settings.RAG_CHUNK_SIZE)
        overlap = max(0, min(self.settings.RAG_CHUNK_OVERLAP, size - 1))
        step = max(1, size - overlap)

        for doc_index, document in enumerate(documents):
            words = document.split()
            if not words:
                continue
            base_metadata = metadata[doc_index] if doc_index < len(metadata) else {}
            start = 0
            chunk_index = 0
            while start < len(words):
                end = min(start + size, len(words))
                chunk_metadata = dict(base_metadata)
                chunk_metadata.update(
                    {
                        "doc_index": doc_index,
                        "chunk_index": chunk_index,
                    }
                )
                chunks.append(
                    {
                        "text": " ".join(words[start:end]),
                        "metadata": chunk_metadata,
                    }
                )
                if end == len(words):
                    break
                start += step
                chunk_index += 1

        return chunks


@lru_cache(maxsize=1)
def get_rag_engine() -> RAGEngine:
    """Return the cached RAG engine singleton."""
    return RAGEngine()

