"""Marking guide models for the Answer Sheet Marker system.

This module defines data models for marking guides and assessment specifications.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from answer_marker.models.question import AnalyzedQuestion


class MarkingGuide(BaseModel):
    """Complete marking guide for an assessment.

    Represents the complete marking scheme for an assessment, including
    all questions, evaluation criteria, and assessment metadata.
    """

    title: str = Field(..., description="Assessment title")
    subject: Optional[str] = Field(None, description="Subject/course")
    date: Optional[datetime] = Field(None, description="Assessment date")
    total_marks: float = Field(..., ge=0, description="Total marks available")
    questions: List[AnalyzedQuestion] = Field(..., description="List of questions")
    instructions: Optional[str] = Field(None, description="General marking instructions")
    pass_percentage: float = Field(default=50.0, description="Pass percentage")
    time_limit: Optional[int] = Field(None, description="Time limit in minutes")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")
    source_file: Optional[str] = Field(None, description="Source file path")

    def get_question(self, question_id: str) -> Optional[AnalyzedQuestion]:
        """Get a specific question by ID.

        Args:
            question_id: The unique identifier of the question

        Returns:
            AnalyzedQuestion object if found, None otherwise
        """
        for question in self.questions:
            if question.id == question_id:
                return question
        return None

    def validate_total_marks(self) -> bool:
        """Validate that question marks sum to total.

        Checks if the sum of all individual question marks matches
        the declared total marks (within a small tolerance for floating point errors).

        Returns:
            True if marks are consistent, False otherwise
        """
        sum_marks = sum(q.max_marks for q in self.questions)
        return abs(sum_marks - self.total_marks) < 0.01
