"""Multi-Agent Orchestration Pipeline for ArchChat."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from app.config import RAGSettings
from app.embeddings import GenerationClient

# Import all 26 specialized agents
from app.agents.core import (
    IntentClassifier,
    PlannerAgent,
    DocumentRouter,
    MetadataAgent,
    ChunkingAgent,
    EmbeddingAgent,
    ContextCompressionAgent
)
from app.agents.extraction import (
    OCRAgent,
    VisionAgent,
    DocumentAnalyst,
    TableExtractionAgent,
    DXFAnalyst,
    IFCAnalyst
)
from app.agents.retrieval import (
    HybridRetrievalAgent,
    GraphRetrievalAgent
)
from app.agents.engineering import (
    CADGeometryAgent,
    CodeComplianceAgent,
    StructuralAgent,
    ArchitecturalReasoningAgent,
    BOQAgent,
    MaterialRecommendationAgent,
    CostEstimationAgent
)
from app.agents.validation import (
    HallucinationDetector,
    CitationValidator,
    QAAgent,
    SynthesisAgent
)

logger = logging.getLogger(__name__)

class AgentPipeline:
    """Orchestrates the parallel and sequential execution of the 26 specialized agents."""

    def __init__(self, settings: RAGSettings) -> None:
        self.settings = settings
        self.generator = GenerationClient(settings)
        
        # Instantiate registry
        self.agents: Dict[str, Any] = {
            "IntentClassifier": IntentClassifier(settings, self.generator),
            "PlannerAgent": PlannerAgent(settings, self.generator),
            "DocumentRouter": DocumentRouter(settings, self.generator),
            "MetadataAgent": MetadataAgent(settings, self.generator),
            "ChunkingAgent": ChunkingAgent(settings, self.generator),
            "EmbeddingAgent": EmbeddingAgent(settings, self.generator),
            "ContextCompressionAgent": ContextCompressionAgent(settings, self.generator),
            
            "OCRAgent": OCRAgent(settings, self.generator),
            "VisionAgent": VisionAgent(settings, self.generator),
            "DocumentAnalyst": DocumentAnalyst(settings, self.generator),
            "TableExtractionAgent": TableExtractionAgent(settings, self.generator),
            "DXFAnalyst": DXFAnalyst(settings, self.generator),
            "IFCAnalyst": IFCAnalyst(settings, self.generator),
            
            "HybridRetrievalAgent": HybridRetrievalAgent(settings, self.generator),
            "GraphRetrievalAgent": GraphRetrievalAgent(settings, self.generator),
            
            "CADGeometryAgent": CADGeometryAgent(settings, self.generator),
            "CodeComplianceAgent": CodeComplianceAgent(settings, self.generator),
            "StructuralAgent": StructuralAgent(settings, self.generator),
            "ArchitecturalReasoningAgent": ArchitecturalReasoningAgent(settings, self.generator),
            "BOQAgent": BOQAgent(settings, self.generator),
            "MaterialRecommendationAgent": MaterialRecommendationAgent(settings, self.generator),
            "CostEstimationAgent": CostEstimationAgent(settings, self.generator),
            
            "HallucinationDetector": HallucinationDetector(settings, self.generator),
            "CitationValidator": CitationValidator(settings, self.generator),
            "QAAgent": QAAgent(settings, self.generator),
            "SynthesisAgent": SynthesisAgent(settings, self.generator)
        }

    def execute_chat(self, question: str, collection: str = "default", filters: Optional[Dict[str, Any]] = None, override_intent: Optional[str] = None) -> Dict[str, Any]:
        """Process user queries through the intent classification, planning, retrieval, reasoning, and QA agents."""
        agents_used = []
        context = {"query": question, "collection": collection, "filters": filters}

        # 1. Intent Classification
        intent_classifier = self.agents["IntentClassifier"]
        intent_output = intent_classifier.run(question, context)
        agents_used.append("IntentClassifier")

        is_relevant = intent_output.output["is_relevant"]
        if override_intent:
            is_relevant = True

        if not is_relevant:
            # Short-circuit and return designated off-topic response formatted correctly
            synthesis_agent = self.agents["SynthesisAgent"]
            synthesis_input = {
                "answer": intent_output.output["response"],
                "confidence": 0.0,
                "sources": [],
                "agents_used": agents_used,
                "reasoning": "Query is outside specified civil/architectural engineering domain restrictions.",
                "findings": {"key_points": [], "warnings": [], "recommendations": []},
                "limitations": ["Domain restriction active."],
                "follow_up_questions": []
            }
            res = synthesis_agent.run(synthesis_input, context)
            return res.output

        intent = override_intent or intent_output.output["intent"]
        context["classified_intent"] = intent

        # 2. Planning
        planner = self.agents["PlannerAgent"]
        plan_output = planner.run({"query": question, "intent": intent}, context)
        agents_used.append("PlannerAgent")
        tasks = plan_output.output["tasks"]

        # Shared execution state
        execution_results: Dict[str, Any] = {
            "answer": "",
            "confidence": 0.95,
            "sources": [],
            "reasoning": "",
            "findings": {"key_points": [], "warnings": [], "recommendations": []},
            "limitations": [],
            "follow_up_questions": []
        }

        # Execute planned tasks
        for task_name in tasks:
            if task_name not in self.agents:
                continue

            agent = self.agents[task_name]
            agents_used.append(task_name)

            try:
                if task_name == "HybridRetrievalAgent":
                    ret_output = agent.run({"query": question, "collection": collection, "filters": filters}, context)
                    execution_results["sources"] = ret_output.output["retrieved_sources"]
                    context["raw_sources"] = ret_output.output["retrieved_sources"]
                    
                elif task_name == "GraphRetrievalAgent":
                    graph_output = agent.run({"query": question}, context)
                    context["graph_context"] = graph_output.output["graph_context"]
                    
                elif task_name == "ContextCompressionAgent":
                    comp_output = agent.run(execution_results["sources"], context)
                    context["compressed_context"] = comp_output.output["compressed_context"]
                    
                elif task_name == "CodeComplianceAgent":
                    comp_check = agent.run({"rooms": context.get("geometry_rooms", [])}, context)
                    execution_results["findings"]["warnings"].extend(comp_check.output["findings"]["warnings"])
                    if "code_reasoning" in comp_check.output["findings"]:
                        execution_results["reasoning"] += "\n" + comp_check.output["findings"]["code_reasoning"]

                elif task_name == "CADGeometryAgent":
                    geom_check = agent.run({}, context)
                    context["geometry_rooms"] = geom_check.output["calculated_rooms"]
                    execution_results["findings"]["key_points"].append(f"Total calculated area: {geom_check.output['total_area']} m2")

                elif task_name == "BOQAgent":
                    boq_check = agent.run({"rooms": context.get("geometry_rooms", [])}, context)
                    context["boq_items"] = boq_check.output["boq_items"]

                elif task_name == "CostEstimationAgent":
                    cost_check = agent.run({"boq_items": context.get("boq_items", [])}, context)
                    execution_results["findings"]["recommendations"].append(f"Estimated Total Material Cost: L.E. {cost_check.output['total_cost']}")

                elif task_name == "SynthesisAgent":
                    # Generate the core answer text using GenerationClient
                    context_block = context.get("compressed_context", "")
                    if context.get("graph_context"):
                        context_block += "\n\n" + context["graph_context"]
                    
                    # Generate text
                    llm_response = self.generator.generate(question=question, context=context_block)
                    execution_results["answer"] = llm_response
                    execution_results["agents_used"] = list(set(agents_used))
                    
                    # Run synthesis format
                    syn_output = agent.run(execution_results, context)
                    execution_results = syn_output.output

                elif task_name == "HallucinationDetector":
                    hall_output = agent.run({"answer": execution_results.get("answer", ""), "sources": execution_results.get("sources", [])}, context)
                    if not hall_output.output["passed"]:
                        execution_results["confidence"] *= 0.8
                        execution_results["limitations"].extend(hall_output.output["hallucinations"])

                elif task_name == "CitationValidator":
                    cit_output = agent.run({"sources": execution_results.get("sources", [])}, context)
                    execution_results["sources"] = cit_output.output["validated_sources"]

                elif task_name == "QAAgent":
                    qa_output = agent.run(execution_results, context)
                    if not qa_output.output["qa_passed"]:
                        execution_results["confidence"] *= 0.9

            except Exception as e:
                logger.error(f"Multi-Agent pipeline error at step {task_name}: {e}", exc_info=True)

        return execution_results
