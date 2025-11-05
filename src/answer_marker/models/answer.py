"""Answer models for the Answer Sheet Marker system.

This module defines data models for student answers and answer sheets.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone


class Answer(BaseModel):
    """Student answer for a single question.

    Represents a student's response to a specific question, including
    the answer text and metadata.
    """

    question_id: str
    answer_text: str = Field(..., description="The student's answer")
    is_blank: bool = Field(default=False, description="Whether the answer is blank/unanswered")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")


class AnswerSheet(BaseModel):
    """Complete answer sheet from a student.

    Represents all answers submitted by a student for an assessment,
    along with student information and submission metadata.
    """

    student_id: Optional[str] = Field(None, description="Student identifier")
    student_name: Optional[str] = Field(None, description="Student name")
    answers: List[Answer] = Field(..., description="List of answers")
    submission_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source_file: Optional[str] = Field(None, description="Source file path")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")

    def get_answer(self, question_id: str) -> Optional[Answer]:
        """Get answer for a specific question.

        Args:
            question_id: The ID of the question to retrieve

        Returns:
            Answer object if found, None otherwise
        """
        for answer in self.answers:
            if answer.question_id == question_id:
                return answer
        return None

    def get_answered_count(self) -> int:
        """Count non-blank answers.

        Returns:
            Number of questions that have non-blank answers
        """
        return sum(1 for answer in self.answers if not answer.is_blank)
