"""Configuration management for Answer Sheet Marker system.

This module provides centralized configuration management using Pydantic Settings.
All configuration values can be set via environment variables or .env file.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from pathlib import Path
import os

# Determine project root (3 levels up from this file)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """Application configuration with validation and environment variable support.

    All settings can be configured via environment variables or .env file.
    Environment variables should be uppercase (e.g., ANTHROPIC_API_KEY).
    """

    # ============================================================
    # LLM Configuration (Flexible Provider Support)
    # ============================================================
    llm_provider: str = "anthropic"
    """LLM provider to use: 'anthropic', 'ollama', 'openai', 'together'. Default: anthropic"""

    llm_model: Optional[str] = None
    """Model name for the selected provider. If None, uses provider-specific default."""

    llm_api_key: Optional[str] = None
    """API key for the LLM provider (required for anthropic, openai, together)."""

    llm_base_url: Optional[str] = None
    """Base URL for LLM API (for Ollama, Together, or custom endpoints). Default: provider-specific"""

    # Backward compatibility with old Anthropic-specific settings
    anthropic_api_key: Optional[str] = None
    """[DEPRECATED] Use llm_api_key instead. For backward compatibility only."""

    claude_model: str = "claude-sonnet-4-5-20250929"
    """[DEPRECATED] Use llm_model instead. Default Claude model."""

    max_tokens: int = 8192
    """Maximum tokens for LLM responses. Default: 8192"""

    temperature: float = 0.0
    """Temperature for LLM (0.0 = deterministic, important for consistent marking). Default: 0.0"""

    # ============================================================
    # Processing Configuration
    # ============================================================
    batch_size: int = 5
    """Number of answer sheets to process in parallel. Default: 5"""

    max_concurrent_requests: int = 3
    """Maximum number of concurrent API requests to Claude. Default: 3"""

    # ============================================================
    # Quality Thresholds
    # ============================================================
    min_confidence_score: float = 0.7
    """Minimum confidence score for automatic marking (0-1). Default: 0.7"""

    require_human_review_below: float = 0.6
    """Confidence threshold below which human review is required (0-1). Default: 0.6"""

    # ============================================================
    # Storage Configuration
    # ============================================================
    data_dir: str = "./data"
    """Base directory for all data storage (guides, reports, cache). Default: ./data"""

    vector_db_path: str = "./data/vector_db"
    """Path to vector database storage for RAG functionality. Default: ./data/vector_db"""

    cache_enabled: bool = True
    """Enable caching for improved performance. Default: True"""

    cache_ttl: int = 3600
    """Cache time-to-live in seconds. Default: 3600 (1 hour)"""

    # ============================================================
    # Logging Configuration
    # ============================================================
    log_level: str = "INFO"
    """Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL). Default: INFO"""

    log_file: Optional[str] = "./logs/app.log"
    """Path to log file. Set to None to disable file logging. Default: ./logs/app.log"""

    log_rotation: str = "10 MB"
    """Log file rotation size. Default: 10 MB"""

    log_retention: str = "1 week"
    """Log file retention period. Default: 1 week"""

    # ============================================================
    # Document Processing
    # ============================================================
    ocr_enabled: bool = True
    """Enable OCR for scanned/handwritten documents. Default: True"""

    ocr_language: str = "eng"
    """OCR language (tesseract language code). Default: eng"""

    pdf_dpi: int = 300
    """DPI for PDF to image conversion. Default: 300"""

    # ============================================================
    # Output Configuration
    # ============================================================
    output_format: str = "pdf"
    """Default output format for reports (pdf, html, json). Default: pdf"""

    output_directory: str = "./output"
    """Directory for generated reports. Default: ./output"""

    include_detailed_feedback: bool = True
    """Include detailed feedback in reports. Default: True"""

    # ============================================================
    # Advanced Settings
    # ============================================================
    enable_extended_thinking: bool = False
    """Enable Claude's extended thinking for complex evaluations. Default: False"""

    retry_attempts: int = 3
    """Number of retry attempts for failed API calls. Default: 3"""

    retry_wait_min: int = 4
    """Minimum wait time (seconds) between retries. Default: 4"""

    retry_wait_max: int = 10
    """Maximum wait time (seconds) between retries. Default: 10"""

    debug_mode: bool = False
    """Enable debug mode with verbose logging. Default: False"""

    # Pydantic Settings configuration
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),  # Look for .env in project root
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  # Ignore extra environment variables
    )

    def validate_paths(self) -> None:
        """Validate and create necessary directories."""
        paths_to_create = [
            self.data_dir,
            self.vector_db_path,
            self.output_directory,
        ]

        # Create log directory if log file is specified
        if self.log_file:
            log_path = Path(self.log_file).parent
            paths_to_create.append(str(log_path))

        for path_str in paths_to_create:
            path = Path(path_str)
            path.mkdir(parents=True, exist_ok=True)

    def get_llm_config(self) -> dict:
        """Get LLM configuration with backward compatibility.

        Returns:
            Dictionary with provider, model, api_key, and base_url
        """
        # Resolve API key with backward compatibility
        api_key = self.llm_api_key or self.anthropic_api_key

        # Resolve model with provider-specific defaults
        model = self.llm_model
        if not model:
            # Use provider-specific defaults
            if self.llm_provider == "anthropic":
                model = self.claude_model
            elif self.llm_provider == "ollama":
                model = "llama3"  # Default Ollama model
            elif self.llm_provider == "openai":
                model = "gpt-4"
            elif self.llm_provider == "together":
                model = "meta-llama/Llama-3-70b-chat-hf"

        return {
            "provider": self.llm_provider,
            "model": model,
            "api_key": api_key,
            "base_url": self.llm_base_url,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }

    def model_post_init(self, __context) -> None:
        """Called after model initialization to perform additional setup."""
        # Update log level if debug mode is enabled
        if self.debug_mode:
            self.log_level = "DEBUG"


# ============================================================
# Global Settings Instance
# ============================================================
# This instance will be used throughout the application
settings = Settings()

# Validate and create necessary directories on import
settings.validate_paths()
