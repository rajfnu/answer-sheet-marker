"""Unit tests for feedback, report, and session models."""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime, timezone
from answer_marker.models.feedback import QuestionFeedback, FeedbackReport
from answer_marker.models.report import EvaluationReport, BatchReport
from answer_marker.models.session import MarkingSession
from answer_marker.models.evaluation import (
    AnswerEvaluation,
    ScoringResult,
    QAResult,
    QuestionScore,
)


class TestQuestionFeedback:
    """Test cases for QuestionFeedback model."""

    def test_question_feedback_creation(self):
        """Test creating QuestionFeedback with valid data."""
        feedback = QuestionFeedback(
            question_id="Q1",
            feedback="Good answer overall",
            strengths=["Clear explanation"],
            improvement_areas=["More examples needed"],
            suggestions=["Include real-world examples"],
            resources=["Chapter 3, textbook"],
        )

        assert feedback.question_id == "Q1"
        assert feedback.feedback == "Good answer overall"
        assert len(feedback.strengths) == 1
        assert len(feedback.resources) == 1

    def test_question_feedback_defaults(self):
        """Test QuestionFeedback with default values."""
        feedback = QuestionFeedback(question_id="Q1", feedback="Test feedback")

        assert feedback.strengths == []
        assert feedback.improvement_areas == []
        assert feedback.suggestions == []
        assert feedback.resources == []


class TestFeedbackReport:
    """Test cases for FeedbackReport model."""

    def test_feedback_report_creation(self):
        """Test creating FeedbackReport with valid data."""
        question_feedbacks = [
            QuestionFeedback(
                question_id="Q1", feedback="Good answer", strengths=["Clear"]
            ),
            QuestionFeedback(
                question_id="Q2", feedback="Needs improvement", improvement_areas=["Detail"]
            ),
        ]

        report = FeedbackReport(
            student_id="STU001",
            overall_feedback="Overall good performance",
            question_feedback=question_feedbacks,
            key_strengths=["Strong fundamentals"],
            key_improvements=["Add more detail"],
            encouragement="Keep up the good work!",
        )

        assert report.student_id == "STU001"
        assert len(report.question_feedback) == 2
        assert report.encouragement == "Keep up the good work!"

    def test_feedback_report_defaults(self):
        """Test FeedbackReport with default values."""
        report = FeedbackReport(
            overall_feedback="Test feedback", question_feedback=[]
        )

        assert report.student_id is None
        assert report.key_strengths == []
        assert report.key_improvements == []
        assert report.study_recommendations == []
        assert report.encouragement == ""
        assert isinstance(report.timestamp, datetime)


