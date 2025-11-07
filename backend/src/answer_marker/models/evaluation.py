"""Evaluation models for the Answer Sheet Marker system.

This module defines data models for evaluations, scoring, and quality assurance.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime, timezone


class ConceptEvaluation(BaseModel):
    """Evaluation of a single concept.

    Represents the evaluation of one key concept within a student's answer,
    including whether it's present, its accuracy, and points earned.
    """

    concept: str
    present: bool = Field(..., description="Whether the concept is present")
    accuracy: Literal["fully_correct", "partially_correct", "incorrect", "not_present"]
    evidence: str = Field(..., description="Evidence from the answer")
    points_earned: float = Field(..., ge=0, description="Points earned for this concept")
    points_possible: float = Field(..., ge=0, description="Maximum points for this concept")
    feedback: Optional[str] = Field(None, description="Specific feedback for this concept")


class AnswerEvaluation(BaseModel):
    """Complete evaluation of a student answer.

    Represents the full evaluation of a student's answer to a question,
    including concept analysis, quality assessment, and feedback.
    """

    question_id: str
    question_number: Optional[str] = Field(None, description="Question number for display (e.g., '1', '2', '3')")
    student_id: Optional[str] = None
    concepts_identified: List[ConceptEvaluation] = Field(..., description="Concept evaluations")
    overall_quality: Literal["excellent", "good", "satisfactory", "poor", "inadequate"]
    strengths: List[str] = Field(default_factory=list, description="Answer strengths")
    weaknesses: List[str] = Field(default_factory=list, description="Answer weaknesses")
    misconceptions: List[str] = Field(default_factory=list, description="Identified misconceptions")
    confidence_score: float = Field(..., ge=0, le=1, description="Confidence in evaluation")
    requires_human_review: bool = Field(default=False, description="Whether human review needed")
    review_reason: Optional[str] = Field(None, description="Reason for human review")
    marks_awarded: float = Field(..., ge=0, description="Total marks awarded")
    max_marks: float = Field(..., ge=0, description="Maximum marks possible")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict = Field(default_factory=dict, description="Additional metadata")

    @property
    def percentage(self) -> float:
        """Calculate percentage score.

        Returns:
            Percentage score (0-100) for this answer
        """
        if self.max_marks == 0:
            return 0.0
        return (self.marks_awarded / self.max_marks) * 100


class QuestionScore(BaseModel):
    """Score for a single question.

    Simple representation of a question's score, used in summary reports.
    """

    question_id: str
    marks_awarded: float = Field(..., ge=0)
    max_marks: float = Field(..., ge=0)
    percentage: float = Field(..., ge=0, le=100)
    quality: Optional[str] = None


class ScoringResult(BaseModel):
    """Final scoring result for an answer sheet.

    Represents the complete scoring summary for a student's answer sheet,
    including total marks, grade, and per-question breakdown.
    """

    student_id: Optional[str] = None
    total_marks: float = Field(..., ge=0, description="Total marks awarded")
    max_marks: float = Field(..., ge=0, description="Maximum marks possible")
    percentage: float = Field(..., ge=0, le=100, description="Percentage score")
    grade: str = Field(..., description="Letter grade")
    question_scores: List[QuestionScore] = Field(..., description="Scores per question")
    passed: bool = Field(..., description="Whether the student passed")
    rank: Optional[str] = Field(None, description="Performance rank")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def questions_passed(self) -> int:
        """Count questions with >50% score.

        Returns:
            Number of questions where student scored above 50%
        """
        return sum(1 for q in self.question_scores if q.percentage >= 50)


class QAFlag(BaseModel):
    """Flag raised by QA agent.

    Represents a quality assurance concern that needs attention.
    """

    question_id: str
    reason: str
    severity: Literal["low", "medium", "high"]
    details: dict = Field(default_factory=dict)


class QAResult(BaseModel):
    """Quality assurance result.

    Represents the result of quality assurance checks on an evaluation,
    including flags, issues, and recommendations.
    """

    passed: bool = Field(..., description="Whether QA checks passed")
    requires_human_review: bool = Field(..., description="Whether human review needed")
    flags: List[QAFlag] = Field(default_factory=list, description="QA flags raised")
    issues: List[dict] = Field(default_factory=list, description="Issues found")
    confidence_level: Literal["high", "medium", "low"]
    consistency_score: float = Field(default=1.0, ge=0, le=1, description="Consistency score")
    recommendations: List[str] = Field(default_factory=list, description="QA recommendations")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
