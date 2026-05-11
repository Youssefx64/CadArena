from __future__ import annotations

import logging
from typing import List, Union, Optional, Any

import httpx

from ..LLMInterface import LLMInterface
from ..LLMEnums import OllamaEnums, DocumentTypeEnum


class OllamaProvider(LLMInterface):
    """
    Minimal Ollama provider using the local HTTP API.
    Supports chat generation and embeddings.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        default_input_max_characters: int = 1000,
        default_generation_max_output_tokens: int = 1000,
        default_generation_temperature: float = 0.5,
        timeout_seconds: int = 120,
    ):
        self.base_url = (base_url or "http://localhost:11434").rstrip("/")
        self.default_input_max_characters = default_input_max_characters
        self.default_generation_max_output_tokens = default_generation_max_output_tokens
        self.default_generation_temperature = default_generation_temperature
        self.timeout_seconds = timeout_seconds

        self.generation_model_id: Optional[str] = None
        self.embedding_model_id: Optional[str] = None
        self.embedding_size: Optional[int] = None

        self.enums = OllamaEnums
        self.logger = logging.getLogger(__name__)

        self._client = httpx.Client(timeout=self.timeout_seconds)

    def set_generation_model(self, model_id: str):
        self.generation_model_id = model_id
        self.logger.info(f"Generation model set to {model_id}")

    def set_embedding_model(self, model_id: str, embedding_size: int):
        self.embedding_model_id = model_id
        self.embedding_size = embedding_size
        self.logger.info(
            f"Embedding model set to {model_id} and embedding size set to {embedding_size}"
        )

    def process_prompt(self, prompt: str) -> str:
        return (prompt or "")[: self.default_input_max_characters].strip()

    def _to_ollama_messages(self, chat_history: list) -> list[dict[str, Any]]:
        """
        Accepts the existing codebase chat_history format (list of dicts).
        Tries to normalize it to Ollama's expected {role, content}.
        """
        normalized: list[dict[str, Any]] = []
        for msg in chat_history or []:
            if not isinstance(msg, dict):
                continue
            role = msg.get("role")
            # OpenAIProvider uses {"role","content"}; CoHere uses {"role","text"}
            content = msg.get("content", msg.get("text", ""))
            if role and content is not None:
                normalized.append({"role": role, "content": str(content)})
        return normalized

    def generate_text(
        self,
        prompt: str,
        chat_history: list = [],
        max_output_tokens: int = None,
        temperature: float = None,
    ):
        if not self.generation_model_id:
            self.logger.error("Generation model is not set.")
            return None

        max_output_tokens = (
            max_output_tokens
            if max_output_tokens is not None
            else self.default_generation_max_output_tokens
        )
        temperature = (
            temperature
            if temperature is not None
            else self.default_generation_temperature
        )

        messages = self._to_ollama_messages(chat_history)
        messages.append(self.construct_prompt(self.process_prompt(prompt), role=OllamaEnums.USER.value))

        payload = {
            "model": self.generation_model_id,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                # Ollama uses num_predict for max tokens
                "num_predict": max_output_tokens,
            },
        }

        try:
            resp = self._client.post(f"{self.base_url}/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            self.logger.error(f"Error while generating text with Ollama: {exc}")
            return None

        message = (data or {}).get("message") or {}
        content = message.get("content")
        if not content:
            self.logger.error("Empty response from Ollama.")
            return None
        return content

    def embed_text(self, prompt: Union[str, List[str]], document_type: str = None):
        if not self.embedding_model_id:
            self.logger.error("Embedding model is not set.")
            return None

        prompts: List[str] = [prompt] if isinstance(prompt, str) else list(prompt or [])
        if not prompts:
            return []

        # Ollama doesn't need document_type, but keep signature compatible.
        _ = document_type  # noqa: F841

        embeddings: list[list[float]] = []
        for item in prompts:
            processed = self.process_prompt(item)
            payload = {"model": self.embedding_model_id, "prompt": processed}
            try:
                resp = self._client.post(f"{self.base_url}/api/embeddings", json=payload)
                resp.raise_for_status()
                data = resp.json()
            except Exception as exc:
                self.logger.error(f"Error while generating embedding with Ollama: {exc}")
                return None

            vector = (data or {}).get("embedding")
            if not vector:
                self.logger.error("Empty embeddings returned from Ollama.")
                return None
            embeddings.append(vector)

        # Update embedding size if caller didn't set it accurately
        if embeddings and (not self.embedding_size or self.embedding_size <= 0):
            self.embedding_size = len(embeddings[0])

        return embeddings

    def construct_prompt(self, prompt: str, role: str):
        # Ollama expects {role, content}
        return {"role": role, "content": prompt}

