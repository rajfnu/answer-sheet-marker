"""API request models."""

from typing import Optional
from pydantic import BaseModel, Field, validator


class MarkingSingleRequest(BaseModel):
    """Request model for marking a single answer sheet."""

    marking_guide_id: str = Field(..., description="ID of the marking guide to use")
    student_id: str = Field(..., description="Student identifier")

    class Config:
        json_schema_extra = {
            "example": {
                "marking_guide_id": "guide_123",
                "student_id": "student_456",
            }
        }


class MarkingBatchRequest(BaseModel):
    """Request model for batch marking multiple answer sheets."""

    marking_guide_id: str = Field(..., description="ID of the marking guide to use")

    class Config:
        json_schema_extra = {
            "example": {
                "marking_guide_id": "guide_123",
            }
        }


class AnalyzeMarkingGuideRequest(BaseModel):
    """Request model for analyzing a marking guide."""

    marking_guide_id: str = Field(..., description="ID of the uploaded marking guide")

    class Config:
        json_schema_extra = {
            "example": {
                "marking_guide_id": "guide_123",
            }
        }


class JobStatusRequest(BaseModel):
    """Request model for checking job status."""

    job_id: str = Field(..., description="Background job ID")

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "job_789",
            }
        }


class MarkingOptionsRequest(BaseModel):
    """Optional marking configuration."""

    temperature: Optional[float] = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="LLM temperature for marking (0.0 = deterministic)",
    )
    max_tokens: Optional[int] = Field(
        default=8192,
        gt=0,
        description="Maximum tokens for LLM responses",
    )
    require_review_below: Optional[float] = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Confidence threshold below which human review is required",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "temperature": 0.0,
                "max_tokens": 8192,
                "require_review_below": 0.6,
            }
        }
