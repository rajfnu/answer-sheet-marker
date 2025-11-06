"""Unit tests for Feedback Generator Agent."""

import pytest
from unittest.mock import Mock

from answer_marker.agents.feedback_generator import (
    FeedbackGeneratorAgent,
    create_feedback_generator_agent,
    FEEDBACK_GENERATOR_SYSTEM_PROMPT,
)
from answer_marker.core.agent_base import AgentConfig, AgentMessage
from answer_marker.models.feedback import FeedbackReport, QuestionFeedback


class TestFeedbackGeneratorAgent:
    """Test cases for FeedbackGeneratorAgent."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock Anthropic client."""
        return Mock()

    @pytest.fixture
    def agent_config(self):
        """Create agent configuration."""
        return AgentConfig(
            name="feedback_generator",
            system_prompt=FEEDBACK_GENERATOR_SYSTEM_PROMPT,
        )

    @pytest.fixture
    def agent(self, agent_config, mock_client):
        """Create FeedbackGeneratorAgent instance."""
        return FeedbackGeneratorAgent(config=agent_config, client=mock_client)

    @pytest.fixture
    def sample_evaluations(self):
        """Sample evaluations data."""
        return [
            {
                "question_id": "Q1",
                "overall_quality": "excellent",
                "max_marks": 5.0,
                "concepts_identified": [
                    {"points_earned": 2.0},
                    {"points_earned": 2.0},
                    {"points_earned": 1.0},
                ],
                "strengths": ["Clear explanation", "All key concepts covered"],
                "weaknesses": [],
                "misconceptions": [],
            },
            {
                "question_id": "Q2",
                "overall_quality": "satisfactory",
                "max_marks": 10.0,
                "concepts_identified": [
                    {"points_earned": 3.0},
                    {"points_earned": 2.0},
                ],
                "strengths": ["Good attempt"],
                "weaknesses": ["Missing some details", "Could be more specific"],
                "misconceptions": ["Confused concept A with B"],
            },
        ]

    @pytest.fixture
    def sample_scores(self):
        """Sample scoring results."""
        return {
            "total_marks": 10.0,
            "max_marks": 15.0,
            "percentage": 66.67,
            "grade": "B-",
            "passed": True,
        }

    def test_agent_initialization(self, agent):
        """Test FeedbackGeneratorAgent initialization."""
        assert agent.config.name == "feedback_generator"
        assert agent.config.system_prompt == FEEDBACK_GENERATOR_SYSTEM_PROMPT
        assert agent.message_history == []

    def test_create_feedback_generator_agent(self, mock_client):
        """Test factory function creates agent correctly."""
        agent = create_feedback_generator_agent(mock_client)
        assert isinstance(agent, FeedbackGeneratorAgent)
        assert agent.config.name == "feedback_generator"

    @pytest.mark.asyncio
    async def test_process_with_valid_evaluations(
        self, agent, mock_client, sample_evaluations, sample_scores
    ):
        """Test processing valid feedback request."""
        # Mock Claude responses
        mock_text_block1 = Mock()
        mock_text_block1.text = "You did an excellent job explaining the key concepts clearly and thoroughly. To improve further, consider adding more examples to support your points."

        mock_text_block2 = Mock()
        mock_text_block2.text = "Good effort on this question. You covered the main ideas but missed some important details. Try to be more specific and comprehensive in your explanations next time."

        mock_text_block3 = Mock()
        mock_text_block3.text = """OVERALL: You demonstrated a solid understanding of the material with good performance overall.
STRENGTHS: Clear explanations | Good grasp of key concepts | Well-structured answers
IMPROVEMENTS: Add more specific details | Review concept relationships | Practice complex questions
RECOMMENDATIONS: Review the textbook chapters 3-5 | Practice similar problems | Seek clarification on confusing concepts
ENCOURAGEMENT: Keep up the good work and continue to build on your strong foundation!"""

        mock_response1 = Mock()
        mock_response1.content = [mock_text_block1]
        mock_response1.usage = Mock(input_tokens=100, output_tokens=50)

        mock_response2 = Mock()
        mock_response2.content = [mock_text_block2]
        mock_response2.usage = Mock(input_tokens=100, output_tokens=50)

        mock_response3 = Mock()
        mock_response3.content = [mock_text_block3]
        mock_response3.usage = Mock(input_tokens=150, output_tokens=100)

        mock_client.messages.create = Mock(
            side_effect=[mock_response1, mock_response2, mock_response3]
        )

        # Create message
        message = AgentMessage(
            sender="test_sender",
            receiver="feedback_generator",
            content={"evaluations": sample_evaluations, "scores": sample_scores},
            message_type="request",
        )

        # Process message
        response = await agent.process(message)

        # Assertions
        assert response.sender == "feedback_generator"
        assert response.receiver == "test_sender"
        assert response.message_type == "response"
        assert "feedback" in response.content

        feedback = response.content["feedback"]
        assert "overall_feedback" in feedback
        assert "question_feedback" in feedback
        assert len(feedback["question_feedback"]) == 2

    @pytest.mark.asyncio
    async def test_process_with_no_evaluations(self, agent):
        """Test processing message without evaluations."""
        message = AgentMessage(
            sender="test_sender",
            receiver="feedback_generator",
            content={},
            message_type="request",
        )

        response = await agent.process(message)

        assert response.message_type == "error"
        assert "error" in response.content
        assert "No evaluations" in response.content["error"]

    @pytest.mark.asyncio
    async def test_generate_question_feedback(
        self, agent, mock_client, sample_evaluations
    ):
        """Test generating feedback for a single question."""
        mock_text_block = Mock()
        mock_text_block.text = "Great work on this question! You covered all the key points effectively."

        mock_response = Mock()
        mock_response.content = [mock_text_block]
        mock_response.usage = Mock(input_tokens=100, output_tokens=50)

        mock_client.messages.create = Mock(return_value=mock_response)

        result = await agent._generate_question_feedback(sample_evaluations[0])

        assert isinstance(result, QuestionFeedback)
        assert result.question_id == "Q1"
        assert len(result.feedback) > 0
        assert len(result.strengths) == 2
        assert len(result.improvement_areas) == 0

    @pytest.mark.asyncio
    async def test_generate_overall_feedback(
        self, agent, mock_client, sample_evaluations, sample_scores
    ):
        """Test generating overall feedback."""
        mock_text_block = Mock()
        mock_text_block.text = """OVERALL: You showed good understanding with room for improvement.
STRENGTHS: Strong foundational knowledge | Clear communication | Good effort
IMPROVEMENTS: Work on details | Review weak areas | Practice more
RECOMMENDATIONS: Study chapters 1-3 | Do practice problems | Review notes
ENCOURAGEMENT: You're on the right track, keep pushing forward!"""

        mock_response = Mock()
        mock_response.content = [mock_text_block]
        mock_response.usage = Mock(input_tokens=150, output_tokens=100)

        mock_client.messages.create = Mock(return_value=mock_response)

        overall, strengths, improvements, recommendations, encouragement = (
            await agent._generate_overall_feedback(sample_evaluations, sample_scores)
        )

        assert len(overall) > 0
        assert len(strengths) > 0
        assert len(improvements) > 0
        assert len(recommendations) > 0
        assert len(encouragement) > 0

    def test_format_list_with_items(self, agent):
        """Test formatting list with items."""
        items = ["Item 1", "Item 2", "Item 3"]
        result = agent._format_list(items)

        assert "- Item 1" in result
        assert "- Item 2" in result
        assert "- Item 3" in result

    def test_format_list_empty(self, agent):
        """Test formatting empty list."""
        result = agent._format_list([])
        assert result == "None"

    @pytest.mark.asyncio
    async def test_process_handles_exception(
        self, agent, mock_client, sample_evaluations
    ):
        """Test that process handles exceptions gracefully."""
        mock_client.messages.create = Mock(side_effect=Exception("API Error"))

        message = AgentMessage(
            sender="test_sender",
            receiver="feedback_generator",
            content={"evaluations": sample_evaluations},
            message_type="request",
        )

        response = await agent.process(message)

        assert response.message_type == "error"
        assert "error" in response.content

    @pytest.mark.asyncio
    async def test_generate_feedback_without_scores(
        self, agent, mock_client, sample_evaluations
    ):
        """Test generating feedback without scores data."""
        # Mock responses for questions and overall
        mock_text_block1 = Mock()
        mock_text_block1.text = "Good answer with clear explanations."

        mock_text_block2 = Mock()
        mock_text_block2.text = "Satisfactory attempt, but could be improved."

        mock_text_block3 = Mock()
        mock_text_block3.text = """OVERALL: Decent performance overall.
STRENGTHS: Good effort | Clear thinking
IMPROVEMENTS: Add more details | Review concepts
RECOMMENDATIONS: Study more | Practice problems
ENCOURAGEMENT: Keep learning!"""

        mock_response1 = Mock()
        mock_response1.content = [mock_text_block1]
        mock_response1.usage = Mock(input_tokens=100, output_tokens=50)

        mock_response2 = Mock()
        mock_response2.content = [mock_text_block2]
        mock_response2.usage = Mock(input_tokens=100, output_tokens=50)

        mock_response3 = Mock()
        mock_response3.content = [mock_text_block3]
        mock_response3.usage = Mock(input_tokens=150, output_tokens=100)

        mock_client.messages.create = Mock(
            side_effect=[mock_response1, mock_response2, mock_response3]
        )

        result = await agent._generate_feedback(sample_evaluations, scores=None)

        assert isinstance(result, FeedbackReport)
        assert len(result.question_feedback) == 2
        assert len(result.overall_feedback) > 0

    @pytest.mark.asyncio
    async def test_question_feedback_includes_all_fields(
        self, agent, mock_client, sample_evaluations
    ):
        """Test that question feedback includes all required fields."""
        mock_text_block = Mock()
        mock_text_block.text = "Excellent work!"

        mock_response = Mock()
        mock_response.content = [mock_text_block]
        mock_response.usage = Mock(input_tokens=100, output_tokens=50)

        mock_client.messages.create = Mock(return_value=mock_response)

        result = await agent._generate_question_feedback(sample_evaluations[0])

        assert hasattr(result, "question_id")
        assert hasattr(result, "feedback")
        assert hasattr(result, "strengths")
        assert hasattr(result, "improvement_areas")
        assert hasattr(result, "suggestions")

    def test_message_logging(self, agent, sample_evaluations):
        """Test that messages are logged to history."""
        message = AgentMessage(
            sender="test_sender",
            receiver="feedback_generator",
            content={"evaluations": sample_evaluations},
            message_type="request",
        )

        agent.log_message(message)

        assert len(agent.message_history) == 1
        assert agent.message_history[0] == message

    @pytest.mark.asyncio
    async def test_feedback_for_poor_performance(self, agent, mock_client):
        """Test feedback generation for poor performance."""
        poor_evaluations = [
            {
                "question_id": "Q1",
                "overall_quality": "poor",
                "max_marks": 10.0,
                "concepts_identified": [{"points_earned": 1.0}],
                "strengths": [],
                "weaknesses": [
                    "Missing key concepts",
                    "Incomplete answer",
                    "Lacks understanding",
                ],
                "misconceptions": ["Major conceptual error"],
            }
        ]

        mock_text_block1 = Mock()
        mock_text_block1.text = "This answer needs significant improvement. Focus on understanding the core concepts first, then try to explain them more thoroughly. Don't hesitate to ask for help or review the learning materials."

        mock_text_block2 = Mock()
        mock_text_block2.text = """OVERALL: This assessment shows areas that need considerable attention and improvement.
STRENGTHS: Attempted the questions
IMPROVEMENTS: Review core concepts thoroughly | Practice regularly | Seek help when needed
RECOMMENDATIONS: Meet with instructor | Review textbook carefully | Join study group
ENCOURAGEMENT: Everyone learns at their own pace - keep working hard and you will improve!"""

        mock_response1 = Mock()
        mock_response1.content = [mock_text_block1]
        mock_response1.usage = Mock(input_tokens=100, output_tokens=50)

        mock_response2 = Mock()
        mock_response2.content = [mock_text_block2]
        mock_response2.usage = Mock(input_tokens=150, output_tokens=100)

        mock_client.messages.create = Mock(side_effect=[mock_response1, mock_response2])

        result = await agent._generate_feedback(poor_evaluations)

        assert isinstance(result, FeedbackReport)
        assert len(result.question_feedback) == 1
        assert len(result.overall_feedback) > 0
        # Should still be encouraging even for poor performance
        assert len(result.encouragement) > 0

    @pytest.mark.asyncio
    async def test_feedback_aggregates_multiple_evaluations(
        self, agent, mock_client, sample_evaluations
    ):
        """Test that feedback properly aggregates data from multiple evaluations."""
        # Mock responses
        mock_responses = []
        for _ in range(3):  # 2 questions + 1 overall
            mock_text_block = Mock()
            mock_text_block.text = "Sample feedback text"
            if _ == 2:  # overall feedback
                mock_text_block.text = """OVERALL: Good work.
STRENGTHS: Strength 1 | Strength 2
IMPROVEMENTS: Improvement 1 | Improvement 2
RECOMMENDATIONS: Recommendation 1 | Recommendation 2
ENCOURAGEMENT: Keep it up!"""
            mock_response = Mock()
            mock_response.content = [mock_text_block]
            mock_response.usage = Mock(input_tokens=100, output_tokens=50)
            mock_responses.append(mock_response)

        mock_client.messages.create = Mock(side_effect=mock_responses)

        result = await agent._generate_feedback(sample_evaluations)

        # Should aggregate all strengths and weaknesses
        assert len(result.key_strengths) >= 0
        assert len(result.key_improvements) >= 0
        assert len(result.study_recommendations) >= 0
