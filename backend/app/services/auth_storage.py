"""SQLite-backed storage for user authentication."""

from __future__ import annotations

import os
import re
import sqlite3
from functools import lru_cache
from pathlib import Path
from uuid import uuid4

from cryptography.fernet import Fernet, InvalidToken

from app.core.env_loader import load_backend_env
from app.services.storage_common import (
    connect_sqlite,
    normalize_email,
    normalize_name,
    normalize_url,
    utc_now,
)
from app.services.storage_logger import StorageLogger
from app.services.workspace_storage import workspace_db_path

load_backend_env()

_SUPPORTED_API_KEY_PROVIDERS = (
    "openai",
    "anthropic",
    "google",
    "huggingface",
    "groq",
    "azure_openai",
    "ollama",
)

logger = StorageLogger()


def _connect() -> sqlite3.Connection:
    db_path = workspace_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(db_path))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _normalize_provider(provider: str) -> str:
    cleaned = provider.strip().lower().replace("-", "_")
    if not cleaned:
        raise ValueError("provider must not be empty")
    if cleaned not in _SUPPORTED_API_KEY_PROVIDERS:
        raise ValueError(f"unsupported provider '{provider}'")
    return cleaned


def _normalize_api_key(api_key: str) -> str:
    cleaned = api_key.strip()
    if not cleaned:
        raise ValueError("api_key must not be empty")
    if len(cleaned) > 4096:
        raise ValueError("api_key is too long")
    return cleaned


def _normalize_optional_field(value: str | None, *, max_length: int) -> str | None:
    if value is None:
        return None
    cleaned = " ".join(value.split())
    if not cleaned:
        return None
    if len(cleaned) > max_length:
        raise ValueError("profile field is too long")
    return cleaned


def _normalize_optional_path(value: str | None, *, max_length: int) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    if len(cleaned) > max_length:
        raise ValueError("path value is too long")
    return cleaned


def _mask_api_key(value: str) -> str:
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}...{value[-4:]}"


@lru_cache(maxsize=1)
def _provider_key_cipher() -> Fernet:
    secret = os.getenv("PROVIDER_KEY_SECRET", "").strip()
    if not secret:
        raise RuntimeError("PROVIDER_KEY_SECRET is required to encrypt provider API keys")
    try:
        return Fernet(secret.encode("ascii"))
    except (ValueError, UnicodeEncodeError) as exc:
        raise RuntimeError("PROVIDER_KEY_SECRET must be a valid Fernet key") from exc


def _looks_like_encrypted_provider_key(value: str) -> bool:
    return value.startswith("gAAAAA")


def _encrypt_provider_api_key(value: str) -> str:
    encrypted = _provider_key_cipher().encrypt(value.encode("utf-8"))
    return encrypted.decode("ascii")


