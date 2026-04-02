import asyncio
import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.core.file_utils import ensure_dxf_output_dir

logger = logging.getLogger(__name__)

# Files older than this are deleted
DXF_RETENTION_HOURS = 48
JSON_RETENTION_HOURS = 72
PNG_RETENTION_HOURS = 48


def cleanup_output_files(*, dry_run: bool = False) -> dict[str, int]:
    """
    Delete old generated output files from backend/output/.

    Retention policy:
      DXF files:  48 hours
      PNG/PDF:    48 hours
      Parse JSON: 72 hours

    Returns count of deleted files per type.
    """
    now = datetime.now(UTC)
    deleted: dict[str, int] = {"dxf": 0, "png_pdf": 0, "json": 0}

    # DXF and PNG/PDF in output/dxf/
    dxf_dir = ensure_dxf_output_dir()
    _cleanup_dir(
        directory=dxf_dir,
        extensions={".dxf"},
        max_age=timedelta(hours=DXF_RETENTION_HOURS),
        now=now,
        counter=deleted,
        key="dxf",
        dry_run=dry_run,
    )
    _cleanup_dir(
        directory=dxf_dir,
        extensions={".png", ".pdf"},
        max_age=timedelta(hours=PNG_RETENTION_HOURS),
        now=now,
        counter=deleted,
        key="png_pdf",
        dry_run=dry_run,
    )

    # Parse JSON in output/parse_design_json/
    json_dir = dxf_dir.parent / "parse_design_json"
    if json_dir.exists():
        _cleanup_dir(
            directory=json_dir,
            extensions={".json"},
            max_age=timedelta(hours=JSON_RETENTION_HOURS),
            now=now,
            counter=deleted,
            key="json",
            dry_run=dry_run,
        )

    logger.info("[OutputCleanup] deleted=%s dry_run=%s", deleted, dry_run)
    return deleted


def _cleanup_dir(
    *,
    directory: Path,
    extensions: set[str],
    max_age: timedelta,
    now: datetime,
    counter: dict[str, int],
    key: str,
    dry_run: bool,
) -> None:
    """Delete files older than max_age in the given directory."""
    for file_path in directory.iterdir():
        if not file_path.is_file():
            continue
        if file_path.suffix.lower() not in extensions:
            continue
        try:
            mtime = datetime.fromtimestamp(
                file_path.stat().st_mtime, tz=UTC
            )
            if now - mtime > max_age:
                if not dry_run:
                    file_path.unlink(missing_ok=True)
                counter[key] += 1
        except OSError:
            continue


async def run_cleanup_loop(interval_hours: int = 6) -> None:
    """
    Background loop that runs cleanup every interval_hours.
    Designed to run as an asyncio task inside FastAPI lifespan.
    """
    while True:
        try:
            await asyncio.sleep(interval_hours * 3600)
            cleanup_output_files()
        except asyncio.CancelledError:
            break
        except Exception as exc:
            logger.warning("[OutputCleanup] error: %s", exc)
