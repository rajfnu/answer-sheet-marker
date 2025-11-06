"""Unit tests for answer models."""

import pytest
from datetime import datetime
from answer_marker.models.answer import Answer, AnswerSheet


class TestAnswer:
    """Test cases for Answer model."""

    def test_answer_creation(self):
        """Test creating an Answer with valid data."""
        answer = Answer(
            question_id="Q1",
            answer_text="This is my answer",
            is_blank=False,
            metadata={"confidence": "high"},
        )

        assert answer.question_id == "Q1"
        assert answer.answer_text == "This is my answer"
        assert answer.is_blank is False
        assert answer.metadata["confidence"] == "high"

    def test_answer_defaults(self):
        """Test Answer with default values."""
        answer = Answer(question_id="Q1", answer_text="Test answer")

        assert answer.is_blank is False
        assert answer.metadata == {}

    def test_blank_answer(self):
        """Test creating a blank answer."""
        answer = Answer(question_id="Q1", answer_text="", is_blank=True)

        assert answer.is_blank is True
        assert answer.answer_text == ""


class TestAnswerSheet:
    """Test cases for AnswerSheet model."""

    def test_answer_sheet_creation(self):
        """Test creating an AnswerSheet with valid data."""
        answers = [
            Answer(question_id="Q1", answer_text="Answer 1"),
            Answer(question_id="Q2", answer_text="Answer 2"),
        ]

        sheet = AnswerSheet(
            student_id="STU001",
            student_name="John Doe",
            answers=answers,
            source_file="student_001.pdf",
        )

        assert sheet.student_id == "STU001"
        assert sheet.student_name == "John Doe"
        assert len(sheet.answers) == 2
        assert sheet.source_file == "student_001.pdf"

    def test_answer_sheet_defaults(self):
        """Test AnswerSheet with default values."""
        answers = [Answer(question_id="Q1", answer_text="Test")]

        sheet = AnswerSheet(answers=answers)

        assert sheet.student_id is None
        assert sheet.student_name is None
        assert sheet.source_file is None
        assert sheet.metadata == {}
        assert isinstance(sheet.submission_time, datetime)

    def test_get_answer(self):
        """Test getting a specific answer by question_id."""
        answers = [
            Answer(question_id="Q1", answer_text="Answer 1"),
            Answer(question_id="Q2", answer_text="Answer 2"),
            Answer(question_id="Q3", answer_text="Answer 3"),
        ]

        sheet = AnswerSheet(answers=answers)

        # Test finding existing answer
        answer = sheet.get_answer("Q2")
        assert answer is not None
        assert answer.question_id == "Q2"
        assert answer.answer_text == "Answer 2"

        # Test non-existent answer
        answer = sheet.get_answer("Q99")
        assert answer is None

    def test_get_answered_count(self):
        """Test counting non-blank answers."""
        answers = [
            Answer(question_id="Q1", answer_text="Answer 1", is_blank=False),
            Answer(question_id="Q2", answer_text="", is_blank=True),
            Answer(question_id="Q3", answer_text="Answer 3", is_blank=False),
            Answer(question_id="Q4", answer_text="", is_blank=True),
            Answer(question_id="Q5", answer_text="Answer 5", is_blank=False),
        ]

        sheet = AnswerSheet(answers=answers)

        assert sheet.get_answered_count() == 3

    def test_get_answered_count_all_blank(self):
        """Test counting when all answers are blank."""
        answers = [
            Answer(question_id="Q1", answer_text="", is_blank=True),
            Answer(question_id="Q2", answer_text="", is_blank=True),
        ]

        sheet = AnswerSheet(answers=answers)

        assert sheet.get_answered_count() == 0

    def test_get_answered_count_none_blank(self):
        """Test counting when no answers are blank."""
        answers = [
            Answer(question_id="Q1", answer_text="A1", is_blank=False),
            Answer(question_id="Q2", answer_text="A2", is_blank=False),
            Answer(question_id="Q3", answer_text="A3", is_blank=False),
        ]

        sheet = AnswerSheet(answers=answers)

        assert sheet.get_answered_count() == 3
