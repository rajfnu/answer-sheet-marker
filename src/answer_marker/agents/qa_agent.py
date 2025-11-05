"""QA Agent for the Answer Sheet Marker system.

This module provides the QA Agent that reviews evaluations for consistency,
fairness, and flags items requiring human review.
"""

from typing import List, Dict, Any
from loguru import logger

from answer_marker.core.agent_base import BaseAgent, AgentMessage, AgentConfig
from answer_marker.models.evaluation import QAResult, QAFlag


class QAAgent(BaseAgent):
    """Quality assurance agent that reviews marking consistency and flags issues.

    This agent performs automated quality checks on evaluations to ensure
    consistency, fairness, and accuracy in the marking process.
    """

    async def process(self, message: AgentMessage) -> AgentMessage:
        """Process QA review request.

        Args:
            message: AgentMessage containing evaluations, scores, and feedback data

        Returns:
            AgentMessage with qa_result data
        """
        logger.info(f"[{self.config.name}] Processing QA review request")
        self.log_message(message)

        evaluations = message.content.get("evaluations")
        scores = message.content.get("scores")
        feedback = message.content.get("feedback")

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
            logger.debug(f"[{self.config.name}] Performing QA checks on {len(evaluations)} evaluations")
            qa_result = await self._perform_qa_check(evaluations, scores, feedback)

            response = AgentMessage(
                sender=self.config.name,
                receiver=message.sender,
                content={"qa_result": qa_result.model_dump()},
                message_type="response",
            )
            self.log_message(response)

            logger.info(
                f"[{self.config.name}] ✓ QA review completed: "
                f"{'PASSED' if qa_result.passed else 'FAILED'}, "
                f"{len(qa_result.flags)} flags, "
                f"{'Requires review' if qa_result.requires_human_review else 'No review needed'}"
            )
            return response

        except Exception as e:
            logger.error(f"[{self.config.name}] QA review failed: {e}")
            return AgentMessage(
                sender=self.config.name,
                receiver=message.sender,
                content={"error": str(e)},
                message_type="error",
            )

    async def _perform_qa_check(
        self,
        evaluations: List[Dict[str, Any]],
        scores: Dict[str, Any] = None,
        feedback: Dict[str, Any] = None,
    ) -> QAResult:
        """Perform quality assurance checks on evaluations.

        Args:
            evaluations: List of evaluation dictionaries
            scores: Optional scoring results dictionary
            feedback: Optional feedback dictionary

        Returns:
            QAResult with flags, issues, and recommendations
        """
        issues = []
        flags = []
        recommendations = []

        # Check 1: Low confidence evaluations
        low_confidence = self._check_low_confidence(evaluations)
        flags.extend(low_confidence)

        # Check 2: Inconsistent scoring
        scoring_issues = self._check_scoring_consistency(evaluations)
        issues.extend(scoring_issues)

        # Check 3: Missing mandatory concepts with high scores
        mandatory_issues = self._check_mandatory_concepts(evaluations)
        flags.extend(mandatory_issues)

        # Check 4: Extreme score discrepancies
        discrepancy_flags = self._check_score_discrepancies(evaluations)
        flags.extend(discrepancy_flags)

        # Check 5: Quality alignment check
        quality_issues = self._check_quality_alignment(evaluations)
        flags.extend(quality_issues)

        # Calculate consistency score
        consistency_score = self._calculate_consistency_score(evaluations, len(issues), len(flags))

        # Generate recommendations
        if consistency_score < 0.8:
            recommendations.append("Review marking criteria for consistency")
        if len(flags) > len(evaluations) * 0.3:  # More than 30% flagged
            recommendations.append("Consider re-evaluating flagged answers")
        if any("Low confidence" in f.reason for f in flags):
            recommendations.append("Human review recommended for low confidence evaluations")

        # Determine overall status
        requires_review = len(flags) > 0
        has_issues = len(issues) > 0

        # Determine confidence level
        if consistency_score >= 0.9 and not flags:
            confidence_level = "high"
        elif consistency_score >= 0.7:
            confidence_level = "medium"
        else:
            confidence_level = "low"

        logger.debug(
            f"[{self.config.name}] QA Summary: "
            f"Consistency: {consistency_score:.2f}, "
            f"Flags: {len(flags)}, "
            f"Issues: {len(issues)}"
        )

        return QAResult(
            passed=not has_issues,
            requires_human_review=requires_review,
            flags=flags,
            issues=issues,
            confidence_level=confidence_level,
            consistency_score=consistency_score,
            recommendations=recommendations,
        )

    def _check_low_confidence(self, evaluations: List[Dict[str, Any]]) -> List[QAFlag]:
        """Check for evaluations with low confidence scores.

        Args:
            evaluations: List of evaluation dictionaries

        Returns:
            List of QAFlags for low confidence evaluations
        """
        flags = []
        for eval_data in evaluations:
            confidence = eval_data.get("confidence_score", 1.0)
            if confidence < 0.6:
                severity = "high" if confidence < 0.4 else "medium"
                flags.append(
                    QAFlag(
                        question_id=eval_data.get("question_id", "unknown"),
                        reason="Low confidence score",
                        severity=severity,
                        details={"confidence": confidence},
                    )
                )
                logger.debug(
                    f"[{self.config.name}] Low confidence flag: "
                    f"{eval_data.get('question_id', 'unknown')} ({confidence:.2f})"
                )
        return flags

    def _check_scoring_consistency(self, evaluations: List[Dict[str, Any]]) -> List[Dict]:
        """Check for scoring inconsistencies.

        Args:
            evaluations: List of evaluation dictionaries

        Returns:
            List of issues found
        """
        issues = []
        for eval_data in evaluations:
            total_concept_points = sum(
                c.get("points_earned", 0) for c in eval_data.get("concepts_identified", [])
            )
            expected_max = eval_data.get("max_marks", 0)

            if total_concept_points > expected_max:
                issues.append(
                    {
                        "question_id": eval_data.get("question_id", "unknown"),
                        "issue": "Score exceeds maximum",
                        "details": f"Awarded {total_concept_points} but max is {expected_max}",
                    }
                )
                logger.warning(
                    f"[{self.config.name}] Scoring inconsistency: "
                    f"{eval_data.get('question_id', 'unknown')} - "
                    f"{total_concept_points} > {expected_max}"
                )
        return issues

    def _check_mandatory_concepts(self, evaluations: List[Dict[str, Any]]) -> List[QAFlag]:
        """Check for missing mandatory concepts with high quality ratings.

        Args:
            evaluations: List of evaluation dictionaries

        Returns:
            List of QAFlags for mandatory concept issues
        """
        flags = []
        for eval_data in evaluations:
            # Count missing mandatory concepts
            missing_mandatory = 0
            for concept in eval_data.get("concepts_identified", []):
                # Check if it's a mandatory concept (from points_possible > 0 and not present)
                if not concept.get("present", False) and concept.get("points_possible", 0) > 1.0:
                    missing_mandatory += 1

            # Flag if quality is high but mandatory concepts are missing
            quality = eval_data.get("overall_quality", "")
            if missing_mandatory > 0 and quality in ["excellent", "good"]:
                flags.append(
                    QAFlag(
                        question_id=eval_data.get("question_id", "unknown"),
                        reason="High score despite missing key concepts",
                        severity="medium",
                        details={"missing_count": missing_mandatory, "quality": quality},
                    )
                )
                logger.debug(
                    f"[{self.config.name}] Mandatory concept flag: "
                    f"{eval_data.get('question_id', 'unknown')} - "
                    f"{missing_mandatory} missing, quality: {quality}"
                )
        return flags

    def _check_score_discrepancies(self, evaluations: List[Dict[str, Any]]) -> List[QAFlag]:
        """Check for extreme score discrepancies.

        Args:
            evaluations: List of evaluation dictionaries

        Returns:
            List of QAFlags for score discrepancies
        """
        flags = []
        for eval_data in evaluations:
            marks_awarded = eval_data.get("marks_awarded", 0)
            max_marks = eval_data.get("max_marks", 1)
            percentage = (marks_awarded / max_marks * 100) if max_marks > 0 else 0

            quality = eval_data.get("overall_quality", "")

            # Check for misalignment between percentage and quality
            if percentage >= 80 and quality in ["poor", "inadequate"]:
                flags.append(
                    QAFlag(
                        question_id=eval_data.get("question_id", "unknown"),
                        reason="High score but poor quality rating",
                        severity="high",
                        details={"percentage": percentage, "quality": quality},
                    )
                )
            elif percentage < 50 and quality in ["excellent", "good"]:
                flags.append(
                    QAFlag(
                        question_id=eval_data.get("question_id", "unknown"),
                        reason="Low score but high quality rating",
                        severity="high",
                        details={"percentage": percentage, "quality": quality},
                    )
                )
        return flags

    def _check_quality_alignment(self, evaluations: List[Dict[str, Any]]) -> List[QAFlag]:
        """Check if quality ratings align with scores.

        Args:
            evaluations: List of evaluation dictionaries

        Returns:
            List of QAFlags for quality alignment issues
        """
        flags = []
        for eval_data in evaluations:
            marks_awarded = eval_data.get("marks_awarded", 0)
            max_marks = eval_data.get("max_marks", 1)
            percentage = (marks_awarded / max_marks * 100) if max_marks > 0 else 0
            quality = eval_data.get("overall_quality", "")

            # Expected quality ranges
            expected_quality = None
            if percentage >= 90:
                expected_quality = "excellent"
            elif percentage >= 70:
                expected_quality = "good"
            elif percentage >= 50:
                expected_quality = "satisfactory"
            elif percentage >= 30:
                expected_quality = "poor"
            else:
                expected_quality = "inadequate"

            # Flag if there's a mismatch
            quality_map = {
                "excellent": 5,
                "good": 4,
                "satisfactory": 3,
                "poor": 2,
                "inadequate": 1,
            }
            expected_level = quality_map.get(expected_quality, 3)
            actual_level = quality_map.get(quality, 3)

            if abs(expected_level - actual_level) >= 2:  # Off by 2+ levels
                flags.append(
                    QAFlag(
                        question_id=eval_data.get("question_id", "unknown"),
                        reason="Quality rating doesn't match score percentage",
                        severity="low",
                        details={
                            "percentage": percentage,
                            "quality": quality,
                            "expected_quality": expected_quality,
                        },
                    )
                )
        return flags

    def _calculate_consistency_score(
        self, evaluations: List[Dict[str, Any]], num_issues: int, num_flags: int
    ) -> float:
        """Calculate overall consistency score.

        Args:
            evaluations: List of evaluation dictionaries
            num_issues: Number of critical issues
            num_flags: Number of flags raised

        Returns:
            Consistency score between 0 and 1
        """
        if not evaluations:
            return 1.0

        # Start with perfect score
        score = 1.0

        # Penalize for issues (critical)
        score -= num_issues * 0.2

        # Penalize for flags (less critical)
        score -= num_flags * 0.05

        # Ensure score is between 0 and 1
        return max(0.0, min(1.0, score))


def create_qa_agent(client) -> QAAgent:
    """Factory function to create a QA Agent.

    Args:
        client: Anthropic client for Claude API (not used by QA agent but required for base class)

    Returns:
        Configured QAAgent instance
    """
    config = AgentConfig(
        name="qa_agent",
        system_prompt="You are a quality assurance agent.",  # Not used but required
    )
    return QAAgent(config=config, client=client)
