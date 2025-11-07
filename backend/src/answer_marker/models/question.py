"""Question models for the Answer Sheet Marker system.

This module defines data models for questions, key concepts, and evaluation criteria.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from enum import Enum


class QuestionType(str, Enum):
    """Types of questions supported by the system."""

    MCQ = "mcq"
    SHORT_ANSWER = "short_answer"
    ESSAY = "essay"
    NUMERICAL = "numerical"
    TRUE_FALSE = "true_false"
    MIXED = "mixed"


class KeyConcept(BaseModel):
    """Key concept to evaluate in an answer.

    Represents a specific concept that should be present in a student's answer
    along with its associated points and evaluation criteria.
    """

    concept: str = Field(..., description="The concept to look for")
    points: float = Field(..., ge=0, description="Points allocated to this concept")
    mandatory: bool = Field(default=False, description="Whether this concept is required")
    keywords: List[str] = Field(default=[], description="Keywords associated with this concept")
    description: Optional[str] = Field(None, description="Detailed description of the concept")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "concept": "Newton's First Law",
                "points": 2.0,
                "mandatory": True,
                "keywords": ["inertia", "force", "motion"],
                "description": "Must mention that objects maintain state of motion unless acted upon by force",
            }
        }
    )


class EvaluationCriteria(BaseModel):
    """Criteria for different performance levels.

    Defines what constitutes excellent, good, satisfactory, and poor performance
    for a specific question.
    """

    excellent: str = Field(..., description="Criteria for excellent performance")
    good: str = Field(..., description="Criteria for good performance")
    satisfactory: str = Field(..., description="Criteria for satisfactory performance")
    poor: str = Field(..., description="Criteria for poor performance")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "excellent": "All concepts clearly explained with examples",
                "good": "Most concepts present with minor gaps",
                "satisfactory": "Basic concepts present but incomplete",
                "poor": "Missing most key concepts",
            }
        }
    )


class AnalyzedQuestion(BaseModel):
    """Question with complete analysis and rubric.

    Represents a fully analyzed question with all necessary information
    for evaluation, including key concepts, evaluation criteria, and marking instructions.
    """

    id: str = Field(..., description="Unique question identifier")
    question_number: str = Field(..., description="Question number (e.g., '1', '2', '3')")
    question_text: str = Field(..., description="The question text")
    question_type: QuestionType
    max_marks: float = Field(..., ge=0, description="Maximum marks for this question")
    key_concepts: List[KeyConcept] = Field(..., description="Key concepts to evaluate")
    evaluation_criteria: EvaluationCriteria
    keywords: List[str] = Field(default=[], description="Important keywords")
    common_mistakes: List[str] = Field(default=[], description="Common mistakes to watch for")
    sample_answer: Optional[str] = Field(None, description="Sample correct answer")
    instructions: Optional[str] = Field(None, description="Special instructions for marking")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "Q1",
                "question_text": "Explain Newton's First Law of Motion",
                "question_type": "short_answer",
                "max_marks": 5.0,
                "key_concepts": [],
                "evaluation_criteria": {},
                "keywords": ["inertia", "force", "motion"],
            }
        }
    )
