"""SQLite-backed storage for user projects and chat messages."""

from __future__ import annotations

import logging
import os
import re
import sqlite3
from datetime import datetime, UTC
from pathlib import Path
from uuid import uuid4

from app.core.env_loader import load_backend_env
from app.core.file_utils import BACKEND_DIR
from app.services.file_token_registry import issue_workspace_file_token

load_backend_env()

logger = logging.getLogger(__name__)


def _resolve_workspace_db_path() -> Path:
    configured_path = os.getenv("CADARENA_WORKSPACE_DB_PATH", "").strip()
    if configured_path:
        return Path(configured_path).expanduser()
    return BACKEND_DIR / "data" / "workspace.db"


DB_PATH = _resolve_workspace_db_path()
_WHITESPACE_RE = re.compile(r"\s+")


def _utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds")


def _normalize_user_id(user_id: str) -> str:
    cleaned = user_id.strip()
    if not cleaned:
        raise ValueError("user_id must not be empty")
    if len(cleaned) > 128:
        raise ValueError("user_id is too long")
    return cleaned


def _normalize_project_name(name: str) -> str:
    cleaned = _WHITESPACE_RE.sub(" ", name.strip())
    if not cleaned:
        raise ValueError("project name must not be empty")
    if len(cleaned) > 120:
        raise ValueError("project name is too long")
    return cleaned


def _connect() -> sqlite3.Connection:
    _prepare_workspace_db_path()
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _prepare_workspace_db_path() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def init_workspace_db() -> None:
    with _connect() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_projects_user ON projects(user_id);

            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'error', 'system')),
                text TEXT NOT NULL,
                created_at TEXT NOT NULL,
                dxf_path TEXT,
                dxf_name TEXT,
                model_used TEXT,
                provider_used TEXT,
                FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_messages_project ON messages(project_id, created_at);
            """
        )
        connection.commit()


def list_projects(*, user_id: str) -> list[dict]:
    normalized_user_id = _normalize_user_id(user_id)
    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT
                p.id,
                p.name,
                p.created_at,
                p.updated_at,
                MAX(m.created_at) AS last_message_at,
                COUNT(m.id) AS message_count
            FROM projects p
            LEFT JOIN messages m ON m.project_id = p.id
            WHERE p.user_id = ?
            GROUP BY p.id
            ORDER BY COALESCE(MAX(m.created_at), p.updated_at) DESC
            """,
            (normalized_user_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def create_project(*, user_id: str, name: str) -> dict:
    normalized_user_id = _normalize_user_id(user_id)
    normalized_name = _normalize_project_name(name)
    now = _utc_now()
    project_id = uuid4().hex

    with _connect() as connection:
        connection.execute(
            """
            INSERT INTO projects (id, user_id, name, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (project_id, normalized_user_id, normalized_name, now, now),
        )
        connection.commit()

    return {
        "id": project_id,
        "name": normalized_name,
        "created_at": now,
        "updated_at": now,
        "last_message_at": None,
        "message_count": 0,
    }


def _fetch_project_for_user(
    connection: sqlite3.Connection,
    *,
    user_id: str,
    project_id: str,
) -> dict | None:
    row = connection.execute(
        """
        SELECT
            p.id,
            p.name,
            p.created_at,
            p.updated_at,
            COALESCE(MAX(m.created_at), p.updated_at) AS last_message_at,
            COUNT(m.id) AS message_count
        FROM projects p
        LEFT JOIN messages m ON m.project_id = p.id
        WHERE p.id = ? AND p.user_id = ?
        GROUP BY p.id
        """,
        (project_id, user_id),
    ).fetchone()
    return dict(row) if row else None


def get_project(*, user_id: str, project_id: str) -> dict | None:
    normalized_user_id = _normalize_user_id(user_id)
    with _connect() as connection:
        return _fetch_project_for_user(
            connection,
            user_id=normalized_user_id,
            project_id=project_id,
        )


def rename_project(*, user_id: str, project_id: str, name: str) -> dict | None:
    normalized_user_id = _normalize_user_id(user_id)
    normalized_name = _normalize_project_name(name)
    updated_at = _utc_now()

    with _connect() as connection:
        updated = connection.execute(
            """
            UPDATE projects
            SET name = ?, updated_at = ?
            WHERE id = ? AND user_id = ?
            """,
            (normalized_name, updated_at, project_id, normalized_user_id),
        ).rowcount
        if updated == 0:
            return None
        connection.commit()
        return _fetch_project_for_user(
            connection,
            user_id=normalized_user_id,
            project_id=project_id,
        )


def delete_project(*, user_id: str, project_id: str) -> bool:
    normalized_user_id = _normalize_user_id(user_id)
    with _connect() as connection:
        deleted = connection.execute(
            "DELETE FROM projects WHERE id = ? AND user_id = ?",
            (project_id, normalized_user_id),
        ).rowcount
        connection.commit()
    return deleted > 0


def list_project_messages(*, user_id: str, project_id: str) -> tuple[dict | None, list[dict]]:
    normalized_user_id = _normalize_user_id(user_id)
    with _connect() as connection:
        project = _fetch_project_for_user(
            connection,
            user_id=normalized_user_id,
            project_id=project_id,
        )
        if project is None:
            return None, []
        rows = connection.execute(
            """
            SELECT
                id,
                role,
                text,
                created_at,
                dxf_path,
                dxf_name,
                model_used,
                provider_used
            FROM messages
            WHERE project_id = ?
            ORDER BY created_at ASC
            """,
            (project_id,),
        ).fetchall()
    return project, [_serialize_message_row(row, user_id=normalized_user_id) for row in rows]


def _serialize_message_row(row: sqlite3.Row, *, user_id: str) -> dict:
    payload = dict(row)
    dxf_path = payload.pop("dxf_path", None)
    if dxf_path:
        try:
            payload["file_token"] = issue_workspace_file_token(user_id=user_id, absolute_path=dxf_path)
        except ValueError as e:
            logger.warning(f"Failed to issue file token for {dxf_path}: {e}", extra={"user_id": user_id, "dxf_path": dxf_path})
            payload["file_token"] = None
    else:
        payload["file_token"] = None
    return payload


def add_message(
    *,
    user_id: str,
    project_id: str,
    role: str,
    text: str,
    dxf_path: str | None = None,
    dxf_name: str | None = None,
    model_used: str | None = None,
    provider_used: str | None = None,
) -> str:
    normalized_user_id = _normalize_user_id(user_id)
    cleaned_text = text.strip()
    if not cleaned_text:
        raise ValueError("message text must not be empty")
    if role not in {"user", "assistant", "error", "system"}:
        raise ValueError("unsupported message role")

    message_id = uuid4().hex
    now = _utc_now()

    with _connect() as connection:
        connection.execute("BEGIN IMMEDIATE")
        try:
            project = _fetch_project_for_user(
                connection,
                user_id=normalized_user_id,
                project_id=project_id,
            )
            if project is None:
                raise KeyError("project not found")

            connection.execute(
                """
                INSERT INTO messages (
                    id,
                    project_id,
                    role,
                    text,
                    created_at,
                    dxf_path,
                    dxf_name,
                    model_used,
                    provider_used
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    message_id,
                    project_id,
                    role,
                    cleaned_text,
                    now,
                    dxf_path,
                    dxf_name,
                    model_used,
                    provider_used,
                ),
            )
            connection.execute(
                "UPDATE projects SET updated_at = ? WHERE id = ?",
                (now, project_id),
            )
            connection.commit()
        except Exception:
            connection.rollback()
            raise

    return message_id


def workspace_db_path() -> Path:
    return DB_PATH
