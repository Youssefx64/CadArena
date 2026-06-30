"""Multi-Agent System Module for ArchChat.

Exposes base Agent definitions and the orchestrator AgentPipeline.
"""
from __future__ import annotations

from app.agents.base import Agent, AgentOutput
from app.agents.orchestrator import AgentPipeline

__all__ = ["Agent", "AgentOutput", "AgentPipeline"]