def _decrypt_provider_api_key(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise RuntimeError("Stored provider API key is empty")
    if not _looks_like_encrypted_provider_key(cleaned):
        return cleaned
    try:
        decrypted = _provider_key_cipher().decrypt(cleaned.encode("ascii"))
    except InvalidToken as exc:
        raise RuntimeError("Unable to decrypt stored provider API key") from exc
    return decrypted.decode("utf-8")


def _ensure_profile_columns(connection: sqlite3.Connection) -> None:
    rows = connection.execute("PRAGMA table_info(user_profiles)").fetchall()
    existing_columns = {row["name"] for row in rows}

    if "profile_image_path" not in existing_columns:
        connection.execute("ALTER TABLE user_profiles ADD COLUMN profile_image_path TEXT")
    if "profile_image_updated_at" not in existing_columns:
        connection.execute("ALTER TABLE user_profiles ADD COLUMN profile_image_updated_at TEXT")


def init_auth_db() -> None:
    with _connect() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users(email);

            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id TEXT PRIMARY KEY,
                display_name TEXT,
                headline TEXT,
                company TEXT,
                website TEXT,
                timezone TEXT,
                profile_image_path TEXT,
                profile_image_updated_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS user_provider_api_keys (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                provider TEXT NOT NULL,
                api_key TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(user_id, provider),
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_user_provider_keys_user ON user_provider_api_keys(user_id);
            CREATE INDEX IF NOT EXISTS idx_user_provider_keys_provider ON user_provider_api_keys(provider);
            """
        )
        _ensure_profile_columns(connection)
        connection.commit()


def create_user(*, name: str, email: str, password_hash: str) -> dict:
    normalized_name = normalize_name(name)
    normalized_email = normalize_email(email)
    user_id = uuid4().hex
    created_at = utc_now()

    with _connect() as connection:
        try:
            connection.execute(
                """
                INSERT INTO users (id, name, email, password_hash, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, normalized_name, normalized_email, password_hash, created_at),
            )
            connection.execute(
                """
                INSERT INTO user_profiles (user_id, display_name, headline, company, website, timezone, created_at, updated_at)
                VALUES (?, ?, NULL, NULL, NULL, NULL, ?, ?)
                """,
                (user_id, normalized_name, created_at, created_at),
            )
            connection.commit()
            logger.log_mutation("CREATE", "users", user_id, user_id=user_id)
        except sqlite3.IntegrityError as exc:
            logger.log_constraint_violation("users", "email_unique", user_id=user_id)
            raise ValueError("email already registered") from exc

    return {
        "id": user_id,
        "name": normalized_name,
        "email": normalized_email,
        "created_at": created_at,
    }


def get_user_by_email(*, email: str) -> dict | None:
    normalized_email = _normalize_email(email)
    with _connect() as connection:
        row = connection.execute(
            """
            SELECT id, name, email, password_hash, created_at
            FROM users
            WHERE email = ?
            """,
            (normalized_email,),
        ).fetchone()

    if row is None:
        return None

    return {
        "id": row["id"],
        "name": row["name"],
        "email": row["email"],
        "password_hash": row["password_hash"],
        "created_at": row["created_at"],
    }


def get_user_by_id(*, user_id: str) -> dict | None:
    cleaned_user_id = user_id.strip()
    if not cleaned_user_id:
        return None

    with _connect() as connection:
        row = connection.execute(
            """
            SELECT id, name, email, password_hash, created_at
            FROM users
            WHERE id = ?
            """,
            (cleaned_user_id,),
        ).fetchone()

    if row is None:
        return None

    return {
        "id": row["id"],
        "name": row["name"],
        "email": row["email"],
        "password_hash": row["password_hash"],
        "created_at": row["created_at"],
    }


def user_exists(*, email: str) -> bool:
    return get_user_by_email(email=email) is not None


def supported_api_key_providers() -> tuple[str, ...]:
    return _SUPPORTED_API_KEY_PROVIDERS


def get_user_profile(*, user_id: str) -> dict | None:
    cleaned_user_id = user_id.strip()
    if not cleaned_user_id:
        return None

    with _connect() as connection:
        row = connection.execute(
            """
            SELECT
                p.user_id,
                p.display_name,
                p.headline,
                p.company,
                p.website,
                p.timezone,
                p.profile_image_path,
                p.profile_image_updated_at,
                p.created_at,
                p.updated_at
            FROM user_profiles p
            WHERE p.user_id = ?
            """,
            (cleaned_user_id,),
        ).fetchone()

    if row is None:
        return None

    return {
        "user_id": row["user_id"],
        "display_name": row["display_name"],
        "headline": row["headline"],
        "company": row["company"],
        "website": row["website"],
        "timezone": row["timezone"],
        "profile_image_path": row["profile_image_path"],
        "profile_image_updated_at": row["profile_image_updated_at"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def ensure_user_profile(*, user_id: str, default_display_name: str) -> dict:
    cleaned_user_id = user_id.strip()
    if not cleaned_user_id:
        raise ValueError("user_id must not be empty")
    name = _normalize_name(default_display_name)
    now = _utc_now()

    with _connect() as connection:
        existing = connection.execute(
            "SELECT user_id FROM user_profiles WHERE user_id = ?",
            (cleaned_user_id,),
        ).fetchone()
        if existing is None:
            connection.execute(
                """
                INSERT INTO user_profiles (user_id, display_name, headline, company, website, timezone, created_at, updated_at)
                VALUES (?, ?, NULL, NULL, NULL, NULL, ?, ?)
                """,
                (cleaned_user_id, name, now, now),
            )
            connection.commit()

    profile = get_user_profile(user_id=cleaned_user_id)
    if profile is None:
        raise ValueError("unable to load user profile")
    return profile


def update_user_profile(
    *,
    user_id: str,
    display_name: str | None = None,
    headline: str | None = None,
    company: str | None = None,
    website: str | None = None,
    timezone: str | None = None,
) -> dict:
    cleaned_user_id = user_id.strip()
    if not cleaned_user_id:
        raise ValueError("user_id must not be empty")

    normalized_display_name = _normalize_optional_field(display_name, max_length=120)
    normalized_headline = _normalize_optional_field(headline, max_length=180)
    normalized_company = _normalize_optional_field(company, max_length=160)
    normalized_website = _normalize_optional_field(website, max_length=320)
    normalized_timezone = _normalize_optional_field(timezone, max_length=80)
    now = _utc_now()

    with _connect() as connection:
        updated = connection.execute(
            """
            UPDATE user_profiles
            SET
                display_name = ?,
                headline = ?,
                company = ?,
                website = ?,
                timezone = ?,
                updated_at = ?
            WHERE user_id = ?
            """,
            (
                normalized_display_name,
                normalized_headline,
                normalized_company,
                normalized_website,
                normalized_timezone,
                now,
                cleaned_user_id,
            ),
        ).rowcount
        if updated == 0:
            raise ValueError("profile not found")
        connection.commit()

    profile = get_user_profile(user_id=cleaned_user_id)
    if profile is None:
        raise ValueError("profile not found")
    return profile


def update_user_profile_image(*, user_id: str, profile_image_path: str | None) -> dict:
    cleaned_user_id = user_id.strip()
    if not cleaned_user_id:
        raise ValueError("user_id must not be empty")

    normalized_profile_image_path = _normalize_optional_path(profile_image_path, max_length=1024)
    profile_image_updated_at = _utc_now() if normalized_profile_image_path else None
    now = _utc_now()

    with _connect() as connection:
        updated = connection.execute(
            """
            UPDATE user_profiles
            SET
                profile_image_path = ?,
                profile_image_updated_at = ?,
                updated_at = ?
            WHERE user_id = ?
            """,
            (
                normalized_profile_image_path,
                profile_image_updated_at,
                now,
                cleaned_user_id,
            ),
        ).rowcount
        if updated == 0:
            raise ValueError("profile not found")
        connection.commit()

    profile = get_user_profile(user_id=cleaned_user_id)
    if profile is None:
        raise ValueError("profile not found")
    return profile


def list_user_provider_api_keys(*, user_id: str) -> list[dict]:
    cleaned_user_id = user_id.strip()
    if not cleaned_user_id:
        raise ValueError("user_id must not be empty")

    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT provider, api_key, created_at, updated_at
            FROM user_provider_api_keys
            WHERE user_id = ?
            ORDER BY provider ASC
            """,
            (cleaned_user_id,),
        ).fetchall()

    records: list[dict] = []
    for row in rows:
        decrypted_key = _decrypt_provider_api_key(row["api_key"])
        records.append(
            {
                "provider": row["provider"],
                "has_key": True,
                "masked_key": _mask_api_key(decrypted_key),
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
        )
    return records


def upsert_user_provider_api_key(*, user_id: str, provider: str, api_key: str) -> dict:
    cleaned_user_id = user_id.strip()
    if not cleaned_user_id:
        raise ValueError("user_id must not be empty")
    normalized_provider = _normalize_provider(provider)
    normalized_key = _normalize_api_key(api_key)
    encrypted_key = _encrypt_provider_api_key(normalized_key)
    now = _utc_now()

    with _connect() as connection:
        connection.execute(
            """
            INSERT INTO user_provider_api_keys (id, user_id, provider, api_key, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, provider) DO UPDATE SET
                api_key = excluded.api_key,
                updated_at = excluded.updated_at
            """,
            (uuid4().hex, cleaned_user_id, normalized_provider, encrypted_key, now, now),
        )
        connection.commit()

    return {
        "provider": normalized_provider,
        "has_key": True,
        "masked_key": _mask_api_key(normalized_key),
        "updated_at": now,
    }


def delete_user_provider_api_key(*, user_id: str, provider: str) -> bool:
    cleaned_user_id = user_id.strip()
    if not cleaned_user_id:
        raise ValueError("user_id must not be empty")
    normalized_provider = _normalize_provider(provider)

    with _connect() as connection:
        deleted = connection.execute(
            """
            DELETE FROM user_provider_api_keys
            WHERE user_id = ? AND provider = ?
            """,
            (cleaned_user_id, normalized_provider),
        ).rowcount
        connection.commit()

    return deleted > 0
