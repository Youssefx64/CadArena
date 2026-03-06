"""Authenticated profile management routes."""

from __future__ import annotations

import mimetypes
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.core.auth import AuthenticatedUser, get_current_user
from app.core.file_utils import BACKEND_DIR, ensure_output_dir, resolve_output_path
from app.models.profile import (
    ProfileResponse,
    ProfileUpdateRequest,
    ProfileRecord,
    ProviderApiKeyRecord,
    ProviderApiKeyUpsertRequest,
)
from app.services.auth_storage import (
    delete_user_provider_api_key,
    ensure_user_profile,
    list_user_provider_api_keys,
    supported_api_key_providers,
    update_user_profile,
    update_user_profile_image,
    upsert_user_provider_api_key,
)

router = APIRouter(prefix="/profile", tags=["profile"])

_DEFAULT_AVATAR_PATH = BACKEND_DIR / "frontend" / "assets" / "cadarena-mark.svg"
_PROFILE_IMAGE_DIR_NAME = "profile_images"
_ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
_CONTENT_TYPE_TO_EXTENSION = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/webp": ".webp",
    "image/gif": ".gif",
}
_MAX_PROFILE_IMAGE_BYTES = 5 * 1024 * 1024


def _profile_image_dir() -> Path:
    directory = ensure_output_dir() / _PROFILE_IMAGE_DIR_NAME
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _infer_image_extension(file: UploadFile) -> str:
    filename = (file.filename or "").strip()
    if filename:
        suffix = Path(filename).suffix.lower()
        if suffix in _ALLOWED_IMAGE_EXTENSIONS:
            return suffix

    content_type = (file.content_type or "").strip().lower()
    extension = _CONTENT_TYPE_TO_EXTENSION.get(content_type)
    if extension:
        return extension

    raise ValueError("Unsupported image type. Allowed: PNG, JPG, JPEG, WEBP, GIF.")


def _delete_profile_image_file(path_value: str | None) -> None:
    if not path_value:
        return
    try:
        image_path = resolve_output_path(path_value)
    except ValueError:
        return
    if image_path.exists() and image_path.is_file():
        try:
            image_path.unlink()
        except OSError:
            # best effort cleanup
            pass


def _build_profile_response(current_user: AuthenticatedUser) -> ProfileResponse:
    profile = ensure_user_profile(user_id=current_user.id, default_display_name=current_user.name)
    available_providers = list(supported_api_key_providers())

    configured_keys = list_user_provider_api_keys(user_id=current_user.id)
    configured_map = {item["provider"]: item for item in configured_keys}

    provider_records = []
    for provider in available_providers:
        configured = configured_map.get(provider)
        if configured:
            provider_records.append(
                ProviderApiKeyRecord(
                    provider=provider,
                    has_key=True,
                    masked_key=configured.get("masked_key"),
                    created_at=configured.get("created_at"),
                    updated_at=configured.get("updated_at"),
                )
            )
            continue

        provider_records.append(
            ProviderApiKeyRecord(
                provider=provider,
                has_key=False,
                masked_key=None,
                created_at=None,
                updated_at=None,
            )
        )

    profile_record = ProfileRecord(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        created_at=current_user.created_at,
        display_name=profile.get("display_name"),
        headline=profile.get("headline"),
        company=profile.get("company"),
        website=profile.get("website"),
        timezone=profile.get("timezone"),
        avatar_url="/api/v1/profile/me/avatar" if profile.get("profile_image_path") else None,
        avatar_updated_at=profile.get("profile_image_updated_at"),
        profile_created_at=profile.get("created_at"),
        profile_updated_at=profile.get("updated_at"),
    )

    return ProfileResponse(
        success=True,
        profile=profile_record,
        providers=provider_records,
        available_providers=available_providers,
    )


@router.get("/me", response_model=ProfileResponse)
def profile_me(current_user: AuthenticatedUser = Depends(get_current_user)):
    return _build_profile_response(current_user)


