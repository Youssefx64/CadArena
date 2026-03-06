"""Pydantic models for authenticated user profile and provider API key management."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProviderApiKeyRecord(BaseModel):
    """Provider API key metadata returned to the client."""

    provider: str = Field(min_length=2, max_length=64)
    has_key: bool = True
    masked_key: str | None = None
    created_at: str | None = None
    updated_at: str | None = None

    model_config = ConfigDict(extra="forbid")


class ProfileRecord(BaseModel):
    """Full user profile details for workspace settings."""

    id: str = Field(min_length=1)
    name: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=3, max_length=320)
    created_at: str = Field(min_length=1)
    display_name: str | None = Field(default=None, max_length=120)
    headline: str | None = Field(default=None, max_length=180)
    company: str | None = Field(default=None, max_length=160)
    website: str | None = Field(default=None, max_length=320)
    timezone: str | None = Field(default=None, max_length=80)
    avatar_url: str | None = Field(default=None, max_length=2048)
    avatar_updated_at: str | None = None
    profile_created_at: str | None = None
    profile_updated_at: str | None = None

    model_config = ConfigDict(extra="forbid")


class ProfileResponse(BaseModel):
    """Profile payload with configured provider keys."""

    success: bool = True
    profile: ProfileRecord
    providers: list[ProviderApiKeyRecord] = Field(default_factory=list)
    available_providers: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class ProfileUpdateRequest(BaseModel):
    """Editable profile fields."""

    display_name: str | None = Field(default=None, max_length=120)
    headline: str | None = Field(default=None, max_length=180)
    company: str | None = Field(default=None, max_length=160)
    website: str | None = Field(default=None, max_length=320)
    timezone: str | None = Field(default=None, max_length=80)

    model_config = ConfigDict(extra="forbid")

    @field_validator("display_name", "headline", "company", "website", "timezone")
    @classmethod
    def _clean_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = " ".join(value.strip().split())
        return cleaned or None


class ProviderApiKeyUpsertRequest(BaseModel):
    """Payload to create/update a provider API key for current user."""

    api_key: str = Field(min_length=1, max_length=4096)

    model_config = ConfigDict(extra="forbid")

    @field_validator("api_key")
    @classmethod
    def _clean_api_key(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("api_key must not be empty")
        return cleaned


class ProfileActionResponse(BaseModel):
    """Generic success message for profile actions."""

    success: bool
    message: str = Field(min_length=1)

    model_config = ConfigDict(extra="forbid")
