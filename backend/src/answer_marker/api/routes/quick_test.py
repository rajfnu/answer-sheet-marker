"""Quick Test API endpoint for single question/answer marking.

This endpoint allows users to test the marking system with a single question
without creating a full assessment or uploading PDFs.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from loguru import logger

from ..services.marking_service import marking_service


router = APIRouter(prefix="/quick-test", tags=["quick-test"])


class QuestionType(str):
    """Question type constants."""
    MCQ = "mcq"
    SHORT_ANSWER = "short_answer"
    LONG_ANSWER = "long_answer"
    NUMERICAL = "numerical"
    TRUE_FALSE = "true_false"


class QuickTestRequest(BaseModel):
    """Request model for quick test marking."""

    question: str = Field(..., description="The question text", min_length=1)
    student_answer: str = Field(..., description="The student's answer", min_length=1)
    question_type: str = Field(
        default=QuestionType.SHORT_ANSWER,
        description="Type of question (mcq, short_answer, long_answer, numerical, true_false)"
    )
    max_marks: float = Field(..., description="Maximum marks for this question", gt=0)
    marking_guide: Optional[str] = Field(
        None,
        description="Marking criteria/rubric. If not provided, will be auto-generated."
    )
    model_answer: Optional[str] = Field(
        None,
        description="Expected/model answer for reference"
    )


class QuickTestResponse(BaseModel):
    """Response model for quick test marking."""

    marks_obtained: float = Field(..., description="Marks awarded to the student")
    max_marks: float = Field(..., description="Maximum marks possible")
    percentage: float = Field(..., description="Percentage score")
    feedback: str = Field(..., description="Detailed feedback for the student")
    marking_breakdown: Dict[str, Any] = Field(
        ...,
        description="Detailed breakdown of how marks were awarded"
    )
    question_analysis: Optional[Dict[str, Any]] = Field(
        None,
        description="Analysis of the question (learning objectives, key concepts, etc.)"
    )


@router.post("/mark", response_model=QuickTestResponse)
async def mark_quick_test(request: QuickTestRequest) -> QuickTestResponse:
    """Mark a single question/answer pair using the LLM marking engine.

    This endpoint provides a lightweight way to test the marking system without
    creating a full assessment or uploading PDFs.

    Args:
        request: Quick test marking request

    Returns:
        Marking results with score, feedback, and breakdown

    Raises:
        HTTPException: If marking fails
    """
    try:
        logger.info(
            f"Quick test marking request: type={request.question_type}, "
            f"max_marks={request.max_marks}"
        )

        # For now, return a simple mock response since the full integration
        # requires creating temporary files and using the full marking service
        # TODO: Implement full integration with marking_service

        # Simple scoring logic for demonstration
        marks_obtained = min(request.max_marks * 0.8, request.max_marks)  # Give 80% for demo
        percentage = (marks_obtained / request.max_marks) * 100

        response = QuickTestResponse(
            marks_obtained=marks_obtained,
            max_marks=request.max_marks,
            percentage=percentage,
            feedback=f"This is a demonstration response for the Quick Test feature. "
                    f"Full LLM-based marking will be available soon. "
                    f"Your answer was evaluated and received {marks_obtained} out of {request.max_marks} marks.",
            marking_breakdown={
                "content_accuracy": marks_obtained * 0.4,
                "completeness": marks_obtained * 0.3,
                "clarity": marks_obtained * 0.3
            },
            question_analysis={
                "question_type": request.question_type,
                "difficulty": "medium",
                "key_concepts": ["To be analyzed by LLM"]
            }
        )

        logger.info(
            f"Quick test completed: {response.marks_obtained}/{response.max_marks} "
            f"({response.percentage}%)"
        )

        return response

    except Exception as e:
        logger.error(f"Quick test marking failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Marking failed: {str(e)}"
        )


@router.get("/examples")
async def get_example_questions():
    """Get example questions for quick testing.

    Returns:
        List of example question/answer pairs
    """
    examples = [
        {
            "name": "Biology - Cell Division",
            "question": "Explain the main difference between mitosis and meiosis.",
            "question_type": QuestionType.SHORT_ANSWER,
            "max_marks": 4.0,
            "model_answer": "Mitosis produces two identical daughter cells with the same number of chromosomes as the parent cell, used for growth and repair. Meiosis produces four non-identical daughter cells with half the number of chromosomes, used for sexual reproduction.",
            "sample_student_answer": "Mitosis makes 2 cells that are the same and meiosis makes 4 cells that are different. Mitosis is for growth and meiosis is for making sex cells."
        },
        {
            "name": "Mathematics - Quadratic Formula",
            "question": "Solve the quadratic equation: x² - 5x + 6 = 0",
            "question_type": QuestionType.NUMERICAL,
            "max_marks": 5.0,
            "model_answer": "Using factoring: (x-2)(x-3) = 0, therefore x = 2 or x = 3",
            "sample_student_answer": "x² - 5x + 6 = 0\n(x-2)(x-3) = 0\nx = 2 or x = 3"
        },
        {
            "name": "History - World War II",
            "question": "What were the main causes of World War II?",
            "question_type": QuestionType.LONG_ANSWER,
            "max_marks": 10.0,
            "model_answer": "The main causes included: 1) Treaty of Versailles creating resentment in Germany, 2) Rise of fascism and totalitarian regimes, 3) Global economic depression, 4) Failure of the League of Nations, 5) German expansionism and appeasement policies.",
            "sample_student_answer": "World War II was caused by several factors. First, the Treaty of Versailles punished Germany harshly after WWI, creating economic hardship and resentment. Second, this allowed Hitler and the Nazi party to rise to power. Third, the Great Depression made things worse economically. Finally, other countries tried to appease Hitler instead of stopping him early."
        }
    ]

    return {"examples": examples}
