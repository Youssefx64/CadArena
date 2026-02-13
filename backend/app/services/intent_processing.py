"""
Intent processing orchestration (defaults + planning + DXF generation).
"""

from app.pipeline.intent_to_agent import generate_dxf_from_intent
from app.schemas.intent_draft import DesignIntentDraft
from app.services.intent_defaults import IntentDefaultsResolver


def generate_dxf_from_payload(payload: DesignIntentDraft | dict):
    resolver = IntentDefaultsResolver()
    intent, planning_context = resolver.resolve(payload)
    return generate_dxf_from_intent(intent, planning_context)
