"""Main FastAPI application for Answer Sheet Marker API.

This module provides a REST API interface for the answer sheet marking system,
exposing endpoints for uploading marking guides, marking answer sheets,
and retrieving marking reports.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from .config import api_settings
from .logging_config import setup_logging
from .exceptions import (
    APIError,
    api_error_handler,
    generic_exception_handler,
    validation_exception_handler,
)
from .routes import health, marking, quick_test

# Setup logging first thing
setup_logging()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance
    """
    app = FastAPI(
        title=api_settings.api_title,
        version=api_settings.api_version,
        description=api_settings.api_description,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # Configure CORS
    if api_settings.cors_enabled:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=api_settings.cors_origins,
            allow_credentials=api_settings.cors_allow_credentials,
            allow_methods=api_settings.cors_allow_methods,
            allow_headers=api_settings.cors_allow_headers,
        )
        logger.info(f"CORS enabled for origins: {api_settings.cors_origins}")

    # Register exception handlers
    app.add_exception_handler(APIError, api_error_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    # Register routes
    app.include_router(health.router)
    app.include_router(marking.router)
    app.include_router(quick_test.router)

    # Startup event
    @app.on_event("startup")
    async def startup_event():
        """Initialize services on startup."""
        logger.info(f"Starting {api_settings.api_title} v{api_settings.api_version}")
        logger.info(f"API server: {api_settings.api_host}:{api_settings.api_port}")
        logger.info(f"Documentation: http://{api_settings.api_host}:{api_settings.api_port}/docs")

    # Shutdown event
    @app.on_event("shutdown")
    async def shutdown_event():
        """Cleanup on shutdown."""
        logger.info("Shutting down API server")

    return app


# Create application instance
app = create_app()


if __name__ == "__main__":
    """Run the API server directly with uvicorn."""
    import uvicorn

    uvicorn.run(
        "answer_marker.api.main:app",
        host=api_settings.api_host,
        port=api_settings.api_port,
        reload=api_settings.api_reload,
        workers=api_settings.api_workers,
    )