@router.get("/me/avatar", include_in_schema=False)
def profile_me_avatar(current_user: AuthenticatedUser = Depends(get_current_user)):
    profile = ensure_user_profile(user_id=current_user.id, default_display_name=current_user.name)
    profile_image_path = profile.get("profile_image_path")
    if profile_image_path:
        try:
            resolved = resolve_output_path(profile_image_path)
        except ValueError:
            resolved = None

        if resolved and resolved.exists() and resolved.is_file():
            media_type, _ = mimetypes.guess_type(str(resolved))
            return FileResponse(resolved, media_type=media_type or "application/octet-stream")

    return FileResponse(_DEFAULT_AVATAR_PATH, media_type="image/svg+xml")


@router.post("/me/avatar", response_model=ProfileResponse)
async def upload_profile_avatar(
    file: UploadFile = File(...),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    content_type = (file.content_type or "").strip().lower()
    if content_type and not content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image uploads are allowed.")

    try:
        extension = _infer_image_extension(file)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    blob = await file.read(_MAX_PROFILE_IMAGE_BYTES + 1)
    if not blob:
        raise HTTPException(status_code=400, detail="Uploaded image is empty.")
    if len(blob) > _MAX_PROFILE_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Image is too large. Maximum size is 5 MB.")

    existing_profile = ensure_user_profile(user_id=current_user.id, default_display_name=current_user.name)
    previous_image_path = existing_profile.get("profile_image_path")

    file_name = f"{current_user.id}_{uuid4().hex[:12]}{extension}"
    relative_path = f"{_PROFILE_IMAGE_DIR_NAME}/{file_name}"
    absolute_path = _profile_image_dir() / file_name

    try:
        absolute_path.write_bytes(blob)
        update_user_profile_image(user_id=current_user.id, profile_image_path=relative_path)
    except ValueError as exc:
        if absolute_path.exists():
            absolute_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except OSError as exc:
        if absolute_path.exists():
            absolute_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail="Failed to store profile image.") from exc

    if previous_image_path and previous_image_path != relative_path:
        _delete_profile_image_file(previous_image_path)

    return _build_profile_response(current_user)


@router.delete("/me/avatar", response_model=ProfileResponse)
def delete_profile_avatar(current_user: AuthenticatedUser = Depends(get_current_user)):
    profile = ensure_user_profile(user_id=current_user.id, default_display_name=current_user.name)
    previous_image_path = profile.get("profile_image_path")
    try:
        update_user_profile_image(user_id=current_user.id, profile_image_path=None)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    _delete_profile_image_file(previous_image_path)
    return _build_profile_response(current_user)


@router.patch("/me", response_model=ProfileResponse)
def update_profile_me(
    request: ProfileUpdateRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    existing_profile = ensure_user_profile(user_id=current_user.id, default_display_name=current_user.name)
    updates = request.model_dump(exclude_unset=True)

    merged_payload = {
        "display_name": existing_profile.get("display_name"),
        "headline": existing_profile.get("headline"),
        "company": existing_profile.get("company"),
        "website": existing_profile.get("website"),
        "timezone": existing_profile.get("timezone"),
    }
    merged_payload.update(updates)

    try:
        update_user_profile(
            user_id=current_user.id,
            display_name=merged_payload["display_name"],
            headline=merged_payload["headline"],
            company=merged_payload["company"],
            website=merged_payload["website"],
            timezone=merged_payload["timezone"],
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return _build_profile_response(current_user)


@router.put("/me/providers/{provider}", response_model=ProfileResponse)
def upsert_profile_provider_key(
    provider: str,
    request: ProviderApiKeyUpsertRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    try:
        upsert_user_provider_api_key(user_id=current_user.id, provider=provider, api_key=request.api_key)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return _build_profile_response(current_user)


@router.delete("/me/providers/{provider}", response_model=ProfileResponse)
def delete_profile_provider_key(
    provider: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    try:
        delete_user_provider_api_key(user_id=current_user.id, provider=provider)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return _build_profile_response(current_user)
