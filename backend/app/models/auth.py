"""Pydantic models for authentication APIs."""

from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class UserRecord(BaseModel):
    """Public user profile data."""

    id: str = Field(min_length=1)
    name: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=3, max_length=320)
    created_at: str = Field(min_length=1)

    model_config = ConfigDict(extra="forbid")


class RegisterRequest(BaseModel):
    """Sign-up payload."""

    name: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=72)

    model_config = ConfigDict(extra="forbid")

    @field_validator("name")
    @classmethod
    def _clean_name(cls, value: str) -> str:
        cleaned = " ".join(value.strip().split())
        if not cleaned:
            raise ValueError("name must not be empty")
        return cleaned

    @field_validator("email")
    @classmethod
    def _clean_email(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if not _EMAIL_RE.fullmatch(cleaned):
            raise ValueError("invalid email format")
        return cleaned


class LoginRequest(BaseModel):
    """Login payload."""

    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=200)

    model_config = ConfigDict(extra="forbid")

    @field_validator("email")
    @classmethod
    def _clean_email(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if not _EMAIL_RE.fullmatch(cleaned):
            raise ValueError("invalid email format")
        return cleaned


class GoogleLoginRequest(BaseModel):
    """Google Sign-In payload."""

    credential: str = Field(min_length=1, max_length=8192)

    model_config = ConfigDict(extra="forbid")

    @field_validator("credential")
    @classmethod
    def _clean_credential(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("credential must not be empty")
        return cleaned


class GoogleAuthConfigResponse(BaseModel):
    """Google Sign-In configuration for frontend."""

    enabled: bool
    client_id: str | None = None

    model_config = ConfigDict(extra="forbid")


class AuthSuccessResponse(BaseModel):
    """Auth success response body."""

    success: bool = True
    token_type: str = "bearer"
    user: UserRecord

    model_config = ConfigDict(extra="forbid")


class CurrentUserResponse(BaseModel):
    """Current authenticated user."""

    authenticated: bool = True
    user: UserRecord

    model_config = ConfigDict(extra="forbid")


class AuthMessageResponse(BaseModel):
    """Simple auth status response."""

    success: bool
    message: str = Field(min_length=1)

    model_config = ConfigDict(extra="forbid")
