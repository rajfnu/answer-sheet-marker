"""Ollama local LLM adapter.

Ollama (https://ollama.ai/) allows running open-source LLMs locally:
- Llama 3, Llama 2
- Mistral, Mixtral
- Phi-3, Gemma
- Many others

This adapter provides full compatibility with the Answer Sheet Marker system.
"""

from typing import List, Dict, Any, Optional
import requests
import json
from loguru import logger

from .base import BaseLLMClient, LLMResponse, ToolUse, StopReason


class OllamaAdapter(BaseLLMClient):
    """Adapter for Ollama locally-hosted LLMs.

    Ollama provides a local API compatible with OpenAI's format, making it
    easy to run powerful open-source models without any API costs.

    Popular models:
    - llama3:70b - Most capable Llama model
    - mistral:latest - Fast and efficient
    - phi3:medium - Small but capable
    - codellama:latest - Code-focused
    """

    def __init__(
        self,
        model: str,
        base_url: str = "http://localhost:11434",
        **kwargs
    ):
        """Initialize Ollama client.

        Args:
            model: Ollama model name (e.g., "llama3", "mistral", "phi3")
            base_url: Ollama server URL
            **kwargs: Additional configuration
        """
        super().__init__(model, **kwargs)
        self.base_url = base_url.rstrip("/")
        self.api_url = f"{self.base_url}/api"
        self._check_connection()
        logger.info(f"Initialized Ollama adapter with model: {model} at {base_url}")

    def _check_connection(self):
        """Check if Ollama server is accessible."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
        except Exception as e:
            logger.warning(
                f"Could not connect to Ollama at {self.base_url}. "
                f"Make sure Ollama is running: {e}"
            )

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
        """Create a message using Ollama API.

        Args:
            system: System prompt
            messages: List of messages
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            tools: Tool definitions (converted to function calling format)
            tool_choice: Tool choice strategy
            **kwargs: Additional Ollama-specific parameters

        Returns:
            Standardized LLMResponse
        """
        try:
            # Prepend system message
            ollama_messages = [
                {"role": "system", "content": system}
            ] + messages

            # Handle tool use with special prompting
            if tools:
                # For models that don't natively support function calling,
                # we'll use structured output prompting
                tool_use_response = self._handle_tool_use(
                    ollama_messages, tools, tool_choice, max_tokens, temperature
                )
                if tool_use_response:
                    return tool_use_response

            # Standard message generation
            payload = {
                "model": self.model,
                "messages": ollama_messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                }
            }

            response = requests.post(
                f"{self.api_url}/chat",
                json=payload,
                timeout=300  # 5 minute timeout for long generations
            )
            response.raise_for_status()

            result = response.json()

            # Extract response content
            content = result["message"]["content"]

            # Determine stop reason
            stop_reason = StopReason.END_TURN
            if result.get("done_reason") == "length":
                stop_reason = StopReason.MAX_TOKENS

            # Extract usage if available
            usage = None
            if "prompt_eval_count" in result:
                usage = {
                    "input_tokens": result.get("prompt_eval_count", 0),
                    "output_tokens": result.get("eval_count", 0),
                }

            return LLMResponse(
                content=content,
                stop_reason=stop_reason,
                tool_uses=[],
                usage=usage
            )

        except Exception as e:
            logger.error(f"Ollama API call failed: {e}")
            raise

    def _handle_tool_use(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        tool_choice: Optional[Dict[str, Any]],
        max_tokens: int,
        temperature: float
    ) -> Optional[LLMResponse]:
        """Handle tool use with structured output prompting.

        For Ollama models, we convert tool definitions into a structured
        prompt that guides the model to generate JSON output.
        """
        # Check if we're forcing a specific tool
        if tool_choice and tool_choice.get("type") == "tool":
            forced_tool_name = tool_choice.get("name")
            forced_tool = next((t for t in tools if t["name"] == forced_tool_name), None)

            if forced_tool:
                # Create a prompt that forces JSON output for the specific tool
                tool_prompt = self._create_tool_prompt(forced_tool)

                # Add tool prompt to messages
                enhanced_messages = messages + [
                    {
                        "role": "user",
                        "content": tool_prompt
                    }
                ]

                # Generate response
                payload = {
                    "model": self.model,
                    "messages": enhanced_messages,
                    "stream": False,
                    "format": "json",  # Request JSON format
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens,
                    }
                }

                response = requests.post(
                    f"{self.api_url}/chat",
                    json=payload,
                    timeout=300
                )
                response.raise_for_status()

                result = response.json()
                content = result["message"]["content"]

                # Try to parse as tool use
                try:
                    tool_input = json.loads(content)
                    tool_use = ToolUse(
                        id="ollama_tool_0",
                        name=forced_tool_name,
                        input=tool_input
                    )

                    usage = None
                    if "prompt_eval_count" in result:
                        usage = {
                            "input_tokens": result.get("prompt_eval_count", 0),
                            "output_tokens": result.get("eval_count", 0),
                        }

                    return LLMResponse(
                        content="",
                        stop_reason=StopReason.TOOL_USE,
                        tool_uses=[tool_use],
                        usage=usage
                    )
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse tool output as JSON: {content}")
                    return None

        return None

    def _create_tool_prompt(self, tool: Dict[str, Any]) -> str:
        """Create a prompt that guides the model to generate structured output.

        Args:
            tool: Tool definition

        Returns:
            Formatted prompt
        """
        schema = tool["input_schema"]
        properties = schema.get("properties", {})
        required = schema.get("required", [])

        prompt = f"Generate a JSON object with the following fields:\n\n"

        for prop_name, prop_info in properties.items():
            prop_type = prop_info.get("type", "string")
            description = prop_info.get("description", "")
            required_marker = " (REQUIRED)" if prop_name in required else " (optional)"

            prompt += f"- {prop_name}{required_marker}: {prop_type}\n"
            if description:
                prompt += f"  Description: {description}\n"

        prompt += "\nRespond ONLY with valid JSON. Do not include any explanations."

        return prompt

    def count_tokens(self, text: str) -> int:
        """Approximate token count.

        Args:
            text: Text to count

        Returns:
            Token count (approximate - 4 chars per token)
        """
        return len(text) // 4

    def supports_tool_use(self) -> bool:
        """Ollama supports tool use through structured prompting."""
        return True

    def supports_vision(self) -> bool:
        """Some Ollama models support vision (llava, bakllava)."""
        vision_models = ["llava", "bakllava"]
        return any(vm in self.model.lower() for vm in vision_models)

    def list_models(self) -> List[str]:
        """List available Ollama models.

        Returns:
            List of model names
        """
        try:
            response = requests.get(f"{self.api_url}/tags")
            response.raise_for_status()
            models = response.json().get("models", [])
            return [m["name"] for m in models]
        except Exception as e:
            logger.error(f"Failed to list Ollama models: {e}")
            return []
