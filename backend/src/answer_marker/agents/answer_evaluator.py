"""Answer Evaluator Agent for the Answer Sheet Marker system.

This module provides the Answer Evaluator Agent that compares student answers
with marking rubrics and identifies correct concepts, errors, and gaps.
"""

from typing import Dict, Any, List
from loguru import logger

from answer_marker.core.agent_base import BaseAgent, AgentMessage, AgentConfig
from answer_marker.models.evaluation import ConceptEvaluation, AnswerEvaluation


# System prompt for Answer Evaluator Agent (from AGENTS.md)
ANSWER_EVALUATOR_SYSTEM_PROMPT = """<role>
You are a fair, consistent, and expert examiner. You evaluate student answers against
marking rubrics with precision and objectivity.
</role>

<principles>
- Be fair and unbiased
- Look for what students know, not just what they don't know
- Award partial credit appropriately
- Identify both strengths and weaknesses
- Be consistent across all evaluations
- Recognize different ways of expressing correct concepts
</principles>

<task>
Evaluate student answers by comparing them with the provided marking rubric and
identify all concepts present and missing.
</task>

<evaluation_process>
1. Read the question and marking rubric carefully
2. Read the student's answer thoroughly
3. Identify each key concept from the rubric
4. Check if the concept is present in the student's answer (with variations in wording)
5. Assess the accuracy and completeness of each identified concept
6. Note any misconceptions or errors
7. Determine partial credit eligibility
8. Provide a confidence score for your evaluation
</evaluation_process>"""


