"""Authentication router for sign-up, login, logout, and current user."""

from __future__ import annotations

import secrets

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.core.auth import AuthenticatedUser, get_current_user
from app.models.auth import (
    AuthMessageResponse,
    AuthSuccessResponse,
    CurrentUserResponse,
    GoogleAuthConfigResponse,
    GoogleLoginRequest,
    LoginRequest,
    RegisterRequest,
    UserRecord,
)
from app.services.auth_security import (
    access_token_ttl_seconds,
    auth_cookie_name,
    auth_cookie_secure,
    create_access_token,
    google_client_id,
    hash_password,
    verify_password,
)
from app.services.auth_storage import create_user, get_user_by_email

try:
    from google.auth.transport import requests as google_requests
    from google.oauth2 import id_token as google_id_token
except ImportError:  # pragma: no cover - dependency can be absent in some local setups
    google_requests = None
    google_id_token = None

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_auth_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=auth_cookie_name(),
        value=token,
        max_age=access_token_ttl_seconds(),
        httponly=True,
        samesite="lax",
        secure=auth_cookie_secure(),
        path="/",
    )
    response.headers["Cache-Control"] = "no-store"


def _to_user_record(user: dict) -> UserRecord:
    return UserRecord(
        id=user["id"],
        name=user["name"],
        email=user["email"],
        created_at=user["created_at"],
    )


@router.post("/register", response_model=AuthSuccessResponse, status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest, response: Response):
    if get_user_by_email(email=request.email) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    try:
        password_hash = hash_password(request.password)
        user = create_user(name=request.name, email=request.email, password_hash=password_hash)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    token = create_access_token(user_id=user["id"], email=user["email"])
    _set_auth_cookie(response, token)

    return AuthSuccessResponse(
        success=True,
        token_type="bearer",
        user=_to_user_record(user),
    )


@router.post("/login", response_model=AuthSuccessResponse)
def login(request: LoginRequest, response: Response):
    user = get_user_by_email(email=request.email)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    if not verify_password(request.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    token = create_access_token(user_id=user["id"], email=user["email"])
    _set_auth_cookie(response, token)

    return AuthSuccessResponse(
        success=True,
        token_type="bearer",
        user=_to_user_record(user),
    )


@router.get("/google/config", response_model=GoogleAuthConfigResponse)
def google_config():
    client_id = google_client_id()
    if not client_id:
        return GoogleAuthConfigResponse(enabled=False, client_id=None)
    return GoogleAuthConfigResponse(enabled=True, client_id=client_id)


@router.post("/google", response_model=AuthSuccessResponse)
def google_login(request: GoogleLoginRequest, response: Response):
    client_id = google_client_id()
    if not client_id:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Google login is not configured")

    if google_id_token is None or google_requests is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Google login is unavailable")

    try:
        token_data = google_id_token.verify_oauth2_token(request.credential, google_requests.Request(), client_id)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Google credential") from exc

    email = str(token_data.get("email", "")).strip().lower()
    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Google account email is missing")

    if token_data.get("email_verified") is False:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Google account email is not verified")

    raw_name = str(token_data.get("name") or token_data.get("given_name") or "").strip()
    fallback_name = email.split("@", 1)[0] if "@" in email else "Google User"
    name = raw_name or fallback_name

    user = get_user_by_email(email=email)
    if user is None:
        try:
            generated_password = secrets.token_urlsafe(48)
            password_hash = hash_password(generated_password)
            user = create_user(name=name, email=email, password_hash=password_hash)
        except ValueError:
            user = get_user_by_email(email=email)

    if user is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to complete Google sign-in")

    token = create_access_token(user_id=user["id"], email=user["email"])
    _set_auth_cookie(response, token)

    return AuthSuccessResponse(
        success=True,
        token_type="bearer",
        user=_to_user_record(user),
    )


@router.post("/logout", response_model=AuthMessageResponse)
def logout(response: Response):
    response.delete_cookie(key=auth_cookie_name(), path="/")
    response.headers["Cache-Control"] = "no-store"
    return AuthMessageResponse(success=True, message="Logged out")


@router.get("/me", response_model=CurrentUserResponse)
def me(current_user: AuthenticatedUser = Depends(get_current_user)):
    return CurrentUserResponse(
        authenticated=True,
        user=UserRecord(id=current_user.id, name=current_user.name, email=current_user.email, created_at=current_user.created_at),
    )
