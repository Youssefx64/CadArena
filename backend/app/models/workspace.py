"""Pydantic models for workspace projects and chat persistence APIs."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.design_parser import (
    LayoutMetrics,
    ParseDesignModel,
    ParsedDesignIntent,
    RecoveryMode,
)


class ProjectRecord(BaseModel):
    """Project metadata for sidebar listing."""

    id: str = Field(min_length=1)
    name: str = Field(min_length=1, max_length=120)
    created_at: str = Field(min_length=1)
    updated_at: str = Field(min_length=1)
    last_message_at: str | None = None
    message_count: int = Field(ge=0)

    model_config = ConfigDict(extra="forbid")


class ProjectListResponse(BaseModel):
    """Response body for listing user projects."""

    projects: list[ProjectRecord]

    model_config = ConfigDict(extra="forbid")


class CreateProjectRequest(BaseModel):
    """Create project payload."""

    user_id: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=120)

    model_config = ConfigDict(extra="forbid")

    @field_validator("name")
    @classmethod
    def _clean_name(cls, value: str) -> str:
        cleaned = " ".join(value.strip().split())
        if not cleaned:
            raise ValueError("name must not be empty")
        return cleaned


class CreateProjectForCurrentUserRequest(BaseModel):
    """Create project payload for authenticated routes."""

    name: str = Field(min_length=1, max_length=120)

    model_config = ConfigDict(extra="forbid")

    @field_validator("name")
    @classmethod
    def _clean_name(cls, value: str) -> str:
        cleaned = " ".join(value.strip().split())
        if not cleaned:
            raise ValueError("name must not be empty")
        return cleaned


class RenameProjectRequest(BaseModel):
    """Rename project payload."""

    user_id: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=120)

    model_config = ConfigDict(extra="forbid")

    @field_validator("name")
    @classmethod
    def _clean_name(cls, value: str) -> str:
        cleaned = " ".join(value.strip().split())
        if not cleaned:
            raise ValueError("name must not be empty")
        return cleaned


class RenameProjectForCurrentUserRequest(BaseModel):
    """Rename project payload for authenticated routes."""

    name: str = Field(min_length=1, max_length=120)

    model_config = ConfigDict(extra="forbid")

    @field_validator("name")
    @classmethod
    def _clean_name(cls, value: str) -> str:
        cleaned = " ".join(value.strip().split())
        if not cleaned:
            raise ValueError("name must not be empty")
        return cleaned


class ChatMessageRecord(BaseModel):
    """Stored chat message."""

    id: str = Field(min_length=1)
    role: Literal["user", "assistant", "error", "system"]
    text: str = Field(min_length=1)
    created_at: str = Field(min_length=1)
    file_token: str | None = None
    dxf_name: str | None = None
    model_used: str | None = None
    provider_used: str | None = None

    model_config = ConfigDict(extra="forbid")


class ProjectMessagesResponse(BaseModel):
    """Project detail with persisted chat thread."""

    project: ProjectRecord
    messages: list[ChatMessageRecord]

    model_config = ConfigDict(extra="forbid")


class WorkspaceGenerateDxfRequest(BaseModel):
    """Generate DXF for a project prompt and persist chat messages."""

    user_id: str = Field(min_length=1, max_length=128)
    prompt: str = Field(min_length=1, max_length=12000)
    model: ParseDesignModel
    # Preserve the existing route shape while allowing concrete cloud model selection.
    model_id: str | None = Field(default=None, min_length=1, max_length=256)
    recovery_mode: RecoveryMode = RecoveryMode.REPAIR

    model_config = ConfigDict(extra="forbid")

    @field_validator("prompt")
    @classmethod
    def _clean_prompt(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("prompt must not be empty")
        return cleaned


class WorkspaceGenerateDxfForCurrentUserRequest(BaseModel):
    """Generate DXF request for authenticated routes."""

    prompt: str = Field(min_length=1, max_length=12000)
    model: ParseDesignModel
    # Preserve the existing route shape while allowing concrete cloud model selection.
    model_id: str | None = Field(default=None, min_length=1, max_length=256)
    recovery_mode: RecoveryMode = RecoveryMode.REPAIR

    model_config = ConfigDict(extra="forbid")

    @field_validator("prompt")
    @classmethod
    def _clean_prompt(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("prompt must not be empty")
        return cleaned


class WorkspaceGenerateDxfSuccessResponse(BaseModel):
    """Successful workspace DXF generation response."""

    success: Literal[True]
    project_id: str
    user_message_id: str
    assistant_message_id: str
    model_used: str
    provider_used: str
    failover_triggered: bool = False
    self_review_triggered: bool = False
    latency_ms: float = Field(ge=0)
    file_token: str = Field(min_length=1)
    dxf_name: str = Field(min_length=1)
    data: ParsedDesignIntent
    metrics: LayoutMetrics

    model_config = ConfigDict(extra="forbid")
