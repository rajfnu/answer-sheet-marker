"""Base LLM client interface for provider abstraction."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class StopReason(str, Enum):
    """Reason why the model stopped generating."""
    END_TURN = "end_turn"
    TOOL_USE = "tool_use"
    MAX_TOKENS = "max_tokens"
    STOP_SEQUENCE = "stop_sequence"


@dataclass
class ToolUse:
    """Represents a tool use request from the LLM."""
    id: str
    name: str
    input: Dict[str, Any]


@dataclass
class LLMResponse:
    """Unified response format across all LLM providers."""
    content: str
    stop_reason: StopReason
    tool_uses: List[ToolUse]
    usage: Optional[Dict[str, int]] = None  # Token usage stats

    @property
    def has_tool_use(self) -> bool:
        """Check if response contains tool uses."""
        return len(self.tool_uses) > 0


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients.

    This provides a unified interface for interacting with different LLM providers,
    whether they are API-based (Anthropic, OpenAI) or locally hosted (Ollama, LM Studio).
    """

    def __init__(self, model: str, **kwargs):
        """Initialize the LLM client.

        Args:
            model: Model identifier (e.g., "claude-sonnet-4", "llama3", "gpt-4")
            **kwargs: Provider-specific configuration
        """
        self.model = model
        self.config = kwargs

    @abstractmethod
    def create_message(
        self,
        system: str,
        messages: List[Dict[str, Any]],
        max_tokens: int = 4096,
        temperature: float = 0.0,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> LLMResponse:
        """Create a message with the LLM.

        This is the main method for interacting with the LLM. All providers
        must implement this method following the same interface.

        Args:
            system: System prompt
            messages: List of message dictionaries with 'role' and 'content'
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 = deterministic)
            tools: List of tool definitions
            tool_choice: Tool selection strategy
            **kwargs: Provider-specific parameters

        Returns:
            LLMResponse object with standardized format

        Raises:
            Exception: If the API call fails
        """
        pass

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Count tokens in text.

        Args:
            text: Text to count tokens for

        Returns:
            Number of tokens
        """
        pass

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model.

        Returns:
            Dictionary with model information
        """
        return {
            "model": self.model,
            "provider": self.__class__.__name__,
            "config": self.config
        }

    def supports_tool_use(self) -> bool:
        """Check if this provider supports tool/function calling.

        Returns:
            True if tool use is supported
        """
        return True  # Override in providers that don't support tools

    def supports_vision(self) -> bool:
        """Check if this provider supports vision/image inputs.

        Returns:
            True if vision is supported
        """
        return False  # Override in providers that support vision
