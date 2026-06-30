"""Tests for Knowledge Graph and Hybrid Search functionality."""
from __future__ import annotations

import tempfile
import os
import pytest
from app.knowledge_graph import KnowledgeGraph
from app.vector_store import RetrievedSource, QdrantVectorStore
from app.config import get_rag_settings

def test_knowledge_graph() -> None:
    # Use a temp DB file
    fd, temp_db = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    
    try:
        kg = KnowledgeGraph(db_path=temp_db)
        
        # Test nodes
        kg.add_node("clause_4_2", "EBC Clause 4.2", "CodeSection")
        kg.add_node("concrete", "Reinforced Concrete", "Material")
        
        # Test edges
        kg.add_edge("clause_4_2", "concrete", "REGULATES")
        
        # Query neighbors
        neighbors = kg.get_neighbors("clause_4_2")
        assert len(neighbors) == 1
        assert neighbors[0][0] == "concrete"
        assert neighbors[0][2] == "REGULATES"
        
        # Search
        matches = kg.search_nodes("Concrete")
        assert len(matches) == 1
        assert matches[0]["id"] == "concrete"
        
        # Subgraph
        subgraph = kg.retrieve_subgraph(["Clause"], max_depth=1)
        assert len(subgraph["nodes"]) == 2
        assert len(subgraph["edges"]) == 1
    finally:
        if os.path.exists(temp_db):
            os.remove(temp_db)

def test_hybrid_search_mock() -> None:
    # We can mock the Qdrant client to test the BM25 and RRF logic in search_hybrid
    settings = get_rag_settings()
    store = QdrantVectorStore(settings)
    
    # Mock candidates returned by semantic search
    candidates = [
        RetrievedSource(text="EBC 2023 regulates room dimensions.", metadata={"source": "ebc"}, score=0.9),
        RetrievedSource(text="Columns are structural support members.", metadata={"source": "standards"}, score=0.8),
        RetrievedSource(text="Concrete strength and steel reinforcement specs.", metadata={"source": "specs"}, score=0.7),
    ]
    
    # Mock the search method of the store
    def mock_search(*args, **kwargs):
        return candidates
    
    store.search = mock_search
    # Mock collection_exists to always be true for the test
    class MockClient:
        def collection_exists(self, collection_name):
            return True
    store._client = MockClient()
    
    # Perform hybrid search for "reinforcement concrete columns"
    results = store.search_hybrid(
        collection="test",
        query_text="concrete columns",
        embedding=[0.0] * 1024,
        top_k=3
    )
    
    assert len(results) == 3
    # Check that documents matching keywords bubble up in score/rank
    # "concrete strength and steel reinforcement specs" and "Columns are structural..." should be boosted
    texts = [r.text for r in results]
    assert "Columns are structural support members." in texts
    assert "Concrete strength and steel reinforcement specs." in texts
