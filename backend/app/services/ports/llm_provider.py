"""LLM provider port."""

from __future__ import annotations

from abc import ABC, abstractmethod


class LLMProviderPort(ABC):
    """Port contract for text generation providers."""

    key: str
    model_id: str

    @abstractmethod
    async def startup(self) -> None:
        """Initialize provider resources."""

    @abstractmethod
    async def shutdown(self) -> None:
        """Release provider resources."""

    @abstractmethod
    async def generate(self, compiled_prompt: str, *, request_id: str) -> str:
        """Generate a response for the compiled prompt."""

