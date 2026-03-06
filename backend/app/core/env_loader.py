"""Utilities for loading local runtime environment variables.

CadArena intentionally loads values from ``backend/.env`` only.
The ``.env.example`` file is treated as a template for source control.
"""

from __future__ import annotations

from pathlib import Path
import os
from threading import Lock

_load_lock = Lock()
_loaded = False
_loaded_path: Path | None = None


def _parse_env_line(line: str) -> tuple[str, str] | None:
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None

    if stripped.startswith("export "):
        stripped = stripped[7:].lstrip()

    if "=" not in stripped:
        return None

    key, raw_value = stripped.split("=", 1)
    key = key.strip()
    if not key:
        return None

    value = raw_value.strip()
    if not value:
        return key, ""

    # Allow inline comments for unquoted values: KEY=value # comment
    if value[0] not in {"'", '"'} and "#" in value:
        value = value.split("#", 1)[0].rstrip()

    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        value = value[1:-1]

    return key, value


def load_backend_env() -> Path | None:
    """Load ``backend/.env`` into ``os.environ`` once and return its path."""
    global _loaded, _loaded_path

    with _load_lock:
        if _loaded:
            return _loaded_path

        backend_dir = Path(__file__).resolve().parents[2]
        env_path = backend_dir / ".env"
        if not env_path.exists():
            _loaded = True
            _loaded_path = None
            return None

        try:
            lines = env_path.read_text(encoding="utf-8").splitlines()
        except OSError:
            _loaded = True
            _loaded_path = None
            return None

        for line in lines:
            parsed = _parse_env_line(line)
            if parsed is None:
                continue
            key, value = parsed
            os.environ.setdefault(key, value)

        _loaded = True
        _loaded_path = env_path
        return env_path
