"""Report models for the Answer Sheet Marker system.

This module defines data models for evaluation reports and batch processing results.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Literal
from datetime import datetime, timezone
from answer_marker.models.evaluation import AnswerEvaluation, ScoringResult, QAResult
from answer_marker.models.feedback import FeedbackReport


class EvaluationReport(BaseModel):
    """Complete evaluation report for an answer sheet.

    Represents the complete evaluation result for a single student's answer sheet,
    including scoring, evaluations, feedback, and quality assurance results.
    """

    # Student Information
    student_id: Optional[str] = None
    student_name: Optional[str] = None

    # Assessment Information
    assessment_title: str
    assessment_date: Optional[datetime] = None

    # Scoring
    scoring_result: ScoringResult

    # Evaluations
    question_evaluations: List[AnswerEvaluation] = Field(
        ..., description="All question evaluations"
    )

    # Feedback
    feedback_report: FeedbackReport

    # Quality Assurance
    qa_result: QAResult

    # Metadata
    marked_by: str = Field(default="AI Marker", description="Marker identifier")
    marked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")
    version: str = Field(default="1.0.0", description="System version")

    # Flags
    requires_review: bool = Field(default=False)
    review_priority: Literal["low", "medium", "high"] = Field(default="low")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "student_id": "STU001",
                "assessment_title": "Mathematics Final Exam",
                "scoring_result": {},
                "question_evaluations": [],
                "feedback_report": {},
                "qa_result": {},
            }
        }
    )

    def to_json_file(self, filepath: str):
        """Save report to JSON file.

        Args:
            filepath: Path where the JSON file will be saved
        """
        import json
        from pathlib import Path

        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w") as f:
            json.dump(self.model_dump(), f, indent=2, default=str)

    @classmethod
    def from_json_file(cls, filepath: str):
        """Load report from JSON file.

        Args:
            filepath: Path to the JSON file to load

        Returns:
            EvaluationReport instance
        """
        import json

        with open(filepath, "r") as f:
            data = json.load(f)
        return cls(**data)


class BatchReport(BaseModel):
    """Report for batch processing.

    Represents the results of processing multiple answer sheets in a batch,
    including statistics and summary information.
    """

    batch_id: str
    assessment_title: str
    total_sheets: int
    processed_sheets: int
    failed_sheets: int
    reports: List[EvaluationReport] = Field(default_factory=list)

    # Statistics
    average_score: float
    median_score: float
    highest_score: float
    lowest_score: float
    pass_rate: float

    # Timing
    started_at: datetime
    completed_at: Optional[datetime] = None
    total_processing_time: Optional[float] = None

    # Flags
    sheets_requiring_review: int = 0

    def generate_summary(self) -> dict:
        """Generate summary statistics.

        Returns:
            Dictionary containing batch processing summary statistics
        """
        return {
            "total_sheets": self.total_sheets,
            "processed": self.processed_sheets,
            "failed": self.failed_sheets,
            "success_rate": (
                (self.processed_sheets / self.total_sheets * 100) if self.total_sheets > 0 else 0
            ),
            "average_score": self.average_score,
            "pass_rate": self.pass_rate,
            "requiring_review": self.sheets_requiring_review,
        }
