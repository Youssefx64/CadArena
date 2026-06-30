"""Pydantic models for the iterative design workspace endpoint."""

from __future__ import annotations

from typing import Any

from app.models.design_parser import ParseDesignModel, RecoveryMode
from pydantic import BaseModel, ConfigDict, Field, field_validator


class IterateRequest(BaseModel):
    """Request body for the iterative design endpoint."""

    prompt: str = Field(..., min_length=3, max_length=2000)
    current_layout: dict[str, Any] | None = Field(
        None,
        description=(
            "The full layout JSON from previous generation. None = start from scratch."
        ),
    )
    user_id: str | None = None
    model: ParseDesignModel = ParseDesignModel.HUGGINGFACE
    model_id: str | None = Field(default=None, min_length=1, max_length=256)
    recovery_mode: RecoveryMode = RecoveryMode.REPAIR
    selection_offset: int = Field(default=0, ge=0)

    model_config = ConfigDict(extra="forbid")

    @field_validator("prompt")
    @classmethod
    def _clean_prompt(cls, value: str) -> str:
        """Trim prompt whitespace and reject empty or too-short content."""

        cleaned = value.strip()
        if len(cleaned) < 3:
            raise ValueError("prompt must contain at least 3 non-whitespace characters")
        return cleaned


class IterateResponse(BaseModel):
    """Response body for the iterative design endpoint."""

    layout: dict[str, Any]
    dxf_path: str | None = None
    preview_token: str | None = None
    intent: str
    is_new_design: bool
    changed_rooms: list[str]
    self_review_triggered: bool = False
    error: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")
