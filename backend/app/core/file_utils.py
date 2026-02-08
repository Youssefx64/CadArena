"""
File utility functions for path management and DXF file generation.

This module provides utilities for managing output directories, generating
timestamped filenames, and resolving file paths with security constraints.
"""

from datetime import datetime
from pathlib import Path


# Backend root directory (two levels up from this file)
BACKEND_DIR = Path(__file__).resolve().parents[2]
# Output directory for generated DXF files
OUTPUT_DIR = BACKEND_DIR / "output"


def ensure_output_dir() -> Path:
    """
    Ensure the output directory exists, creating it if necessary.
    
    Returns:
        Path to the output directory.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIR


def generate_dxf_filename(prefix: str = "drawing") -> Path:
    """
    Generate a unique DXF filename with timestamp.
    
    Args:
        prefix: Filename prefix (default: "drawing").
    
    Returns:
        Path object pointing to the generated filename in the output directory.
    """
    output_dir = ensure_output_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{prefix}_{timestamp}.dxf"
    return output_dir / filename


def resolve_output_path(path_value: str | Path) -> Path:
    """
    Resolve and validate a file path, ensuring it's within the output directory.
    
    Security: Only allows paths within backend/output to prevent directory traversal.
    
    Args:
        path_value: Path string or Path object to resolve.
    
    Returns:
        Resolved Path object within the output directory.
    
    Raises:
        ValueError: If the resolved path is outside the output directory.
    """
    raw_path = Path(path_value)

    # Determine candidate path based on input type
    if raw_path.is_absolute():
        candidate = raw_path
    elif raw_path.parent == Path("."):
        # Filename only - place in output directory
        candidate = OUTPUT_DIR / raw_path
    else:
        # Relative path - resolve from backend root
        candidate = BACKEND_DIR / raw_path

    resolved = candidate.resolve(strict=False)
    output_root = OUTPUT_DIR.resolve(strict=False)

    # Security check: ensure path is within output directory
    try:
        resolved.relative_to(output_root)
    except ValueError as exc:
        raise ValueError("Only files inside backend/output are allowed") from exc

    return resolved
