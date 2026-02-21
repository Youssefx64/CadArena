"""Adapter for DXF generator port."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.pipeline.intent_to_agent import generate_dxf_from_intent
from app.services.ports.dxf_generator import DXFGeneratorPort


class PipelineDXFGenerator(DXFGeneratorPort):
    """DXF generator using the existing intent pipeline."""

    def generate(self, intent: Any, planning_context: Any | None = None) -> Path:
        return generate_dxf_from_intent(intent, planning_context)

