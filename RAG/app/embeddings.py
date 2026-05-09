"""
Embedding and generation clients for the integration-ready RAG service.

These wrappers preserve the existing RAG project's Cohere/OpenAI provider
choices while keeping imports lazy so smoke tests and startup do not require
cloud SDKs or API keys.
"""
from __future__ import annotations

from typing import Any

from .config import RAGSettings


class EmbeddingClient:
    """Thin provider wrapper for Cohere and OpenAI embeddings."""

    def __init__(self, settings: RAGSettings) -> None:
        self.settings = settings
        self.provider = settings.RAG_EMBEDDING_PROVIDER
        self.model = settings.RAG_EMBEDDING_MODEL

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed document chunks using the configured provider."""
        return self._embed(texts=texts, input_type="search_document")

    def embed_query(self, text: str) -> list[float]:
        """Embed a single query using the configured provider."""
        embeddings = self._embed(texts=[text], input_type="search_query")
        return embeddings[0]

    def _embed(self, texts: list[str], input_type: str) -> list[list[float]]:
        if self.provider == "COHERE":
            return self._embed_with_cohere(texts=texts, input_type=input_type)
        if self.provider == "OPENAI":
            return self._embed_with_openai(texts=texts)
        raise ValueError(f"Unsupported RAG embedding provider: {self.provider}")

    def _embed_with_cohere(self, texts: list[str], input_type: str) -> list[list[float]]:
        api_key = self.settings.RAG_COHERE_API_KEY.strip()
        if not api_key:
            raise RuntimeError("RAG_COHERE_API_KEY is required for Cohere embeddings")

        import cohere

        client = cohere.Client(api_key=api_key)
        response = client.embed(
            model=self.model,
            texts=[self._trim(text) for text in texts],
            input_type=input_type,
            embedding_types=["float"],
        )
        embeddings = getattr(response.embeddings, "float", None)
        if not embeddings:
            raise RuntimeError("Cohere returned no embeddings")
        return [list(vector) for vector in embeddings]

    def _embed_with_openai(self, texts: list[str]) -> list[list[float]]:
        api_key = self.settings.RAG_OPENAI_API_KEY.strip()
        if not api_key:
            raise RuntimeError("RAG_OPENAI_API_KEY is required for OpenAI embeddings")

        from openai import OpenAI

        client_kwargs: dict[str, Any] = {"api_key": api_key}
        if self.settings.RAG_OPENAI_API_URL.strip():
            client_kwargs["base_url"] = self.settings.RAG_OPENAI_API_URL.strip()
        client = OpenAI(**client_kwargs)
        response = client.embeddings.create(
            model=self.model,
            input=[self._trim(text) for text in texts],
        )
        return [list(item.embedding) for item in response.data]

    def _trim(self, text: str) -> str:
        """Apply the legacy RAG maximum input length before provider calls."""
        return text[: self.settings.RAG_INPUT_MAX_CHARACTERS].strip()


class GenerationClient:
    """Thin provider wrapper for Cohere and OpenAI answer generation."""

    def __init__(self, settings: RAGSettings) -> None:
        self.settings = settings
        self.provider = settings.RAG_LLM_PROVIDER
        self.model = settings.RAG_LLM_MODEL

    def generate(self, question: str, context: str) -> str:
        """Generate a grounded answer using the configured provider."""
        prompt = self._build_prompt(question=question, context=context)
        if self.provider == "COHERE":
            return self._generate_with_cohere(prompt)
        if self.provider == "OPENAI":
            return self._generate_with_openai(prompt)
        raise ValueError(f"Unsupported RAG LLM provider: {self.provider}")

    def _generate_with_cohere(self, prompt: str) -> str:
        api_key = self.settings.RAG_COHERE_API_KEY.strip()
        if not api_key:
            raise RuntimeError("RAG_COHERE_API_KEY is required for Cohere generation")

        import cohere

        client = cohere.Client(api_key=api_key)
        response = client.chat(
            model=self.model,
            message=prompt,
            temperature=self.settings.RAG_GENERATION_TEMPERATURE,
            max_tokens=self.settings.RAG_GENERATION_MAX_TOKENS,
        )
        answer = getattr(response, "text", None)
        if not answer:
            raise RuntimeError("Cohere returned no answer")
        return answer.strip()

    def _generate_with_openai(self, prompt: str) -> str:
        api_key = self.settings.RAG_OPENAI_API_KEY.strip()
        if not api_key:
            raise RuntimeError("RAG_OPENAI_API_KEY is required for OpenAI generation")

        from openai import OpenAI

        client_kwargs: dict[str, Any] = {"api_key": api_key}
        if self.settings.RAG_OPENAI_API_URL.strip():
            client_kwargs["base_url"] = self.settings.RAG_OPENAI_API_URL.strip()
        client = OpenAI(**client_kwargs)
        response = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=self.settings.RAG_GENERATION_MAX_TOKENS,
            temperature=self.settings.RAG_GENERATION_TEMPERATURE,
        )
        answer = response.choices[0].message.content
        if not answer:
            raise RuntimeError("OpenAI returned no answer")
        return answer.strip()

    @staticmethod
    def _build_prompt(question: str, context: str) -> str:
        """Build the engineering-focused grounded RAG prompt."""
        return "\n\n".join(
            [
                "You are CadArena's RAG assistant for civil engineers, architects, BIM/CAD users, and construction teams.",
                "Answer using only the provided source documents. Do not invent code clauses, dimensions, loads, material strengths, or regulatory requirements.",
                "If the documents are insufficient, say that the answer is not available in the indexed context and mention what document is needed.",
                "When useful, organize the answer as: direct answer, engineering considerations, source-backed notes, and assumptions.",
                "Keep the same language as the user's question when possible, including Arabic.",
                "For safety-critical structural or code decisions, state that a licensed engineer must verify the final design.",
                "Cite retrieved evidence by source number when the answer depends on it.",
                f"Source documents:\n{context or '[No relevant documents retrieved]'}",
                f"Question:\n{question}",
                "Answer:",
            ]
        )
