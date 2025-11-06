"""API response models."""

from typing import Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class JobStatus(str, Enum):
    """Background job status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(default_factory=datetime.now, description="Current timestamp")
    llm_provider: str = Field(..., description="Configured LLM provider")
    llm_model: str = Field(..., description="Configured LLM model")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "timestamp": "2025-01-06T10:30:00",
                "llm_provider": "anthropic",
                "llm_model": "claude-sonnet-4-5-20250929",
            }
        }


class UploadResponse(BaseModel):
    """File upload response."""

    file_id: str = Field(..., description="Unique file identifier")
    filename: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    file_type: str = Field(..., description="File type/extension")
    uploaded_at: datetime = Field(default_factory=datetime.now, description="Upload timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "file_id": "file_123",
                "filename": "assessment.pdf",
                "file_size": 524288,
                "file_type": "pdf",
                "uploaded_at": "2025-01-06T10:30:00",
            }
        }


class QuestionSummary(BaseModel):
    """Summary of a question in the marking guide."""

    question_id: str
    question_number: str
    max_marks: float
    question_type: str
    has_rubric: bool


class MarkingGuideResponse(BaseModel):
    """Marking guide response."""

    guide_id: str = Field(..., description="Marking guide ID")
    title: str = Field(..., description="Assessment title")
    total_marks: float = Field(..., description="Total marks available")
    num_questions: int = Field(..., description="Number of questions")
    questions: List[QuestionSummary] = Field(..., description="Question summaries")
    analyzed: bool = Field(default=False, description="Whether questions are analyzed")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "guide_id": "guide_123",
                "title": "Financial Accounting Assessment",
                "total_marks": 118.0,
                "num_questions": 10,
                "questions": [
                    {
                        "question_id": "Q1",
                        "question_number": "1",
                        "max_marks": 10.0,
                        "question_type": "short_answer",
                        "has_rubric": True,
                    }
                ],
                "analyzed": True,
                "created_at": "2025-01-06T10:30:00",
            }
        }


class JobResponse(BaseModel):
    """Background job response."""

    job_id: str = Field(..., description="Job ID")
    status: JobStatus = Field(..., description="Job status")
    created_at: datetime = Field(default_factory=datetime.now, description="Job creation time")
    started_at: Optional[datetime] = Field(None, description="Job start time")
    completed_at: Optional[datetime] = Field(None, description="Job completion time")
    progress: Optional[float] = Field(None, ge=0.0, le=1.0, description="Progress (0.0 to 1.0)")
    message: Optional[str] = Field(None, description="Status message")
    error: Optional[str] = Field(None, description="Error message if failed")
    result: Optional[dict[str, Any]] = Field(None, description="Job result if completed")

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "job_789",
                "status": "running",
                "created_at": "2025-01-06T10:30:00",
                "started_at": "2025-01-06T10:30:05",
                "progress": 0.5,
                "message": "Marking question 5 of 10",
            }
        }


class QuestionEvaluationResponse(BaseModel):
    """Question-level evaluation details."""

    question_id: str = Field(..., description="Question identifier")
    marks_awarded: float = Field(..., description="Marks awarded for this question")
    max_marks: float = Field(..., description="Maximum marks for this question")
    percentage: float = Field(..., description="Percentage score for this question")
    overall_quality: str = Field(..., description="Quality assessment")
    strengths: List[str] = Field(..., description="Answer strengths")
    weaknesses: List[str] = Field(..., description="Answer weaknesses")
    requires_human_review: bool = Field(..., description="Whether this question needs review")

    class Config:
        json_schema_extra = {
            "example": {
                "question_id": "Q1",
                "marks_awarded": 8.5,
                "max_marks": 10.0,
                "percentage": 85.0,
                "overall_quality": "good",
                "strengths": ["Clear explanation", "Good examples"],
                "weaknesses": ["Missing key concept"],
                "requires_human_review": False,
            }
        }


class ScoreSummary(BaseModel):
    """Score summary for a student."""

    total_marks: float
    max_marks: float
    percentage: float
    grade: str
    passed: bool


class MarkingReportResponse(BaseModel):
    """Marking report response."""

    report_id: str = Field(..., description="Report ID")
    student_id: str = Field(..., description="Student ID")
    marking_guide_id: str = Field(..., description="Marking guide ID used")
    assessment_title: str = Field(..., description="Assessment title")
    score: ScoreSummary = Field(..., description="Score summary")
    num_questions: int = Field(..., description="Number of questions")
    requires_review: bool = Field(..., description="Whether human review is required")
    processing_time: float = Field(..., description="Processing time in seconds")
    marked_at: datetime = Field(default_factory=datetime.now, description="Marking timestamp")
    question_evaluations: Optional[List[QuestionEvaluationResponse]] = Field(
        None, description="Question-by-question evaluation breakdown"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "report_id": "report_456",
                "student_id": "student_789",
                "marking_guide_id": "guide_123",
                "assessment_title": "Financial Accounting Assessment",
                "score": {
                    "total_marks": 85.5,
                    "max_marks": 118.0,
                    "percentage": 72.5,
                    "grade": "B",
                    "passed": True,
                },
                "num_questions": 10,
                "requires_review": False,
                "processing_time": 45.2,
                "marked_at": "2025-01-06T10:35:00",
            }
        }


class BatchMarkingResponse(BaseModel):
    """Batch marking response."""

    batch_id: str = Field(..., description="Batch ID")
    job_id: str = Field(..., description="Background job ID")
    marking_guide_id: str = Field(..., description="Marking guide ID")
    num_students: int = Field(..., description="Number of students to mark")
    status: JobStatus = Field(..., description="Job status")
    message: str = Field(..., description="Status message")

    class Config:
        json_schema_extra = {
            "example": {
                "batch_id": "batch_123",
                "job_id": "job_789",
                "marking_guide_id": "guide_123",
                "num_students": 50,
                "status": "pending",
                "message": "Batch marking job queued",
            }
        }


class ErrorResponse(BaseModel):
    """Error response."""

    error: dict[str, Any] = Field(..., description="Error details")

    class Config:
        json_schema_extra = {
            "example": {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid request parameters",
                    "details": {"field": "marking_guide_id", "issue": "required"},
                }
            }
        }
