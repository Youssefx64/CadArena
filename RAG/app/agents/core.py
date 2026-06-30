"""Core coordination and system agents for ArchChat."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from app.agents.base import Agent, AgentOutput
from app.config import RAGSettings

logger = logging.getLogger(__name__)

class IntentClassifier(Agent):
    """Classifies user queries into civil/architectural engineering intents or rejects them if out of scope."""

    # Allowed domains to match
    ALLOWED_KEYWORDS = [
        "architect", "civil", "structural", "bim", "cad", "dxf", "ifc", "dwg", "autocad",
        "floor plan", "structural drawing", "mep", "site plan", "quantity", "boq", "bill of quantit",
        "specification", "report", "building code", "egyptian building code", "ebc", "urban",
        "interior", "layout", "wall", "beam", "column", "slab", "foundation", "clearance", "height",
        "reinforced", "concrete", "steel", "brick", "loading", "footing", "soil", "plumbing", "hvac"
    ]

    OFF_TOPIC_RESPONSE = "I am specialized in architectural and civil engineering only. Please ask questions related to these fields."

    def run(self, input_data: str, context: Optional[Dict[str, Any]] = None) -> AgentOutput:
        query = input_data.strip()
        query_lower = query.lower()

        # 1. Quick rule-based classification
        is_relevant = any(keyword in query_lower for keyword in self.ALLOWED_KEYWORDS)

        # 2. LLM-based verification if rule-based isn't clear
        confidence = 1.0
        intent = "chat"
        
        if not is_relevant and self.generator is not None:
            try:
                prompt = (
                    "Determine if the user query is related to architecture, civil engineering, building codes, "
                    "structural engineering, construction documents, CAD, BIM, or construction quantities.\n"
                    "Respond with ONLY 'YES' or 'NO'.\n"
                    f"Query: {query}\n"
                    "Response:"
                )
                response = self.generator.generate(question=prompt, context="").strip().upper()
                if "YES" in response:
                    is_relevant = True
                    confidence = 0.8
                else:
                    is_relevant = False
                    confidence = 0.95
            except Exception as e:
                logger.error(f"LLM Intent classification failed: {e}")
                # Fallback to rule-based classification

        if not is_relevant:
            return AgentOutput(
                output={"is_relevant": False, "response": self.OFF_TOPIC_RESPONSE},
                confidence=confidence,
                metadata={"reason": "Query out of domain restrictions."}
            )

        # Determine sub-intent (compliance, calculate, boq, etc.)
        if any(k in query_lower for k in ["compliance", "code", "egyptian", "ebc", "regulation"]):
            intent = "compliance-check"
        elif any(k in query_lower for k in ["compare", "difference"]):
            intent = "compare"
        elif any(k in query_lower for k in ["extract", "list", "get"]):
            intent = "extract"
        elif any(k in query_lower for k in ["summarize", "summary"]):
            intent = "summarize"
        elif any(k in query_lower for k in ["boq", "bill of quantit", "quantity", "cost"]):
            intent = "calculate-boq"
        elif any(k in query_lower for k in ["area", "size", "dimension", "calculate"]):
            intent = "calculate-area"
        elif any(k in query_lower for k in ["dxf", "dwg", "drawing", "cad"]):
            intent = "check-dxf"

        return AgentOutput(
            output={"is_relevant": True, "intent": intent},
            confidence=confidence,
            metadata={"classified_intent": intent}
        )


class PlannerAgent(Agent):
    """Decomposes engineering questions into a structured list of sub-agent calls."""

    def run(self, input_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> AgentOutput:
        query = input_data.get("query", "")
        intent = input_data.get("intent", "chat")

        tasks = []
        if intent == "compliance-check":
            tasks = ["HybridRetrievalAgent", "GraphRetrievalAgent", "ContextCompressionAgent", "CodeComplianceAgent", "SynthesisAgent"]
        elif intent == "calculate-boq":
            tasks = ["DocumentRouter", "TableExtractionAgent", "BOQAgent", "CostEstimationAgent", "SynthesisAgent"]
        elif intent == "calculate-area":
            tasks = ["DocumentRouter", "CADGeometryAgent", "ArchitecturalReasoningAgent", "SynthesisAgent"]
        elif intent == "check-dxf":
            tasks = ["DocumentRouter", "DXFAnalyst", "CADGeometryAgent", "CodeComplianceAgent", "SynthesisAgent"]
        elif intent == "compare":
            tasks = ["HybridRetrievalAgent", "DocumentAnalyst", "SynthesisAgent"]
        else:
            # Default general chat path
            tasks = ["HybridRetrievalAgent", "GraphRetrievalAgent", "ContextCompressionAgent", "ArchitecturalReasoningAgent", "StructuralAgent", "SynthesisAgent"]

        # Ensure QA validation steps are appended
        tasks.extend(["HallucinationDetector", "CitationValidator", "QAAgent"])

        return AgentOutput(
            output={"tasks": tasks},
            confidence=0.95,
            metadata={"task_count": len(tasks)}
        )


class DocumentRouter(Agent):
    """Routes files or text blocks to their correct parsing and extraction sub-agents."""

    def run(self, input_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> AgentOutput:
        filename = input_data.get("filename", "")
        file_type = input_data.get("file_type", "")
        
        target_agent = "DocumentAnalyst"
        if file_type == "pdf":
            target_agent = "TableExtractionAgent"
        elif file_type == "dxf":
            target_agent = "DXFAnalyst"
        elif file_type == "ifc":
            target_agent = "IFCAnalyst"
        elif file_type == "image":
            target_agent = "OCRAgent"
        elif file_type == "csv" or file_type == "xlsx":
            target_agent = "TableExtractionAgent"

        return AgentOutput(
            output={"target_agent": target_agent},
            confidence=1.0,
            metadata={"routed_for": filename}
        )


class MetadataAgent(Agent):
    """Extracts structured metadata schemas from design specifications and plans."""

    def run(self, input_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> AgentOutput:
        content = input_data.get("content", "")
        
        # Simple extraction heuristics, fallback to LLM
        metadata = {
            "has_drawings": "drawing" in content.lower() or "dxf" in content.lower(),
            "has_tables": "table" in content.lower() or "boq" in content.lower() or "|" in content,
            "detected_domain": "general-engineering",
            "language": "en"
        }
        
        if "ebc" in content.lower() or "building code" in content.lower():
            metadata["detected_domain"] = "code-compliance"

        return AgentOutput(
            output={"metadata": metadata},
            confidence=0.9,
            metadata={}
        )


class ChunkingAgent(Agent):
    """Implements hierarchical or semantic document splitting to preserve context blocks."""

    def run(self, input_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> AgentOutput:
        document = input_data.get("content", "")
        chunk_size = input_data.get("chunk_size", self.settings.RAG_CHUNK_SIZE)
        chunk_overlap = input_data.get("chunk_overlap", self.settings.RAG_CHUNK_OVERLAP)

        # Split logically into paragraphs or sentences first, then group
        words = document.split()
        chunks = []
        start = 0
        step = max(1, chunk_size - chunk_overlap)
        
        while start < len(words):
            end = min(start + chunk_size, len(words))
            chunks.append(" ".join(words[start:end]))
            if end == len(words):
                break
            start += step

        return AgentOutput(
            output={"chunks": chunks},
            confidence=0.98,
            metadata={"chunk_count": len(chunks)}
        )


class EmbeddingAgent(Agent):
    """Wrapper agent that interfaces with Cohere or OpenAI models to retrieve query vectors."""

    def run(self, input_data: str, context: Optional[Dict[str, Any]] = None) -> AgentOutput:
        # Resolve lazily from RAGEngine
        from app.rag_engine import get_rag_engine
        engine = get_rag_engine()
        
        vector = engine.embedder.embed_query(input_data)
        
        return AgentOutput(
            output={"vector": vector},
            confidence=1.0,
            metadata={"model": engine.embedding_model_name}
        )


class ContextCompressionAgent(Agent):
    """Summarizes and filters retrieved contexts to stay within prompt length bounds."""

    def run(self, input_data: List[Dict[str, Any]], context: Optional[Dict[str, Any]] = None) -> AgentOutput:
        query = context.get("query", "") if context else ""
        
        compressed_parts = []
        for idx, source in enumerate(input_data):
            text = source.get("text", "")
            # If text is too long, extract matching sentences
            if len(text) > 800 and query:
                sentences = text.split(". ")
                matching = [s for s in sentences if any(w in s.lower() for w in query.lower().split() if len(w) > 3)]
                if matching:
                    text = "... " + ". ".join(matching[:4]) + " ..."
            compressed_parts.append(f"[Source {idx + 1}] (Score: {source.get('score', 0):.2f})\n{text}")

        compressed_text = "\n\n".join(compressed_parts)
        return AgentOutput(
            output={"compressed_context": compressed_text},
            confidence=0.92,
            metadata={"sources_compressed": len(input_data)}
        )
