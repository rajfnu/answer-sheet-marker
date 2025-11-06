"""Unit tests for Scoring Agent."""

import pytest
from unittest.mock import Mock

from answer_marker.agents.scoring_agent import (
    ScoringAgent,
    create_scoring_agent,
)
from answer_marker.core.agent_base import AgentConfig, AgentMessage
from answer_marker.models.evaluation import ScoringResult


class TestScoringAgent:
    """Test cases for ScoringAgent."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock Anthropic client."""
        return Mock()

    @pytest.fixture
    def agent_config(self):
        """Create agent configuration."""
        return AgentConfig(
            name="scoring_agent",
            system_prompt="You are a scoring agent.",
        )

    @pytest.fixture
    def agent(self, agent_config, mock_client):
        """Create ScoringAgent instance."""
        return ScoringAgent(config=agent_config, client=mock_client)

    @pytest.fixture
    def sample_evaluations(self):
        """Sample evaluations data."""
        return [
            {
                "question_id": "Q1",
                "concepts_identified": [
                    {"concept": "Concept 1", "points_earned": 2.0, "points_possible": 2.0},
                    {"concept": "Concept 2", "points_earned": 2.0, "points_possible": 2.0},
                    {"concept": "Concept 3", "points_earned": 1.0, "points_possible": 1.0},
                ],
                "max_marks": 5.0,
                "overall_quality": "excellent",
            },
            {
                "question_id": "Q2",
                "concepts_identified": [
                    {"concept": "Concept A", "points_earned": 3.0, "points_possible": 5.0},
                    {"concept": "Concept B", "points_earned": 2.0, "points_possible": 5.0},
                ],
                "max_marks": 10.0,
                "overall_quality": "satisfactory",
            },
        ]

    def test_agent_initialization(self, agent):
        """Test ScoringAgent initialization."""
        assert agent.config.name == "scoring_agent"
        assert agent.message_history == []

    def test_create_scoring_agent(self, mock_client):
        """Test factory function creates agent correctly."""
        agent = create_scoring_agent(mock_client)
        assert isinstance(agent, ScoringAgent)
        assert agent.config.name == "scoring_agent"

    @pytest.mark.asyncio
    async def test_process_with_valid_evaluations(self, agent, sample_evaluations):
        """Test processing valid evaluations."""
        message = AgentMessage(
            sender="test_sender",
            receiver="scoring_agent",
            content={"evaluations": sample_evaluations},
            message_type="request",
        )

        response = await agent.process(message)

        assert response.sender == "scoring_agent"
        assert response.receiver == "test_sender"
        assert response.message_type == "response"
        assert "scores" in response.content

        scores = response.content["scores"]
        assert scores["total_marks"] == 10.0  # 5.0 + 5.0
        assert scores["max_marks"] == 15.0  # 5.0 + 10.0
        assert scores["percentage"] == pytest.approx(66.67, rel=0.1)
        assert scores["grade"] == "B-"
        assert len(scores["question_scores"]) == 2

    @pytest.mark.asyncio
    async def test_process_with_no_evaluations(self, agent):
        """Test processing message without evaluations."""
        message = AgentMessage(
            sender="test_sender",
            receiver="scoring_agent",
            content={},
            message_type="request",
        )

        response = await agent.process(message)

        assert response.message_type == "error"
        assert "error" in response.content
        assert "No evaluations" in response.content["error"]

    @pytest.mark.asyncio
    async def test_calculate_scores_perfect_score(self, agent):
        """Test calculating perfect score."""
        evaluations = [
            {
                "question_id": "Q1",
                "concepts_identified": [
                    {"points_earned": 5.0},
                ],
                "max_marks": 5.0,
                "overall_quality": "excellent",
            },
            {
                "question_id": "Q2",
                "concepts_identified": [
                    {"points_earned": 10.0},
                ],
                "max_marks": 10.0,
                "overall_quality": "excellent",
            },
        ]

        result = await agent._calculate_scores(evaluations)

        assert isinstance(result, ScoringResult)
        assert result.total_marks == 15.0
        assert result.max_marks == 15.0
        assert result.percentage == 100.0
        assert result.grade == "A+"

    @pytest.mark.asyncio
    async def test_calculate_scores_failing_grade(self, agent):
        """Test calculating failing score."""
        evaluations = [
            {
                "question_id": "Q1",
                "concepts_identified": [
                    {"points_earned": 2.0},
                ],
                "max_marks": 10.0,
                "overall_quality": "poor",
            },
        ]

        result = await agent._calculate_scores(evaluations)

        assert result.total_marks == 2.0
        assert result.max_marks == 10.0
        assert result.percentage == 20.0
        assert result.grade == "F"

    @pytest.mark.asyncio
    async def test_calculate_scores_caps_at_maximum(self, agent):
        """Test that scores don't exceed maximum marks."""
        evaluations = [
            {
                "question_id": "Q1",
                "concepts_identified": [
                    {"points_earned": 12.0},  # More than max_marks
                ],
                "max_marks": 10.0,
                "overall_quality": "excellent",
            },
        ]

        result = await agent._calculate_scores(evaluations)

        # Should be capped at max_marks
        assert result.total_marks == 10.0
        assert result.max_marks == 10.0
        assert result.percentage == 100.0

    @pytest.mark.asyncio
    async def test_calculate_scores_empty_concepts(self, agent):
        """Test calculating scores with no concepts."""
        evaluations = [
            {
                "question_id": "Q1",
                "concepts_identified": [],
                "max_marks": 10.0,
                "overall_quality": "poor",
            },
        ]

        result = await agent._calculate_scores(evaluations)

        assert result.total_marks == 0.0
        assert result.max_marks == 10.0
        assert result.percentage == 0.0
        assert result.grade == "F"

    @pytest.mark.asyncio
    async def test_calculate_scores_zero_max_marks(self, agent):
        """Test calculating scores with zero max marks."""
        evaluations = [
            {
                "question_id": "Q1",
                "concepts_identified": [
                    {"points_earned": 0.0},
                ],
                "max_marks": 0.0,
                "overall_quality": "poor",
            },
        ]

        result = await agent._calculate_scores(evaluations)

        assert result.total_marks == 0.0
        assert result.max_marks == 0.0
        assert result.percentage == 0.0

    def test_calculate_grade_a_plus(self, agent):
        """Test grade calculation for A+."""
        assert agent._calculate_grade(100) == "A+"
        assert agent._calculate_grade(95) == "A+"
        assert agent._calculate_grade(90) == "A+"

    def test_calculate_grade_a(self, agent):
        """Test grade calculation for A."""
        assert agent._calculate_grade(89) == "A"
        assert agent._calculate_grade(87) == "A"
        assert agent._calculate_grade(85) == "A"

    def test_calculate_grade_a_minus(self, agent):
        """Test grade calculation for A-."""
        assert agent._calculate_grade(84) == "A-"
        assert agent._calculate_grade(82) == "A-"
        assert agent._calculate_grade(80) == "A-"

    def test_calculate_grade_b_plus(self, agent):
        """Test grade calculation for B+."""
        assert agent._calculate_grade(79) == "B+"
        assert agent._calculate_grade(77) == "B+"
        assert agent._calculate_grade(75) == "B+"

    def test_calculate_grade_b(self, agent):
        """Test grade calculation for B."""
        assert agent._calculate_grade(74) == "B"
        assert agent._calculate_grade(72) == "B"
        assert agent._calculate_grade(70) == "B"

    def test_calculate_grade_b_minus(self, agent):
        """Test grade calculation for B-."""
        assert agent._calculate_grade(69) == "B-"
        assert agent._calculate_grade(67) == "B-"
        assert agent._calculate_grade(65) == "B-"

    def test_calculate_grade_c_plus(self, agent):
        """Test grade calculation for C+."""
        assert agent._calculate_grade(64) == "C+"
        assert agent._calculate_grade(62) == "C+"
        assert agent._calculate_grade(60) == "C+"

    def test_calculate_grade_c(self, agent):
        """Test grade calculation for C."""
        assert agent._calculate_grade(59) == "C"
        assert agent._calculate_grade(57) == "C"
        assert agent._calculate_grade(55) == "C"

    def test_calculate_grade_c_minus(self, agent):
        """Test grade calculation for C-."""
        assert agent._calculate_grade(54) == "C-"
        assert agent._calculate_grade(52) == "C-"
        assert agent._calculate_grade(50) == "C-"

    def test_calculate_grade_f(self, agent):
        """Test grade calculation for F."""
        assert agent._calculate_grade(49) == "F"
        assert agent._calculate_grade(30) == "F"
        assert agent._calculate_grade(0) == "F"

    def test_message_logging(self, agent, sample_evaluations):
        """Test that messages are logged to history."""
        message = AgentMessage(
            sender="test_sender",
            receiver="scoring_agent",
            content={"evaluations": sample_evaluations},
            message_type="request",
        )

        agent.log_message(message)

        assert len(agent.message_history) == 1
        assert agent.message_history[0] == message

    @pytest.mark.asyncio
    async def test_process_handles_exception(self, agent):
        """Test that process handles exceptions gracefully."""
        # Pass invalid data that will cause an error
        message = AgentMessage(
            sender="test_sender",
            receiver="scoring_agent",
            content={"evaluations": "invalid"},  # Should be a list
            message_type="request",
        )

        response = await agent.process(message)

        assert response.message_type == "error"
        assert "error" in response.content

    @pytest.mark.asyncio
    async def test_question_scores_include_all_fields(self, agent, sample_evaluations):
        """Test that question scores include all required fields."""
        result = await agent._calculate_scores(sample_evaluations)

        for q_score in result.question_scores:
            assert hasattr(q_score, "question_id")
            assert hasattr(q_score, "marks_awarded")
            assert hasattr(q_score, "max_marks")
            assert hasattr(q_score, "percentage")
            assert hasattr(q_score, "quality")

    @pytest.mark.asyncio
    async def test_partial_credit_scoring(self, agent):
        """Test partial credit scoring."""
        evaluations = [
            {
                "question_id": "Q1",
                "concepts_identified": [
                    {"points_earned": 1.5, "points_possible": 2.0},
                    {"points_earned": 2.5, "points_possible": 3.0},
                ],
                "max_marks": 5.0,
                "overall_quality": "good",
            },
        ]

        result = await agent._calculate_scores(evaluations)

        assert result.total_marks == 4.0
        assert result.max_marks == 5.0
        assert result.percentage == 80.0
        assert result.grade == "A-"
