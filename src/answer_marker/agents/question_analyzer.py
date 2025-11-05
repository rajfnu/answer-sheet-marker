"""Question Analyzer Agent for the Answer Sheet Marker system.

This module provides the Question Analyzer Agent that analyzes marking guides,
extracts evaluation criteria, and creates structured rubrics.
"""

from typing import Dict, Any, List
from loguru import logger

from answer_marker.core.agent_base import BaseAgent, AgentMessage, AgentConfig
from answer_marker.models.question import (
    AnalyzedQuestion,
    QuestionType,
    KeyConcept,
    EvaluationCriteria,
)


# System prompt for Question Analyzer Agent (from AGENTS.md)
QUESTION_ANALYZER_SYSTEM_PROMPT = """<role>
You are an expert examiner and educational assessment specialist. Your role is to analyze
marking guides and extract clear, structured evaluation criteria.
</role>

<task>
Analyze the provided marking guide and create a structured evaluation rubric for each question.
</task>

<instructions>
1. Identify the question type (MCQ, short answer, essay, numerical, etc.)
2. Extract all key concepts, keywords, and evaluation points
3. Determine the marking scheme and point allocation
4. Identify mandatory requirements vs. optional points
5. Create a clear rubric for consistent evaluation
6. Note any specific instructions or edge cases
</instructions>

<output_requirements>
For each question, provide:
- Question ID and type
- Maximum marks available
- List of key concepts (with point values)
- Required keywords or phrases
- Evaluation criteria (what constitutes full marks, partial marks, zero marks)
- Common mistakes to watch for
- Rubric tiers (excellent, good, satisfactory, poor)
</output_requirements>"""


