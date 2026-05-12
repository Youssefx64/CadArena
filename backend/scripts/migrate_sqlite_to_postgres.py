#!/usr/bin/env python3
"""
SQLite → PostgreSQL Migration Script
=====================================
Migrates all data from workspace.db (SQLite) into the unified
cadarena PostgreSQL database using ON CONFLICT DO NOTHING so it
is safe to run multiple times (idempotent).

Tables migrated:
  - users
  - user_profiles
  - user_provider_api_keys
  - projects
  - messages
  - community_questions
  - community_answers
  - community_votes

Usage:
    cd /home/mango/Coding/Projects/CadArena/backend
    python scripts/migrate_sqlite_to_postgres.py
"""

from __future__ import annotations

import sqlite3
import sys
import os
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor

# ── Config ─────────────────────────────────────────────────────────────────
SQLITE_PATH = Path(__file__).parent.parent / "data" / "workspace.db"
PG_DSN = os.getenv(
    "CADARENA_DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/cadarena",
).replace("postgresql+psycopg2://", "postgresql://")

# ── Helpers ─────────────────────────────────────────────────────────────────

def sqlite_rows(sqlite_conn: sqlite3.Connection, table: str) -> list[dict]:
    sqlite_conn.row_factory = sqlite3.Row
    cur = sqlite_conn.execute(f"SELECT * FROM {table}")
    return [dict(row) for row in cur.fetchall()]


def pg_insert_ignore(pg_cur, table: str, rows: list[dict], filter_col: str | None = None, valid_ids: set | None = None) -> int:
    if not rows:
        return 0
    # Filter rows whose FK parent doesn't exist in Postgres
    if filter_col and valid_ids is not None:
        original = len(rows)
        rows = [r for r in rows if r.get(filter_col) in valid_ids]
        dropped = original - len(rows)
        if dropped:
            print(f"      ⚠️  {dropped} row(s) dropped — parent key not in Postgres (FK: {filter_col})")
    if not rows:
        return 0
    cols = list(rows[0].keys())
    placeholders = ", ".join(["%s"] * len(cols))
    col_names = ", ".join(cols)
    sql = (
        f"INSERT INTO {table} ({col_names}) "
        f"VALUES ({placeholders}) "
        f"ON CONFLICT DO NOTHING"
    )
    count = 0
    for row in rows:
        pg_cur.execute(sql, [row[c] for c in cols])
        if pg_cur.rowcount > 0:
            count += 1
    return count


def check_table_exists(sqlite_conn: sqlite3.Connection, table: str) -> bool:
    cur = sqlite_conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
    )
    return cur.fetchone() is not None


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    if not SQLITE_PATH.exists():
        print(f"❌  SQLite file not found: {SQLITE_PATH}")
        sys.exit(1)

    print(f"📂  SQLite source : {SQLITE_PATH}")
    print(f"🐘  PostgreSQL DSN: {PG_DSN}\n")

    sqlite_conn = sqlite3.connect(str(SQLITE_PATH))
    pg_conn = psycopg2.connect(PG_DSN)
    pg_conn.autocommit = False
    pg_cur = pg_conn.cursor(cursor_factory=RealDictCursor)

    TABLES_ORDER = [
        # parent tables first (FK order)
        "users",
        "user_profiles",
        "user_provider_api_keys",
        "projects",
        "messages",
        "community_questions",
        "community_answers",
        "community_votes",
    ]

    total_migrated = 0
    try:
        # Collect existing IDs in Postgres for FK checks
        pg_cur.execute("SELECT id FROM users")
        pg_user_ids = {r["id"] for r in pg_cur.fetchall()}
        pg_cur.execute("SELECT id FROM projects")
        pg_project_ids = {r["id"] for r in pg_cur.fetchall()}
        pg_cur.execute("SELECT id FROM community_questions")
        pg_question_ids = {r["id"] for r in pg_cur.fetchall()}
        pg_cur.execute("SELECT id FROM community_answers")
        pg_answer_ids = {r["id"] for r in pg_cur.fetchall()}

        # FK parent mapping: table -> (filter_col, valid_ids_set)
        FK_GUARD: dict[str, tuple[str, set]] = {
            "user_profiles":          ("user_id",   pg_user_ids),
            "user_provider_api_keys": ("user_id",   pg_user_ids),
            "projects":               ("user_id",   pg_user_ids),
            "messages":               ("project_id", pg_project_ids),
            "community_answers":      ("question_id", pg_question_ids),
            "community_votes":        ("question_id", pg_question_ids),
        }

        for table in TABLES_ORDER:
            if not check_table_exists(sqlite_conn, table):
                print(f"  ⚠️   Table '{table}' not in SQLite — skipped")
                continue

            rows = sqlite_rows(sqlite_conn, table)
            if not rows:
                print(f"  ⬜  {table:<30} 0 rows (empty)")
                continue

            fk_col, fk_ids = FK_GUARD.get(table, (None, None))
            inserted = pg_insert_ignore(pg_cur, table, rows, filter_col=fk_col, valid_ids=fk_ids)
            skipped  = len(rows) - inserted
            total_migrated += inserted
            status = "✅" if inserted > 0 else "⬜"
            print(
                f"  {status}  {table:<30} "
                f"{len(rows):>4} rows in SQLite → "
                f"{inserted:>4} inserted, {skipped:>4} already existed (skipped)"
            )

        pg_conn.commit()
        print(f"\n🎉  Migration complete — {total_migrated} new rows inserted into PostgreSQL.")

    except Exception as exc:
        pg_conn.rollback()
        print(f"\n❌  Error during migration: {exc}")
        raise
    finally:
        sqlite_conn.close()
        pg_cur.close()
        pg_conn.close()


if __name__ == "__main__":
    # Load .env if available
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip().strip('"'))

    main()
