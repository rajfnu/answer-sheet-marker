"""OpenAI-compatible API adapter.

This adapter works with:
- OpenAI (GPT-4, GPT-3.5)
- Together.ai (Llama, Mistral, etc.)
- Any OpenAI-compatible API endpoint
"""

from typing import List, Dict, Any, Optional
import json
from loguru import logger

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI package not installed. Install with: pip install openai")

from .base import BaseLLMClient, LLMResponse, ToolUse, StopReason


class OpenAIAdapter(BaseLLMClient):
    """Adapter for OpenAI and compatible APIs.

    Compatible with:
    - OpenAI API (gpt-4, gpt-3.5-turbo)
    - Together.ai
    - Anyscale Endpoints
    - Any OpenAI-compatible API
    """

    def __init__(
        self,
        model: str,
        api_key: str,
        base_url: Optional[str] = None,
        **kwargs
    ):
        """Initialize OpenAI-compatible client.

        Args:
            model: Model name (e.g., "gpt-4", "meta-llama/Llama-3-70b")
            api_key: API key
            base_url: Custom API base URL (for compatible services)
            **kwargs: Additional configuration
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI package required. Install with: pip install openai")

        super().__init__(model, **kwargs)

        client_kwargs = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url

        self.client = OpenAI(**client_kwargs)
        logger.info(f"Initialized OpenAI adapter with model: {model}")

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
        """Create a message using OpenAI-compatible API.

        Args:
            system: System prompt
            messages: List of messages
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            tools: Tool definitions (OpenAI function calling format)
            tool_choice: Tool choice strategy
            **kwargs: Additional API parameters

        Returns:
            Standardized LLMResponse
        """
        try:
            # Convert system prompt to message format
            openai_messages = [
                {"role": "system", "content": system}
            ] + messages

            # Convert tools to OpenAI format if provided
            openai_tools = None
            if tools:
                openai_tools = self._convert_tools_to_openai_format(tools)

            # Convert tool_choice to OpenAI format
            openai_tool_choice = None
            if tool_choice:
                openai_tool_choice = self._convert_tool_choice_to_openai_format(tool_choice)

            # Build API call parameters
            api_params = {
                "model": self.model,
                "messages": openai_messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }

            if openai_tools:
                api_params["tools"] = openai_tools
            if openai_tool_choice:
                api_params["tool_choice"] = openai_tool_choice

            # Call OpenAI API
            response = self.client.chat.completions.create(**api_params)

            # Extract response
            choice = response.choices[0]
            message = choice.message

            # Extract text content
            text_content = message.content or ""

            # Extract tool calls if any
            tool_uses = []
            if message.tool_calls:
                for tool_call in message.tool_calls:
                    try:
                        tool_input = json.loads(tool_call.function.arguments)
                        tool_uses.append(
                            ToolUse(
                                id=tool_call.id,
                                name=tool_call.function.name,
                                input=tool_input
                            )
                        )
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse tool arguments: {tool_call.function.arguments}")

            # Map finish reason to stop reason
            finish_reason_map = {
                "stop": StopReason.END_TURN,
                "tool_calls": StopReason.TOOL_USE,
                "length": StopReason.MAX_TOKENS,
                "content_filter": StopReason.STOP_SEQUENCE,
            }
            stop_reason = finish_reason_map.get(choice.finish_reason, StopReason.END_TURN)

            # Extract usage
            usage = None
            if response.usage:
                usage = {
                    "input_tokens": response.usage.prompt_tokens,
                    "output_tokens": response.usage.completion_tokens,
                }

            return LLMResponse(
                content=text_content,
                stop_reason=stop_reason,
                tool_uses=tool_uses,
                usage=usage
            )

        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise

    def _convert_tools_to_openai_format(
        self,
        tools: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Convert Anthropic tool format to OpenAI function format.

        Args:
            tools: List of tools in Anthropic format

        Returns:
            List of tools in OpenAI format
        """
        openai_tools = []

        for tool in tools:
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool.get("input_schema", {})
                }
            })

        return openai_tools

    def _convert_tool_choice_to_openai_format(
        self,
        tool_choice: Dict[str, Any]
    ) -> Any:
        """Convert Anthropic tool_choice to OpenAI format.

        Args:
            tool_choice: Tool choice in Anthropic format

        Returns:
            Tool choice in OpenAI format
        """
        if tool_choice.get("type") == "tool":
            # Force specific tool
            return {
                "type": "function",
                "function": {"name": tool_choice.get("name")}
            }
        elif tool_choice.get("type") == "any":
            return "required"
        elif tool_choice.get("type") == "auto":
            return "auto"

        return "auto"

    def count_tokens(self, text: str) -> int:
        """Count tokens using tiktoken.

        Args:
            text: Text to count

        Returns:
            Token count
        """
        try:
            import tiktoken

            # Try to get encoding for the model
            try:
                encoding = tiktoken.encoding_for_model(self.model)
            except KeyError:
                # Use cl100k_base as default (GPT-4/3.5)
                encoding = tiktoken.get_encoding("cl100k_base")

            return len(encoding.encode(text))

        except ImportError:
            # Fallback to approximation
            return len(text) // 4

    def supports_tool_use(self) -> bool:
        """OpenAI models support function calling."""
        return True

    def supports_vision(self) -> bool:
        """GPT-4 Vision and some other models support vision."""
        vision_models = ["gpt-4-vision", "gpt-4o", "gpt-4-turbo"]
        return any(vm in self.model.lower() for vm in vision_models)
