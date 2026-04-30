"""Shared database utilities and common patterns for all storage modules."""

import re
import sqlite3
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Generator, Optional

SLOW_QUERY_THRESHOLD_MS = 100


def utc_now() -> str:
    """Return current UTC time in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def normalize_email(email: str) -> str:
    """Validate and normalize email address."""
    email = email.strip().lower()
    if not email or len(email) > 320:
        raise ValueError(f"Invalid email: must be 1-320 characters")
    if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
        raise ValueError(f"Invalid email format: {email}")
    return email


def normalize_name(name: str, max_length: int = 120) -> str:
    """Normalize name: strip whitespace, limit length."""
    name = " ".join(name.split())
    if not name or len(name) > max_length:
        raise ValueError(f"Invalid name: must be 1-{max_length} characters")
    return name


def normalize_url(url: Optional[str], max_length: int = 2048) -> Optional[str]:
    """Validate and normalize URL (optional field)."""
    if not url:
        return None
    url = url.strip()
    if len(url) > max_length:
        raise ValueError(f"URL too long: max {max_length} characters")
    if not re.match(r"^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", url):
        raise ValueError(f"Invalid URL format: {url}")
    return url


def normalize_body(body: str, min_length: int = 20, max_length: int = 5000) -> str:
    """Normalize body text: strip, validate length."""
    body = body.strip()
    if len(body) < min_length or len(body) > max_length:
        raise ValueError(f"Body must be {min_length}-{max_length} characters")
    return body


def normalize_title(title: str, min_length: int = 8, max_length: int = 160) -> str:
    """Normalize title: strip, validate length."""
    title = title.strip()
    if len(title) < min_length or len(title) > max_length:
        raise ValueError(f"Title must be {min_length}-{max_length} characters")
    return title


def coerce_int(value: Any, default: int = 0, min_value: Optional[int] = None, max_value: Optional[int] = None) -> int:
    """Safely coerce value to int with bounds checking."""
    if value is None:
        return default
    try:
        result = int(value)
        if min_value is not None and result < min_value:
            raise ValueError(f"Value {result} below minimum {min_value}")
        if max_value is not None and result > max_value:
            raise ValueError(f"Value {result} exceeds maximum {max_value}")
        return result
    except (TypeError, ValueError) as e:
        raise ValueError(f"Cannot coerce {value} to int: {e}")


def coerce_bool(value: Any, default: bool = False) -> bool:
    """Safely coerce value to bool (SQLite stores as 0/1)."""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return bool(value)
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes")
    return bool(value)


def coerce_json(value: Any, default: Optional[dict] = None) -> dict:
    """Safely parse JSON string to dict."""
    import json
    if value is None:
        return default or {}
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return default or {}
    return default or {}


@contextmanager
def connect_sqlite(db_path: Path) -> Generator[sqlite3.Connection, None, None]:
    """Context manager for SQLite connections with consistent setup."""
    connection = sqlite3.connect(str(db_path))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def execute_with_timing(
    connection: sqlite3.Connection,
    query: str,
    params: tuple = (),
    operation_type: str = "query",
) -> sqlite3.Cursor:
    """Execute query and log if slow."""
    start = time.time()
    cursor = connection.execute(query, params)
    duration_ms = (time.time() - start) * 1000

    if duration_ms > SLOW_QUERY_THRESHOLD_MS:
        from app.services.storage_logger import logger
        logger.warning(
            f"Slow {operation_type} ({duration_ms:.1f}ms): {query[:100]}",
            extra={"duration_ms": duration_ms, "query": query[:200]},
        )

    return cursor
