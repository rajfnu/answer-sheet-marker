"""Base agent classes for the Answer Sheet Marker system.

This module provides the foundational classes for all agents in the multi-agent architecture.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from pydantic import BaseModel, Field
from anthropic import Anthropic
from loguru import logger
from datetime import datetime, timezone


class AgentConfig(BaseModel):
    """Configuration for each agent.

    Defines the behavior and settings for an agent instance.
    """

    name: str = Field(..., description="Agent name/identifier")
    model: str = Field(
        default="claude-sonnet-4-5-20250929", description="Claude model to use"
    )
    max_tokens: int = Field(default=8192, description="Maximum tokens for responses")
    temperature: float = Field(default=0.0, description="Temperature for determinism")
    system_prompt: str = Field(..., description="System prompt for the agent")
    tools: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Tools available to the agent"
    )


class AgentMessage(BaseModel):
    """Standard message format between agents.

    Provides a structured communication protocol for agent interactions.
    """

    sender: str = Field(..., description="Sender agent name")
    receiver: str = Field(..., description="Receiver agent name")
    content: Dict[str, Any] = Field(..., description="Message payload")
    message_type: str = Field(
        ..., description="Message type: request, response, error, info"
    )
    priority: int = Field(default=1, description="Message priority (1=highest)")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Message timestamp"
    )


class BaseAgent(ABC):
    """Base class for all agents.

    Provides common functionality for agent communication, logging,
    and Claude API interactions.
    """

    def __init__(self, config: AgentConfig, client: Anthropic):
        """Initialize base agent.

        Args:
            config: Agent configuration
            client: Anthropic client for Claude API
        """
        self.config = config
        self.client = client
        self.message_history: List[AgentMessage] = []

        logger.info(f"Initialized {self.config.name} agent")

    @abstractmethod
    async def process(self, message: AgentMessage) -> AgentMessage:
        """Process incoming message and return response.

        This method must be implemented by all agent subclasses.

        Args:
            message: Incoming message to process

        Returns:
            Response message
        """
        pass

    async def _call_claude(
        self,
        user_message: str,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Dict[str, Any]] = None,
        retry_count: int = 0,
    ) -> Any:
        """Call Claude API with error handling and retry logic for Gemini.

        Args:
            user_message: User message content
            system_prompt: Override system prompt (uses config default if None)
            tools: Tools to provide to Claude (uses config default if None)
            tool_choice: Tool choice configuration
            retry_count: Current retry attempt (for internal use)

        Returns:
            Claude API response

        Raises:
            Exception: If API call fails after retries
        """
        try:
            logger.debug(f"[{self.config.name}] Calling Claude API (attempt {retry_count + 1})")

            # Use slightly higher temperature on retry for more stable JSON generation
            temperature = self.config.temperature
            if retry_count > 0:
                temperature = min(0.3, self.config.temperature + 0.2)
                logger.debug(f"[{self.config.name}] Using temperature={temperature} for retry")

            response = self.client.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                temperature=temperature,
                system=system_prompt or self.config.system_prompt,
                messages=[{"role": "user", "content": user_message}],
                tools=tools or self.config.tools,
                tool_choice=tool_choice,
            )

            logger.debug(
                f"[{self.config.name}] Received response: "
                f"{response.usage.input_tokens} input tokens, "
                f"{response.usage.output_tokens} output tokens"
            )

            return response

        except ValueError as e:
            error_msg = str(e)

            # Check if it's a Gemini MALFORMED_FUNCTION_CALL error
            if "malformed function call" in error_msg.lower() and retry_count == 0:
                logger.warning(
                    f"[{self.config.name}] Gemini returned MALFORMED_FUNCTION_CALL. "
                    f"Retrying with temperature=0.1 for more stable output..."
                )

                # Retry once with slightly higher temperature for more stability
                return await self._call_claude(
                    user_message=user_message,
                    system_prompt=system_prompt,
                    tools=tools,
                    tool_choice=tool_choice,
                    retry_count=retry_count + 1
                )
            else:
                # Re-raise if not a malformed function call or already retried
                logger.error(f"[{self.config.name}] API call failed: {e}")
                raise

        except Exception as e:
            logger.error(f"[{self.config.name}] API call failed: {e}")
            raise

    def log_message(self, message: AgentMessage):
        """Log agent communication.

        Args:
            message: Message to log
        """
        self.message_history.append(message)
        logger.info(
            f"[{self.config.name}] {message.message_type.upper()}: "
            f"{message.sender} → {message.receiver}"
        )

    def get_message_history(self) -> List[AgentMessage]:
        """Get message history for this agent.

        Returns:
            List of all messages sent/received by this agent
        """
        return self.message_history

    def clear_message_history(self):
        """Clear message history."""
        self.message_history = []
        logger.debug(f"[{self.config.name}] Message history cleared")
