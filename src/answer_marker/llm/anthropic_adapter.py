"""Anthropic Claude API adapter."""

from typing import List, Dict, Any, Optional
from anthropic import Anthropic
from loguru import logger

from .base import BaseLLMClient, LLMResponse, ToolUse, StopReason


class AnthropicAdapter(BaseLLMClient):
    """Adapter for Anthropic Claude API.

    This adapter wraps the Anthropic Python SDK to provide a unified interface
    compatible with our BaseLLMClient abstraction.
    """

    def __init__(self, model: str, api_key: str, **kwargs):
        """Initialize Anthropic client.

        Args:
            model: Claude model name (e.g., "claude-sonnet-4-5-20250929")
            api_key: Anthropic API key
            **kwargs: Additional configuration
        """
        super().__init__(model, **kwargs)
        self.client = Anthropic(api_key=api_key)
        logger.info(f"Initialized Anthropic adapter with model: {model}")

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
        """Create a message using Claude API.

        Args:
            system: System prompt
            messages: List of messages
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            tools: Tool definitions
            tool_choice: Tool choice strategy
            **kwargs: Additional Anthropic-specific parameters

        Returns:
            Standardized LLMResponse
        """
        try:
            # Call Anthropic API
            response = self.client.messages.create(
                model=self.model,
                system=system,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                tools=tools or [],
                tool_choice=tool_choice,
                **kwargs
            )

            # Extract tool uses if any
            tool_uses = []
            text_content = ""

            for block in response.content:
                if block.type == "text":
                    text_content += block.text
                elif block.type == "tool_use":
                    tool_uses.append(
                        ToolUse(
                            id=block.id,
                            name=block.name,
                            input=block.input
                        )
                    )

            # Map stop reason
            stop_reason_map = {
                "end_turn": StopReason.END_TURN,
                "tool_use": StopReason.TOOL_USE,
                "max_tokens": StopReason.MAX_TOKENS,
                "stop_sequence": StopReason.STOP_SEQUENCE,
            }
            stop_reason = stop_reason_map.get(response.stop_reason, StopReason.END_TURN)

            # Extract usage statistics
            usage = {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            }

            return LLMResponse(
                content=text_content,
                stop_reason=stop_reason,
                tool_uses=tool_uses,
                usage=usage
            )

        except Exception as e:
            logger.error(f"Anthropic API call failed: {e}")
            raise

    def count_tokens(self, text: str) -> int:
        """Count tokens using Anthropic's counting method.

        Args:
            text: Text to count

        Returns:
            Token count (approximate)
        """
        # Anthropic uses roughly 3.5 chars per token
        # For more accurate counting, you could use the count_tokens API
        return len(text) // 4

    def supports_tool_use(self) -> bool:
        """Anthropic Claude supports tool use."""
        return True

    def supports_vision(self) -> bool:
        """Claude Sonnet and Opus support vision."""
        return "sonnet" in self.model.lower() or "opus" in self.model.lower()