class AnswerEvaluatorAgent(BaseAgent):
    """Evaluates student answers against marking rubrics.

    This agent performs detailed evaluation of student answers by comparing them
    with marking rubrics, identifying correct concepts, errors, and gaps.
    """

    async def process(self, message: AgentMessage) -> AgentMessage:
        """Process answer evaluation request.

        Args:
            message: AgentMessage containing question and student_answer data

        Returns:
            AgentMessage with evaluation data
        """
        logger.info(f"[{self.config.name}] Processing answer evaluation request")
        self.log_message(message)

        question = message.content.get("question")
        student_answer = message.content.get("student_answer")

        if not question:
            error_msg = "No question found in message content"
            logger.error(f"[{self.config.name}] {error_msg}")
            return AgentMessage(
                sender=self.config.name,
                receiver=message.sender,
                content={"error": error_msg},
                message_type="error",
            )

        if not student_answer:
            error_msg = "No student_answer found in message content"
            logger.error(f"[{self.config.name}] {error_msg}")
            return AgentMessage(
                sender=self.config.name,
                receiver=message.sender,
                content={"error": error_msg},
                message_type="error",
            )

        try:
            logger.debug(
                f"[{self.config.name}] Evaluating answer for question {question.get('id', 'unknown')}"
            )
            evaluation = await self._evaluate_answer(question, student_answer)

            response = AgentMessage(
                sender=self.config.name,
                receiver=message.sender,
                content={"evaluation": evaluation.model_dump()},
                message_type="response",
            )
            self.log_message(response)

            logger.info(
                f"[{self.config.name}] ✓ Evaluation completed for question {question.get('id', 'unknown')} "
                f"(confidence: {evaluation.confidence_score:.2f})"
            )
            return response

        except Exception as e:
            logger.error(f"[{self.config.name}] Evaluation failed: {e}")
            return AgentMessage(
                sender=self.config.name,
                receiver=message.sender,
                content={"error": str(e)},
                message_type="error",
            )

    async def _evaluate_answer(
        self, question: Dict[str, Any], student_answer: str
    ) -> AnswerEvaluation:
        """Perform detailed evaluation of a student answer.

        Args:
            question: Question dictionary with rubric information
            student_answer: Student's answer text

        Returns:
            AnswerEvaluation with detailed concept-level assessment

        Raises:
            ValueError: If Claude doesn't return structured output
        """
        # Define structured output tool for evaluation
        evaluation_tool = {
            "name": "submit_evaluation",
            "description": "Submit the evaluation of a student answer",
            "input_schema": {
                "type": "object",
                "properties": {
                    "concepts_identified": {
                        "type": "array",
                        "description": "Evaluation of each key concept",
                        "items": {
                            "type": "object",
                            "properties": {
                                "concept": {
                                    "type": "string",
                                    "description": "The concept being evaluated",
                                },
                                "present": {
                                    "type": "boolean",
                                    "description": "Whether concept is present in answer",
                                },
                                "accuracy": {
                                    "type": "string",
                                    "enum": [
                                        "fully_correct",
                                        "partially_correct",
                                        "incorrect",
                                        "not_present",
                                    ],
                                    "description": "Accuracy of the concept",
                                },
                                "evidence": {
                                    "type": "string",
                                    "description": "Quote from answer showing this concept (empty string if not present)",
                                },
                                "points_earned": {
                                    "type": "number",
                                    "description": "Points earned for this concept",
                                },
                                "points_possible": {
                                    "type": "number",
                                    "description": "Maximum points possible for this concept",
                                },
                            },
                            "required": ["concept", "present", "accuracy", "evidence", "points_earned", "points_possible"],
                        },
                    },
                    "overall_quality": {
                        "type": "string",
                        "enum": ["excellent", "good", "satisfactory", "poor", "inadequate"],
                        "description": "Overall quality of the answer",
                    },
                    "strengths": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Strengths in the answer",
                    },
                    "weaknesses": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Weaknesses in the answer",
                    },
                    "misconceptions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Misconceptions or errors identified",
                    },
                    "confidence_score": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 1,
                        "description": "Confidence in this evaluation (0-1)",
                    },
                    "requires_human_review": {
                        "type": "boolean",
                        "description": "Whether this needs human review",
                    },
                    "review_reason": {
                        "type": "string",
                        "description": "Reason for human review if needed",
                    },
                },
                "required": ["concepts_identified", "overall_quality", "confidence_score"],
            },
        }

        # Build prompt with question and rubric
        question_type = question.get('question_type', 'unknown')

        # Format options for MCQ/true_false questions
        options_text = ""
        if question_type in ['mcq', 'true_false'] and question.get('options'):
            options_list = []
            correct_answer = question.get('correct_answer', '')
            for opt in question.get('options', []):
                label = opt.get('label', '')
                text = opt.get('text', '')
                is_correct = opt.get('is_correct', False) or (label == correct_answer)
                correct_marker = " ✓ CORRECT ANSWER" if is_correct else ""
                options_list.append(f"  {label}. {text}{correct_marker}")
            options_text = f"\n\nOptions:\n" + "\n".join(options_list)

        prompt = f"""<question>
{question.get('question_text', '')}
{options_text}
</question>

<marking_rubric>
Question Type: {question_type}
Maximum Marks: {question.get('max_marks', 0)}

Key Concepts to Look For:
{self._format_key_concepts(question.get('key_concepts', []))}

Evaluation Criteria:
- Excellent: {question.get('evaluation_criteria', {}).get('excellent', 'N/A')}
- Good: {question.get('evaluation_criteria', {}).get('good', 'N/A')}
- Satisfactory: {question.get('evaluation_criteria', {}).get('satisfactory', 'N/A')}
- Poor: {question.get('evaluation_criteria', {}).get('poor', 'N/A')}

Keywords: {', '.join(question.get('keywords', []))}
</marking_rubric>

<student_answer>
{student_answer}
</student_answer>

<instructions>
Evaluate this answer carefully:

{'FOR MCQ/TRUE_FALSE QUESTIONS:' if question_type in ['mcq', 'true_false'] else ''}
{'- The student may answer with just the letter (e.g., "B") or with the letter and full option text (e.g., "B - Financial accounting...")' if question_type in ['mcq', 'true_false'] else ''}
{'- BOTH formats are correct if the letter matches the correct answer' if question_type in ['mcq', 'true_false'] else ''}
{'- Award FULL marks if the student selected the correct option' if question_type in ['mcq', 'true_false'] else ''}
{'- Award ZERO marks if the student selected an incorrect option' if question_type in ['mcq', 'true_false'] else ''}
{'- Be flexible with formatting - ignore question numbers, bold text, or extra punctuation' if question_type in ['mcq', 'true_false'] else ''}
{'- The student answer may contain prefixes like "Q1:", "**Q1:**", "Question 1:", etc. - ignore these' if question_type in ['mcq', 'true_false'] else ''}
{'- Focus on extracting the actual answer choice from the student response' if question_type in ['mcq', 'true_false'] else ''}

FOR ALL QUESTIONS:
1. Check for each key concept in the rubric
2. Assess accuracy of concepts present
3. Identify strengths and weaknesses
4. Note any misconceptions
5. Determine your confidence in this evaluation
6. Flag for human review if confidence is low or answer is ambiguous

Use the submit_evaluation tool to provide your structured evaluation.
</instructions>"""

        logger.debug(
            f"[{self.config.name}] Calling Claude for evaluation of question {question.get('id', 'unknown')}"
        )

        # Call Claude with the evaluation tool
        response = await self._call_claude(
            user_message=prompt,
            tools=[evaluation_tool],
            tool_choice={"type": "tool", "name": "submit_evaluation"},
        )

        # Extract and return evaluation
        for block in response.content:
            if block.type == "tool_use":
                evaluation_data = block.input
                logger.debug(
                    f"[{self.config.name}] Received structured evaluation for question {question.get('id', 'unknown')}"
                )

                # Convert concepts_identified to ConceptEvaluation objects
                concepts_identified = [
                    ConceptEvaluation(**concept)
                    for concept in evaluation_data.get("concepts_identified", [])
                ]

                # Calculate marks awarded
                marks_awarded = sum(c.points_earned for c in concepts_identified)

                # Build AnswerEvaluation with optional fields
                eval_kwargs = {
                    "question_id": question.get("id", ""),
                    "question_number": question.get("question_number"),  # Preserve question number
                    "concepts_identified": concepts_identified,
                    "overall_quality": evaluation_data.get("overall_quality", "satisfactory"),
                    "confidence_score": evaluation_data.get("confidence_score", 0.0),
                    "marks_awarded": marks_awarded,
                    "max_marks": question.get("max_marks", 0),
                    "strengths": evaluation_data.get("strengths", []),
                    "weaknesses": evaluation_data.get("weaknesses", []),
                    "misconceptions": evaluation_data.get("misconceptions", []),
                }

                # Add optional fields only if present
                if "requires_human_review" in evaluation_data:
                    eval_kwargs["requires_human_review"] = evaluation_data["requires_human_review"]
                if "review_reason" in evaluation_data:
                    eval_kwargs["review_reason"] = evaluation_data["review_reason"]

                answer_evaluation = AnswerEvaluation(**eval_kwargs)

                return answer_evaluation

        # If we get here, Claude didn't return the expected tool use
        error_msg = f"Claude did not return structured output for question {question.get('id', 'unknown')}"
        logger.error(f"[{self.config.name}] {error_msg}")
        raise ValueError(error_msg)

    def _format_key_concepts(self, concepts: List[Dict[str, Any]]) -> str:
        """Format key concepts for prompt.

        Args:
            concepts: List of key concept dictionaries

        Returns:
            Formatted string representation of concepts
        """
        if not concepts:
            return "No key concepts specified"

        formatted = []
        for i, concept in enumerate(concepts, 1):
            mandatory = "MANDATORY" if concept.get("mandatory", False) else "Optional"
            keywords = concept.get("keywords", [])
            keywords_str = f" (Keywords: {', '.join(keywords)})" if keywords else ""

            formatted.append(
                f"{i}. {concept.get('concept', 'Unknown')} - "
                f"{concept.get('points', 0)} marks [{mandatory}]{keywords_str}"
            )
        return "\n".join(formatted)


def create_answer_evaluator_agent(client) -> AnswerEvaluatorAgent:
    """Factory function to create an Answer Evaluator Agent.

    Args:
        client: Anthropic client for Claude API

    Returns:
        Configured AnswerEvaluatorAgent instance
    """
    config = AgentConfig(
        name="answer_evaluator",
        system_prompt=ANSWER_EVALUATOR_SYSTEM_PROMPT,
    )
    return AnswerEvaluatorAgent(config=config, client=client)
