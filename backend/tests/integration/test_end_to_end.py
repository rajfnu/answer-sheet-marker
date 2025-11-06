"""Integration tests for end-to-end marking workflow."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path
from datetime import datetime, timezone

from answer_marker.core.orchestrator import create_orchestrator_agent
from answer_marker.agents.question_analyzer import create_question_analyzer_agent
from answer_marker.agents.answer_evaluator import create_answer_evaluator_agent
from answer_marker.agents.scoring_agent import create_scoring_agent
from answer_marker.agents.feedback_generator import create_feedback_generator_agent
from answer_marker.agents.qa_agent import create_qa_agent
from answer_marker.models.marking_guide import MarkingGuide
from answer_marker.models.question import AnalyzedQuestion, QuestionType, KeyConcept, EvaluationCriteria
from answer_marker.models.answer import AnswerSheet, Answer
from answer_marker.models.report import EvaluationReport


class TestEndToEndMarking:
    """End-to-end integration tests for the marking workflow."""

    @pytest.fixture
    def mock_anthropic_client(self):
        """Create a mock Anthropic client."""
        mock_client = Mock()

        # Mock messages API
        mock_messages = Mock()
        mock_client.messages = mock_messages

        return mock_client

    @pytest.fixture
    def sample_marking_guide(self):
        """Create a sample marking guide for testing."""
        return MarkingGuide(
            title="Mathematics Test",
            subject="Mathematics",
            total_marks=20.0,
            questions=[
                AnalyzedQuestion(
                    id="Q1",
                    question_text="What is 2 + 2?",
                    question_type=QuestionType.SHORT_ANSWER,
                    max_marks=10.0,
                    key_concepts=[
                        KeyConcept(
                            concept="Correct answer (4)",
                            points=10.0,
                            mandatory=True,
                            keywords=["4", "four"],
                            description="Student should provide the correct answer"
                        )
                    ],
                    evaluation_criteria=EvaluationCriteria(
                        excellent="Correct answer provided clearly",
                        good="Answer is close or with minor error",
                        satisfactory="Attempted the question",
                        poor="No meaningful attempt"
                    ),
                    keywords=["addition", "sum"],
                    common_mistakes=["Subtracting instead of adding"]
                ),
                AnalyzedQuestion(
                    id="Q2",
                    question_text="What is 3 * 5?",
                    question_type=QuestionType.SHORT_ANSWER,
                    max_marks=10.0,
                    key_concepts=[
                        KeyConcept(
                            concept="Correct answer (15)",
                            points=10.0,
                            mandatory=True,
                            keywords=["15", "fifteen"],
                            description="Student should provide the correct answer"
                        )
                    ],
                    evaluation_criteria=EvaluationCriteria(
                        excellent="Correct answer provided clearly",
                        good="Answer is close or with minor error",
                        satisfactory="Attempted the question",
                        poor="No meaningful attempt"
                    ),
                    keywords=["multiplication", "product"],
                    common_mistakes=["Adding instead of multiplying"]
                ),
            ],
            pass_percentage=50.0,
        )

    @pytest.fixture
    def sample_answer_sheet_excellent(self):
        """Create a sample answer sheet with excellent answers."""
        return AnswerSheet(
            student_id="STU001",
            answers=[
                Answer(
                    question_id="Q1",
                    answer_text="The answer is 4",
                    is_blank=False
                ),
                Answer(
                    question_id="Q2",
                    answer_text="3 * 5 = 15",
                    is_blank=False
                ),
            ],
            submission_time=datetime.now(timezone.utc),
        )

    @pytest.fixture
    def sample_answer_sheet_partial(self):
        """Create a sample answer sheet with partial answers."""
        return AnswerSheet(
            student_id="STU002",
            answers=[
                Answer(
                    question_id="Q1",
                    answer_text="The answer is 4",
                    is_blank=False
                ),
                Answer(
                    question_id="Q2",
                    answer_text="I'm not sure",
                    is_blank=False
                ),
            ],
            submission_time=datetime.now(timezone.utc),
        )

    @pytest.fixture
    def sample_answer_sheet_poor(self):
        """Create a sample answer sheet with poor answers."""
        return AnswerSheet(
            student_id="STU003",
            answers=[
                Answer(
                    question_id="Q1",
                    answer_text="",
                    is_blank=True
                ),
                Answer(
                    question_id="Q2",
                    answer_text="",
                    is_blank=True
                ),
            ],
            submission_time=datetime.now(timezone.utc),
        )

    def _mock_tool_response(self, tool_name, input_data):
        """Generate mock tool response based on input."""

        if tool_name == "analyze_question":
            # Return analyzed question
            return {
                "id": input_data["id"],
                "question_text": input_data["question_text"],
                "question_type": input_data.get("question_type", "short_answer"),
                "max_marks": input_data.get("max_marks", 10.0),
                "key_concepts": [
                    {
                        "concept": "Test concept",
                        "points": 10.0,
                        "mandatory": True,
                        "keywords": ["test"],
                        "description": "Test description"
                    }
                ],
                "evaluation_criteria": {
                    "excellent": "Perfect answer",
                    "good": "Good answer",
                    "satisfactory": "Okay answer",
                    "poor": "Poor answer"
                },
                "keywords": ["test"],
                "common_mistakes": []
            }

        elif tool_name == "evaluate_answer":
            # Return evaluation based on answer quality
            answer_text = input_data.get("student_answer", "").lower()

            if "4" in answer_text or "15" in answer_text:
                # Good answer
                return {
                    "concepts_identified": [
                        {
                            "concept": "Correct answer",
                            "points_earned": 10.0,
                            "points_possible": 10.0,
                            "present": True,
                            "accuracy": "fully_correct",
                            "evidence": "Student provided correct answer"
                        }
                    ],
                    "overall_quality": "excellent",
                    "confidence_score": 0.95,
                    "marks_awarded": 10.0,
                    "max_marks": 10.0,
                    "strengths": ["Correct answer"],
                    "weaknesses": [],
                    "misconceptions": []
                }
            else:
                # Poor answer
                return {
                    "concepts_identified": [
                        {
                            "concept": "Attempted answer",
                            "points_earned": 1.0,
                            "points_possible": 10.0,
                            "present": False,
                            "accuracy": "incorrect",
                            "evidence": "Student did not provide correct answer"
                        }
                    ],
                    "overall_quality": "poor",
                    "confidence_score": 0.9,
                    "marks_awarded": 1.0,
                    "max_marks": 10.0,
                    "strengths": [],
                    "weaknesses": ["Incorrect answer"],
                    "misconceptions": []
                }

        elif tool_name == "generate_feedback":
            return {
                "overall_feedback": "Test feedback",
                "strengths": ["Test strength"],
                "improvement_areas": ["Test improvement"],
                "recommendations": ["Test recommendation"]
            }

        return {}

    def _setup_mock_client(self, mock_client):
        """Setup mock client with tool responses."""

        def create_mock_response(tool_name, tool_input):
            """Create a mock response with tool use."""
            mock_response = Mock()
            mock_response.stop_reason = "tool_use"

            # Create mock tool use block
            mock_tool_use = Mock()
            mock_tool_use.type = "tool_use"
            mock_tool_use.name = tool_name
            mock_tool_use.input = tool_input
            mock_tool_use.id = "mock_tool_id"

            mock_response.content = [mock_tool_use]
            return mock_response

        def mock_create_side_effect(**kwargs):
            """Side effect for messages.create calls."""
            messages = kwargs.get("messages", [])
            tools = kwargs.get("tools", [])

            if not messages:
                return Mock(stop_reason="end_turn", content=[])

            last_message = messages[-1]

            # Detect which agent is calling based on system prompt or tools
            if tools:
                tool_name = tools[0].get("name", "")

                if tool_name == "evaluate_answer":
                    # Extract student answer from message
                    content = last_message.get("content", "")
                    if "student_answer" in str(content):
                        mock_response = create_mock_response("evaluate_answer", {
                            "question": {},
                            "student_answer": "test answer"
                        })

                        # Add actual response
                        result = self._mock_tool_response("evaluate_answer", {"student_answer": "The answer is 4"})
                        mock_tool_result = Mock()
                        mock_tool_result.type = "tool_result"
                        mock_tool_result.name = "evaluate_answer"
                        mock_tool_result.input = result
                        mock_response.content[0].input = result

                        return mock_response
                elif tool_name == "generate_question_feedback":
                    result = {
                        "feedback": "Good work",
                        "strengths": ["Correct answer"],
                        "improvement_areas": [],
                        "suggestions": []
                    }
                    mock_response = create_mock_response("generate_question_feedback", result)
                    mock_response.content[0].input = result
                    return mock_response
                elif tool_name == "generate_overall_feedback":
                    result = {
                        "overall_feedback": "Excellent work!",
                        "key_strengths": ["Strong understanding"],
                        "key_improvements": [],
                        "study_recommendations": [],
                        "encouragement": "Keep it up!"
                    }
                    mock_response = create_mock_response("generate_overall_feedback", result)
                    mock_response.content[0].input = result
                    return mock_response

            # Default response
            return Mock(stop_reason="end_turn", content=[])

        mock_client.messages.create = Mock(side_effect=mock_create_side_effect)

    @pytest.mark.asyncio
    async def test_end_to_end_marking_excellent_performance(
        self,
        mock_anthropic_client,
        sample_marking_guide,
        sample_answer_sheet_excellent
    ):
        """Test complete marking workflow with excellent performance."""

        # Setup mock client
        self._setup_mock_client(mock_anthropic_client)

        # Create agent system
        agents = {
            "question_analyzer": create_question_analyzer_agent(mock_anthropic_client),
            "answer_evaluator": create_answer_evaluator_agent(mock_anthropic_client),
            "scoring_agent": create_scoring_agent(mock_anthropic_client),
            "feedback_generator": create_feedback_generator_agent(mock_anthropic_client),
            "qa_agent": create_qa_agent(mock_anthropic_client),
        }

        orchestrator = create_orchestrator_agent(mock_anthropic_client, agents)

        # Execute marking
        report = await orchestrator.mark_answer_sheet(
            marking_guide=sample_marking_guide,
            answer_sheet=sample_answer_sheet_excellent,
            assessment_title="Mathematics Test"
        )

        # Assertions
        assert isinstance(report, EvaluationReport)
        assert report.student_id == "STU001"
        assert report.assessment_title == "Mathematics Test"
        assert report.scoring_result.total_marks > 0
        assert report.scoring_result.max_marks == 20.0
        assert len(report.question_evaluations) == 2
        assert report.processing_time > 0

        # Check that report has all required components
        assert report.feedback_report is not None
        assert report.qa_result is not None
        assert report.scoring_result.grade in ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "F"]

    @pytest.mark.asyncio
    async def test_end_to_end_marking_partial_performance(
        self,
        mock_anthropic_client,
        sample_marking_guide,
        sample_answer_sheet_partial
    ):
        """Test complete marking workflow with partial performance."""

        # Setup mock client
        self._setup_mock_client(mock_anthropic_client)

        # Create agent system
        agents = {
            "question_analyzer": create_question_analyzer_agent(mock_anthropic_client),
            "answer_evaluator": create_answer_evaluator_agent(mock_anthropic_client),
            "scoring_agent": create_scoring_agent(mock_anthropic_client),
            "feedback_generator": create_feedback_generator_agent(mock_anthropic_client),
            "qa_agent": create_qa_agent(mock_anthropic_client),
        }

        orchestrator = create_orchestrator_agent(mock_anthropic_client, agents)

        # Execute marking
        report = await orchestrator.mark_answer_sheet(
            marking_guide=sample_marking_guide,
            answer_sheet=sample_answer_sheet_partial,
            assessment_title="Mathematics Test"
        )

        # Assertions
        assert isinstance(report, EvaluationReport)
        assert report.student_id == "STU002"
        assert len(report.question_evaluations) == 2

        # Should have some score but not perfect
        assert report.scoring_result.total_marks < report.scoring_result.max_marks

    @pytest.mark.asyncio
    async def test_end_to_end_marking_poor_performance(
        self,
        mock_anthropic_client,
        sample_marking_guide,
        sample_answer_sheet_poor
    ):
        """Test complete marking workflow with poor performance."""

        # Setup mock client
        self._setup_mock_client(mock_anthropic_client)

        # Create agent system
        agents = {
            "question_analyzer": create_question_analyzer_agent(mock_anthropic_client),
            "answer_evaluator": create_answer_evaluator_agent(mock_anthropic_client),
            "scoring_agent": create_scoring_agent(mock_anthropic_client),
            "feedback_generator": create_feedback_generator_agent(mock_anthropic_client),
            "qa_agent": create_qa_agent(mock_anthropic_client),
        }

        orchestrator = create_orchestrator_agent(mock_anthropic_client, agents)

        # Execute marking
        report = await orchestrator.mark_answer_sheet(
            marking_guide=sample_marking_guide,
            answer_sheet=sample_answer_sheet_poor,
            assessment_title="Mathematics Test"
        )

        # Assertions
        assert isinstance(report, EvaluationReport)
        assert report.student_id == "STU003"

        # Should have low or zero score
        assert report.scoring_result.total_marks <= report.scoring_result.max_marks * 0.3
        assert report.scoring_result.passed is False

    @pytest.mark.asyncio
    async def test_marking_with_missing_answers(
        self,
        mock_anthropic_client,
        sample_marking_guide
    ):
        """Test marking when some answers are missing."""

        # Setup mock client
        self._setup_mock_client(mock_anthropic_client)

        # Create answer sheet with only one answer
        answer_sheet = AnswerSheet(
            student_id="STU004",
            answers=[
                Answer(
                    question_id="Q1",
                    answer_text="The answer is 4",
                    is_blank=False
                ),
                # Q2 is missing
            ],
            submission_time=datetime.now(timezone.utc),
        )

        # Create agent system
        agents = {
            "question_analyzer": create_question_analyzer_agent(mock_anthropic_client),
            "answer_evaluator": create_answer_evaluator_agent(mock_anthropic_client),
            "scoring_agent": create_scoring_agent(mock_anthropic_client),
            "feedback_generator": create_feedback_generator_agent(mock_anthropic_client),
            "qa_agent": create_qa_agent(mock_anthropic_client),
        }

        orchestrator = create_orchestrator_agent(mock_anthropic_client, agents)

        # Execute marking
        report = await orchestrator.mark_answer_sheet(
            marking_guide=sample_marking_guide,
            answer_sheet=answer_sheet,
            assessment_title="Mathematics Test"
        )

        # Assertions
        assert isinstance(report, EvaluationReport)
        # Should only have 1 evaluation (for Q1)
        assert len(report.question_evaluations) == 1
        assert report.question_evaluations[0].question_id == "Q1"

    @pytest.mark.asyncio
    async def test_report_includes_all_components(
        self,
        mock_anthropic_client,
        sample_marking_guide,
        sample_answer_sheet_excellent
    ):
        """Test that the report includes all required components."""

        # Setup mock client
        self._setup_mock_client(mock_anthropic_client)

        # Create agent system
        agents = {
            "question_analyzer": create_question_analyzer_agent(mock_anthropic_client),
            "answer_evaluator": create_answer_evaluator_agent(mock_anthropic_client),
            "scoring_agent": create_scoring_agent(mock_anthropic_client),
            "feedback_generator": create_feedback_generator_agent(mock_anthropic_client),
            "qa_agent": create_qa_agent(mock_anthropic_client),
        }

        orchestrator = create_orchestrator_agent(mock_anthropic_client, agents)

        # Execute marking
        report = await orchestrator.mark_answer_sheet(
            marking_guide=sample_marking_guide,
            answer_sheet=sample_answer_sheet_excellent,
            assessment_title="Mathematics Test"
        )

        # Check all required components
        assert hasattr(report, "student_id")
        assert hasattr(report, "assessment_title")
        assert hasattr(report, "scoring_result")
        assert hasattr(report, "question_evaluations")
        assert hasattr(report, "feedback_report")
        assert hasattr(report, "qa_result")
        assert hasattr(report, "processing_time")
        assert hasattr(report, "requires_review")
        assert hasattr(report, "review_priority")

        # Check scoring result components
        assert hasattr(report.scoring_result, "total_marks")
        assert hasattr(report.scoring_result, "max_marks")
        assert hasattr(report.scoring_result, "percentage")
        assert hasattr(report.scoring_result, "grade")
        assert hasattr(report.scoring_result, "passed")

        # Check QA result components
        assert hasattr(report.qa_result, "passed")
        assert hasattr(report.qa_result, "confidence_level")
        assert hasattr(report.qa_result, "requires_human_review")
