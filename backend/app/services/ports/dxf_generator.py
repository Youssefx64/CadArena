"""DXF generation port."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class DXFGeneratorPort(ABC):
    """Port contract for DXF generation from validated intent."""

    @abstractmethod
    def generate(self, intent: Any, planning_context: Any | None = None) -> Path:
        """Generate a DXF file path from intent."""

