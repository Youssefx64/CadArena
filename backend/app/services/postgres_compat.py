"""Small Postgres compatibility layer for legacy sqlite-style storage modules."""

from __future__ import annotations

import os
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Iterator


def database_url() -> str:
    return os.getenv("CADARENA_DATABASE_URL", "").strip()


def _to_psycopg_dsn(url: str) -> str:
    """
    Convert SQLAlchemy-style URLs to psycopg2 DSN URL form.
    Example:
    - postgresql+psycopg2://... -> postgresql://...
    """
    normalized = (url or "").strip()
    if normalized.startswith("postgresql+psycopg2://"):
        return "postgresql://" + normalized[len("postgresql+psycopg2://") :]
    return normalized


def _convert_params_sql(sql: str) -> str:
    # Legacy storage modules use sqlite '?' placeholders.
    return sql.replace("?", "%s")


@dataclass
class CursorCompat:
    _cursor: Any

    @property
    def rowcount(self) -> int:
        return self._cursor.rowcount

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()


class ConnectionCompat:
    def __init__(self, conn: Any):
        self._conn = conn

    def execute(self, sql: str, params: tuple | list = ()):
        from psycopg2.extras import RealDictCursor

        cur = self._conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(_convert_params_sql(sql), tuple(params or ()))
        return CursorCompat(cur)

    def executescript(self, script: str):
        # Best-effort split for DDL statements separated by ';'
        statements = [s.strip() for s in script.split(";") if s.strip()]
        for statement in statements:
            self.execute(statement)

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type:
            self.rollback()
        self.close()
        return False


@contextmanager
def connect_postgres() -> Iterator[ConnectionCompat]:
    url = _to_psycopg_dsn(database_url())
    if not url:
        raise RuntimeError("CADARENA_DATABASE_URL is required.")
    try:
        import psycopg2
    except ModuleNotFoundError as exc:  # pragma: no cover
        raise RuntimeError(
            "psycopg2-binary is required for Postgres backend. Install backend requirements."
        ) from exc

    conn = psycopg2.connect(url)
    conn.autocommit = False
    compat = ConnectionCompat(conn)
    try:
        yield compat
    finally:
        conn.close()

