from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


ArchChatRole = Literal["user", "assistant", "system", "error"]


class ArchChatThreadRecord(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    last_message_at: str | None = None


class ArchChatMessageRecord(BaseModel):
    id: str
    role: ArchChatRole
    content: str
    created_at: str
    rag_sources: Any | None = None


class ListThreadsResponse(BaseModel):
    threads: list[ArchChatThreadRecord]


class CreateThreadResponse(BaseModel):
    thread: ArchChatThreadRecord


class RenameThreadRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=160)


class SendMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)
    top_k: int = Field(5, ge=1, le=20)
    collection: str = Field("default", min_length=1, max_length=80)
    filters: dict[str, Any] | None = None
    llm_provider: str | None = Field(default=None, description="COHERE, OPENAI, or OLLAMA")
    llm_model: str | None = Field(default=None, description="Model name override")


class SendMessageResponse(BaseModel):
    user_message: ArchChatMessageRecord
    assistant_message: ArchChatMessageRecord
    sources: list[dict[str, Any]] = []
    thread: ArchChatThreadRecord

