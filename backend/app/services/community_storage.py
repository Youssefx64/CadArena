"""SQLite-backed storage for engineering community questions and answers."""

from __future__ import annotations

import json
import re
import sqlite3
from datetime import UTC, datetime
from uuid import uuid4

from app.models.community import CommunitySort
from app.services.workspace_storage import workspace_db_path

_WHITESPACE_RE = re.compile(r"\s+")
_TAG_CLEAN_RE = re.compile(r"[^a-z0-9+-]+")


def _utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds")


def _connect() -> sqlite3.Connection:
    db_path = workspace_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_community_db() -> None:
    """Create community tables if they do not exist."""
    with _connect() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS community_questions (
                id TEXT PRIMARY KEY,
                author_id TEXT,
                author_name TEXT NOT NULL,
                discipline TEXT NOT NULL,
                title TEXT NOT NULL,
                body TEXT NOT NULL,
                tags_json TEXT NOT NULL,
                score INTEGER NOT NULL DEFAULT 0,
                view_count INTEGER NOT NULL DEFAULT 0,
                accepted_answer_id TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                last_activity_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_community_questions_activity
                ON community_questions(last_activity_at DESC);
            CREATE INDEX IF NOT EXISTS idx_community_questions_created
                ON community_questions(created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_community_questions_discipline
                ON community_questions(discipline);

            CREATE TABLE IF NOT EXISTS community_answers (
                id TEXT PRIMARY KEY,
                question_id TEXT NOT NULL,
                author_id TEXT,
                author_name TEXT NOT NULL,
                body TEXT NOT NULL,
                score INTEGER NOT NULL DEFAULT 0,
                accepted INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(question_id) REFERENCES community_questions(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_community_answers_question
                ON community_answers(question_id, created_at);
            """
        )
        connection.commit()


def _normalize_author_name(author_name: str | None) -> str:
    cleaned = _WHITESPACE_RE.sub(" ", (author_name or "").strip())
    if not cleaned:
        raise ValueError("author_name is required")
    if len(cleaned) > 120:
        raise ValueError("author_name is too long")
    return cleaned


def _normalize_title(title: str) -> str:
    cleaned = _WHITESPACE_RE.sub(" ", title.strip())
    if len(cleaned) < 8:
        raise ValueError("title is too short")
    if len(cleaned) > 160:
        raise ValueError("title is too long")
    return cleaned


def _normalize_body(body: str) -> str:
    cleaned = body.strip()
    if len(cleaned) < 20:
        raise ValueError("body is too short")
    if len(cleaned) > 5000:
        raise ValueError("body is too long")
    return cleaned


def _normalize_tag(tag: str) -> str:
    cleaned = _TAG_CLEAN_RE.sub("-", tag.strip().lower()).strip("-")
    if not cleaned:
        raise ValueError("tag must not be empty")
    if len(cleaned) > 32:
        raise ValueError("tag is too long")
    return cleaned


def _normalize_tags(tags: list[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for item in tags:
        tag = _normalize_tag(item)
        if tag in seen:
            continue
        normalized.append(tag)
        seen.add(tag)
        if len(normalized) > 5:
            raise ValueError("maximum of 5 tags allowed")
    return normalized


def _serialize_question(row: sqlite3.Row | dict) -> dict:
    payload = dict(row)
    raw_tags = payload.pop("tags_json", "[]")
    try:
        payload["tags"] = json.loads(raw_tags)
    except json.JSONDecodeError:
        payload["tags"] = []
    payload["answer_count"] = int(payload.get("answer_count") or 0)
    payload["view_count"] = int(payload.get("view_count") or 0)
    payload["score"] = int(payload.get("score") or 0)
    return payload


def _serialize_answer(row: sqlite3.Row | dict) -> dict:
    payload = dict(row)
    payload["accepted"] = bool(payload.get("accepted"))
    payload["score"] = int(payload.get("score") or 0)
    return payload


def _question_select_sql() -> str:
    return """
        SELECT
            q.id,
            q.author_id,
            q.author_name,
            q.discipline,
            q.title,
            q.body,
            q.tags_json,
            q.score,
            q.view_count,
            q.accepted_answer_id,
            q.created_at,
            q.updated_at,
            q.last_activity_at,
            COUNT(a.id) AS answer_count
        FROM community_questions q
        LEFT JOIN community_answers a ON a.question_id = q.id
    """


def list_questions(
    *,
    query: str | None = None,
    tag: str | None = None,
    discipline: str | None = None,
    sort: CommunitySort = "active",
    limit: int = 40,
    offset: int = 0,
) -> list[dict]:
    """List community questions with lightweight search and filtering."""
    clauses: list[str] = []
    params: list[object] = []

    cleaned_query = _WHITESPACE_RE.sub(" ", (query or "").strip().lower())
    if cleaned_query:
        needle = f"%{cleaned_query}%"
        clauses.append("(LOWER(q.title) LIKE ? OR LOWER(q.body) LIKE ? OR LOWER(q.tags_json) LIKE ?)")
        params.extend([needle, needle, needle])

    cleaned_tag = (tag or "").strip()
    if cleaned_tag:
        normalized_tag = _normalize_tag(cleaned_tag)
        clauses.append("q.tags_json LIKE ?")
        params.append(f"%\"{normalized_tag}\"%")

    cleaned_discipline = (discipline or "").strip().lower()
    if cleaned_discipline and cleaned_discipline != "all":
        clauses.append("q.discipline = ?")
        params.append(cleaned_discipline)

    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    having_sql = "HAVING COUNT(a.id) = 0" if sort == "unanswered" else ""
    order_sql = {
        "active": "ORDER BY q.last_activity_at DESC",
        "newest": "ORDER BY q.created_at DESC",
        "score": "ORDER BY q.score DESC, q.last_activity_at DESC",
        "unanswered": "ORDER BY q.created_at DESC",
    }.get(sort, "ORDER BY q.last_activity_at DESC")

    bounded_limit = min(max(limit, 1), 100)
    bounded_offset = max(offset, 0)

    sql = f"""
        {_question_select_sql()}
        {where_sql}
        GROUP BY q.id
        {having_sql}
        {order_sql}
        LIMIT ? OFFSET ?
    """
    params.extend([bounded_limit, bounded_offset])

    with _connect() as connection:
        rows = connection.execute(sql, params).fetchall()
    return [_serialize_question(row) for row in rows]


def create_question(
    *,
    title: str,
    body: str,
    tags: list[str],
    discipline: str,
    author_id: str | None,
    author_name: str,
) -> dict:
    normalized_title = _normalize_title(title)
    normalized_body = _normalize_body(body)
    normalized_tags = _normalize_tags(tags)
    normalized_author = _normalize_author_name(author_name)
    normalized_discipline = (discipline or "general").strip().lower() or "general"
    now = _utc_now()
    question_id = uuid4().hex

    with _connect() as connection:
        connection.execute(
            """
            INSERT INTO community_questions (
                id,
                author_id,
                author_name,
                discipline,
                title,
                body,
                tags_json,
                score,
                view_count,
                accepted_answer_id,
                created_at,
                updated_at,
                last_activity_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0, NULL, ?, ?, ?)
            """,
            (
                question_id,
                author_id,
                normalized_author,
                normalized_discipline,
                normalized_title,
                normalized_body,
                json.dumps(normalized_tags),
                now,
                now,
                now,
            ),
        )
        connection.commit()

    created = get_question(question_id=question_id, increment_views=False)
    if created is None:
        raise RuntimeError("created question could not be loaded")
    return created["question"]


def get_question(*, question_id: str, increment_views: bool = True) -> dict | None:
    with _connect() as connection:
        if increment_views:
            connection.execute(
                "UPDATE community_questions SET view_count = view_count + 1 WHERE id = ?",
                (question_id,),
            )
            connection.commit()

        question_row = connection.execute(
            f"""
            {_question_select_sql()}
            WHERE q.id = ?
            GROUP BY q.id
            """,
            (question_id,),
        ).fetchone()
        if question_row is None:
            return None

        answer_rows = connection.execute(
            """
            SELECT
                id,
                question_id,
                author_id,
                author_name,
                body,
                score,
                accepted,
                created_at,
                updated_at
            FROM community_answers
            WHERE question_id = ?
            ORDER BY accepted DESC, score DESC, created_at ASC
            """,
            (question_id,),
        ).fetchall()

    return {
        "question": _serialize_question(question_row),
        "answers": [_serialize_answer(row) for row in answer_rows],
    }


def add_answer(
    *,
    question_id: str,
    body: str,
    author_id: str | None,
    author_name: str,
) -> dict | None:
    normalized_body = _normalize_body(body)
    normalized_author = _normalize_author_name(author_name)
    now = _utc_now()
    answer_id = uuid4().hex

    with _connect() as connection:
        question_exists = connection.execute(
            "SELECT 1 FROM community_questions WHERE id = ?",
            (question_id,),
        ).fetchone()
        if question_exists is None:
            return None

        connection.execute(
            """
            INSERT INTO community_answers (
                id,
                question_id,
                author_id,
                author_name,
                body,
                score,
                accepted,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, 0, 0, ?, ?)
            """,
            (
                answer_id,
                question_id,
                author_id,
                normalized_author,
                normalized_body,
                now,
                now,
            ),
        )
        connection.execute(
            """
            UPDATE community_questions
            SET updated_at = ?, last_activity_at = ?
            WHERE id = ?
            """,
            (now, now, question_id),
        )
        row = connection.execute(
            """
            SELECT
                id,
                question_id,
                author_id,
                author_name,
                body,
                score,
                accepted,
                created_at,
                updated_at
            FROM community_answers
            WHERE id = ?
            """,
            (answer_id,),
        ).fetchone()
        connection.commit()

    return _serialize_answer(row) if row else None


def vote_question(*, question_id: str, direction: int) -> dict | None:
    delta = 1 if direction > 0 else -1
    with _connect() as connection:
        updated = connection.execute(
            """
            UPDATE community_questions
            SET score = score + ?, updated_at = ?
            WHERE id = ?
            """,
            (delta, _utc_now(), question_id),
        ).rowcount
        connection.commit()
    if updated == 0:
        return None
    detail = get_question(question_id=question_id, increment_views=False)
    return detail["question"] if detail else None


def vote_answer(*, answer_id: str, direction: int) -> dict | None:
    delta = 1 if direction > 0 else -1
    with _connect() as connection:
        updated = connection.execute(
            """
            UPDATE community_answers
            SET score = score + ?, updated_at = ?
            WHERE id = ?
            """,
            (delta, _utc_now(), answer_id),
        ).rowcount
        row = connection.execute(
            """
            SELECT
                id,
                question_id,
                author_id,
                author_name,
                body,
                score,
                accepted,
                created_at,
                updated_at
            FROM community_answers
            WHERE id = ?
            """,
            (answer_id,),
        ).fetchone()
        connection.commit()
    if updated == 0 or row is None:
        return None
    return _serialize_answer(row)
