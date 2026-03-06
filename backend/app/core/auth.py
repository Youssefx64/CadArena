"""Authentication dependencies for protected routes."""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.services.auth_security import auth_cookie_name, decode_access_token
from app.services.auth_storage import get_user_by_id

_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthenticatedUser:
    """Authenticated user resolved from JWT token."""

    id: str
    name: str
    email: str
    created_at: str


def _extract_token(
    *,
    request: Request,
    credentials: HTTPAuthorizationCredentials | None,
) -> str | None:
    cookie_token = request.cookies.get(auth_cookie_name())
    if cookie_token:
        return cookie_token

    if credentials and credentials.scheme.lower() == "bearer":
        return credentials.credentials

    return None


def get_optional_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> AuthenticatedUser | None:
    token = _extract_token(request=request, credentials=credentials)
    if not token:
        return None

    payload = decode_access_token(token)
    if payload is None:
        return None

    user_id = str(payload.get("sub", "")).strip()
    if not user_id:
        return None

    user = get_user_by_id(user_id=user_id)
    if user is None:
        return None

    return AuthenticatedUser(
        id=user["id"],
        name=user["name"],
        email=user["email"],
        created_at=user["created_at"],
    )


def get_current_user(
    current_user: AuthenticatedUser | None = Depends(get_optional_current_user),
) -> AuthenticatedUser:
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return current_user
