"""LLM abstraction layer for Answer Sheet Marker.

This package provides a unified interface for different LLM providers,
allowing easy switching between API-based and locally-hosted models.
"""

from .base import BaseLLMClient, LLMResponse, ToolUse
from .factory import create_llm_client, LLMProvider
from .anthropic_adapter import AnthropicAdapter
from .ollama_adapter import OllamaAdapter
from .openai_adapter import OpenAIAdapter

__all__ = [
    "BaseLLMClient",
    "LLMResponse",
    "ToolUse",
    "create_llm_client",
    "LLMProvider",
    "AnthropicAdapter",
    "OllamaAdapter",
    "OpenAIAdapter",
]
