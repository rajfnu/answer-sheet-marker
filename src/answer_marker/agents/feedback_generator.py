"""Feedback Generator Agent for the Answer Sheet Marker system.

This module provides the Feedback Generator Agent that creates constructive,
personalized feedback for students based on their evaluations.
"""

from typing import List, Dict, Any
from loguru import logger

from answer_marker.core.agent_base import BaseAgent, AgentMessage, AgentConfig
from answer_marker.models.feedback import FeedbackReport, QuestionFeedback


# System prompt for Feedback Generator Agent (from AGENTS.md)
FEEDBACK_GENERATOR_SYSTEM_PROMPT = """<role>
You are an experienced, encouraging teacher who provides constructive feedback
to help students learn and improve.
</role>

<principles>
- Be constructive and encouraging
- Highlight strengths before weaknesses
- Provide specific, actionable suggestions
- Maintain a positive tone
- Focus on learning and improvement
- Be specific about what was good and what needs work
</principles>

<feedback_structure>
1. Overall performance summary
2. Strengths (what the student did well)
3. Areas for improvement (specific gaps)
4. Actionable suggestions (how to improve)
5. Encouragement (motivational closing)
</feedback_structure>"""


class FeedbackGeneratorAgent(BaseAgent):
    """Generates constructive feedback for students.

    This agent creates personalized, encouraging feedback based on
    evaluation results, highlighting strengths and providing actionable
    suggestions for improvement.
    """

    async def process(self, message: AgentMessage) -> AgentMessage:
        """Process feedback generation request.

        Args:
            message: AgentMessage containing evaluations data

        Returns:
            AgentMessage with feedback data
        """
        logger.info(f"[{self.config.name}] Processing feedback generation request")
        self.log_message(message)

        evaluations = message.content.get("evaluations")
        scores = message.content.get("scores")

        if not evaluations:
            error_msg = "No evaluations found in message content"
            logger.error(f"[{self.config.name}] {error_msg}")
            return AgentMessage(
                sender=self.config.name,
                receiver=message.sender,
                content={"error": error_msg},
                message_type="error",
            )

        try:
            logger.debug(
                f"[{self.config.name}] Generating feedback for {len(evaluations)} evaluations"
            )
            feedback = await self._generate_feedback(evaluations, scores)

            response = AgentMessage(
                sender=self.config.name,
                receiver=message.sender,
                content={"feedback": feedback.model_dump()},
                message_type="response",
            )
            self.log_message(response)

            logger.info(f"[{self.config.name}] ✓ Feedback generation completed")
            return response

        except Exception as e:
            logger.error(f"[{self.config.name}] Feedback generation failed: {e}")
            return AgentMessage(
                sender=self.config.name,
                receiver=message.sender,
                content={"error": str(e)},
                message_type="error",
            )

    async def _generate_feedback(
        self, evaluations: List[Dict[str, Any]], scores: Dict[str, Any] = None
    ) -> FeedbackReport:
        """Generate comprehensive feedback report.

        Args:
            evaluations: List of evaluation dictionaries
            scores: Optional scoring results dictionary

        Returns:
            FeedbackReport with overall and per-question feedback
        """
        question_feedback_list = []

        # Generate feedback for each question
        for evaluation in evaluations:
            logger.debug(
                f"[{self.config.name}] Generating feedback for question {evaluation.get('question_id', 'unknown')}"
            )

            question_feedback = await self._generate_question_feedback(evaluation)
            question_feedback_list.append(question_feedback)

        # Generate overall feedback
        overall_feedback, key_strengths, key_improvements, study_recommendations, encouragement = (
            await self._generate_overall_feedback(evaluations, scores)
        )

        return FeedbackReport(
            overall_feedback=overall_feedback,
            question_feedback=question_feedback_list,
            key_strengths=key_strengths,
            key_improvements=key_improvements,
            study_recommendations=study_recommendations,
            encouragement=encouragement,
        )

    async def _generate_question_feedback(
        self, evaluation: Dict[str, Any]
    ) -> QuestionFeedback:
        """Generate feedback for a single question.

        Args:
            evaluation: Evaluation dictionary for one question

        Returns:
            QuestionFeedback object
        """
        # Calculate marks earned
        marks_earned = sum(
            c.get("points_earned", 0) for c in evaluation.get("concepts_identified", [])
        )
        max_marks = evaluation.get("max_marks", 0)

        # Build prompt for question feedback
        prompt = f"""<evaluation_summary>
Question ID: {evaluation.get('question_id', 'unknown')}
Overall Quality: {evaluation.get('overall_quality', 'unknown')}
Marks: {marks_earned} / {max_marks}

Strengths Identified:
{self._format_list(evaluation.get('strengths', []))}

Weaknesses Identified:
{self._format_list(evaluation.get('weaknesses', []))}

Misconceptions:
{self._format_list(evaluation.get('misconceptions', []))}
</evaluation_summary>

Generate constructive, encouraging feedback for this question following these guidelines:
1. Start with positive aspects (strengths)
2. Address areas for improvement specifically
3. Provide actionable suggestions
4. Maintain an encouraging tone
5. Keep it concise (3-5 sentences)

Return only the feedback text, no additional formatting."""

        # Call Claude for feedback text
        response = await self._call_claude(user_message=prompt)

        # Extract text from response
        feedback_text = ""
        for block in response.content:
            if hasattr(block, "text"):
                feedback_text += block.text

        return QuestionFeedback(
            question_id=evaluation.get("question_id", ""),
            feedback=feedback_text.strip(),
            strengths=evaluation.get("strengths", []),
            improvement_areas=evaluation.get("weaknesses", []),
            suggestions=[],  # Could be extracted from feedback_text if needed
        )

    async def _generate_overall_feedback(
        self, evaluations: List[Dict[str, Any]], scores: Dict[str, Any] = None
    ) -> tuple:
        """Generate overall feedback summary.

        Args:
            evaluations: List of all evaluations
            scores: Optional scoring results

        Returns:
            Tuple of (overall_feedback, key_strengths, key_improvements, study_recommendations, encouragement)
        """
        # Aggregate strengths and weaknesses across all questions
        all_strengths = []
        all_weaknesses = []
        all_misconceptions = []

        for evaluation in evaluations:
            all_strengths.extend(evaluation.get("strengths", []))
            all_weaknesses.extend(evaluation.get("weaknesses", []))
            all_misconceptions.extend(evaluation.get("misconceptions", []))

        # Build prompt for overall feedback
        score_summary = ""
        if scores:
            score_summary = f"""
Total Score: {scores.get('total_marks', 0)} / {scores.get('max_marks', 0)} ({scores.get('percentage', 0):.1f}%)
Grade: {scores.get('grade', 'N/A')}
Passed: {'Yes' if scores.get('passed', False) else 'No'}
"""

        prompt = f"""<performance_summary>
Number of Questions: {len(evaluations)}
{score_summary}

Overall Strengths Across All Questions:
{self._format_list(all_strengths[:5])}

Overall Weaknesses Across All Questions:
{self._format_list(all_weaknesses[:5])}

Misconceptions Identified:
{self._format_list(all_misconceptions[:3])}
</performance_summary>

Generate comprehensive overall feedback for the student covering:
1. Overall performance summary (1-2 sentences)
2. Key strengths to maintain (2-3 key points)
3. Key areas for improvement (2-3 specific areas)
4. Study recommendations (2-3 actionable suggestions)
5. Encouragement (1 motivational sentence)

Format your response as:
OVERALL: [overall summary text]
STRENGTHS: [bullet point 1] | [bullet point 2] | [bullet point 3]
IMPROVEMENTS: [bullet point 1] | [bullet point 2] | [bullet point 3]
RECOMMENDATIONS: [bullet point 1] | [bullet point 2] | [bullet point 3]
ENCOURAGEMENT: [encouragement text]"""

        # Call Claude for overall feedback
        response = await self._call_claude(user_message=prompt)

        # Extract text from response
        response_text = ""
        for block in response.content:
            if hasattr(block, "text"):
                response_text += block.text

        # Parse structured response
        overall_feedback = ""
        key_strengths = []
        key_improvements = []
        study_recommendations = []
        encouragement = ""

        for line in response_text.split("\n"):
            if line.startswith("OVERALL:"):
                overall_feedback = line.replace("OVERALL:", "").strip()
            elif line.startswith("STRENGTHS:"):
                key_strengths = [
                    s.strip() for s in line.replace("STRENGTHS:", "").split("|") if s.strip()
                ]
            elif line.startswith("IMPROVEMENTS:"):
                key_improvements = [
                    i.strip() for i in line.replace("IMPROVEMENTS:", "").split("|") if i.strip()
                ]
            elif line.startswith("RECOMMENDATIONS:"):
                study_recommendations = [
                    r.strip() for r in line.replace("RECOMMENDATIONS:", "").split("|") if r.strip()
                ]
            elif line.startswith("ENCOURAGEMENT:"):
                encouragement = line.replace("ENCOURAGEMENT:", "").strip()

        return (
            overall_feedback,
            key_strengths,
            key_improvements,
            study_recommendations,
            encouragement,
        )

    def _format_list(self, items: List[str]) -> str:
        """Format list for prompt.

        Args:
            items: List of strings to format

        Returns:
            Formatted string with bullet points
        """
        if not items:
            return "None"
        return "\n".join(f"- {item}" for item in items)


def create_feedback_generator_agent(client) -> FeedbackGeneratorAgent:
    """Factory function to create a Feedback Generator Agent.

    Args:
        client: Anthropic client for Claude API

    Returns:
        Configured FeedbackGeneratorAgent instance
    """
    config = AgentConfig(
        name="feedback_generator",
        system_prompt=FEEDBACK_GENERATOR_SYSTEM_PROMPT,
    )
    return FeedbackGeneratorAgent(config=config, client=client)
