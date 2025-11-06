"""Compatibility layer for existing agents to work with new LLM abstraction.

This module provides a wrapper that makes our BaseLLMClient compatible with
the existing Anthropic-style API that agents expect.
"""

from typing import List, Dict, Any, Optional
from .base import BaseLLMClient


class LLMClientCompat:
    """Compatibility wrapper that makes BaseLLMClient work like Anthropic client.

    This allows existing agents to work without modification while using
    any LLM provider through our abstraction layer.
    """

    def __init__(self, llm_client: BaseLLMClient):
        """Initialize compatibility wrapper.

        Args:
            llm_client: Any BaseLLMClient implementation
        """
        self.llm_client = llm_client
        self.messages = self  # For client.messages.create() pattern

    def create(
        self,
        model: Optional[str] = None,  # Ignored, uses client's model
        system: str = "",
        messages: List[Dict[str, Any]] = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """Create a message (Anthropic-compatible API).

        Args:
            model: Ignored (uses client's configured model)
            system: System prompt
            messages: List of messages
            max_tokens: Maximum tokens
            temperature: Sampling temperature
            tools: Tool definitions
            tool_choice: Tool selection strategy
            **kwargs: Additional parameters

        Returns:
            Response object compatible with Anthropic format
        """
        # Call our unified LLM client
        response = self.llm_client.create_message(
            system=system,
            messages=messages or [],
            max_tokens=max_tokens,
            temperature=temperature,
            tools=tools,
            tool_choice=tool_choice,
            **kwargs
        )

        # Convert to Anthropic-compatible format
        return AnthropicCompatResponse(response)


class AnthropicCompatResponse:
    """Response object compatible with Anthropic's response format."""

    def __init__(self, llm_response):
        """Initialize from LLMResponse.

        Args:
            llm_response: LLMResponse object from BaseLLMClient
        """
        self._response = llm_response

        # Map stop reason
        self.stop_reason = llm_response.stop_reason.value

        # Create content blocks
        self.content = []

        # Add text content if present
        if llm_response.content:
            text_block = TextBlock(llm_response.content)
            self.content.append(text_block)

        # Add tool use blocks
        for tool_use in llm_response.tool_uses:
            tool_block = ToolUseBlock(
                id=tool_use.id,
                name=tool_use.name,
                input=tool_use.input
            )
            self.content.append(tool_block)

        # Usage info
        if llm_response.usage:
            self.usage = UsageInfo(
                input_tokens=llm_response.usage.get("input_tokens", 0),
                output_tokens=llm_response.usage.get("output_tokens", 0)
            )
        else:
            self.usage = UsageInfo(input_tokens=0, output_tokens=0)


class TextBlock:
    """Text content block (Anthropic-compatible)."""

    def __init__(self, text: str):
        self.type = "text"
        self.text = text


class ToolUseBlock:
    """Tool use block (Anthropic-compatible)."""

    def __init__(self, id: str, name: str, input: Dict[str, Any]):
        self.type = "tool_use"
        self.id = id
        self.name = name
        self.input = input


class UsageInfo:
    """Usage information (Anthropic-compatible)."""

    def __init__(self, input_tokens: int, output_tokens: int):
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
