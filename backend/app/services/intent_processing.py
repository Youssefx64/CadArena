"""
Intent processing orchestration (defaults + planning + DXF generation).
"""

from app.schemas.intent_draft import DesignIntentDraft
from app.services.adapters.dxf_generator_adapter import PipelineDXFGenerator
from app.services.intent_defaults import IntentDefaultsResolver
from app.services.ports.dxf_generator import DXFGeneratorPort


_DEFAULT_DXF_GENERATOR: DXFGeneratorPort = PipelineDXFGenerator()


def generate_dxf_from_payload(
    payload: DesignIntentDraft | dict,
    dxf_generator: DXFGeneratorPort = _DEFAULT_DXF_GENERATOR,
):
    resolver = IntentDefaultsResolver()
    intent, planning_context = resolver.resolve(payload)
    return dxf_generator.generate(intent, planning_context)
