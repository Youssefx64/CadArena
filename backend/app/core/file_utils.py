from datetime import datetime
from pathlib import Path


OUTPUT_DIR = Path("output")


def generate_dxf_filename(prefix: str = "drawing") -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{prefix}_{timestamp}.dxf"
    return OUTPUT_DIR / filename
