"""Factory for creating LLM clients based on configuration."""

from enum import Enum
from typing import Optional
from loguru import logger

from .base import BaseLLMClient
from .anthropic_adapter import AnthropicAdapter
from .ollama_adapter import OllamaAdapter
from .openai_adapter import OpenAIAdapter


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    OPENAI = "openai"
    TOGETHER = "together"  # Uses OpenAI-compatible API


def create_llm_client(
    provider: str,
    model: str,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    **kwargs
) -> BaseLLMClient:
    """Factory function to create the appropriate LLM client.

    This factory creates the correct LLM adapter based on the provider
    specification, allowing easy switching between different LLM services.

    Args:
        provider: LLM provider name ("anthropic", "ollama", "openai", "together")
        model: Model identifier
        api_key: API key (required for Anthropic, OpenAI, Together)
        base_url: Custom API base URL (for Ollama, Together)
        **kwargs: Additional provider-specific configuration

    Returns:
        Configured LLM client

    Raises:
        ValueError: If provider is not supported
        ImportError: If required dependencies are missing

    Examples:
        >>> # Anthropic Claude
        >>> client = create_llm_client(
        ...     provider="anthropic",
        ...     model="claude-sonnet-4-5-20250929",
        ...     api_key="sk-ant-..."
        ... )

        >>> # Ollama local LLM
        >>> client = create_llm_client(
        ...     provider="ollama",
        ...     model="llama3:70b",
        ...     base_url="http://localhost:11434"
        ... )

        >>> # OpenAI
        >>> client = create_llm_client(
        ...     provider="openai",
        ...     model="gpt-4",
        ...     api_key="sk-..."
        ... )

        >>> # Together.ai
        >>> client = create_llm_client(
        ...     provider="together",
        ...     model="meta-llama/Llama-3-70b-chat-hf",
        ...     api_key="...",
        ...     base_url="https://api.together.xyz/v1"
        ... )
    """
    provider = provider.lower()

    logger.info(f"Creating LLM client for provider: {provider}, model: {model}")

    if provider == LLMProvider.ANTHROPIC:
        if not api_key:
            raise ValueError("API key required for Anthropic")
        return AnthropicAdapter(model=model, api_key=api_key, **kwargs)

    elif provider == LLMProvider.OLLAMA:
        default_url = "http://localhost:11434"
        return OllamaAdapter(
            model=model,
            base_url=base_url or default_url,
            **kwargs
        )

    elif provider == LLMProvider.OPENAI:
        if not api_key:
            raise ValueError("API key required for OpenAI")
        return OpenAIAdapter(
            model=model,
            api_key=api_key,
            base_url=base_url,
            **kwargs
        )

    elif provider == LLMProvider.TOGETHER:
        if not api_key:
            raise ValueError("API key required for Together.ai")
        together_url = base_url or "https://api.together.xyz/v1"
        return OpenAIAdapter(
            model=model,
            api_key=api_key,
            base_url=together_url,
            **kwargs
        )

    else:
        supported = ", ".join([p.value for p in LLMProvider])
        raise ValueError(
            f"Unsupported provider: {provider}. "
            f"Supported providers: {supported}"
        )


def create_llm_client_from_config(config) -> BaseLLMClient:
    """Create LLM client from application configuration.

    Args:
        config: Application settings object with LLM configuration

    Returns:
        Configured LLM client

    Example:
        >>> from answer_marker.config import settings
        >>> client = create_llm_client_from_config(settings)
    """
    llm_config = config.get_llm_config()
    return create_llm_client(
        provider=llm_config["provider"],
        model=llm_config["model"],
        api_key=llm_config["api_key"],
        base_url=llm_config["base_url"],
        max_tokens=llm_config["max_tokens"],
        temperature=llm_config["temperature"],
    )
