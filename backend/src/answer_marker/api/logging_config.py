"""Logging configuration for the API."""

import sys
from pathlib import Path
from loguru import logger

from .config import api_settings


def setup_logging():
    """Configure logging for the application.

    Sets up loguru to log to both console and file based on settings.
    Creates separate log files for different log levels.
    """
    # Remove default handler
    logger.remove()

    # Create logs directory if it doesn't exist
    log_dir = Path(api_settings.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    # Console logging
    if api_settings.log_to_console:
        logger.add(
            sys.stderr,
            format=api_settings.log_format,
            level=api_settings.log_level,
            colorize=True,
        )

    # File logging
    if api_settings.log_to_file:
        # Main log file - all levels
        logger.add(
            log_dir / "app.log",
            format=api_settings.log_format,
            level=api_settings.log_level,
            rotation=api_settings.log_rotation,
            retention=api_settings.log_retention,
            compression="zip",
            enqueue=True,  # Thread-safe logging
        )

        # Error log file - ERROR and CRITICAL only
        logger.add(
            log_dir / "error.log",
            format=api_settings.log_format,
            level="ERROR",
            rotation=api_settings.log_rotation,
            retention=api_settings.log_retention,
            compression="zip",
            enqueue=True,
        )

        # API access log
        logger.add(
            log_dir / "access.log",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {extra[method]} {extra[path]} - {extra[status_code]} - {extra[duration]}ms",
            level="INFO",
            rotation=api_settings.log_rotation,
            retention=api_settings.log_retention,
            compression="zip",
            enqueue=True,
            filter=lambda record: "access_log" in record["extra"],
        )

    logger.info(f"Logging configured - Level: {api_settings.log_level}, Dir: {api_settings.log_dir}")


def log_request(method: str, path: str, status_code: int, duration_ms: float):
    """Log an API request.

    Args:
        method: HTTP method (GET, POST, etc.)
        path: Request path
        status_code: HTTP status code
        duration_ms: Request duration in milliseconds
    """
    logger.bind(
        access_log=True,
        method=method,
        path=path,
        status_code=status_code,
        duration=f"{duration_ms:.2f}",
    ).info("API Request")
