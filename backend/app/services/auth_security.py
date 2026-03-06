"""Security utilities for password hashing and JWT handling."""

from __future__ import annotations

import base64
from datetime import UTC, datetime, timedelta
import hashlib
import hmac
import json
import os
import secrets

import bcrypt

_JWT_ALGORITHM = "HS256"
_RUNTIME_SECRET = secrets.token_urlsafe(48)
_JWT_SECRET = os.getenv("CADARENA_JWT_SECRET", "").strip() or _RUNTIME_SECRET
_AUTH_COOKIE_NAME = os.getenv("CADARENA_AUTH_COOKIE_NAME", "cadarena_auth").strip() or "cadarena_auth"


def _bool_from_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    normalized = raw.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default


def _int_from_env(name: str, default: int, *, min_value: int, max_value: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        parsed = int(raw.strip())
    except ValueError:
        return default
    return max(min_value, min(parsed, max_value))


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def _jwt_signature(message: bytes) -> str:
    digest = hmac.new(_JWT_SECRET.encode("utf-8"), message, hashlib.sha256).digest()
    return _b64url_encode(digest)


_AUTH_COOKIE_SECURE = _bool_from_env("CADARENA_AUTH_COOKIE_SECURE", False)
_ACCESS_TOKEN_TTL_SECONDS = _int_from_env(
    "CADARENA_AUTH_TOKEN_TTL_SECONDS",
    60 * 60 * 24 * 7,
    min_value=60,
    max_value=60 * 60 * 24 * 30,
)


def auth_cookie_name() -> str:
    return _AUTH_COOKIE_NAME


def auth_cookie_secure() -> bool:
    return _AUTH_COOKIE_SECURE


def access_token_ttl_seconds() -> int:
    return _ACCESS_TOKEN_TTL_SECONDS


def google_client_id() -> str:
    return os.getenv("CADARENA_GOOGLE_CLIENT_ID", "").strip()


def hash_password(password: str) -> str:
    encoded = password.encode("utf-8")
    if len(encoded) > 72:
        raise ValueError("password is too long")
    return bcrypt.hashpw(encoded, bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(*, user_id: str, email: str) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": user_id,
        "email": email,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=_ACCESS_TOKEN_TTL_SECONDS)).timestamp()),
    }

    header = {"alg": _JWT_ALGORITHM, "typ": "JWT"}
    header_segment = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_segment = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_segment}.{payload_segment}".encode("ascii")
    signature_segment = _jwt_signature(signing_input)
    return f"{header_segment}.{payload_segment}.{signature_segment}"


def decode_access_token(token: str) -> dict | None:
    parts = token.split(".")
    if len(parts) != 3:
        return None

    header_segment, payload_segment, signature_segment = parts
    signing_input = f"{header_segment}.{payload_segment}".encode("ascii")
    expected_signature = _jwt_signature(signing_input)
    if not hmac.compare_digest(signature_segment, expected_signature):
        return None

    try:
        payload_raw = _b64url_decode(payload_segment)
        payload = json.loads(payload_raw)
    except (ValueError, json.JSONDecodeError, UnicodeDecodeError):
        return None

    if not isinstance(payload, dict):
        return None

    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject.strip():
        return None

    exp = payload.get("exp")
    if not isinstance(exp, int):
        return None
    if exp <= int(datetime.now(UTC).timestamp()):
        return None

    return payload
