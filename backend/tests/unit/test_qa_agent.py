"""Unit tests for QA Agent."""

import pytest
from unittest.mock import Mock

from answer_marker.agents.qa_agent import (
    QAAgent,
    create_qa_agent,
)
from answer_marker.core.agent_base import AgentConfig, AgentMessage
from answer_marker.models.evaluation import QAResult, QAFlag


class TestQAAgent:
    """Test cases for QAAgent."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock Anthropic client."""
        return Mock()

    @pytest.fixture
    def agent_config(self):
        """Create agent configuration."""
        return AgentConfig(
            name="qa_agent",
            system_prompt="You are a QA agent.",
        )

    @pytest.fixture
    def agent(self, agent_config, mock_client):
        """Create QAAgent instance."""
        return QAAgent(config=agent_config, client=mock_client)

    @pytest.fixture
    def sample_good_evaluations(self):
        """Sample evaluations with good quality."""
        return [
            {
                "question_id": "Q1",
                "concepts_identified": [
                    {"points_earned": 2.0, "points_possible": 2.0, "present": True},
                    {"points_earned": 2.0, "points_possible": 2.0, "present": True},
                ],
                "overall_quality": "excellent",
                "confidence_score": 0.95,
                "marks_awarded": 4.0,
                "max_marks": 5.0,
            }
        ]

    @pytest.fixture
    def sample_low_confidence_evaluations(self):
        """Sample evaluations with low confidence."""
        return [
            {
                "question_id": "Q1",
                "concepts_identified": [{"points_earned": 3.0, "points_possible": 5.0}],
                "overall_quality": "satisfactory",
                "confidence_score": 0.45,
                "marks_awarded": 3.0,
                "max_marks": 5.0,
            }
        ]

    @pytest.fixture
    def sample_scoring_issue_evaluations(self):
        """Sample evaluations with scoring issues."""
        return [
            {
                "question_id": "Q1",
                "concepts_identified": [
                    {"points_earned": 7.0},
                ],
                "overall_quality": "excellent",
                "confidence_score": 0.9,
                "marks_awarded": 7.0,
                "max_marks": 5.0,  # Score exceeds max!
            }
        ]

    def test_agent_initialization(self, agent):
        """Test QAAgent initialization."""
        assert agent.config.name == "qa_agent"
        assert agent.message_history == []

    def test_create_qa_agent(self, mock_client):
        """Test factory function creates agent correctly."""
        agent = create_qa_agent(mock_client)
        assert isinstance(agent, QAAgent)
        assert agent.config.name == "qa_agent"

    @pytest.mark.asyncio
    async def test_process_with_good_evaluations(self, agent, sample_good_evaluations):
        """Test processing evaluations that pass QA."""
        message = AgentMessage(
            sender="test_sender",
            receiver="qa_agent",
            content={"evaluations": sample_good_evaluations, "scores": {}, "feedback": {}},
            message_type="request",
        )

        response = await agent.process(message)

        assert response.sender == "qa_agent"
        assert response.receiver == "test_sender"
        assert response.message_type == "response"
        assert "qa_result" in response.content

        qa_result = response.content["qa_result"]
        assert qa_result["passed"] is True
        assert qa_result["confidence_level"] in ["high", "medium", "low"]

    @pytest.mark.asyncio
    async def test_process_with_no_evaluations(self, agent):
        """Test processing message without evaluations."""
        message = AgentMessage(
            sender="test_sender",
            receiver="qa_agent",
            content={},
            message_type="request",
        )

        response = await agent.process(message)

        assert response.message_type == "error"
        assert "error" in response.content
        assert "No evaluations" in response.content["error"]

    @pytest.mark.asyncio
    async def test_check_low_confidence(self, agent, sample_low_confidence_evaluations):
        """Test low confidence check."""
        flags = agent._check_low_confidence(sample_low_confidence_evaluations)

        assert len(flags) == 1
        assert flags[0].reason == "Low confidence score"
        assert flags[0].severity in ["high", "medium"]
        assert flags[0].details["confidence"] == 0.45

    @pytest.mark.asyncio
    async def test_check_scoring_consistency(self, agent, sample_scoring_issue_evaluations):
        """Test scoring consistency check."""
        issues = agent._check_scoring_consistency(sample_scoring_issue_evaluations)

        assert len(issues) == 1
        assert issues[0]["issue"] == "Score exceeds maximum"
        assert "7.0" in issues[0]["details"]
        assert "5.0" in issues[0]["details"]

    @pytest.mark.asyncio
    async def test_check_mandatory_concepts(self, agent):
        """Test mandatory concept check."""
        evaluations = [
            {
                "question_id": "Q1",
                "concepts_identified": [
                    {"points_earned": 0.0, "points_possible": 3.0, "present": False},  # Missing important concept
                ],
                "overall_quality": "excellent",  # But rated excellent!
                "confidence_score": 0.9,
                "marks_awarded": 2.0,
                "max_marks": 5.0,
            }
        ]

        flags = agent._check_mandatory_concepts(evaluations)

        assert len(flags) > 0
        assert flags[0].reason == "High score despite missing key concepts"

    @pytest.mark.asyncio
    async def test_check_score_discrepancies_high_score_poor_quality(self, agent):
        """Test score discrepancy check - high score but poor quality."""
        evaluations = [
            {
                "question_id": "Q1",
                "concepts_identified": [],
                "overall_quality": "poor",
                "confidence_score": 0.9,
                "marks_awarded": 9.0,
                "max_marks": 10.0,  # 90% but poor quality!
            }
        ]

        flags = agent._check_score_discrepancies(evaluations)

        assert len(flags) > 0
        assert "High score but poor quality rating" in flags[0].reason
        assert flags[0].severity == "high"

    @pytest.mark.asyncio
    async def test_check_score_discrepancies_low_score_good_quality(self, agent):
        """Test score discrepancy check - low score but good quality."""
        evaluations = [
            {
                "question_id": "Q1",
                "concepts_identified": [],
                "overall_quality": "excellent",
                "confidence_score": 0.9,
                "marks_awarded": 2.0,
                "max_marks": 10.0,  # 20% but excellent quality!
            }
        ]

        flags = agent._check_score_discrepancies(evaluations)

        assert len(flags) > 0
        assert "Low score but high quality rating" in flags[0].reason

    @pytest.mark.asyncio
    async def test_check_quality_alignment(self, agent):
        """Test quality alignment check."""
        evaluations = [
            {
                "question_id": "Q1",
                "concepts_identified": [],
                "overall_quality": "inadequate",  # Says inadequate
                "confidence_score": 0.9,
                "marks_awarded": 9.5,
                "max_marks": 10.0,  # But score is 95%!
            }
        ]

        flags = agent._check_quality_alignment(evaluations)

        assert len(flags) > 0
        assert "Quality rating doesn't match score percentage" in flags[0].reason

    @pytest.mark.asyncio
    async def test_calculate_consistency_score_perfect(self, agent):
        """Test consistency score calculation with no issues."""
        score = agent._calculate_consistency_score(sample_good_evaluations := [{}], 0, 0)

        assert score == 1.0

    @pytest.mark.asyncio
    async def test_calculate_consistency_score_with_issues(self, agent):
        """Test consistency score calculation with issues."""
        score = agent._calculate_consistency_score([{}], num_issues=2, num_flags=3)

        # Score should be reduced
        assert score < 1.0
        # 1.0 - (2 * 0.2) - (3 * 0.05) = 1.0 - 0.4 - 0.15 = 0.45
        assert score == pytest.approx(0.45)

    @pytest.mark.asyncio
    async def test_calculate_consistency_score_capped(self, agent):
        """Test consistency score is capped at 0."""
        score = agent._calculate_consistency_score([{}], num_issues=10, num_flags=50)

        assert score == 0.0

    @pytest.mark.asyncio
    async def test_perform_qa_check_all_passed(self, agent, sample_good_evaluations):
        """Test QA check that passes all tests."""
        result = await agent._perform_qa_check(sample_good_evaluations, {}, {})

        assert isinstance(result, QAResult)
        assert result.passed is True
        assert result.confidence_level == "high"
        assert len(result.flags) == 0
        assert len(result.issues) == 0
        assert result.consistency_score == 1.0

    @pytest.mark.asyncio
    async def test_perform_qa_check_with_flags(
        self, agent, sample_low_confidence_evaluations
    ):
        """Test QA check that raises flags."""
        result = await agent._perform_qa_check(
            sample_low_confidence_evaluations, {}, {}
        )

        assert result.requires_human_review is True
        assert len(result.flags) > 0
        assert result.confidence_level in ["medium", "low"]

    @pytest.mark.asyncio
    async def test_perform_qa_check_with_issues(
        self, agent, sample_scoring_issue_evaluations
    ):
        """Test QA check that finds issues."""
        result = await agent._perform_qa_check(sample_scoring_issue_evaluations, {}, {})

        assert result.passed is False
        assert len(result.issues) > 0

    @pytest.mark.asyncio
    async def test_perform_qa_check_recommendations(
        self, agent, sample_low_confidence_evaluations
    ):
        """Test that QA check generates recommendations."""
        result = await agent._perform_qa_check(
            sample_low_confidence_evaluations, {}, {}
        )

        assert len(result.recommendations) > 0
        assert any(
            "review" in rec.lower() or "recommend" in rec.lower()
            for rec in result.recommendations
        )

    def test_message_logging(self, agent, sample_good_evaluations):
        """Test that messages are logged to history."""
        message = AgentMessage(
            sender="test_sender",
            receiver="qa_agent",
            content={"evaluations": sample_good_evaluations},
            message_type="request",
        )

        agent.log_message(message)

        assert len(agent.message_history) == 1
        assert agent.message_history[0] == message

    @pytest.mark.asyncio
    async def test_process_handles_incomplete_data(self, agent):
        """Test that process handles incomplete evaluation data gracefully."""
        # Create evaluations with incomplete data
        incomplete_evaluations = [{"question_id": "Q1"}]  # Missing most fields

        message = AgentMessage(
            sender="test_sender",
            receiver="qa_agent",
            content={"evaluations": incomplete_evaluations},
            message_type="request",
        )

        response = await agent.process(message)

        # Should still process, just with default values
        assert response.message_type == "response"
        assert "qa_result" in response.content

    @pytest.mark.asyncio
    async def test_qa_flags_have_required_fields(self, agent, sample_low_confidence_evaluations):
        """Test that QA flags have all required fields."""
        flags = agent._check_low_confidence(sample_low_confidence_evaluations)

        for flag in flags:
            assert hasattr(flag, "question_id")
            assert hasattr(flag, "reason")
            assert hasattr(flag, "severity")
            assert hasattr(flag, "details")
            assert flag.severity in ["low", "medium", "high"]

    @pytest.mark.asyncio
    async def test_confidence_level_determination(self, agent):
        """Test confidence level is determined correctly."""
        # High confidence
        good_evaluations = [
            {
                "question_id": "Q1",
                "concepts_identified": [],
                "overall_quality": "excellent",
                "confidence_score": 0.95,
                "marks_awarded": 9.0,
                "max_marks": 10.0,
            }
        ]

        result = await agent._perform_qa_check(good_evaluations, {}, {})
        assert result.confidence_level == "high"

        # Low confidence
        bad_evaluations = [
            {
                "question_id": "Q1",
                "concepts_identified": [],
                "overall_quality": "poor",
                "confidence_score": 0.3,
                "marks_awarded": 9.0,
                "max_marks": 10.0,  # Score mismatch
            }
        ]

        result = await agent._perform_qa_check(bad_evaluations, {}, {})
        assert result.confidence_level in ["low", "medium"]

    @pytest.mark.asyncio
    async def test_multiple_flags_and_issues(self, agent):
        """Test handling multiple flags and issues."""
        complex_evaluations = [
            {
                "question_id": "Q1",
                "concepts_identified": [{"points_earned": 10.0}],
                "overall_quality": "poor",  # Quality mismatch
                "confidence_score": 0.35,  # Low confidence
                "marks_awarded": 10.0,
                "max_marks": 5.0,  # Scoring issue
            }
        ]

        result = await agent._perform_qa_check(complex_evaluations, {}, {})

        # Should have multiple flags and issues
        assert result.passed is False
        assert result.requires_human_review is True
        assert len(result.flags) > 1  # Multiple flags
        assert len(result.issues) > 0  # At least one issue
        assert len(result.recommendations) > 0
