"""Unit tests for the new ArchChat REST API endpoints with pipeline mocking."""
from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import patch
import httpx
import pytest

async def _request(method: str, path: str, **kwargs: Any) -> httpx.Response:
    """Call the RAG ASGI app without binding a network port."""
    from app.main import app

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.request(method, path, **kwargs)

def _call(method: str, path: str, **kwargs: Any) -> httpx.Response:
    """Run an ASGI request from synchronous pytest tests."""
    return asyncio.run(_request(method, path, **kwargs))

# Mock response for AgentPipeline.execute_chat
MOCK_PIPELINE_RESPONSE = {
    "answer": "Mocked engineering response.",
    "confidence": 0.95,
    "sources": [{"id": 1, "source_name": "test.txt", "text_snippet": "test text", "confidence_score": 0.9}],
    "agents_used": ["IntentClassifier", "SynthesisAgent"],
    "reasoning": "Mocked pipeline reasoning.",
    "findings": {
        "key_points": ["Key point 1"],
        "warnings": ["Warning 1"],
        "recommendations": ["Recommendation 1"]
    },
    "limitations": ["Mock limitation"],
    "follow_up_questions": ["Mock question"]
}

@patch("app.agents.orchestrator.AgentPipeline.execute_chat", return_value=MOCK_PIPELINE_RESPONSE)
def test_endpoints_general(mock_execute: Any) -> None:
    # 1. Chat
    resp = _call("POST", "/rag/chat", json={"question": "What is the concrete strength needed for footing?"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["answer"] == "Mocked engineering response."
    assert data["findings"]["key_points"] == ["Key point 1"]
    assert data["confidence"] == 0.95
    
    # 2. Analyze
    resp = _call("POST", "/rag/analyze", json={"question": "Analyze these beam dimensions: span 5m, depth 400mm."})
    assert resp.status_code == 200
    
    # 3. Compliance Check
    resp = _call("POST", "/rag/compliance-check", json={"question": "Check bedroom dimensions: 3m x 3.5m."})
    assert resp.status_code == 200
    
    # 4. Compare
    resp = _call("POST", "/rag/compare", json={"question": "Compare C30 vs C45 concrete grades."})
    assert resp.status_code == 200

    # 5. Extract
    resp = _call("POST", "/rag/extract", json={"question": "Extract materials from this calculation sheet."})
    assert resp.status_code == 200

    # 6. Summarize
    resp = _call("POST", "/rag/summarize", json={"question": "Summarize standard concrete specs."})
    assert resp.status_code == 200

    # 7. Calculate Area
    resp = _call("POST", "/rag/calculate-area", json={"question": "Calculate room area for living room: 4m x 5m."})
    assert resp.status_code == 200

    # 8. Calculate BOQ
    resp = _call("POST", "/rag/calculate-boq", json={"question": "Calculate BOQ for concrete slabs."})
    assert resp.status_code == 200

    # 9. Check DXF
    resp = _call("POST", "/rag/check-dxf", json={"question": "Check layers in DXF model."})
    assert resp.status_code == 200

    # 10. Vector Store collections
    resp = _call("GET", "/rag/vector-store")
    assert resp.status_code == 200
    store_data = resp.json()
    assert "collections" in store_data
    assert "ebc_2023" in store_data["collections"]
