"""Session-scoped DXF file token registry."""

from __future__ import annotations

import secrets
from pathlib import Path
from threading import Lock

from fastapi import Request, Response

from app.core.file_utils import resolve_output_path
from app.services.auth_security import (
    access_token_ttl_seconds,
    auth_cookie_name,
    auth_cookie_secure,
    decode_access_token,
)

_WORKSPACE_GUEST_COOKIE_NAME = "cadarena_workspace_guest"
_FILE_SESSION_COOKIE_NAME = "cadarena_file_session"
_owner_tokens: dict[str, dict[str, str]] = {}
_owner_paths: dict[str, dict[str, str]] = {}
_registry_lock = Lock()


def workspace_owner_scope(user_id: str) -> str:
    cleaned = user_id.strip()
    if not cleaned:
        raise ValueError("user_id must not be empty")
    return f"workspace:{cleaned}"

def bind_workspace_guest_cookie(response: Response | None, user_id: str) -> None:
    if response is None:
        return

    cleaned = user_id.strip()
    if not cleaned:
        return

    response.set_cookie(
        key=_WORKSPACE_GUEST_COOKIE_NAME,
        value=cleaned,
        max_age=access_token_ttl_seconds(),
        httponly=True,
        samesite="lax",
        secure=auth_cookie_secure(),
        path="/",
    )
    response.headers["Cache-Control"] = "no-store"

def issue_workspace_file_token(*, user_id: str, absolute_path: str | Path) -> str:
    return _issue_file_token(owner_scope=workspace_owner_scope(user_id), absolute_path=absolute_path)

def issue_session_file_token(*, request: Request, response: Response | None, absolute_path: str | Path) -> str:
    owner_scope = _session_owner_scope_for_request(request=request, response=response)
    return _issue_file_token(owner_scope=owner_scope, absolute_path=absolute_path)

def resolve_request_file_token(*, request: Request, file_token: str) -> Path | None:
    cleaned = file_token.strip()
    if not cleaned:
        return None

    with _registry_lock:
        path_value = None
        for owner_scope in _candidate_owner_scopes(request):
            path_value = _owner_tokens.get(owner_scope, {}).get(cleaned)
            if path_value is not None:
                break

    if path_value is None:
        return None

    try:
        return resolve_output_path(path_value)
    except ValueError:
        return None

def _issue_file_token(*, owner_scope: str, absolute_path: str | Path) -> str:
    resolved_path = resolve_output_path(absolute_path)
    path_value = str(resolved_path)

    with _registry_lock:
        owner_path_map = _owner_paths.setdefault(owner_scope, {})
        existing_token = owner_path_map.get(path_value)
        if existing_token is not None:
            return existing_token

        owner_token_map = _owner_tokens.setdefault(owner_scope, {})
        token = _generate_token()
        while token in owner_token_map:
            token = _generate_token()

        owner_token_map[token] = path_value
        owner_path_map[path_value] = token
        return token

def _generate_token() -> str:
    return secrets.token_urlsafe(8)

def _candidate_owner_scopes(request: Request) -> list[str]:
    candidates: list[str] = []

    auth_user_id = _auth_user_id_from_request(request)
    if auth_user_id:
        candidates.append(workspace_owner_scope(auth_user_id))
        candidates.append(_session_owner_scope(auth_user_id))

    workspace_guest_id = request.cookies.get(_WORKSPACE_GUEST_COOKIE_NAME, "").strip()
    if workspace_guest_id:
        candidates.append(workspace_owner_scope(workspace_guest_id))

    file_session_id = request.cookies.get(_FILE_SESSION_COOKIE_NAME, "").strip()
    if file_session_id:
        candidates.append(_session_owner_scope(file_session_id))

    unique_candidates: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        unique_candidates.append(candidate)
    return unique_candidates

def _session_owner_scope_for_request(*, request: Request, response: Response | None) -> str:
    auth_user_id = _auth_user_id_from_request(request)
    if auth_user_id:
        return _session_owner_scope(auth_user_id)

    session_id = request.cookies.get(_FILE_SESSION_COOKIE_NAME, "").strip()
    if not session_id:
        session_id = _generate_token()
        if response is not None:
            response.set_cookie(
                key=_FILE_SESSION_COOKIE_NAME,
                value=session_id,
                max_age=access_token_ttl_seconds(),
                httponly=True,
                samesite="lax",
                secure=auth_cookie_secure(),
                path="/",
            )
            response.headers["Cache-Control"] = "no-store"
    return _session_owner_scope(session_id)

def _session_owner_scope(session_id: str) -> str:
    return f"session:{session_id}"

def _auth_user_id_from_request(request: Request) -> str | None:
    token = request.cookies.get(auth_cookie_name(), "").strip()
    if not token:
        authorization = request.headers.get("Authorization", "")
        scheme, _, credentials = authorization.partition(" ")
        if scheme.lower() == "bearer" and credentials.strip():
            token = credentials.strip()

    if not token:
        return None

    payload = decode_access_token(token)
    if payload is None:
        return None

    user_id = str(payload.get("sub", "")).strip()
    return user_id or None
