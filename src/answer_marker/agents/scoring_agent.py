"""Scoring Agent for the Answer Sheet Marker system.

This module provides the Scoring Agent that aggregates evaluations and
calculates final marks based on rubrics and partial credit rules.
"""

from typing import List, Dict, Any
from loguru import logger

from answer_marker.core.agent_base import BaseAgent, AgentMessage, AgentConfig
from answer_marker.models.evaluation import ScoringResult, QuestionScore


class ScoringAgent(BaseAgent):
    """Calculates final scores from evaluations.

    This agent aggregates individual question evaluations and computes
    total scores, percentages, and letter grades.
    """

    async def process(self, message: AgentMessage) -> AgentMessage:
        """Process scoring request.

        Args:
            message: AgentMessage containing evaluations data

        Returns:
            AgentMessage with scores data
        """
        logger.info(f"[{self.config.name}] Processing scoring request")
        self.log_message(message)

        evaluations = message.content.get("evaluations")
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
            logger.debug(f"[{self.config.name}] Calculating scores for {len(evaluations)} evaluations")
            scores = await self._calculate_scores(evaluations)

            response = AgentMessage(
                sender=self.config.name,
                receiver=message.sender,
                content={"scores": scores.model_dump()},
                message_type="response",
            )
            self.log_message(response)

            logger.info(
                f"[{self.config.name}] ✓ Scoring completed: "
                f"{scores.total_marks}/{scores.max_marks} ({scores.percentage:.1f}%) - Grade: {scores.grade}"
            )
            return response

        except Exception as e:
            logger.error(f"[{self.config.name}] Scoring failed: {e}")
            return AgentMessage(
                sender=self.config.name,
                receiver=message.sender,
                content={"error": str(e)},
                message_type="error",
            )

    async def _calculate_scores(self, evaluations: List[Dict[str, Any]]) -> ScoringResult:
        """Calculate scores with validation.

        Args:
            evaluations: List of evaluation dictionaries

        Returns:
            ScoringResult with total marks, percentages, and grades
        """
        total_marks = 0.0
        max_marks = 0.0
        question_scores = []

        for eval_data in evaluations:
            # Calculate score for this question
            question_score = sum(
                concept.get("points_earned", 0) for concept in eval_data.get("concepts_identified", [])
            )

            question_max = eval_data.get("max_marks", 0)

            # Ensure score doesn't exceed maximum
            question_score = min(question_score, question_max)

            total_marks += question_score
            max_marks += question_max

            # Calculate percentage for this question
            question_percentage = (question_score / question_max * 100) if question_max > 0 else 0

            # Create question score entry
            question_scores.append(
                QuestionScore(
                    question_id=eval_data.get("question_id", ""),
                    marks_awarded=question_score,
                    max_marks=question_max,
                    percentage=question_percentage,
                    quality=eval_data.get("overall_quality"),
                )
            )

            logger.debug(
                f"[{self.config.name}] Question {eval_data.get('question_id', 'unknown')}: "
                f"{question_score}/{question_max} ({question_percentage:.1f}%)"
            )

        # Calculate overall percentage
        percentage = (total_marks / max_marks * 100) if max_marks > 0 else 0

        # Calculate letter grade
        grade = self._calculate_grade(percentage)

        # Determine if passed (50% threshold)
        passed = percentage >= 50.0

        return ScoringResult(
            total_marks=total_marks,
            max_marks=max_marks,
            percentage=percentage,
            question_scores=question_scores,
            grade=grade,
            passed=passed,
        )

    def _calculate_grade(self, percentage: float) -> str:
        """Convert percentage to letter grade.

        Args:
            percentage: Percentage score (0-100)

        Returns:
            Letter grade (A+, A, A-, B+, B, B-, C+, C, C-, F)
        """
        if percentage >= 90:
            return "A+"
        elif percentage >= 85:
            return "A"
        elif percentage >= 80:
            return "A-"
        elif percentage >= 75:
            return "B+"
        elif percentage >= 70:
            return "B"
        elif percentage >= 65:
            return "B-"
        elif percentage >= 60:
            return "C+"
        elif percentage >= 55:
            return "C"
        elif percentage >= 50:
            return "C-"
        else:
            return "F"


def create_scoring_agent(client) -> ScoringAgent:
    """Factory function to create a Scoring Agent.

    Args:
        client: Anthropic client for Claude API (not used by scoring agent but required for base class)

    Returns:
        Configured ScoringAgent instance
    """
    config = AgentConfig(
        name="scoring_agent",
        system_prompt="You are a scoring agent that calculates final marks.",  # Not used but required
    )
    return ScoringAgent(config=config, client=client)
