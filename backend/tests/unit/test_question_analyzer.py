"""Unit tests for Question Analyzer Agent."""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock
from datetime import datetime, timezone

from answer_marker.agents.question_analyzer import (
    QuestionAnalyzerAgent,
    create_question_analyzer_agent,
    QUESTION_ANALYZER_SYSTEM_PROMPT,
)
from answer_marker.core.agent_base import AgentConfig, AgentMessage
from answer_marker.models.question import (
    AnalyzedQuestion,
    QuestionType,
    KeyConcept,
    EvaluationCriteria,
)


class TestQuestionAnalyzerAgent:
    """Test cases for QuestionAnalyzerAgent."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock Anthropic client."""
        return Mock()

    @pytest.fixture
    def agent_config(self):
        """Create agent configuration."""
        return AgentConfig(
            name="question_analyzer",
            system_prompt=QUESTION_ANALYZER_SYSTEM_PROMPT,
        )

    @pytest.fixture
    def agent(self, agent_config, mock_client):
        """Create QuestionAnalyzerAgent instance."""
        return QuestionAnalyzerAgent(config=agent_config, client=mock_client)

    @pytest.fixture
    def sample_question(self):
        """Sample question data."""
        return {
            "id": "Q1",
            "question_text": "What is photosynthesis?",
            "marks": 5.0,
            "marking_scheme": "Process by which plants convert light to energy. Award 2 marks for mentioning chlorophyll, 2 marks for light energy conversion, 1 mark for glucose production.",
            "sample_answer": "Photosynthesis is the process by which green plants use sunlight, water, and carbon dioxide to produce glucose and oxygen using chlorophyll.",
        }

    @pytest.fixture
    def sample_marking_guide(self, sample_question):
        """Sample marking guide data."""
        return {
            "questions": [sample_question],
            "total_marks": 5.0,
        }

    def test_agent_initialization(self, agent, agent_config):
        """Test QuestionAnalyzerAgent initialization."""
        assert agent.config.name == "question_analyzer"
        assert agent.config.system_prompt == QUESTION_ANALYZER_SYSTEM_PROMPT
        assert agent.message_history == []

    def test_create_question_analyzer_agent(self, mock_client):
        """Test factory function creates agent correctly."""
        agent = create_question_analyzer_agent(mock_client)
        assert isinstance(agent, QuestionAnalyzerAgent)
        assert agent.config.name == "question_analyzer"
        assert agent.config.system_prompt == QUESTION_ANALYZER_SYSTEM_PROMPT

    @pytest.mark.asyncio
    async def test_process_with_valid_marking_guide(
        self, agent, mock_client, sample_marking_guide
    ):
        """Test processing valid marking guide."""
        # Mock Claude response
        mock_block = Mock()
        mock_block.type = "tool_use"
        mock_block.input = {
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
                    "keywords": ["chlorophyll", "green", "pigment"],
                },
                {
                    "concept": "Glucose production",
                    "points": 1.0,
                    "mandatory": False,
                    "keywords": ["glucose", "sugar", "production"],
                },
            ],
            "evaluation_criteria": {
                "excellent": "All key concepts present with detailed explanation",
                "good": "Most key concepts present with adequate explanation",
                "satisfactory": "Some key concepts present",
                "poor": "Few or no key concepts present",
            },
            "keywords": ["photosynthesis", "light", "chlorophyll", "glucose"],
            "common_mistakes": ["Confusing respiration with photosynthesis"],
        }

        mock_response = Mock()
        mock_response.content = [mock_block]
        mock_response.usage = Mock(input_tokens=100, output_tokens=200)

        mock_client.messages.create = Mock(return_value=mock_response)

        # Create message
        message = AgentMessage(
            sender="test_sender",
            receiver="question_analyzer",
            content={"marking_guide": sample_marking_guide},
            message_type="request",
        )

        # Process message
        response = await agent.process(message)

        # Assertions
        assert response.sender == "question_analyzer"
        assert response.receiver == "test_sender"
        assert response.message_type == "response"
        assert "analyzed_questions" in response.content
        assert "Q1" in response.content["analyzed_questions"]

        analyzed = response.content["analyzed_questions"]["Q1"]
        assert analyzed["id"] == "Q1"
        assert analyzed["question_type"] == "short_answer"
        assert analyzed["max_marks"] == 5.0
        assert len(analyzed["key_concepts"]) == 3

    @pytest.mark.asyncio
    async def test_process_with_no_marking_guide(self, agent):
        """Test processing message without marking_guide."""
        message = AgentMessage(
            sender="test_sender",
            receiver="question_analyzer",
            content={},
            message_type="request",
        )

        response = await agent.process(message)

        assert response.message_type == "error"
        assert "error" in response.content
        assert "No marking_guide" in response.content["error"]

    @pytest.mark.asyncio
    async def test_process_with_empty_questions(self, agent):
        """Test processing marking guide with no questions."""
        message = AgentMessage(
            sender="test_sender",
            receiver="question_analyzer",
            content={"marking_guide": {"questions": []}},
            message_type="request",
        )

        response = await agent.process(message)

        assert response.message_type == "response"
        assert response.content["analyzed_questions"] == {}

    @pytest.mark.asyncio
    async def test_process_with_multiple_questions(self, agent, mock_client):
        """Test processing multiple questions."""
        marking_guide = {
            "questions": [
                {
                    "id": "Q1",
                    "question_text": "Question 1?",
                    "marks": 5.0,
                },
                {
                    "id": "Q2",
                    "question_text": "Question 2?",
                    "marks": 10.0,
                },
            ]
        }

        # Mock responses for two questions
        def create_mock_block(q_id, marks):
            mock_block = Mock()
            mock_block.type = "tool_use"
            mock_block.input = {
                "id": q_id,
                "question_text": f"Question {q_id[-1]}?",
                "question_type": "short_answer",
                "max_marks": marks,
                "key_concepts": [
                    {"concept": "Test concept", "points": marks, "mandatory": True}
                ],
                "evaluation_criteria": {
                    "excellent": "Excellent",
                    "good": "Good",
                    "satisfactory": "Satisfactory",
                    "poor": "Poor",
                },
                "keywords": ["test"],
                "common_mistakes": [],
            }
            return mock_block

        mock_response_1 = Mock()
        mock_response_1.content = [create_mock_block("Q1", 5.0)]
        mock_response_1.usage = Mock(input_tokens=100, output_tokens=200)

        mock_response_2 = Mock()
        mock_response_2.content = [create_mock_block("Q2", 10.0)]
        mock_response_2.usage = Mock(input_tokens=100, output_tokens=200)

        mock_client.messages.create = Mock(side_effect=[mock_response_1, mock_response_2])

        message = AgentMessage(
            sender="test_sender",
            receiver="question_analyzer",
            content={"marking_guide": marking_guide},
            message_type="request",
        )

        response = await agent.process(message)

        assert response.message_type == "response"
        assert len(response.content["analyzed_questions"]) == 2
        assert "Q1" in response.content["analyzed_questions"]
        assert "Q2" in response.content["analyzed_questions"]

    @pytest.mark.asyncio
    async def test_analyze_single_question_mcq(self, agent, mock_client):
        """Test analyzing MCQ question."""
        question = {
            "id": "Q1",
            "question_text": "What is 2 + 2?\nA) 3\nB) 4\nC) 5\nD) 6",
            "marks": 1.0,
            "marking_scheme": "Answer: B",
        }

        mock_block = Mock()
        mock_block.type = "tool_use"
        mock_block.input = {
            "id": "Q1",
            "question_text": question["question_text"],
            "question_type": "mcq",
            "max_marks": 1.0,
            "key_concepts": [{"concept": "Correct answer is B", "points": 1.0, "mandatory": True}],
            "evaluation_criteria": {
                "excellent": "Selected B",
                "good": "Selected B",
                "satisfactory": "Selected B",
                "poor": "Selected any other option",
            },
        }

        mock_response = Mock()
        mock_response.content = [mock_block]
        mock_response.usage = Mock(input_tokens=50, output_tokens=100)

        mock_client.messages.create = Mock(return_value=mock_response)

        result = await agent._analyze_single_question(question)

        assert isinstance(result, AnalyzedQuestion)
        assert result.id == "Q1"
        assert result.question_type == QuestionType.MCQ
        assert result.max_marks == 1.0
        assert len(result.key_concepts) == 1

    @pytest.mark.asyncio
    async def test_analyze_single_question_essay(self, agent, mock_client):
        """Test analyzing essay question."""
        question = {
            "id": "Q1",
            "question_text": "Discuss the causes of World War I.",
            "marks": 20.0,
            "marking_scheme": "Award marks for: nationalism (5), alliances (5), militarism (5), imperialism (5)",
        }

        mock_block = Mock()
        mock_block.type = "tool_use"
        mock_block.input = {
            "id": "Q1",
            "question_text": question["question_text"],
            "question_type": "essay",
            "max_marks": 20.0,
            "key_concepts": [
                {"concept": "Nationalism", "points": 5.0, "mandatory": True},
                {"concept": "Alliances", "points": 5.0, "mandatory": True},
                {"concept": "Militarism", "points": 5.0, "mandatory": True},
                {"concept": "Imperialism", "points": 5.0, "mandatory": True},
            ],
            "evaluation_criteria": {
                "excellent": "All four causes discussed with examples",
                "good": "Three or four causes discussed",
                "satisfactory": "Two causes discussed",
                "poor": "One or no causes discussed",
            },
        }

        mock_response = Mock()
        mock_response.content = [mock_block]
        mock_response.usage = Mock(input_tokens=150, output_tokens=250)

        mock_client.messages.create = Mock(return_value=mock_response)

        result = await agent._analyze_single_question(question)

        assert isinstance(result, AnalyzedQuestion)
        assert result.question_type == QuestionType.ESSAY
        assert result.max_marks == 20.0
        assert len(result.key_concepts) == 4
        assert all(isinstance(kc, KeyConcept) for kc in result.key_concepts)

    @pytest.mark.asyncio
    async def test_analyze_single_question_no_tool_use(self, agent, mock_client):
        """Test handling when Claude doesn't return tool use."""
        question = {"id": "Q1", "question_text": "Test?", "marks": 5.0}

        mock_block = Mock()
        mock_block.type = "text"
        mock_block.text = "Some text response"

        mock_response = Mock()
        mock_response.content = [mock_block]
        mock_response.usage = Mock(input_tokens=50, output_tokens=100)

        mock_client.messages.create = Mock(return_value=mock_response)

        with pytest.raises(ValueError, match="Claude did not return structured output"):
            await agent._analyze_single_question(question)

    @pytest.mark.asyncio
    async def test_analyze_question_with_all_fields(self, agent, mock_client):
        """Test analyzing question with all optional fields."""
        question = {
            "id": "Q1",
            "question_text": "Explain Newton's First Law.",
            "marks": 5.0,
            "marking_scheme": "Law of inertia: 2 marks. Example: 2 marks. Explanation: 1 mark.",
            "sample_answer": "An object at rest stays at rest, and an object in motion stays in motion unless acted upon by an external force.",
        }

        mock_block = Mock()
        mock_block.type = "tool_use"
        mock_block.input = {
            "id": "Q1",
            "question_text": question["question_text"],
            "question_type": "short_answer",
            "max_marks": 5.0,
            "key_concepts": [
                {
                    "concept": "Law of inertia",
                    "points": 2.0,
                    "mandatory": True,
                    "keywords": ["inertia", "rest", "motion"],
                }
            ],
            "evaluation_criteria": {
                "excellent": "Complete explanation with example",
                "good": "Good explanation",
                "satisfactory": "Basic understanding",
                "poor": "Minimal understanding",
            },
            "keywords": ["newton", "inertia", "force"],
            "common_mistakes": ["Confusing with second law"],
        }

        mock_response = Mock()
        mock_response.content = [mock_block]
        mock_response.usage = Mock(input_tokens=100, output_tokens=200)

        mock_client.messages.create = Mock(return_value=mock_response)

        result = await agent._analyze_single_question(question)

        assert result.keywords == ["newton", "inertia", "force"]
        assert result.common_mistakes == ["Confusing with second law"]

    @pytest.mark.asyncio
    async def test_process_handles_question_analysis_error(self, agent, mock_client):
        """Test that process continues when one question fails."""
        marking_guide = {
            "questions": [
                {"id": "Q1", "question_text": "Question 1?", "marks": 5.0},
                {"id": "Q2", "question_text": "Question 2?", "marks": 10.0},
            ]
        }

        # First call raises error, second succeeds
        mock_block = Mock()
        mock_block.type = "tool_use"
        mock_block.input = {
            "id": "Q2",
            "question_text": "Question 2?",
            "question_type": "short_answer",
            "max_marks": 10.0,
            "key_concepts": [{"concept": "Test", "points": 10.0}],
            "evaluation_criteria": {
                "excellent": "Excellent",
                "good": "Good",
                "satisfactory": "Satisfactory",
                "poor": "Poor",
            },
        }

        mock_response = Mock()
        mock_response.content = [mock_block]
        mock_response.usage = Mock(input_tokens=100, output_tokens=200)

        mock_client.messages.create = Mock(
            side_effect=[Exception("API Error"), mock_response]
        )

        message = AgentMessage(
            sender="test_sender",
            receiver="question_analyzer",
            content={"marking_guide": marking_guide},
            message_type="request",
        )

        response = await agent.process(message)

        # Should only have Q2 (Q1 failed)
        assert response.message_type == "response"
        assert len(response.content["analyzed_questions"]) == 1
        assert "Q2" in response.content["analyzed_questions"]
        assert "Q1" not in response.content["analyzed_questions"]

    def test_message_logging(self, agent, sample_marking_guide):
        """Test that messages are logged to history."""
        message = AgentMessage(
            sender="test_sender",
            receiver="question_analyzer",
            content={"marking_guide": sample_marking_guide},
            message_type="request",
        )

        agent.log_message(message)

        assert len(agent.message_history) == 1
        assert agent.message_history[0] == message

    def test_get_message_history(self, agent):
        """Test getting message history."""
        message1 = AgentMessage(
            sender="test", receiver="question_analyzer", content={}, message_type="request"
        )
        message2 = AgentMessage(
            sender="question_analyzer", receiver="test", content={}, message_type="response"
        )

        agent.log_message(message1)
        agent.log_message(message2)

        history = agent.get_message_history()
        assert len(history) == 2
        assert history[0] == message1
        assert history[1] == message2

    def test_clear_message_history(self, agent):
        """Test clearing message history."""
        message = AgentMessage(
            sender="test", receiver="question_analyzer", content={}, message_type="request"
        )

        agent.log_message(message)
        assert len(agent.message_history) == 1

        agent.clear_message_history()
        assert len(agent.message_history) == 0
