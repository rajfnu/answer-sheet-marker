"""Unit tests for configuration module."""

import pytest
from pathlib import Path
from unittest.mock import patch
from pydantic import ValidationError
from answer_marker.config import Settings


class TestSettings:
    """Test cases for Settings configuration class."""

    def test_settings_with_valid_env(self, monkeypatch):
        """Test Settings initialization with valid environment variables."""
        # Set required environment variables
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")

        # Create settings instance
        settings = Settings()

        # Check required fields
        assert settings.anthropic_api_key == "test-api-key"
        assert settings.claude_model == "claude-sonnet-4-5-20250929"
        assert settings.max_tokens == 8192
        assert settings.temperature == 0.0

    def test_settings_missing_required_field(self, monkeypatch, tmp_path):
        """Test that Settings raises ValidationError when API key is missing."""
        # Clear ANTHROPIC_API_KEY if it exists
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        # Change to a directory without .env file
        monkeypatch.chdir(tmp_path)

        # Should raise ValidationError
        with pytest.raises(ValidationError) as exc_info:
            Settings()

        assert "anthropic_api_key" in str(exc_info.value)

    def test_settings_default_values(self, monkeypatch):
        """Test that default values are set correctly."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        settings = Settings()

        # Check default values
        assert settings.batch_size == 5
        assert settings.max_concurrent_requests == 3
        assert settings.min_confidence_score == 0.7
        assert settings.require_human_review_below == 0.6
        assert settings.cache_enabled is True
        assert settings.log_level == "INFO"

    def test_settings_custom_values(self, monkeypatch):
        """Test that custom environment variables override defaults."""
        # Set custom values
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        monkeypatch.setenv("BATCH_SIZE", "10")
        monkeypatch.setenv("MAX_TOKENS", "4096")
        monkeypatch.setenv("TEMPERATURE", "0.5")
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")

        settings = Settings()

        # Check custom values
        assert settings.batch_size == 10
        assert settings.max_tokens == 4096
        assert settings.temperature == 0.5
        assert settings.log_level == "DEBUG"

    def test_settings_case_insensitive(self, monkeypatch):
        """Test that environment variables are case insensitive."""
        # Set lowercase environment variable
        monkeypatch.setenv("anthropic_api_key", "test-key")
        monkeypatch.setenv("claude_model", "claude-opus-4")

        settings = Settings()

        assert settings.anthropic_api_key == "test-key"
        assert settings.claude_model == "claude-opus-4"

    def test_validate_paths_creates_directories(self, monkeypatch, tmp_path):
        """Test that validate_paths creates necessary directories."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        # Use temporary paths
        vector_db_path = tmp_path / "vector_db"
        output_path = tmp_path / "output"
        log_path = tmp_path / "logs" / "app.log"

        monkeypatch.setenv("VECTOR_DB_PATH", str(vector_db_path))
        monkeypatch.setenv("OUTPUT_DIRECTORY", str(output_path))
        monkeypatch.setenv("LOG_FILE", str(log_path))

        settings = Settings()
        settings.validate_paths()

        # Check directories were created
        assert vector_db_path.exists()
        assert output_path.exists()
        assert log_path.parent.exists()

    def test_debug_mode_sets_log_level(self, monkeypatch):
        """Test that debug mode automatically sets log level to DEBUG."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        monkeypatch.setenv("DEBUG_MODE", "true")

        settings = Settings()

        # Debug mode should set log level to DEBUG
        assert settings.debug_mode is True
        assert settings.log_level == "DEBUG"

    def test_settings_extra_env_vars_ignored(self, monkeypatch):
        """Test that extra environment variables are ignored."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        monkeypatch.setenv("SOME_RANDOM_VAR", "should-be-ignored")

        # Should not raise an error
        settings = Settings()
        assert not hasattr(settings, "some_random_var")

    def test_quality_thresholds_range(self, monkeypatch):
        """Test that quality thresholds are within valid range."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        settings = Settings()

        # Check thresholds are between 0 and 1
        assert 0 <= settings.min_confidence_score <= 1
        assert 0 <= settings.require_human_review_below <= 1

    def test_retry_settings(self, monkeypatch):
        """Test retry configuration settings."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        monkeypatch.setenv("RETRY_ATTEMPTS", "5")
        monkeypatch.setenv("RETRY_WAIT_MIN", "2")
        monkeypatch.setenv("RETRY_WAIT_MAX", "20")

        settings = Settings()

        assert settings.retry_attempts == 5
        assert settings.retry_wait_min == 2
        assert settings.retry_wait_max == 20
