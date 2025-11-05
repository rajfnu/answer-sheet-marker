"""Unit tests for evaluation models."""

import pytest
from datetime import datetime
from pydantic import ValidationError
from answer_marker.models.evaluation import (
    ConceptEvaluation,
    AnswerEvaluation,
    QuestionScore,
    ScoringResult,
    QAFlag,
    QAResult,
)


class TestConceptEvaluation:
    """Test cases for ConceptEvaluation model."""

    def test_concept_evaluation_creation(self):
        """Test creating ConceptEvaluation with valid data."""
        eval = ConceptEvaluation(
            concept="Newton's First Law",
            present=True,
            accuracy="fully_correct",
            evidence="Student clearly stated the law",
            points_earned=2.0,
            points_possible=2.0,
            feedback="Excellent explanation",
        )

        assert eval.concept == "Newton's First Law"
        assert eval.present is True
        assert eval.accuracy == "fully_correct"
        assert eval.points_earned == 2.0
        assert eval.feedback == "Excellent explanation"

    def test_invalid_accuracy_value(self):
        """Test that invalid accuracy values raise ValidationError."""
        with pytest.raises(ValidationError):
            ConceptEvaluation(
                concept="Test",
                present=True,
                accuracy="invalid_value",
                evidence="Test",
                points_earned=1.0,
                points_possible=2.0,
            )


class TestAnswerEvaluation:
    """Test cases for AnswerEvaluation model."""

    def test_answer_evaluation_creation(self):
        """Test creating AnswerEvaluation with valid data."""
        concepts = [
            ConceptEvaluation(
                concept="Concept 1",
                present=True,
                accuracy="fully_correct",
                evidence="Present in answer",
                points_earned=2.0,
                points_possible=2.0,
            )
        ]

        eval = AnswerEvaluation(
            question_id="Q1",
            student_id="STU001",
            concepts_identified=concepts,
            overall_quality="good",
            strengths=["Clear explanation"],
            weaknesses=["Could use more examples"],
            confidence_score=0.85,
            marks_awarded=7.5,
            max_marks=10.0,
        )

        assert eval.question_id == "Q1"
        assert eval.confidence_score == 0.85
        assert eval.marks_awarded == 7.5
        assert len(eval.strengths) == 1

    def test_percentage_property(self):
        """Test percentage calculation."""
        eval = AnswerEvaluation(
            question_id="Q1",
            concepts_identified=[],
            overall_quality="good",
            confidence_score=0.8,
            marks_awarded=7.5,
            max_marks=10.0,
        )

        assert eval.percentage == 75.0

    def test_percentage_zero_max_marks(self):
        """Test percentage when max_marks is zero."""
        eval = AnswerEvaluation(
            question_id="Q1",
            concepts_identified=[],
            overall_quality="poor",
            confidence_score=0.5,
            marks_awarded=0.0,
            max_marks=0.0,
        )

        assert eval.percentage == 0.0

    def test_confidence_score_validation(self):
        """Test that confidence score must be between 0 and 1."""
        with pytest.raises(ValidationError):
            AnswerEvaluation(
                question_id="Q1",
                concepts_identified=[],
                overall_quality="good",
                confidence_score=1.5,
                marks_awarded=5.0,
                max_marks=10.0,
            )

    def test_default_values(self):
        """Test AnswerEvaluation with default values."""
        eval = AnswerEvaluation(
            question_id="Q1",
            concepts_identified=[],
            overall_quality="satisfactory",
            confidence_score=0.7,
            marks_awarded=5.0,
            max_marks=10.0,
        )

        assert eval.strengths == []
        assert eval.weaknesses == []
        assert eval.misconceptions == []
        assert eval.requires_human_review is False
        assert eval.review_reason is None
        assert isinstance(eval.timestamp, datetime)


class TestQuestionScore:
    """Test cases for QuestionScore model."""

    def test_question_score_creation(self):
        """Test creating QuestionScore with valid data."""
        score = QuestionScore(
            question_id="Q1",
            marks_awarded=8.0,
            max_marks=10.0,
            percentage=80.0,
            quality="good",
        )

        assert score.question_id == "Q1"
        assert score.marks_awarded == 8.0
        assert score.percentage == 80.0
        assert score.quality == "good"

    def test_percentage_validation(self):
        """Test that percentage must be between 0 and 100."""
        with pytest.raises(ValidationError):
            QuestionScore(
                question_id="Q1",
                marks_awarded=5.0,
                max_marks=10.0,
                percentage=150.0,
            )


class TestScoringResult:
    """Test cases for ScoringResult model."""

    def test_scoring_result_creation(self):
        """Test creating ScoringResult with valid data."""
        question_scores = [
            QuestionScore(
                question_id="Q1", marks_awarded=8.0, max_marks=10.0, percentage=80.0
            ),
            QuestionScore(
                question_id="Q2", marks_awarded=6.0, max_marks=10.0, percentage=60.0
            ),
        ]

        result = ScoringResult(
            student_id="STU001",
            total_marks=14.0,
            max_marks=20.0,
            percentage=70.0,
            grade="B",
            question_scores=question_scores,
            passed=True,
        )

        assert result.total_marks == 14.0
        assert result.percentage == 70.0
        assert result.grade == "B"
        assert result.passed is True

    def test_questions_passed_property(self):
        """Test counting questions with >50% score."""
        question_scores = [
            QuestionScore(
                question_id="Q1", marks_awarded=8.0, max_marks=10.0, percentage=80.0
            ),
            QuestionScore(
                question_id="Q2", marks_awarded=3.0, max_marks=10.0, percentage=30.0
            ),
            QuestionScore(
                question_id="Q3", marks_awarded=5.0, max_marks=10.0, percentage=50.0
            ),
            QuestionScore(
                question_id="Q4", marks_awarded=7.0, max_marks=10.0, percentage=70.0
            ),
        ]

        result = ScoringResult(
            total_marks=23.0,
            max_marks=40.0,
            percentage=57.5,
            grade="C+",
            question_scores=question_scores,
            passed=True,
        )

        assert result.questions_passed == 3


class TestQAFlag:
    """Test cases for QAFlag model."""

    def test_qa_flag_creation(self):
        """Test creating QAFlag with valid data."""
        flag = QAFlag(
            question_id="Q1",
            reason="Low confidence score",
            severity="medium",
            details={"confidence": 0.55},
        )

        assert flag.question_id == "Q1"
        assert flag.severity == "medium"
        assert flag.details["confidence"] == 0.55


class TestQAResult:
    """Test cases for QAResult model."""

    def test_qa_result_creation(self):
        """Test creating QAResult with valid data."""
        flags = [
            QAFlag(question_id="Q1", reason="Low confidence", severity="medium")
        ]

        result = QAResult(
            passed=False,
            requires_human_review=True,
            flags=flags,
            confidence_level="medium",
            consistency_score=0.75,
            recommendations=["Review Q1 manually"],
        )

        assert result.passed is False
        assert result.requires_human_review is True
        assert len(result.flags) == 1
        assert result.consistency_score == 0.75

    def test_qa_result_defaults(self):
        """Test QAResult with default values."""
        result = QAResult(
            passed=True,
            requires_human_review=False,
            confidence_level="high",
        )

        assert result.flags == []
        assert result.issues == []
        assert result.consistency_score == 1.0
        assert result.recommendations == []
        assert isinstance(result.timestamp, datetime)
