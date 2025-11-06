"""Feedback models for the Answer Sheet Marker system.

This module defines data models for generating and storing feedback for students.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone


class QuestionFeedback(BaseModel):
    """Feedback for a single question.

    Represents constructive feedback for a student's answer to a specific question,
    including strengths, areas for improvement, and suggestions.
    """

    question_id: str
    feedback: str = Field(..., description="Main feedback text")
    strengths: List[str] = Field(default_factory=list, description="Specific strengths")
    improvement_areas: List[str] = Field(
        default_factory=list, description="Areas for improvement"
    )
    suggestions: List[str] = Field(default_factory=list, description="Actionable suggestions")
    resources: List[str] = Field(
        default_factory=list, description="Recommended learning resources"
    )


class FeedbackReport(BaseModel):
    """Complete feedback report.

    Represents a comprehensive feedback report for a student's entire assessment,
    including overall feedback and per-question feedback.
    """

    student_id: Optional[str] = None
    overall_feedback: str = Field(..., description="Overall feedback summary")
    question_feedback: List[QuestionFeedback] = Field(..., description="Per-question feedback")
    key_strengths: List[str] = Field(default_factory=list, description="Overall strengths")
    key_improvements: List[str] = Field(
        default_factory=list, description="Key areas to improve"
    )
    study_recommendations: List[str] = Field(
        default_factory=list, description="Study recommendations"
    )
    encouragement: str = Field(default="", description="Encouraging message")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
