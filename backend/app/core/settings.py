"""
Environment-aware application settings.
"""

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class AppSettings:
    """
    Application settings resolved from environment variables.
    """
    env: str
    api_version: str
    app_name: str
    docs_enabled: bool


def get_settings() -> AppSettings:
    """
    Resolve settings from environment with deterministic defaults.
    """
    env = os.getenv("CADARENA_ENV", "dev").strip().lower()
    api_version = os.getenv("CADARENA_API_VERSION", "v1").strip()
    app_name = os.getenv("CADARENA_APP_NAME", "CadArena").strip()
    docs_enabled = env != "prod"
    return AppSettings(
        env=env,
        api_version=api_version,
        app_name=app_name,
        docs_enabled=docs_enabled,
    )