class QuestionAnalyzerAgent(BaseAgent):
    """Analyzes marking guides and creates evaluation rubrics.

    This agent processes marking guides to extract structured evaluation criteria,
    identify question types, and create consistent rubrics for answer evaluation.
    """

    async def process(self, message: AgentMessage) -> AgentMessage:
        """Process question analysis request.

        Args:
            message: AgentMessage containing marking_guide data

        Returns:
            AgentMessage with analyzed_questions data
        """
        logger.info(f"[{self.config.name}] Processing question analysis request")
        self.log_message(message)

        marking_guide = message.content.get("marking_guide")
        if not marking_guide:
            error_msg = "No marking_guide found in message content"
            logger.error(f"[{self.config.name}] {error_msg}")
            return AgentMessage(
                sender=self.config.name,
                receiver=message.sender,
                content={"error": error_msg},
                message_type="error",
            )

        questions = marking_guide.get("questions", [])
        logger.info(f"[{self.config.name}] Analyzing {len(questions)} questions")

        analyzed_questions = {}
        for i, question in enumerate(questions, 1):
            try:
                logger.debug(f"[{self.config.name}] Analyzing question {i}/{len(questions)}")
                analysis = await self._analyze_single_question(question)
                analyzed_questions[question["id"]] = analysis.model_dump()
                logger.info(f"[{self.config.name}] ✓ Question {question['id']} analyzed")
            except Exception as e:
                logger.error(
                    f"[{self.config.name}] Failed to analyze question {question.get('id', 'unknown')}: {e}"
                )
                # Continue with other questions
                continue

        response = AgentMessage(
            sender=self.config.name,
            receiver=message.sender,
            content={"analyzed_questions": analyzed_questions},
            message_type="response",
        )
        self.log_message(response)

        logger.info(
            f"[{self.config.name}] Completed analysis of {len(analyzed_questions)}/{len(questions)} questions"
        )
        return response

    async def _analyze_single_question(self, question: Dict[str, Any]) -> AnalyzedQuestion:
        """Analyze a single question using Claude.

        Args:
            question: Question dictionary with question_text, marking_scheme, etc.

        Returns:
            AnalyzedQuestion with structured evaluation criteria

        Raises:
            ValueError: If Claude doesn't return structured output
        """
        # Define structured output tool for question analysis
        analysis_tool = {
            "name": "submit_question_analysis",
            "description": "Submit the structured analysis of a question",
            "input_schema": {
                "type": "object",
                "properties": {
                    "id": {"type": "string", "description": "Question ID"},
                    "question_text": {
                        "type": "string",
                        "description": "The question text",
                    },
                    "question_type": {
                        "type": "string",
                        "enum": ["mcq", "short_answer", "essay", "numerical", "true_false"],
                        "description": "Type of question",
                    },
                    "max_marks": {
                        "type": "number",
                        "description": "Maximum marks for this question",
                    },
                    "key_concepts": {
                        "type": "array",
                        "description": "List of key concepts to evaluate",
                        "items": {
                            "type": "object",
                            "properties": {
                                "concept": {
                                    "type": "string",
                                    "description": "The concept description",
                                },
                                "points": {
                                    "type": "number",
                                    "description": "Points allocated to this concept",
                                },
                                "mandatory": {
                                    "type": "boolean",
                                    "description": "Whether this concept is mandatory",
                                },
                                "keywords": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Keywords associated with this concept",
                                },
                            },
                            "required": ["concept", "points"],
                        },
                    },
                    "evaluation_criteria": {
                        "type": "object",
                        "description": "Criteria for different quality levels",
                        "properties": {
                            "excellent": {
                                "type": "string",
                                "description": "Criteria for excellent answer (90-100%)",
                            },
                            "good": {
                                "type": "string",
                                "description": "Criteria for good answer (70-89%)",
                            },
                            "satisfactory": {
                                "type": "string",
                                "description": "Criteria for satisfactory answer (50-69%)",
                            },
                            "poor": {
                                "type": "string",
                                "description": "Criteria for poor answer (<50%)",
                            },
                        },
                        "required": ["excellent", "good", "satisfactory", "poor"],
                    },
                    "keywords": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Overall keywords to look for",
                    },
                    "common_mistakes": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Common mistakes students make",
                    },
                },
                "required": [
                    "id",
                    "question_text",
                    "question_type",
                    "max_marks",
                    "key_concepts",
                    "evaluation_criteria",
                ],
            },
        }

        # Build prompt with question details
        prompt = f"""<question>
{question.get('question_text', '')}
</question>

<max_marks>
{question.get('marks', 0)} marks
</max_marks>

<marking_guide>
{question.get('marking_scheme', 'No marking scheme provided')}
</marking_guide>

<sample_answer>
{question.get('sample_answer', 'No sample answer provided')}
</sample_answer>

Analyze this question thoroughly and use the submit_question_analysis tool to provide
a structured evaluation rubric. Extract all key concepts, their point allocations,
and create clear evaluation criteria for different quality levels."""

        logger.debug(
            f"[{self.config.name}] Calling Claude for question {question.get('id', 'unknown')}"
        )

        # Call Claude with the analysis tool
        response = await self._call_claude(
            user_message=prompt,
            tools=[analysis_tool],
            tool_choice={"type": "tool", "name": "submit_question_analysis"},
        )

        # Extract tool use result
        for block in response.content:
            if block.type == "tool_use":
                analysis_data = block.input
                logger.debug(
                    f"[{self.config.name}] Received structured analysis for question {question.get('id', 'unknown')}"
                )

                # Convert key_concepts to KeyConcept objects
                key_concepts = [
                    KeyConcept(**concept) for concept in analysis_data.get("key_concepts", [])
                ]

                # Convert evaluation_criteria to EvaluationCriteria object
                evaluation_criteria = EvaluationCriteria(
                    **analysis_data.get("evaluation_criteria", {})
                )

                # Build AnalyzedQuestion
                analyzed_question = AnalyzedQuestion(
                    id=analysis_data.get("id", question.get("id", "")),
                    question_text=analysis_data.get(
                        "question_text", question.get("question_text", "")
                    ),
                    question_type=QuestionType(analysis_data.get("question_type", "short_answer")),
                    max_marks=analysis_data.get("max_marks", question.get("marks", 0)),
                    key_concepts=key_concepts,
                    evaluation_criteria=evaluation_criteria,
                    keywords=analysis_data.get("keywords", []),
                    common_mistakes=analysis_data.get("common_mistakes", []),
                )

                return analyzed_question

        # If we get here, Claude didn't return the expected tool use
        error_msg = f"Claude did not return structured output for question {question.get('id', 'unknown')}"
        logger.error(f"[{self.config.name}] {error_msg}")
        raise ValueError(error_msg)


def create_question_analyzer_agent(client) -> QuestionAnalyzerAgent:
    """Factory function to create a Question Analyzer Agent.

    Args:
        client: Anthropic client for Claude API

    Returns:
        Configured QuestionAnalyzerAgent instance
    """
    config = AgentConfig(
        name="question_analyzer",
        system_prompt=QUESTION_ANALYZER_SYSTEM_PROMPT,
    )
    return QuestionAnalyzerAgent(config=config, client=client)
