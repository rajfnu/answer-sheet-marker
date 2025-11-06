"""Health check routes."""

from datetime import datetime
from fastapi import APIRouter

from answer_marker.config import settings
from ..config import api_settings
from ..models.responses import HealthResponse

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Check API health status and configuration",
)
async def health_check() -> HealthResponse:
    """Check API health and return configuration details."""
    return HealthResponse(
        status="healthy",
        version=api_settings.api_version,
        timestamp=datetime.now(),
        llm_provider=settings.llm_provider,
        llm_model=settings.get_llm_config()["model"],
    )


@router.get(
    "/",
    response_model=dict,
    summary="API Root",
    description="API root endpoint with basic information",
)
async def root() -> dict:
    """Root endpoint."""
    return {
        "name": api_settings.api_title,
        "version": api_settings.api_version,
        "description": "AI-powered answer sheet marking system",
        "docs_url": "/docs",
        "health_url": "/health",
    }
