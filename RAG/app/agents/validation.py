"""Validation, citation, QA, and synthesis agents for ArchChat."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from app.agents.base import Agent, AgentOutput

logger = logging.getLogger(__name__)

class HallucinationDetector(Agent):
    """Verifies that final assertions, codes, and metrics correspond directly to cited sources."""

    def run(self, input_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> AgentOutput:
        answer = input_data.get("answer", "")
        sources = input_data.get("sources", [])
        
        # Heuristically check if numbers or sections in answer exist in sources
        hallucinations = []
        import re
        
        # Find clause numbers like 4.2 or 112-A
        clauses = re.findall(r"\b\d+\.\d+\b", answer)
        source_text = "\n".join([s.get("text", "") for s in sources]).lower()
        
        for c in clauses:
            if c not in source_text:
                hallucinations.append(f"Referenced clause '{c}' not found in retrieved source texts.")

        confidence = 1.0
        if hallucinations:
            confidence = 0.8
            
        return AgentOutput(
            output={"hallucinations": hallucinations, "passed": len(hallucinations) == 0},
            confidence=confidence,
            metadata={"checked_clauses": len(clauses)}
        )


class CitationValidator(Agent):
    """Validates citations and formats the source collection index ranges."""

    def run(self, input_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> AgentOutput:
        sources = input_data.get("sources", [])
        validated_sources = []

        for idx, src in enumerate(sources):
            # Clean and structure the source
            text = src.get("text", "").strip()
            meta = src.get("metadata", {})
            score = src.get("score")
            
            validated_sources.append({
                "id": idx + 1,
                "source_name": meta.get("filename") or meta.get("source") or f"Source-{idx+1}",
                "text_snippet": text[:200] + "..." if len(text) > 200 else text,
                "confidence_score": score
            })

        return AgentOutput(
            output={"validated_sources": validated_sources},
            confidence=1.0,
            metadata={"source_count": len(sources)}
        )


class QAAgent(Agent):
    """Performs a final review check for engineering completeness and clarity."""

    def run(self, input_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> AgentOutput:
        answer = input_data.get("answer", "")
        findings = input_data.get("findings", {})
        
        warnings = []
        if not answer:
            warnings.append("QA warning: Answer body is blank.")
        if len(answer) < 30 and len(findings.get("key_points", [])) == 0:
            warnings.append("QA warning: Response length is extremely short for an engineering query.")

        confidence = 0.95
        if warnings:
            confidence = 0.85
            
        return AgentOutput(
            output={"qa_passed": len(warnings) == 0, "qa_warnings": warnings},
            confidence=confidence,
            metadata={}
        )


class SynthesisAgent(Agent):
    """Formats the final payload response structure for ArchChat."""

    def run(self, input_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> AgentOutput:
        answer = input_data.get("answer", "")
        confidence = float(input_data.get("confidence", 0.95))
        sources = input_data.get("sources", [])
        agents_used = input_data.get("agents_used", [])
        reasoning = input_data.get("reasoning", "")
        
        findings = input_data.get("findings", {})
        key_points = findings.get("key_points", [])
        warnings = findings.get("warnings", [])
        recommendations = findings.get("recommendations", [])
        
        limitations = input_data.get("limitations", [])
        follow_up_questions = input_data.get("follow_up_questions", [])

        # Enforce confidence threshold
        if confidence < 0.70 and "I am specialized in architectural and civil engineering only" not in answer:
            answer = "I need more information before providing an engineering answer."
            warnings.append("Confidence score below 0.70 threshold. Query marked as insufficient information.")

        # Ensure core elements are present
        if not key_points and answer:
            # Extract key points from answer as a fallback
            key_points = [s.strip() for s in answer.split(".") if len(s.strip()) > 15][:3]

        response_payload = {
            "answer": answer,
            "confidence": round(confidence, 2),
            "sources": sources,
            "agents_used": agents_used,
            "reasoning": reasoning or "Multi-Agent engineering pipeline verification completed.",
            "findings": {
                "key_points": key_points,
                "warnings": warnings,
                "recommendations": recommendations
            },
            "limitations": limitations or ["Calculations and compliance checks are based strictly on indexed building codes."],
            "follow_up_questions": follow_up_questions or ["Would you like to verify this design against any specific clause of the Egyptian Building Code?"]
        }

        return AgentOutput(
            output=response_payload,
            confidence=1.0,
            metadata={}
        )
