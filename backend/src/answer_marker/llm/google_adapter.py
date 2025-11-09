"""Google Gemini API adapter.

This adapter works with Google's Gemini models via the generativeai SDK.
"""

from typing import List, Dict, Any, Optional
import json
from loguru import logger

try:
    import google.generativeai as genai
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False
    logger.warning("Google Generative AI package not installed. Install with: pip install google-generativeai")

from .base import BaseLLMClient, LLMResponse, ToolUse, StopReason


class GoogleAdapter(BaseLLMClient):
    """Adapter for Google Gemini API.

    Compatible with:
    - Gemini 2.0 Flash
    - Gemini 1.5 Pro
    - Gemini 1.5 Flash
    """

    def __init__(
        self,
        model: str,
        api_key: str,
        **kwargs
    ):
        """Initialize Google Gemini client.

        Args:
            model: Model name (e.g., "gemini-2.0-flash-exp", "gemini-1.5-pro")
            api_key: Google API key
            **kwargs: Additional configuration
        """
        if not GOOGLE_AVAILABLE:
            raise ImportError("Google Generative AI package required. Install with: pip install google-generativeai")

        super().__init__(model, **kwargs)

        # Configure the API
        genai.configure(api_key=api_key)

        # Initialize the model
        self.client = genai.GenerativeModel(model)
        logger.info(f"Initialized Google Gemini adapter with model: {model}")

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
        """Create a message using Google Gemini API.

        Args:
            system: System prompt
            messages: List of messages
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            tools: Tool definitions (will be converted to Gemini format)
            tool_choice: Tool choice strategy
            **kwargs: Additional API parameters

        Returns:
            Standardized LLMResponse
        """
        try:
            # Convert messages to Gemini format
            gemini_messages = self._convert_messages_to_gemini_format(messages, system)

            # Configure generation parameters
            generation_config = {
                "max_output_tokens": max_tokens,
                "temperature": temperature,
            }

            # Convert tools to Gemini format if provided
            gemini_tools = None
            if tools:
                gemini_tools = self._convert_tools_to_gemini_format(tools)

            # Start chat session or generate content
            if len(messages) > 1 or gemini_tools:
                # Use chat for multi-turn conversations or tool use
                chat = self.client.start_chat(history=[])

                # Build the final prompt combining system and user messages
                full_prompt = self._build_full_prompt(system, messages)

                # Configure for tool use if needed
                if gemini_tools:
                    response = chat.send_message(
                        full_prompt,
                        generation_config=generation_config,
                        tools=gemini_tools
                    )
                else:
                    response = chat.send_message(
                        full_prompt,
                        generation_config=generation_config
                    )
            else:
                # Single message generation
                full_prompt = self._build_full_prompt(system, messages)
                response = self.client.generate_content(
                    full_prompt,
                    generation_config=generation_config
                )

            # Extract text content and tool calls
            text_content = ""
            tool_uses = []

            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate.content, 'parts'):
                    for part in candidate.content.parts:
                        # Extract text from text parts
                        if hasattr(part, 'text') and part.text:
                            text_content += part.text
                        # Extract function calls
                        elif hasattr(part, 'function_call') and part.function_call:
                            func_call = part.function_call
                            tool_uses.append(
                                ToolUse(
                                    id=f"toolu_{hash(func_call.name)}",  # Generate ID
                                    name=func_call.name,
                                    input=dict(func_call.args)
                                )
                            )

            # Map finish reason to stop reason
            stop_reason = StopReason.END_TURN
            if response.candidates:
                finish_reason = response.candidates[0].finish_reason
                finish_reason_name = str(finish_reason)

                # Check for MALFORMED_FUNCTION_CALL (finish_reason = 6)
                if finish_reason == 6 or 'MALFORMED_FUNCTION_CALL' in finish_reason_name:
                    logger.error(f"Gemini returned MALFORMED_FUNCTION_CALL. This usually means the generated function call JSON is invalid.")
                    raise ValueError(
                        "Gemini generated a malformed function call. This is often due to complex nested schemas. "
                        "Try simplifying the tool schema or using a different model."
                    )

                if finish_reason == 1:  # STOP
                    stop_reason = StopReason.END_TURN
                elif finish_reason == 2:  # MAX_TOKENS
                    stop_reason = StopReason.MAX_TOKENS
                elif tool_uses:
                    stop_reason = StopReason.TOOL_USE

            # Extract usage
            usage = None
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                usage = {
                    "input_tokens": response.usage_metadata.prompt_token_count,
                    "output_tokens": response.usage_metadata.candidates_token_count,
                }

            return LLMResponse(
                content=text_content,
                stop_reason=stop_reason,
                tool_uses=tool_uses,
                usage=usage
            )

        except Exception as e:
            logger.error(f"Google Gemini API call failed: {e}")
            raise

    def _build_full_prompt(self, system: str, messages: List[Dict[str, Any]]) -> str:
        """Build a full prompt combining system and user messages.

        Args:
            system: System prompt
            messages: List of messages

        Returns:
            Combined prompt string
        """
        prompt_parts = []

        if system:
            prompt_parts.append(f"System: {system}\n")

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")

        return "\n\n".join(prompt_parts)

    def _convert_messages_to_gemini_format(
        self,
        messages: List[Dict[str, Any]],
        system: str
    ) -> List[Dict[str, Any]]:
        """Convert messages to Gemini format.

        Args:
            messages: List of messages in standard format
            system: System prompt

        Returns:
            List of messages in Gemini format
        """
        gemini_messages = []

        # Gemini doesn't have a separate system role, so we prepend it to the first user message
        first_message = True

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if first_message and system:
                content = f"{system}\n\n{content}"
                first_message = False

            # Map roles
            gemini_role = "user" if role in ["user", "system"] else "model"

            gemini_messages.append({
                "role": gemini_role,
                "parts": [{"text": content}]
            })

        return gemini_messages

    def _clean_schema_for_gemini(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Clean JSON schema to be compatible with Gemini.

        Gemini doesn't support certain JSON schema fields like 'minimum', 'maximum', etc.
        This function recursively removes unsupported fields and simplifies complex schemas.

        Args:
            schema: JSON schema dictionary

        Returns:
            Cleaned schema dictionary
        """
        if not isinstance(schema, dict):
            return schema

        # Fields not supported by Gemini
        unsupported_fields = {
            'minimum', 'maximum', 'exclusiveMinimum', 'exclusiveMaximum',
            'multipleOf', 'minLength', 'maxLength', 'pattern',
            'minItems', 'maxItems', 'uniqueItems',
            'minProperties', 'maxProperties', 'additionalProperties',
            'const', 'contentMediaType', 'contentEncoding', 'format'
        }

        cleaned = {}
        for key, value in schema.items():
            if key in unsupported_fields:
                # Log which fields we're removing for debugging
                logger.debug(f"Removing unsupported Gemini field: {key} = {value}")
                continue  # Skip unsupported fields
            elif key == 'required' and isinstance(value, list):
                # Keep required but limit to essential fields to reduce complexity
                # Gemini struggles with too many required fields
                if len(value) > 5:
                    logger.debug(f"Simplifying 'required' list from {len(value)} to top 5 fields")
                    cleaned[key] = value[:5]  # Only keep first 5 required fields
                else:
                    cleaned[key] = value
            elif isinstance(value, dict):
                cleaned[key] = self._clean_schema_for_gemini(value)
            elif isinstance(value, list):
                cleaned[key] = [
                    self._clean_schema_for_gemini(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                cleaned[key] = value

        return cleaned

    def _convert_tools_to_gemini_format(
        self,
        tools: List[Dict[str, Any]]
    ) -> List[Any]:
        """Convert Anthropic tool format to Gemini function format.

        Args:
            tools: List of tools in Anthropic format

        Returns:
            List of tools in Gemini format
        """
        try:
            from google.generativeai.types import FunctionDeclaration, Tool

            gemini_functions = []

            for tool in tools:
                # Clean the schema to remove unsupported fields
                input_schema = tool.get("input_schema", {})
                cleaned_schema = self._clean_schema_for_gemini(input_schema)

                func_declaration = FunctionDeclaration(
                    name=tool["name"],
                    description=tool.get("description", ""),
                    parameters=cleaned_schema
                )
                gemini_functions.append(func_declaration)

            return [Tool(function_declarations=gemini_functions)]

        except Exception as e:
            logger.warning(f"Failed to convert tools to Gemini format: {e}")
            return None

    def count_tokens(self, text: str) -> int:
        """Count tokens using Gemini's token counting.

        Args:
            text: Text to count

        Returns:
            Token count
        """
        try:
            # Use Gemini's built-in token counting
            result = self.client.count_tokens(text)
            return result.total_tokens
        except Exception:
            # Fallback to approximation (Gemini uses similar tokenization to GPT)
            return len(text) // 4

    def supports_tool_use(self) -> bool:
        """Gemini 1.5+ models support function calling."""
        # Gemini 1.5 and 2.0 support function calling
        return "1.5" in self.model or "2.0" in self.model

    def supports_vision(self) -> bool:
        """Gemini Pro and Flash models support vision."""
        # Most Gemini models support vision
        return True
