"""Unit tests for Answer Evaluator Agent."""

import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime, timezone

from answer_marker.agents.answer_evaluator import (
    AnswerEvaluatorAgent,
    create_answer_evaluator_agent,
    ANSWER_EVALUATOR_SYSTEM_PROMPT,
)
from answer_marker.core.agent_base import AgentConfig, AgentMessage
from answer_marker.models.evaluation import ConceptEvaluation, AnswerEvaluation


class TestAnswerEvaluatorAgent:
    """Test cases for AnswerEvaluatorAgent."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock Anthropic client."""
        return Mock()

    @pytest.fixture
    def agent_config(self):
        """Create agent configuration."""
        return AgentConfig(
            name="answer_evaluator",
            system_prompt=ANSWER_EVALUATOR_SYSTEM_PROMPT,
        )

    @pytest.fixture
    def agent(self, agent_config, mock_client):
        """Create AnswerEvaluatorAgent instance."""
        return AnswerEvaluatorAgent(config=agent_config, client=mock_client)

    @pytest.fixture
    def sample_question(self):
        """Sample analyzed question data."""
        return {
            "id": "Q1",
            "question_text": "What is photosynthesis?",
            "question_type": "short_answer",
            "max_marks": 5.0,
            "key_concepts": [
                {
                    "concept": "Light energy conversion",
                    "points": 2.0,
                    "mandatory": True,
                    "keywords": ["light", "energy", "conversion"],
                },
                {
                    "concept": "Chlorophyll role",
                    "points": 2.0,
                    "mandatory": True,
                    "keywords": ["chlorophyll", "green"],
                },
                {
                    "concept": "Glucose production",
                    "points": 1.0,
                    "mandatory": False,
                    "keywords": ["glucose", "sugar"],
                },
            ],
            "evaluation_criteria": {
                "excellent": "All key concepts present with detailed explanation",
                "good": "Most key concepts present",
                "satisfactory": "Some key concepts present",
                "poor": "Few or no key concepts present",
            },
            "keywords": ["photosynthesis", "light", "chlorophyll", "glucose"],
        }

    @pytest.fixture
    def sample_student_answer(self):
        """Sample student answer."""
        return "Photosynthesis is the process where plants use sunlight to convert carbon dioxide and water into glucose. Chlorophyll in the leaves captures light energy."

    def test_agent_initialization(self, agent, agent_config):
        """Test AnswerEvaluatorAgent initialization."""
        assert agent.config.name == "answer_evaluator"
        assert agent.config.system_prompt == ANSWER_EVALUATOR_SYSTEM_PROMPT
        assert agent.message_history == []

    def test_create_answer_evaluator_agent(self, mock_client):
        """Test factory function creates agent correctly."""
        agent = create_answer_evaluator_agent(mock_client)
        assert isinstance(agent, AnswerEvaluatorAgent)
        assert agent.config.name == "answer_evaluator"
        assert agent.config.system_prompt == ANSWER_EVALUATOR_SYSTEM_PROMPT

    @pytest.mark.asyncio
    async def test_process_with_valid_input(
        self, agent, mock_client, sample_question, sample_student_answer
    ):
        """Test processing valid evaluation request."""
        # Mock Claude response
        mock_block = Mock()
        mock_block.type = "tool_use"
        mock_block.input = {
            "concepts_identified": [
                {
                    "concept": "Light energy conversion",
                    "present": True,
                    "accuracy": "fully_correct",
                    "evidence": "use sunlight to convert",
                    "points_earned": 2.0,
                    "points_possible": 2.0,
                },
                {
                    "concept": "Chlorophyll role",
                    "present": True,
                    "accuracy": "fully_correct",
                    "evidence": "Chlorophyll in the leaves captures light energy",
                    "points_earned": 2.0,
                    "points_possible": 2.0,
                },
                {
                    "concept": "Glucose production",
                    "present": True,
                    "accuracy": "fully_correct",
                    "evidence": "into glucose",
                    "points_earned": 1.0,
                    "points_possible": 1.0,
                },
            ],
            "overall_quality": "excellent",
            "strengths": ["Clear explanation", "All key concepts covered"],
            "weaknesses": [],
            "misconceptions": [],
            "confidence_score": 0.95,
            "requires_human_review": False,
        }

        mock_response = Mock()
        mock_response.content = [mock_block]
        mock_response.usage = Mock(input_tokens=150, output_tokens=250)

        mock_client.messages.create = Mock(return_value=mock_response)

        # Create message
        message = AgentMessage(
            sender="test_sender",
            receiver="answer_evaluator",
            content={"question": sample_question, "student_answer": sample_student_answer},
            message_type="request",
        )

        # Process message
        response = await agent.process(message)

        # Assertions
        assert response.sender == "answer_evaluator"
        assert response.receiver == "test_sender"
        assert response.message_type == "response"
        assert "evaluation" in response.content

        evaluation = response.content["evaluation"]
        assert evaluation["question_id"] == "Q1"
        assert evaluation["marks_awarded"] == 5.0
        assert evaluation["max_marks"] == 5.0
        assert evaluation["confidence_score"] == 0.95
        assert len(evaluation["concepts_identified"]) == 3

    @pytest.mark.asyncio
    async def test_process_with_no_question(self, agent):
        """Test processing message without question."""
        message = AgentMessage(
            sender="test_sender",
            receiver="answer_evaluator",
            content={"student_answer": "Some answer"},
            message_type="request",
        )

        response = await agent.process(message)

        assert response.message_type == "error"
        assert "error" in response.content
        assert "No question" in response.content["error"]

    @pytest.mark.asyncio
    async def test_process_with_no_student_answer(self, agent, sample_question):
        """Test processing message without student answer."""
        message = AgentMessage(
            sender="test_sender",
            receiver="answer_evaluator",
            content={"question": sample_question},
            message_type="request",
        )

        response = await agent.process(message)

        assert response.message_type == "error"
        assert "error" in response.content
        assert "No student_answer" in response.content["error"]

    @pytest.mark.asyncio
    async def test_evaluate_answer_partially_correct(
        self, agent, mock_client, sample_question
    ):
        """Test evaluating partially correct answer."""
        partial_answer = "Plants use sunlight to make food. Chlorophyll is important."

        mock_block = Mock()
        mock_block.type = "tool_use"
        mock_block.input = {
            "concepts_identified": [
                {
                    "concept": "Light energy conversion",
                    "present": True,
                    "accuracy": "partially_correct",
                    "evidence": "use sunlight to make food",
                    "points_earned": 1.0,
                    "points_possible": 2.0,
                },
                {
                    "concept": "Chlorophyll role",
                    "present": True,
                    "accuracy": "partially_correct",
                    "evidence": "Chlorophyll is important",
                    "points_earned": 1.0,
                    "points_possible": 2.0,
                },
                {
                    "concept": "Glucose production",
                    "present": False,
                    "accuracy": "not_present",
                    "evidence": "",
                    "points_earned": 0.0,
                    "points_possible": 1.0,
                },
            ],
            "overall_quality": "satisfactory",
            "strengths": ["Mentions key terms"],
            "weaknesses": ["Lacks detail", "Misses glucose production"],
            "misconceptions": [],
            "confidence_score": 0.85,
            "requires_human_review": False,
        }

        mock_response = Mock()
        mock_response.content = [mock_block]
        mock_response.usage = Mock(input_tokens=150, output_tokens=250)

        mock_client.messages.create = Mock(return_value=mock_response)

        result = await agent._evaluate_answer(sample_question, partial_answer)

        assert isinstance(result, AnswerEvaluation)
        assert result.question_id == "Q1"
        assert result.marks_awarded == 2.0
        assert result.max_marks == 5.0
        assert result.overall_quality == "satisfactory"
        assert result.confidence_score == 0.85
        assert len(result.concepts_identified) == 3

    @pytest.mark.asyncio
    async def test_evaluate_answer_poor_quality(self, agent, mock_client, sample_question):
        """Test evaluating poor quality answer."""
        poor_answer = "It's about plants."

        mock_block = Mock()
        mock_block.type = "tool_use"
        mock_block.input = {
            "concepts_identified": [
                {
                    "concept": "Light energy conversion",
                    "present": False,
                    "accuracy": "not_present",
                    "evidence": "",
                    "points_earned": 0.0,
                    "points_possible": 2.0,
                },
                {
                    "concept": "Chlorophyll role",
                    "present": False,
                    "accuracy": "not_present",
                    "evidence": "",
                    "points_earned": 0.0,
                    "points_possible": 2.0,
                },
                {
                    "concept": "Glucose production",
                    "present": False,
                    "accuracy": "not_present",
                    "evidence": "",
                    "points_earned": 0.0,
                    "points_possible": 1.0,
                },
            ],
            "overall_quality": "poor",
            "strengths": [],
            "weaknesses": ["Too brief", "No key concepts present"],
            "misconceptions": [],
            "confidence_score": 0.95,
            "requires_human_review": False,
        }

        mock_response = Mock()
        mock_response.content = [mock_block]
        mock_response.usage = Mock(input_tokens=100, output_tokens=200)

        mock_client.messages.create = Mock(return_value=mock_response)

        result = await agent._evaluate_answer(sample_question, poor_answer)

        assert result.marks_awarded == 0.0
        assert result.overall_quality == "poor"
        assert all(not c.present for c in result.concepts_identified)

    @pytest.mark.asyncio
    async def test_evaluate_answer_with_misconceptions(
        self, agent, mock_client, sample_question
    ):
        """Test evaluating answer with misconceptions."""
        wrong_answer = "Photosynthesis is when plants breathe in oxygen and release carbon dioxide."

        mock_block = Mock()
        mock_block.type = "tool_use"
        mock_block.input = {
            "concepts_identified": [
                {
                    "concept": "Light energy conversion",
                    "present": False,
                    "accuracy": "not_present",
                    "evidence": "",
                    "points_earned": 0.0,
                    "points_possible": 2.0,
                },
                {
                    "concept": "Chlorophyll role",
                    "present": False,
                    "accuracy": "not_present",
                    "evidence": "",
                    "points_earned": 0.0,
                    "points_possible": 2.0,
                },
                {
                    "concept": "Glucose production",
                    "present": False,
                    "accuracy": "not_present",
                    "evidence": "",
                    "points_earned": 0.0,
                    "points_possible": 1.0,
                },
            ],
            "overall_quality": "inadequate",
            "strengths": [],
            "weaknesses": ["Completely incorrect explanation"],
            "misconceptions": ["Confuses photosynthesis with respiration"],
            "confidence_score": 0.98,
            "requires_human_review": False,
        }

        mock_response = Mock()
        mock_response.content = [mock_block]
        mock_response.usage = Mock(input_tokens=120, output_tokens=220)

        mock_client.messages.create = Mock(return_value=mock_response)

        result = await agent._evaluate_answer(sample_question, wrong_answer)

        assert result.marks_awarded == 0.0
        assert result.overall_quality == "inadequate"
        assert len(result.misconceptions) > 0
        assert "Confuses photosynthesis with respiration" in result.misconceptions

    @pytest.mark.asyncio
    async def test_evaluate_answer_requires_human_review(
        self, agent, mock_client, sample_question
    ):
        """Test evaluation flagging for human review."""
        ambiguous_answer = "The process involves light and some chemicals."

        mock_block = Mock()
        mock_block.type = "tool_use"
        mock_block.input = {
            "concepts_identified": [
                {
                    "concept": "Light energy conversion",
                    "present": True,
                    "accuracy": "partially_correct",
                    "evidence": "involves light",
                    "points_earned": 0.5,
                    "points_possible": 2.0,
                },
                {
                    "concept": "Chlorophyll role",
                    "present": False,
                    "accuracy": "not_present",
                    "evidence": "",
                    "points_earned": 0.0,
                    "points_possible": 2.0,
                },
                {
                    "concept": "Glucose production",
                    "present": False,
                    "accuracy": "not_present",
                    "evidence": "",
                    "points_earned": 0.0,
                    "points_possible": 1.0,
                },
            ],
            "overall_quality": "poor",
            "strengths": ["Mentions light"],
            "weaknesses": ["Too vague", "Lacks specificity"],
            "misconceptions": [],
            "confidence_score": 0.45,
            "requires_human_review": True,
            "review_reason": "Low confidence due to ambiguous answer",
        }

        mock_response = Mock()
        mock_response.content = [mock_block]
        mock_response.usage = Mock(input_tokens=110, output_tokens=210)

        mock_client.messages.create = Mock(return_value=mock_response)

        result = await agent._evaluate_answer(sample_question, ambiguous_answer)

        assert result.requires_human_review is True
        assert result.review_reason is not None
        assert result.confidence_score < 0.5

    @pytest.mark.asyncio
    async def test_evaluate_answer_no_tool_use(self, agent, mock_client, sample_question):
        """Test handling when Claude doesn't return tool use."""
        mock_block = Mock()
        mock_block.type = "text"
        mock_block.text = "Some text response"

        mock_response = Mock()
        mock_response.content = [mock_block]
        mock_response.usage = Mock(input_tokens=100, output_tokens=150)

        mock_client.messages.create = Mock(return_value=mock_response)

        with pytest.raises(ValueError, match="Claude did not return structured output"):
            await agent._evaluate_answer(sample_question, "Some answer")

    def test_format_key_concepts_with_concepts(self, agent):
        """Test formatting key concepts."""
        concepts = [
            {
                "concept": "Concept A",
                "points": 3.0,
                "mandatory": True,
                "keywords": ["key1", "key2"],
            },
            {
                "concept": "Concept B",
                "points": 2.0,
                "mandatory": False,
                "keywords": ["key3"],
            },
        ]

        result = agent._format_key_concepts(concepts)

        assert "Concept A" in result
        assert "3.0 marks" in result
        assert "MANDATORY" in result
        assert "Concept B" in result
        assert "2.0 marks" in result
        assert "Optional" in result
        assert "key1, key2" in result

    def test_format_key_concepts_empty(self, agent):
        """Test formatting empty key concepts."""
        result = agent._format_key_concepts([])
        assert result == "No key concepts specified"

    def test_format_key_concepts_no_keywords(self, agent):
        """Test formatting concepts without keywords."""
        concepts = [
            {"concept": "Concept A", "points": 3.0, "mandatory": True, "keywords": []}
        ]

        result = agent._format_key_concepts(concepts)

        assert "Concept A" in result
        assert "MANDATORY" in result
        assert "Keywords:" not in result

    def test_message_logging(self, agent, sample_question, sample_student_answer):
        """Test that messages are logged to history."""
        message = AgentMessage(
            sender="test_sender",
            receiver="answer_evaluator",
            content={"question": sample_question, "student_answer": sample_student_answer},
            message_type="request",
        )

        agent.log_message(message)

        assert len(agent.message_history) == 1
        assert agent.message_history[0] == message

    @pytest.mark.asyncio
    async def test_process_handles_exception(
        self, agent, mock_client, sample_question, sample_student_answer
    ):
        """Test that process handles exceptions gracefully."""
        mock_client.messages.create = Mock(side_effect=Exception("API Error"))

        message = AgentMessage(
            sender="test_sender",
            receiver="answer_evaluator",
            content={"question": sample_question, "student_answer": sample_student_answer},
            message_type="request",
        )

        response = await agent.process(message)

        assert response.message_type == "error"
        assert "error" in response.content
        assert "API Error" in response.content["error"]
