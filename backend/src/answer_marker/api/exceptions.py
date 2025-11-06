"""Custom API exceptions and error handlers."""

from typing import Any, Optional
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse


class APIError(HTTPException):
    """Base API error class."""

    def __init__(
        self,
        status_code: int,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(status_code=status_code, detail=message)


class AuthenticationError(APIError):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed", **kwargs):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message=message,
            error_code="AUTHENTICATION_ERROR",
            **kwargs,
        )


class AuthorizationError(APIError):
    """Raised when user is not authorized to perform an action."""

    def __init__(self, message: str = "Not authorized", **kwargs):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            message=message,
            error_code="AUTHORIZATION_ERROR",
            **kwargs,
        )


class ValidationError(APIError):
    """Raised when request validation fails."""

    def __init__(self, message: str = "Validation error", **kwargs):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message=message,
            error_code="VALIDATION_ERROR",
            **kwargs,
        )


class ResourceNotFoundError(APIError):
    """Raised when a requested resource is not found."""

    def __init__(self, resource: str = "Resource", resource_id: Optional[str] = None, **kwargs):
        message = f"{resource} not found"
        if resource_id:
            message = f"{resource} with ID '{resource_id}' not found"
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            message=message,
            error_code="RESOURCE_NOT_FOUND",
            **kwargs,
        )


class ResourceConflictError(APIError):
    """Raised when a resource already exists."""

    def __init__(self, message: str = "Resource already exists", **kwargs):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            message=message,
            error_code="RESOURCE_CONFLICT",
            **kwargs,
        )


class ProcessingError(APIError):
    """Raised when processing fails."""

    def __init__(self, message: str = "Processing failed", **kwargs):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=message,
            error_code="PROCESSING_ERROR",
            **kwargs,
        )


class FileUploadError(APIError):
    """Raised when file upload fails."""

    def __init__(self, message: str = "File upload failed", **kwargs):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=message,
            error_code="FILE_UPLOAD_ERROR",
            **kwargs,
        )


class RateLimitError(APIError):
    """Raised when rate limit is exceeded."""

    def __init__(self, message: str = "Rate limit exceeded", **kwargs):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            message=message,
            error_code="RATE_LIMIT_ERROR",
            **kwargs,
        )


class JobError(APIError):
    """Raised when background job fails."""

    def __init__(self, message: str = "Job execution failed", job_id: Optional[str] = None, **kwargs):
        if job_id:
            message = f"Job {job_id} failed: {message}"
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=message,
            error_code="JOB_ERROR",
            **kwargs,
        )


# Global exception handlers


async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    """Handle custom API errors."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
            }
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "details": {"exception_type": type(exc).__name__},
            }
        },
    )


async def validation_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle Pydantic validation errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": {"errors": str(exc)},
            }
        },
    )
