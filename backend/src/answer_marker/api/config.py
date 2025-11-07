"""API configuration settings."""

from pydantic_settings import BaseSettings


class APISettings(BaseSettings):
    """API-specific configuration settings.

    These settings extend the core application settings with API-specific
    configuration like CORS, authentication, and rate limiting.
    """

    # API Metadata
    api_title: str = "Answer Sheet Marker API"
    api_version: str = "1.0.0"
    api_description: str = """
    AI-powered answer sheet marking system using multi-agent architecture.

    This API provides endpoints for:
    - Uploading and analyzing marking guides
    - Marking individual and batch answer sheets
    - Retrieving marking reports and statistics
    - Real-time progress tracking via WebSockets
    """

    # Server Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 1  # Number of uvicorn workers
    api_reload: bool = False  # Auto-reload on code changes (dev only)

    # CORS Configuration
    cors_enabled: bool = True
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000", "http://localhost:8000"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]

    # Authentication
    api_key_header: str = "X-API-Key"
    api_keys: list[str] = ["dev-key-12345"]  # Should be loaded from env in production
    jwt_secret: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration: int = 3600  # 1 hour

    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_calls: int = 100  # Max calls per window
    rate_limit_period: int = 60  # Window in seconds

    # File Upload Limits
    max_file_size: int = 10 * 1024 * 1024  # 10 MB
    allowed_extensions: list[str] = [".pdf"]
    upload_dir: str = "./data/uploads"

    # Background Tasks
    max_concurrent_marking_jobs: int = 3
    job_timeout: int = 1800  # 30 minutes

    # Response Configuration
    include_token_usage: bool = True
    include_processing_time: bool = True

    # Logging Configuration
    log_dir: str = "./logs"
    log_level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    log_rotation: str = "100 MB"  # Rotate when file reaches this size
    log_retention: str = "30 days"  # Keep logs for this duration
    log_format: str = "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}"
    log_to_console: bool = True
    log_to_file: bool = True

    class Config:
        env_prefix = "API_"
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from .env


# Global settings instance
api_settings = APISettings()