class TestEvaluationReport:
    """Test cases for EvaluationReport model."""

    def test_evaluation_report_creation(self):
        """Test creating EvaluationReport with valid data."""
        scoring = ScoringResult(
            total_marks=80.0,
            max_marks=100.0,
            percentage=80.0,
            grade="A",
            question_scores=[],
            passed=True,
        )

        qa_result = QAResult(
            passed=True, requires_human_review=False, confidence_level="high"
        )

        feedback = FeedbackReport(
            overall_feedback="Great job", question_feedback=[]
        )

        report = EvaluationReport(
            student_id="STU001",
            student_name="John Doe",
            assessment_title="Math Test",
            scoring_result=scoring,
            question_evaluations=[],
            feedback_report=feedback,
            qa_result=qa_result,
        )

        assert report.student_id == "STU001"
        assert report.assessment_title == "Math Test"
        assert report.scoring_result.percentage == 80.0

    def test_evaluation_report_to_json_file(self):
        """Test saving EvaluationReport to JSON file."""
        scoring = ScoringResult(
            total_marks=80.0,
            max_marks=100.0,
            percentage=80.0,
            grade="A",
            question_scores=[],
            passed=True,
        )

        qa_result = QAResult(
            passed=True, requires_human_review=False, confidence_level="high"
        )

        feedback = FeedbackReport(
            overall_feedback="Test", question_feedback=[]
        )

        report = EvaluationReport(
            assessment_title="Test",
            scoring_result=scoring,
            question_evaluations=[],
            feedback_report=feedback,
            qa_result=qa_result,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "report.json"
            report.to_json_file(str(filepath))

            assert filepath.exists()

            # Verify file content
            with open(filepath, "r") as f:
                data = json.load(f)
                assert data["assessment_title"] == "Test"

    def test_evaluation_report_from_json_file(self):
        """Test loading EvaluationReport from JSON file."""
        scoring = ScoringResult(
            total_marks=80.0,
            max_marks=100.0,
            percentage=80.0,
            grade="A",
            question_scores=[],
            passed=True,
        )

        qa_result = QAResult(
            passed=True, requires_human_review=False, confidence_level="high"
        )

        feedback = FeedbackReport(
            overall_feedback="Test", question_feedback=[]
        )

        original = EvaluationReport(
            student_id="STU001",
            assessment_title="Test",
            scoring_result=scoring,
            question_evaluations=[],
            feedback_report=feedback,
            qa_result=qa_result,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "report.json"
            original.to_json_file(str(filepath))

            loaded = EvaluationReport.from_json_file(str(filepath))

            assert loaded.student_id == "STU001"
            assert loaded.assessment_title == "Test"


class TestBatchReport:
    """Test cases for BatchReport model."""

    def test_batch_report_creation(self):
        """Test creating BatchReport with valid data."""
        report = BatchReport(
            batch_id="BATCH001",
            assessment_title="Math Test",
            total_sheets=10,
            processed_sheets=9,
            failed_sheets=1,
            average_score=75.5,
            median_score=78.0,
            highest_score=95.0,
            lowest_score=45.0,
            pass_rate=80.0,
            started_at=datetime.now(timezone.utc),
            sheets_requiring_review=2,
        )

        assert report.batch_id == "BATCH001"
        assert report.total_sheets == 10
        assert report.processed_sheets == 9
        assert report.average_score == 75.5

    def test_generate_summary(self):
        """Test generating summary statistics."""
        report = BatchReport(
            batch_id="BATCH001",
            assessment_title="Test",
            total_sheets=10,
            processed_sheets=8,
            failed_sheets=2,
            average_score=72.0,
            median_score=70.0,
            highest_score=90.0,
            lowest_score=50.0,
            pass_rate=75.0,
            started_at=datetime.now(timezone.utc),
            sheets_requiring_review=3,
        )

        summary = report.generate_summary()

        assert summary["total_sheets"] == 10
        assert summary["processed"] == 8
        assert summary["failed"] == 2
        assert summary["success_rate"] == 80.0
        assert summary["average_score"] == 72.0
        assert summary["pass_rate"] == 75.0
        assert summary["requiring_review"] == 3


class TestMarkingSession:
    """Test cases for MarkingSession model."""

    def test_marking_session_creation(self):
        """Test creating MarkingSession with valid data."""
        session = MarkingSession(
            session_id="SES001",
            marking_guide_path="/path/to/guide.pdf",
            answer_sheets_path="/path/to/sheets",
            output_path="/path/to/output",
            total_sheets=10,
        )

        assert session.session_id == "SES001"
        assert session.status == "initialized"
        assert session.total_sheets == 10
        assert session.processed_sheets == 0
        assert session.failed_sheets == 0

    def test_update_progress(self):
        """Test updating session progress."""
        session = MarkingSession(
            session_id="SES001",
            marking_guide_path="/path/to/guide.pdf",
            answer_sheets_path="/path/to/sheets",
            output_path="/path/to/output",
            total_sheets=10,
        )

        session.update_progress(processed=5, failed=1)

        assert session.processed_sheets == 5
        assert session.failed_sheets == 1
        assert session.status == "initialized"

    def test_update_progress_completion(self):
        """Test that status changes to completed when all sheets processed."""
        session = MarkingSession(
            session_id="SES001",
            marking_guide_path="/path/to/guide.pdf",
            answer_sheets_path="/path/to/sheets",
            output_path="/path/to/output",
            total_sheets=10,
        )

        session.update_progress(processed=9, failed=1)

        assert session.status == "completed"
        assert session.completed_at is not None

    def test_get_progress_percentage(self):
        """Test calculating progress percentage."""
        session = MarkingSession(
            session_id="SES001",
            marking_guide_path="/path/to/guide.pdf",
            answer_sheets_path="/path/to/sheets",
            output_path="/path/to/output",
            total_sheets=10,
        )

        # 0% progress
        assert session.get_progress_percentage() == 0.0

        # 50% progress
        session.update_progress(processed=3, failed=2)
        assert session.get_progress_percentage() == 50.0

        # 100% progress
        session.update_progress(processed=8, failed=2)
        assert session.get_progress_percentage() == 100.0

    def test_get_progress_percentage_zero_total(self):
        """Test progress percentage when total_sheets is zero."""
        session = MarkingSession(
            session_id="SES001",
            marking_guide_path="/path/to/guide.pdf",
            answer_sheets_path="/path/to/sheets",
            output_path="/path/to/output",
            total_sheets=0,
        )

        assert session.get_progress_percentage() == 0.0
