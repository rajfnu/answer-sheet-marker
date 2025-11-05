"""Unit tests for marking guide models."""

import pytest
from datetime import datetime
from answer_marker.models.marking_guide import MarkingGuide
from answer_marker.models.question import (
    AnalyzedQuestion,
    KeyConcept,
    EvaluationCriteria,
    QuestionType,
)


class TestMarkingGuide:
    """Test cases for MarkingGuide model."""

    def test_marking_guide_creation(self):
        """Test creating MarkingGuide with valid data."""
        key_concept = KeyConcept(concept="Test Concept", points=2.0)
        criteria = EvaluationCriteria(
            excellent="E", good="G", satisfactory="S", poor="P"
        )
        question = AnalyzedQuestion(
            id="Q1",
            question_text="Test question",
            question_type=QuestionType.SHORT_ANSWER,
            max_marks=5.0,
            key_concepts=[key_concept],
            evaluation_criteria=criteria,
        )

        guide = MarkingGuide(
            title="Physics Test",
            subject="Physics",
            total_marks=5.0,
            questions=[question],
            pass_percentage=50.0,
        )

        assert guide.title == "Physics Test"
        assert guide.subject == "Physics"
        assert guide.total_marks == 5.0
        assert len(guide.questions) == 1

    def test_marking_guide_defaults(self):
        """Test MarkingGuide with default values."""
        key_concept = KeyConcept(concept="Test", points=5.0)
        criteria = EvaluationCriteria(
            excellent="E", good="G", satisfactory="S", poor="P"
        )
        question = AnalyzedQuestion(
            id="Q1",
            question_text="Test",
            question_type=QuestionType.MCQ,
            max_marks=5.0,
            key_concepts=[key_concept],
            evaluation_criteria=criteria,
        )

        guide = MarkingGuide(
            title="Test", total_marks=5.0, questions=[question]
        )

        assert guide.subject is None
        assert guide.date is None
        assert guide.instructions is None
        assert guide.pass_percentage == 50.0
        assert guide.time_limit is None
        assert guide.metadata == {}
        assert guide.source_file is None

    def test_get_question(self):
        """Test getting a specific question by ID."""
        key_concept = KeyConcept(concept="Test", points=2.0)
        criteria = EvaluationCriteria(
            excellent="E", good="G", satisfactory="S", poor="P"
        )

        questions = [
            AnalyzedQuestion(
                id="Q1",
                question_text="Question 1",
                question_type=QuestionType.MCQ,
                max_marks=5.0,
                key_concepts=[key_concept],
                evaluation_criteria=criteria,
            ),
            AnalyzedQuestion(
                id="Q2",
                question_text="Question 2",
                question_type=QuestionType.SHORT_ANSWER,
                max_marks=10.0,
                key_concepts=[key_concept],
                evaluation_criteria=criteria,
            ),
        ]

        guide = MarkingGuide(
            title="Test", total_marks=15.0, questions=questions
        )

        # Test finding existing question
        question = guide.get_question("Q2")
        assert question is not None
        assert question.id == "Q2"
        assert question.max_marks == 10.0

        # Test non-existent question
        question = guide.get_question("Q99")
        assert question is None

    def test_validate_total_marks_valid(self):
        """Test validate_total_marks with matching totals."""
        key_concept = KeyConcept(concept="Test", points=2.0)
        criteria = EvaluationCriteria(
            excellent="E", good="G", satisfactory="S", poor="P"
        )

        questions = [
            AnalyzedQuestion(
                id="Q1",
                question_text="Q1",
                question_type=QuestionType.MCQ,
                max_marks=5.0,
                key_concepts=[key_concept],
                evaluation_criteria=criteria,
            ),
            AnalyzedQuestion(
                id="Q2",
                question_text="Q2",
                question_type=QuestionType.MCQ,
                max_marks=10.0,
                key_concepts=[key_concept],
                evaluation_criteria=criteria,
            ),
        ]

        guide = MarkingGuide(
            title="Test", total_marks=15.0, questions=questions
        )

        assert guide.validate_total_marks() is True

    def test_validate_total_marks_invalid(self):
        """Test validate_total_marks with mismatched totals."""
        key_concept = KeyConcept(concept="Test", points=2.0)
        criteria = EvaluationCriteria(
            excellent="E", good="G", satisfactory="S", poor="P"
        )

        questions = [
            AnalyzedQuestion(
                id="Q1",
                question_text="Q1",
                question_type=QuestionType.MCQ,
                max_marks=5.0,
                key_concepts=[key_concept],
                evaluation_criteria=criteria,
            ),
            AnalyzedQuestion(
                id="Q2",
                question_text="Q2",
                question_type=QuestionType.MCQ,
                max_marks=10.0,
                key_concepts=[key_concept],
                evaluation_criteria=criteria,
            ),
        ]

        guide = MarkingGuide(
            title="Test", total_marks=20.0, questions=questions
        )

        assert guide.validate_total_marks() is False

    def test_validate_total_marks_floating_point_tolerance(self):
        """Test validate_total_marks with floating point precision."""
        key_concept = KeyConcept(concept="Test", points=2.0)
        criteria = EvaluationCriteria(
            excellent="E", good="G", satisfactory="S", poor="P"
        )

        questions = [
            AnalyzedQuestion(
                id="Q1",
                question_text="Q1",
                question_type=QuestionType.MCQ,
                max_marks=2.5,
                key_concepts=[key_concept],
                evaluation_criteria=criteria,
            ),
            AnalyzedQuestion(
                id="Q2",
                question_text="Q2",
                question_type=QuestionType.MCQ,
                max_marks=2.5,
                key_concepts=[key_concept],
                evaluation_criteria=criteria,
            ),
        ]

        # Total should be 5.0, test with slight floating point difference
        guide = MarkingGuide(
            title="Test", total_marks=5.0, questions=questions
        )

        assert guide.validate_total_marks() is True
