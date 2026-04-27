"""Pydantic models for the CadArena engineering community APIs."""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


CommunityDiscipline = Literal[
    "architecture",
    "civil",
    "structural",
    "construction",
    "mep",
    "materials",
    "surveying",
    "general",
]
CommunitySort = Literal["active", "newest", "score", "unanswered"]
VoteDirection = Literal[-1, 1]

_TAG_CLEAN_RE = re.compile(r"[^a-z0-9+-]+")


def _clean_text(value: str) -> str:
    return " ".join(value.strip().split())


def _normalize_tag(value: str) -> str:
    cleaned = _TAG_CLEAN_RE.sub("-", value.strip().lower()).strip("-")
    if not cleaned:
        raise ValueError("tag must not be empty")
    if len(cleaned) > 32:
        raise ValueError("tag is too long")
    return cleaned


class CommunityQuestionRecord(BaseModel):
    """Question card data used by the community feed."""

    id: str = Field(min_length=1)
    title: str = Field(min_length=1, max_length=160)
    body: str = Field(min_length=1, max_length=5000)
    tags: list[str] = Field(default_factory=list, max_length=5)
    discipline: CommunityDiscipline = "general"
    author_id: str | None = None
    author_name: str = Field(min_length=1, max_length=120)
    score: int = 0
    view_count: int = Field(ge=0)
    answer_count: int = Field(ge=0)
    accepted_answer_id: str | None = None
    created_at: str = Field(min_length=1)
    updated_at: str = Field(min_length=1)
    last_activity_at: str = Field(min_length=1)

    model_config = ConfigDict(extra="forbid")


class CommunityAnswerRecord(BaseModel):
    """Answer data for a single question."""

    id: str = Field(min_length=1)
    question_id: str = Field(min_length=1)
    body: str = Field(min_length=1, max_length=5000)
    author_id: str | None = None
    author_name: str = Field(min_length=1, max_length=120)
    score: int = 0
    accepted: bool = False
    created_at: str = Field(min_length=1)
    updated_at: str = Field(min_length=1)

    model_config = ConfigDict(extra="forbid")


class CommunityQuestionListResponse(BaseModel):
    """Community question feed response."""

    questions: list[CommunityQuestionRecord]

    model_config = ConfigDict(extra="forbid")


class CommunityQuestionDetailResponse(BaseModel):
    """Question detail response with all answers."""

    question: CommunityQuestionRecord
    answers: list[CommunityAnswerRecord]

    model_config = ConfigDict(extra="forbid")


class CreateCommunityQuestionRequest(BaseModel):
    """Create question payload."""

    title: str = Field(min_length=8, max_length=160)
    body: str = Field(min_length=20, max_length=5000)
    tags: list[str] = Field(default_factory=list, max_length=5)
    discipline: CommunityDiscipline = "general"
    author_name: str | None = Field(default=None, max_length=120)

    model_config = ConfigDict(extra="forbid")

    @field_validator("title")
    @classmethod
    def _clean_title(cls, value: str) -> str:
        cleaned = _clean_text(value)
        if len(cleaned) < 8:
            raise ValueError("title is too short")
        return cleaned

    @field_validator("body")
    @classmethod
    def _clean_body(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 20:
            raise ValueError("body is too short")
        return cleaned

    @field_validator("tags", mode="before")
    @classmethod
    def _clean_tags(cls, value) -> list[str]:
        if value is None:
            return []
        raw_items = value.split(",") if isinstance(value, str) else list(value)
        tags: list[str] = []
        seen: set[str] = set()
        for item in raw_items:
            tag = _normalize_tag(str(item))
            if tag not in seen:
                tags.append(tag)
                seen.add(tag)
            if len(tags) > 5:
                raise ValueError("maximum of 5 tags allowed")
        return tags

    @field_validator("author_name")
    @classmethod
    def _clean_author_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = _clean_text(value)
        return cleaned or None


class CreateCommunityAnswerRequest(BaseModel):
    """Create answer payload."""

    body: str = Field(min_length=20, max_length=5000)
    author_name: str | None = Field(default=None, max_length=120)

    model_config = ConfigDict(extra="forbid")

    @field_validator("body")
    @classmethod
    def _clean_body(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 20:
            raise ValueError("answer is too short")
        return cleaned

    @field_validator("author_name")
    @classmethod
    def _clean_author_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = _clean_text(value)
        return cleaned or None


class CommunityVoteRequest(BaseModel):
    """Vote payload for questions and answers."""

    direction: VoteDirection

    model_config = ConfigDict(extra="forbid")
