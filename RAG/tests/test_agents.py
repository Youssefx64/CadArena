"""Unit tests for ArchChat Multi-Agent orchestration pipeline."""
from __future__ import annotations

import pytest
from app.config import get_rag_settings
from app.agents import AgentPipeline

def test_pipeline_on_topic() -> None:
    settings = get_rag_settings()
    pipeline = AgentPipeline(settings)
    
    # Mock the LLM generator to avoid cloud network calls
    class MockGenerator:
        def generate(self, question: str, context: str) -> str:
            return "Concrete slab thickness should be verified against EBC Clause 4.2."
    pipeline.generator = MockGenerator()
    for agent in pipeline.agents.values():
        agent.generator = MockGenerator()

    # Query about building structures
    res = pipeline.execute_chat("What is the required thickness of reinforced concrete slab?")
    
    assert isinstance(res, dict)
    assert "answer" in res
    assert "Concrete slab" in res["answer"]
    assert res["confidence"] >= 0.7
    assert isinstance(res["sources"], list)
    assert "IntentClassifier" in res["agents_used"]
    assert "SynthesisAgent" in res["agents_used"]
    assert isinstance(res["findings"], dict)
    assert "key_points" in res["findings"]
    assert "warnings" in res["findings"]

def test_pipeline_off_topic() -> None:
    settings = get_rag_settings()
    pipeline = AgentPipeline(settings)
    
    # Mock the LLM generator to return a rejection/no answer just in case
    class MockGenerator:
        def generate(self, question: str, context: str) -> str:
            return "NO"
    pipeline.generator = MockGenerator()
    for agent in pipeline.agents.values():
        agent.generator = MockGenerator()

    # Off topic query
    res = pipeline.execute_chat("Explain how to write a quicksort algorithm in python.")
    
    assert isinstance(res, dict)
    assert res["answer"] == "I am specialized in architectural and civil engineering only. Please ask questions related to these fields."
    assert res["confidence"] == 0.0
    assert len(res["sources"]) == 0
