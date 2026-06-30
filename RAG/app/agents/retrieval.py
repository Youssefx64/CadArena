"""Retrieval and GraphRAG agents for ArchChat."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from app.agents.base import Agent, AgentOutput
from app.knowledge_graph import get_knowledge_graph

logger = logging.getLogger(__name__)

class HybridRetrievalAgent(Agent):
    """Retrieves document chunks combining dense semantic similarity and exact keyword BM25 ranks."""

    def run(self, input_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> AgentOutput:
        query = input_data.get("query", "")
        collection = input_data.get("collection", "default")
        top_k = input_data.get("top_k", self.settings.RAG_TOP_K)
        filters = input_data.get("filters", None)

        from app.rag_engine import get_rag_engine
        engine = get_rag_engine()
        
        # 1. Embed query
        query_embedding = engine.embedder.embed_query(query)
        
        # 2. Hybrid search using vector store
        sources = engine.vector_store.search_hybrid(
            collection=collection,
            query_text=query,
            embedding=query_embedding,
            top_k=top_k,
            filters=filters
        )
        
        source_dicts = [s.to_dict() for s in sources]
        
        return AgentOutput(
            output={"retrieved_sources": source_dicts},
            confidence=0.95 if sources else 0.5,
            metadata={"source_count": len(sources)}
        )


class GraphRetrievalAgent(Agent):
    """Retrieves connected entity subgraphs based on search keywords for GraphRAG context expansion."""

    def run(self, input_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> AgentOutput:
        query = input_data.get("query", "")
        max_depth = input_data.get("max_depth", 1)

        kg = get_knowledge_graph()
        
        # Extract seed keywords from query (nouns or capital words)
        words = [w.strip("?,.!-()\"'") for w in query.split() if len(w) > 3]
        
        subgraph = kg.retrieve_subgraph(seed_keywords=words, max_depth=max_depth)
        
        # Format the subgraph into readable context
        nodes = subgraph.get("nodes", [])
        edges = subgraph.get("edges", [])
        
        output_text = ""
        if nodes:
            output_parts = ["Knowledge Graph Entities found:"]
            for node in nodes:
                output_parts.append(f"  - Node: {node['name']} (Type: {node['type']})")
            if edges:
                output_parts.append("\nRelationships:")
                for edge in edges:
                    output_parts.append(f"  - {edge['source']} --[{edge['type']}]--> {edge['target']}")
            output_text = "\n".join(output_parts)

        return AgentOutput(
            output={"graph_context": output_text, "subgraph": subgraph},
            confidence=0.9 if nodes else 0.5,
            metadata={"nodes_retrieved": len(nodes), "edges_retrieved": len(edges)}
        )
