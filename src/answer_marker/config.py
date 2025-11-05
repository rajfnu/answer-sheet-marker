"""Configuration management for Answer Sheet Marker system.

This module provides centralized configuration management using Pydantic Settings.
All configuration values can be set via environment variables or .env file.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from pathlib import Path


class Settings(BaseSettings):
    """Application configuration with validation and environment variable support.

    All settings can be configured via environment variables or .env file.
    Environment variables should be uppercase (e.g., ANTHROPIC_API_KEY).
    """

    # ============================================================
    # API Configuration
    # ============================================================
    anthropic_api_key: str
    """Anthropic API key for Claude access. Required."""

    claude_model: str = "claude-sonnet-4-5-20250929"
    """Claude model to use for evaluations. Default: claude-sonnet-4-5-20250929"""

    max_tokens: int = 8192
    """Maximum tokens for Claude API responses. Default: 8192"""

    temperature: float = 0.0
    """Temperature for Claude API (0.0 = deterministic, important for consistent marking). Default: 0.0"""

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
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  # Ignore extra environment variables
    )

    def validate_paths(self) -> None:
        """Validate and create necessary directories."""
        paths_to_create = [
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
