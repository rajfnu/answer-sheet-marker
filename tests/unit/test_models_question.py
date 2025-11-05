"""Unit tests for question models."""

import pytest
from pydantic import ValidationError
from answer_marker.models.question import (
    QuestionType,
    KeyConcept,
    EvaluationCriteria,
    AnalyzedQuestion,
)


class TestQuestionType:
    """Test cases for QuestionType enum."""

    def test_question_types(self):
        """Test that all question types are available."""
        assert QuestionType.MCQ == "mcq"
        assert QuestionType.SHORT_ANSWER == "short_answer"
        assert QuestionType.ESSAY == "essay"
        assert QuestionType.NUMERICAL == "numerical"
        assert QuestionType.TRUE_FALSE == "true_false"
        assert QuestionType.MIXED == "mixed"


class TestKeyConcept:
    """Test cases for KeyConcept model."""

    def test_key_concept_creation(self):
        """Test creating a KeyConcept with valid data."""
        concept = KeyConcept(
            concept="Newton's First Law",
            points=2.0,
            mandatory=True,
            keywords=["inertia", "force", "motion"],
            description="Objects maintain state of motion unless acted upon by force",
        )

        assert concept.concept == "Newton's First Law"
        assert concept.points == 2.0
        assert concept.mandatory is True
        assert len(concept.keywords) == 3
        assert concept.description is not None

    def test_key_concept_defaults(self):
        """Test KeyConcept with default values."""
        concept = KeyConcept(concept="Test Concept", points=1.0)

        assert concept.mandatory is False
        assert concept.keywords == []
        assert concept.description is None

    def test_negative_points_validation(self):
        """Test that negative points raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            KeyConcept(concept="Test", points=-1.0)

        assert "points" in str(exc_info.value)

    def test_zero_points_allowed(self):
        """Test that zero points are allowed."""
        concept = KeyConcept(concept="Test", points=0.0)
        assert concept.points == 0.0


class TestEvaluationCriteria:
    """Test cases for EvaluationCriteria model."""

    def test_evaluation_criteria_creation(self):
        """Test creating EvaluationCriteria with valid data."""
        criteria = EvaluationCriteria(
            excellent="All concepts clearly explained with examples",
            good="Most concepts present with minor gaps",
            satisfactory="Basic concepts present but incomplete",
            poor="Missing most key concepts",
        )

        assert criteria.excellent is not None
        assert criteria.good is not None
        assert criteria.satisfactory is not None
        assert criteria.poor is not None

    def test_missing_required_field(self):
        """Test that missing required fields raise ValidationError."""
        with pytest.raises(ValidationError):
            EvaluationCriteria(
                excellent="Test",
                good="Test",
                satisfactory="Test"
                # Missing 'poor'
            )


class TestAnalyzedQuestion:
    """Test cases for AnalyzedQuestion model."""

    def test_analyzed_question_creation(self):
        """Test creating AnalyzedQuestion with valid data."""
        key_concept = KeyConcept(concept="Test Concept", points=2.0)
        criteria = EvaluationCriteria(
            excellent="Excellent",
            good="Good",
            satisfactory="Satisfactory",
            poor="Poor",
        )

        question = AnalyzedQuestion(
            id="Q1",
            question_text="Explain Newton's First Law",
            question_type=QuestionType.SHORT_ANSWER,
            max_marks=5.0,
            key_concepts=[key_concept],
            evaluation_criteria=criteria,
            keywords=["inertia", "force"],
        )

        assert question.id == "Q1"
        assert question.question_text is not None
        assert question.question_type == QuestionType.SHORT_ANSWER
        assert question.max_marks == 5.0
        assert len(question.key_concepts) == 1
        assert len(question.keywords) == 2

    def test_analyzed_question_defaults(self):
        """Test AnalyzedQuestion with default values."""
        key_concept = KeyConcept(concept="Test", points=1.0)
        criteria = EvaluationCriteria(
            excellent="E", good="G", satisfactory="S", poor="P"
        )

        question = AnalyzedQuestion(
            id="Q1",
            question_text="Test question",
            question_type=QuestionType.MCQ,
            max_marks=2.0,
            key_concepts=[key_concept],
            evaluation_criteria=criteria,
        )

        assert question.keywords == []
        assert question.common_mistakes == []
        assert question.sample_answer is None
        assert question.instructions is None
        assert question.metadata == {}

    def test_negative_max_marks_validation(self):
        """Test that negative max_marks raise ValidationError."""
        key_concept = KeyConcept(concept="Test", points=1.0)
        criteria = EvaluationCriteria(
            excellent="E", good="G", satisfactory="S", poor="P"
        )

        with pytest.raises(ValidationError):
            AnalyzedQuestion(
                id="Q1",
                question_text="Test",
                question_type=QuestionType.MCQ,
                max_marks=-5.0,
                key_concepts=[key_concept],
                evaluation_criteria=criteria,
            )

    def test_metadata_field(self):
        """Test that metadata can store arbitrary data."""
        key_concept = KeyConcept(concept="Test", points=1.0)
        criteria = EvaluationCriteria(
            excellent="E", good="G", satisfactory="S", poor="P"
        )

        question = AnalyzedQuestion(
            id="Q1",
            question_text="Test",
            question_type=QuestionType.ESSAY,
            max_marks=10.0,
            key_concepts=[key_concept],
            evaluation_criteria=criteria,
            metadata={"difficulty": "medium", "chapter": 3},
        )

        assert question.metadata["difficulty"] == "medium"
        assert question.metadata["chapter"] == 3
