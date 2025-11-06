"""Core package for the Answer Sheet Marker system.

This package provides the base agent infrastructure and orchestration logic.
"""

from .agent_base import BaseAgent, AgentConfig, AgentMessage
from .orchestrator import OrchestratorAgent, create_orchestrator_agent

__all__ = [
    "BaseAgent",
    "AgentConfig",
    "AgentMessage",
    "OrchestratorAgent",
    "create_orchestrator_agent",
]
