"""Answer Marker REST API.

This package provides a REST API interface for the answer sheet marking system.

Usage:
    Run the API server:
    ```bash
    poetry run python -m answer_marker.api.main
    ```

    Or with uvicorn directly:
    ```bash
    poetry run uvicorn answer_marker.api.main:app --reload
    ```
"""

from .main import app

__all__ = ["app"]
