"""
RAG System Configuration.

All runtime settings use the RAG_ prefix so this service can coexist with
the main CadArena backend without environment variable collisions.
"""
from __future__ import annotations

from functools import lru_cache
import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

try:  # Prefer the real Pydantic settings package when installed.
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ModuleNotFoundError:  # pragma: no cover - exercised only in lean envs.
    SettingsConfigDict = dict  # type: ignore[assignment]

    class BaseSettings(BaseModel):
        """Small fallback for local smoke tests when pydantic-settings is absent."""

        model_config = ConfigDict(extra="ignore")

        def __init__(self, **data: Any) -> None:
            env_file = data.pop("_env_file", None)
            values = _read_env_file(env_file)
            values.update(os.environ)
            for name in self.__class__.model_fields:
                if name in values and name not in data:
                    data[name] = values[name]
            super().__init__(**data)


def _read_env_file(env_file: str | os.PathLike[str] | None) -> dict[str, str]:
    """Read simple KEY=VALUE lines from an env file without mutating os.environ."""
    if env_file is None:
        env_file = Path.cwd() / ".env"

    path = Path(env_file)
    if not path.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if value and value[0] not in {"'", '"'} and "#" in value:
            value = value.split("#", 1)[0].rstrip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        values[key] = value
    return values


class RAGSettings(BaseSettings):
    """
    RAG system settings.

    Every field maps directly to an environment variable with the same name.
    Example: RAG_PORT=8001 RAG_VECTOR_STORE=QDRANT.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Server
    RAG_HOST: str = "0.0.0.0"
    RAG_PORT: int = 8001
    RAG_PREFIX: str = "/rag"
    RAG_CORS_ORIGINS: str = "*"

    # Vector store
    RAG_VECTOR_STORE: str = "QDRANT"
    RAG_VECTOR_STORE_PATH: str = "./data/qdrant_db"
    RAG_COLLECTION_NAME: str = "default"
    RAG_VECTOR_DISTANCE: str = "cosine"
    RAG_EMBEDDING_SIZE: int = 1024

    # LLM and embeddings
    RAG_LLM_PROVIDER: str = "COHERE"
    RAG_EMBEDDING_PROVIDER: str = "COHERE"
    RAG_LLM_MODEL: str = "command-a-03-2025"
    RAG_EMBEDDING_MODEL: str = "embed-multilingual-v3.0"
    RAG_OPENAI_API_KEY: str = ""
    RAG_OPENAI_API_URL: str = ""
    RAG_COHERE_API_KEY: str = ""

    # Chunking and retrieval
    RAG_CHUNK_SIZE: int = 700
    RAG_CHUNK_OVERLAP: int = 100
    RAG_TOP_K: int = 5
    RAG_INPUT_MAX_CHARACTERS: int = 4096
    RAG_GENERATION_MAX_TOKENS: int = 700
    RAG_GENERATION_TEMPERATURE: float = 0.1

    @field_validator(
        "RAG_VECTOR_STORE",
        "RAG_LLM_PROVIDER",
        "RAG_EMBEDDING_PROVIDER",
        mode="before",
    )
    @classmethod
    def _normalize_upper(cls, value: Any) -> str:
        """Normalize enum-like settings to the existing RAG provider names."""
        return str(value).strip().upper()

    @field_validator("RAG_PREFIX")
    @classmethod
    def _normalize_prefix(cls, value: str) -> str:
        """Ensure the URL prefix starts with one slash and has no trailing slash."""
        cleaned = value.strip() or "/rag"
        cleaned = "/" + cleaned.strip("/")
        return cleaned

    @property
    def cors_origins(self) -> list[str]:
        """Return CORS origins from a comma-separated string setting."""
        return [
            item.strip().strip("'\"")
            for item in self.RAG_CORS_ORIGINS.strip().strip("[]").split(",")
            if item.strip()
        ] or ["*"]

    @model_validator(mode="after")
    def _apply_legacy_rag_env_fallbacks(self) -> "RAGSettings":
        """
        Read legacy RAG/src/.env values only as local fallbacks.

        This preserves the RAG_ public interface while allowing the prepared
        wrapper to run against the existing RAG project configuration.
        """
        legacy_env = _read_env_file(Path(__file__).resolve().parents[1] / "src" / ".env")
        fallback_map = {
            "RAG_COHERE_API_KEY": "COHERE_API_KEY",
            "RAG_OPENAI_API_KEY": "OPENAI_API_KEY",
            "RAG_OPENAI_API_URL": "OPENAI_API_URL",
            "RAG_LLM_MODEL": "GENERATION_MODEL_ID",
            "RAG_EMBEDDING_MODEL": "EMBEDDING_MODEL_ID",
            "RAG_EMBEDDING_SIZE": "EMBEDDING_MODEL_SIZE",
            "RAG_LLM_PROVIDER": "GENERATION_BACKEND",
            "RAG_EMBEDDING_PROVIDER": "EMBEDDING_BACKEND",
        }
        for rag_key, legacy_key in fallback_map.items():
            current = getattr(self, rag_key)
            legacy_value = legacy_env.get(legacy_key, "").strip()
            if current in {"", None} and legacy_value:
                object.__setattr__(self, rag_key, legacy_value)

        embedding_size = legacy_env.get("EMBEDDING_MODEL_SIZE", "").strip()
        if self.RAG_EMBEDDING_SIZE == 1024 and embedding_size:
            try:
                object.__setattr__(self, "RAG_EMBEDDING_SIZE", int(embedding_size))
            except ValueError:
                pass

        return self


@lru_cache(maxsize=1)
def get_rag_settings() -> RAGSettings:
    """Return the cached RAG settings instance."""
    return RAGSettings()
