"""Unit tests for Orchestrator Agent."""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timezone

from answer_marker.core.orchestrator import (
    OrchestratorAgent,
    create_orchestrator_agent,
)
from answer_marker.core.agent_base import AgentConfig, AgentMessage
from answer_marker.models.marking_guide import MarkingGuide
from answer_marker.models.question import AnalyzedQuestion, QuestionType, KeyConcept, EvaluationCriteria
from answer_marker.models.answer import AnswerSheet, Answer
from answer_marker.models.report import EvaluationReport


class TestOrchestratorAgent:
    """Test cases for OrchestratorAgent."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock Anthropic client."""
        return Mock()

    @pytest.fixture
    def mock_agents(self):
        """Create mock specialized agents."""
        return {
            "question_analyzer": Mock(),
            "answer_evaluator": Mock(),
            "scoring_agent": Mock(),
            "feedback_generator": Mock(),
            "qa_agent": Mock(),
        }

    @pytest.fixture
    def agent_config(self):
        """Create agent configuration."""
        return AgentConfig(
            name="orchestrator",
            system_prompt="You are the orchestrator.",
        )

    @pytest.fixture
    def orchestrator(self, agent_config, mock_client, mock_agents):
        """Create OrchestratorAgent instance."""
        return OrchestratorAgent(config=agent_config, client=mock_client, agents=mock_agents)

    @pytest.fixture
    def sample_marking_guide(self):
        """Create sample marking guide."""
        return MarkingGuide(
            title="Test Assessment",
            questions=[
                AnalyzedQuestion(
                    id="Q1",
                    question_text="What is 2+2?",
                    max_marks=5.0,
                    question_type=QuestionType.SHORT_ANSWER,
                    key_concepts=[
                        KeyConcept(
                            concept="Correct answer",
                            points=5.0,
                            mandatory=True,
                            keywords=["4", "four"],
                            description="Student should provide the correct answer: 4"
                        )
                    ],
                    evaluation_criteria=EvaluationCriteria(
                        excellent="Correct answer provided",
                        good="Answer is close to correct",
                        satisfactory="Attempted the question",
                        poor="No meaningful attempt"
                    )
                )
            ],
            total_marks=5.0,
        )

    @pytest.fixture
    def sample_answer_sheet(self):
        """Create sample answer sheet."""
        return AnswerSheet(
            student_id="STU001",
            answers=[
                Answer(question_id="Q1", answer_text="The answer is 4", is_blank=False)
            ],
            submission_time=datetime.now(timezone.utc),
        )

    def test_orchestrator_initialization(self, orchestrator, mock_agents):
        """Test OrchestratorAgent initialization."""
        assert orchestrator.config.name == "orchestrator"
        assert len(orchestrator.agents) == 5
        assert "question_analyzer" in orchestrator.agents
        assert "answer_evaluator" in orchestrator.agents

    def test_create_orchestrator_agent(self, mock_client, mock_agents):
        """Test factory function creates orchestrator correctly."""
        orchestrator = create_orchestrator_agent(mock_client, mock_agents)
        assert isinstance(orchestrator, OrchestratorAgent)
        assert orchestrator.config.name == "orchestrator"
        assert len(orchestrator.agents) == 5

    @pytest.mark.asyncio
    async def test_process_returns_info_message(self, orchestrator):
        """Test that process method returns info message."""
        message = AgentMessage(
            sender="test",
            receiver="orchestrator",
            content={},
            message_type="request",
        )

        response = await orchestrator.process(message)

        assert response.message_type == "info"
        assert "mark_answer_sheet" in response.content["status"]

    @pytest.mark.asyncio
    async def test_mark_answer_sheet_complete_workflow(
        self, orchestrator, mock_agents, sample_marking_guide, sample_answer_sheet
    ):
        """Test complete marking workflow."""
        # Mock Question Analyzer response
        mock_qa_response = AgentMessage(
            sender="question_analyzer",
            receiver="orchestrator",
            content={
                "analyzed_questions": {
                    "Q1": {
                        "id": "Q1",
                        "question_text": "What is 2+2?",
                        "question_type": "short_answer",
                        "max_marks": 5.0,
                        "key_concepts": [],
                        "evaluation_criteria": {},
                    }
                }
            },
            message_type="response",
        )
        mock_agents["question_analyzer"].process = AsyncMock(return_value=mock_qa_response)

        # Mock Answer Evaluator response
        mock_ae_response = AgentMessage(
            sender="answer_evaluator",
            receiver="orchestrator",
            content={
                "evaluation": {
                    "question_id": "Q1",
                    "concepts_identified": [
                        {"concept": "Correct answer", "points_earned": 5.0, "points_possible": 5.0, "present": True, "accuracy": "fully_correct", "evidence": "The answer is 4"}
                    ],
                    "overall_quality": "excellent",
                    "confidence_score": 0.95,
                    "marks_awarded": 5.0,
                    "max_marks": 5.0,
                    "strengths": ["Correct"],
                    "weaknesses": [],
                    "misconceptions": [],
                }
            },
            message_type="response",
        )
        mock_agents["answer_evaluator"].process = AsyncMock(return_value=mock_ae_response)

        # Mock Scoring Agent response
        mock_scoring_response = AgentMessage(
            sender="scoring_agent",
            receiver="orchestrator",
            content={
                "scores": {
                    "total_marks": 5.0,
                    "max_marks": 5.0,
                    "percentage": 100.0,
                    "grade": "A+",
                    "passed": True,
                    "question_scores": [
                        {
                            "question_id": "Q1",
                            "marks_awarded": 5.0,
                            "max_marks": 5.0,
                            "percentage": 100.0,
                        }
                    ],
                }
            },
            message_type="response",
        )
        mock_agents["scoring_agent"].process = AsyncMock(return_value=mock_scoring_response)

        # Mock Feedback Generator response
        mock_feedback_response = AgentMessage(
            sender="feedback_generator",
            receiver="orchestrator",
            content={
                "feedback": {
                    "overall_feedback": "Excellent work!",
                    "question_feedback": [
                        {
                            "question_id": "Q1",
                            "feedback": "Perfect answer",
                            "strengths": ["Correct"],
                            "improvement_areas": [],
                            "suggestions": [],
                        }
                    ],
                    "key_strengths": ["Good understanding"],
                    "key_improvements": [],
                    "study_recommendations": [],
                    "encouragement": "Keep it up!",
                }
            },
            message_type="response",
        )
        mock_agents["feedback_generator"].process = AsyncMock(return_value=mock_feedback_response)

        # Mock QA Agent response
        mock_qa_review_response = AgentMessage(
            sender="qa_agent",
            receiver="orchestrator",
            content={
                "qa_result": {
                    "passed": True,
                    "requires_human_review": False,
                    "flags": [],
                    "issues": [],
                    "confidence_level": "high",
                    "consistency_score": 1.0,
                    "recommendations": [],
                }
            },
            message_type="response",
        )
        mock_agents["qa_agent"].process = AsyncMock(return_value=mock_qa_review_response)

        # Execute marking workflow
        report = await orchestrator.mark_answer_sheet(
            marking_guide=sample_marking_guide,
            answer_sheet=sample_answer_sheet,
            assessment_title="Test Assessment",
        )

        # Verify report
        assert isinstance(report, EvaluationReport)
        assert report.student_id == "STU001"
        assert report.assessment_title == "Test Assessment"
        assert report.scoring_result.total_marks == 5.0
        assert report.scoring_result.grade == "A+"
        assert len(report.question_evaluations) == 1
        assert report.qa_result.passed is True
        assert report.processing_time is not None
        assert report.processing_time > 0

        # Verify all agents were called
        assert mock_agents["question_analyzer"].process.called
        assert mock_agents["answer_evaluator"].process.called
        assert mock_agents["scoring_agent"].process.called
        assert mock_agents["feedback_generator"].process.called
        assert mock_agents["qa_agent"].process.called

    @pytest.mark.asyncio
    async def test_analyze_questions_success(
        self, orchestrator, mock_agents, sample_marking_guide
    ):
        """Test question analysis step."""
        mock_response = AgentMessage(
            sender="question_analyzer",
            receiver="orchestrator",
            content={
                "analyzed_questions": {
                    "Q1": {"id": "Q1", "question_text": "What is 2+2?"}
                }
            },
            message_type="response",
        )
        mock_agents["question_analyzer"].process = AsyncMock(return_value=mock_response)

        result = await orchestrator._analyze_questions(sample_marking_guide)

        assert "Q1" in result
        assert result["Q1"]["id"] == "Q1"

    @pytest.mark.asyncio
    async def test_analyze_questions_error(
        self, orchestrator, mock_agents, sample_marking_guide
    ):
        """Test question analysis with error."""
        mock_response = AgentMessage(
            sender="question_analyzer",
            receiver="orchestrator",
            content={"error": "Analysis failed"},
            message_type="error",
        )
        mock_agents["question_analyzer"].process = AsyncMock(return_value=mock_response)

        with pytest.raises(Exception, match="Question analysis failed"):
            await orchestrator._analyze_questions(sample_marking_guide)

    @pytest.mark.asyncio
    async def test_evaluate_answer_success(self, orchestrator, mock_agents):
        """Test answer evaluation step."""
        question = {"id": "Q1", "question_text": "What is 2+2?"}
        answer = Mock()
        answer.answer_text = "4"

        mock_response = AgentMessage(
            sender="answer_evaluator",
            receiver="orchestrator",
            content={"evaluation": {"question_id": "Q1", "marks_awarded": 5.0}},
            message_type="response",
        )
        mock_agents["answer_evaluator"].process = AsyncMock(return_value=mock_response)

        result = await orchestrator._evaluate_answer(question, answer)

        assert result["question_id"] == "Q1"
        assert result["marks_awarded"] == 5.0

    @pytest.mark.asyncio
    async def test_calculate_scores_success(self, orchestrator, mock_agents):
        """Test scoring calculation step."""
        evaluations = [{"question_id": "Q1", "marks_awarded": 5.0}]

        mock_response = AgentMessage(
            sender="scoring_agent",
            receiver="orchestrator",
            content={"scores": {"total_marks": 5.0, "grade": "A+"}},
            message_type="response",
        )
        mock_agents["scoring_agent"].process = AsyncMock(return_value=mock_response)

        result = await orchestrator._calculate_scores(evaluations)

        assert result["total_marks"] == 5.0
        assert result["grade"] == "A+"

    @pytest.mark.asyncio
    async def test_generate_feedback_success(self, orchestrator, mock_agents):
        """Test feedback generation step."""
        evaluations = [{"question_id": "Q1"}]
        scores = {"total_marks": 5.0}

        mock_response = AgentMessage(
            sender="feedback_generator",
            receiver="orchestrator",
            content={"feedback": {"overall_feedback": "Good work"}},
            message_type="response",
        )
        mock_agents["feedback_generator"].process = AsyncMock(return_value=mock_response)

        result = await orchestrator._generate_feedback(evaluations, scores)

        assert result["overall_feedback"] == "Good work"

    @pytest.mark.asyncio
    async def test_qa_review_success(self, orchestrator, mock_agents):
        """Test QA review step."""
        evaluations = [{"question_id": "Q1"}]
        scores = {"total_marks": 5.0}
        feedback = {"overall_feedback": "Good"}

        mock_response = AgentMessage(
            sender="qa_agent",
            receiver="orchestrator",
            content={"qa_result": {"passed": True, "confidence_level": "high"}},
            message_type="response",
        )
        mock_agents["qa_agent"].process = AsyncMock(return_value=mock_response)

        result = await orchestrator._qa_review(evaluations, scores, feedback)

        assert result["passed"] is True
        assert result["confidence_level"] == "high"

    @pytest.mark.asyncio
    async def test_mark_answer_sheet_with_missing_answer(
        self, orchestrator, mock_agents, sample_marking_guide
    ):
        """Test marking when student hasn't answered a question."""
        # Answer sheet with no answers
        empty_answer_sheet = AnswerSheet(
            student_id="STU002",
            answers=[],
            submission_time=datetime.now(timezone.utc),
        )

        # Mock Question Analyzer
        mock_qa_response = AgentMessage(
            sender="question_analyzer",
            receiver="orchestrator",
            content={"analyzed_questions": {"Q1": {"id": "Q1"}}},
            message_type="response",
        )
        mock_agents["question_analyzer"].process = AsyncMock(return_value=mock_qa_response)

        # Mock other agents with minimal responses
        mock_agents["scoring_agent"].process = AsyncMock(
            return_value=AgentMessage(
                sender="scoring_agent",
                receiver="orchestrator",
                content={
                    "scores": {
                        "total_marks": 0.0,
                        "max_marks": 5.0,
                        "percentage": 0.0,
                        "grade": "F",
                        "passed": False,
                        "question_scores": [],
                    }
                },
                message_type="response",
            )
        )

        mock_agents["feedback_generator"].process = AsyncMock(
            return_value=AgentMessage(
                sender="feedback_generator",
                receiver="orchestrator",
                content={
                    "feedback": {
                        "overall_feedback": "No answers provided",
                        "question_feedback": [],
                        "key_strengths": [],
                        "key_improvements": [],
                        "study_recommendations": [],
                        "encouragement": "",
                    }
                },
                message_type="response",
            )
        )

        mock_agents["qa_agent"].process = AsyncMock(
            return_value=AgentMessage(
                sender="qa_agent",
                receiver="orchestrator",
                content={
                    "qa_result": {
                        "passed": True,
                        "requires_human_review": False,
                        "flags": [],
                        "issues": [],
                        "confidence_level": "high",
                        "consistency_score": 1.0,
                        "recommendations": [],
                    }
                },
                message_type="response",
            )
        )

        report = await orchestrator.mark_answer_sheet(
            marking_guide=sample_marking_guide,
            answer_sheet=empty_answer_sheet,
        )

        # Should complete without evaluating any answers
        assert len(report.question_evaluations) == 0
        assert report.scoring_result.total_marks == 0.0

    @pytest.mark.asyncio
    async def test_mark_answer_sheet_requires_review(
        self, orchestrator, mock_agents, sample_marking_guide, sample_answer_sheet
    ):
        """Test marking that requires human review."""
        # Setup mocks with low confidence
        mock_agents["question_analyzer"].process = AsyncMock(
            return_value=AgentMessage(
                sender="question_analyzer",
                receiver="orchestrator",
                content={"analyzed_questions": {"Q1": {"id": "Q1"}}},
                message_type="response",
            )
        )

        mock_agents["answer_evaluator"].process = AsyncMock(
            return_value=AgentMessage(
                sender="answer_evaluator",
                receiver="orchestrator",
                content={
                    "evaluation": {
                        "question_id": "Q1",
                        "concepts_identified": [{"concept": "Test", "points_earned": 2.0, "points_possible": 5.0, "present": True, "accuracy": "partially_correct", "evidence": "partial"}],
                        "overall_quality": "satisfactory",
                        "confidence_score": 0.45,  # Low confidence
                        "marks_awarded": 2.0,
                        "max_marks": 5.0,
                        "strengths": [],
                        "weaknesses": [],
                        "misconceptions": [],
                    }
                },
                message_type="response",
            )
        )

        mock_agents["scoring_agent"].process = AsyncMock(
            return_value=AgentMessage(
                sender="scoring_agent",
                receiver="orchestrator",
                content={
                    "scores": {
                        "total_marks": 2.0,
                        "max_marks": 5.0,
                        "percentage": 40.0,
                        "grade": "F",
                        "passed": False,
                        "question_scores": [],
                    }
                },
                message_type="response",
            )
        )

        mock_agents["feedback_generator"].process = AsyncMock(
            return_value=AgentMessage(
                sender="feedback_generator",
                receiver="orchestrator",
                content={
                    "feedback": {
                        "overall_feedback": "Needs improvement",
                        "question_feedback": [],
                        "key_strengths": [],
                        "key_improvements": [],
                        "study_recommendations": [],
                        "encouragement": "",
                    }
                },
                message_type="response",
            )
        )

        # QA agent flags for review due to low confidence
        mock_agents["qa_agent"].process = AsyncMock(
            return_value=AgentMessage(
                sender="qa_agent",
                receiver="orchestrator",
                content={
                    "qa_result": {
                        "passed": True,
                        "requires_human_review": True,  # Requires review
                        "flags": [{"question_id": "Q1", "reason": "Low confidence", "severity": "medium", "details": {}}],
                        "issues": [],
                        "confidence_level": "low",  # Low confidence
                        "consistency_score": 0.7,
                        "recommendations": ["Human review recommended"],
                    }
                },
                message_type="response",
            )
        )

        report = await orchestrator.mark_answer_sheet(
            marking_guide=sample_marking_guide,
            answer_sheet=sample_answer_sheet,
        )

        # Verify review flags
        assert report.requires_review is True
        assert report.review_priority == "high"  # High priority due to low confidence

    def test_message_logging(self, orchestrator):
        """Test that messages are logged to history."""
        message = AgentMessage(
            sender="test",
            receiver="orchestrator",
            content={},
            message_type="request",
        )

        orchestrator.log_message(message)

        assert len(orchestrator.message_history) == 1
        assert orchestrator.message_history[0] == message
