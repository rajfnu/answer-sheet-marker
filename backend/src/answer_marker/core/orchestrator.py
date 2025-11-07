"""Orchestrator Agent for the Answer Sheet Marker system.

This module provides the Orchestrator Agent that coordinates all specialized agents
and manages the overall marking workflow.
"""

from typing import Dict, Any, List
from loguru import logger
import time

from answer_marker.core.agent_base import BaseAgent, AgentMessage, AgentConfig
from answer_marker.models.marking_guide import MarkingGuide
from answer_marker.models.answer import AnswerSheet
from answer_marker.models.report import EvaluationReport
from answer_marker.models.evaluation import AnswerEvaluation, ScoringResult, QAResult
from answer_marker.models.feedback import FeedbackReport


class OrchestratorAgent(BaseAgent):
    """Main orchestrator that coordinates the marking workflow.

    This agent manages the entire marking process by coordinating all
    specialized agents in the correct sequence and aggregating their results.
    """

    def __init__(self, config: AgentConfig, client, agents: Dict[str, BaseAgent]):
        """Initialize orchestrator with specialized agents.

        Args:
            config: Agent configuration
            client: Anthropic client for Claude API
            agents: Dictionary of specialized agents by name
        """
        super().__init__(config, client)
        self.agents = agents
        self.workflow_state = {}
        logger.info(f"[{self.config.name}] Initialized with {len(agents)} specialized agents")

    async def process(self, message: AgentMessage) -> AgentMessage:
        """Process orchestration request (not typically used directly).

        Args:
            message: AgentMessage with request data

        Returns:
            AgentMessage with response
        """
        logger.info(f"[{self.config.name}] Processing orchestration request")
        self.log_message(message)

        # This is typically not used directly - users call mark_answer_sheet instead
        return AgentMessage(
            sender=self.config.name,
            receiver=message.sender,
            content={"status": "Use mark_answer_sheet() method instead"},
            message_type="info",
        )

    async def mark_answer_sheet(
        self,
        marking_guide: MarkingGuide,
        answer_sheet: AnswerSheet,
        assessment_title: str = "Assessment",
    ) -> EvaluationReport:
        """Main entry point for marking process.

        Workflow:
        1. Question analysis (analyze all questions in marking guide)
        2. Answer evaluation (evaluate each student answer)
        3. Scoring (calculate final scores and grades)
        4. Feedback generation (create personalized feedback)
        5. QA review (quality assurance checks)
        6. Report generation (compile final report)

        Args:
            marking_guide: The marking guide with questions and rubrics
            answer_sheet: The student's answer sheet
            assessment_title: Title of the assessment

        Returns:
            Complete EvaluationReport with all results

        Raises:
            Exception: If any step in the marking process fails
        """
        start_time = time.time()
        student_id = answer_sheet.student_id or "Unknown"

        logger.info(
            f"[{self.config.name}] Starting marking process for student {student_id} "
            f"on '{assessment_title}'"
        )

        try:
            # Note: marking_guide.questions are ALREADY AnalyzedQuestion objects with correct IDs
            # No need to re-analyze them - that causes ID mismatches!
            logger.info(f"[{self.config.name}] Step 1/2: Using {len(marking_guide.questions)} pre-analyzed questions from marking guide...")

            # Step 2: Evaluate each answer
            logger.info(f"[{self.config.name}] Step 2/5: Evaluating answers...")
            evaluations = []
            for question in marking_guide.questions:
                student_answer = answer_sheet.get_answer(question.id)
                if student_answer:
                    # Convert AnalyzedQuestion to dict for evaluator
                    question_dict = question.model_dump()
                    evaluation = await self._evaluate_answer(
                        question=question_dict, student_answer=student_answer
                    )
                    evaluations.append(evaluation)
                else:
                    logger.warning(
                        f"[{self.config.name}] No answer found for question {question.id}"
                    )

            # Step 3: Calculate scores
            logger.info(f"[{self.config.name}] Step 3/5: Calculating scores...")
            scores = await self._calculate_scores(evaluations)

            # Step 4: Generate feedback
            logger.info(f"[{self.config.name}] Step 4/5: Generating feedback...")
            feedback = await self._generate_feedback(evaluations, scores)

            # Step 5: QA Review
            logger.info(f"[{self.config.name}] Step 5/5: Performing QA review...")
            qa_result = await self._qa_review(evaluations, scores, feedback)

            # Step 6: Generate final report
            logger.info(f"[{self.config.name}] Generating final report...")
            report = await self._generate_report(
                answer_sheet=answer_sheet,
                assessment_title=assessment_title,
                evaluations=evaluations,
                scores=scores,
                feedback=feedback,
                qa_result=qa_result,
            )

            processing_time = time.time() - start_time
            report.processing_time = processing_time

            logger.info(
                f"[{self.config.name}] ✓ Marking completed for {student_id} in {processing_time:.2f}s "
                f"- Score: {scores['total_marks']}/{scores['max_marks']} ({scores['percentage']:.1f}%) "
                f"- Grade: {scores['grade']}"
            )

            return report

        except Exception as e:
            logger.error(f"[{self.config.name}] Marking process failed: {e}")
            raise

    async def _analyze_questions(self, marking_guide: MarkingGuide) -> Dict[str, Any]:
        """Send questions to Question Analyzer Agent.

        Args:
            marking_guide: The marking guide to analyze

        Returns:
            Dictionary of analyzed questions by question ID
        """
        message = AgentMessage(
            sender="orchestrator",
            receiver="question_analyzer",
            content={"marking_guide": marking_guide.model_dump()},
            message_type="request",
        )

        response = await self.agents["question_analyzer"].process(message)

        if response.message_type == "error":
            raise Exception(f"Question analysis failed: {response.content.get('error', 'Unknown error')}")

        return response.content["analyzed_questions"]

    async def _evaluate_answer(
        self, question: Dict[str, Any], student_answer: Any
    ) -> Dict[str, Any]:
        """Send to Answer Evaluator Agent.

        Args:
            question: Analyzed question data
            student_answer: Student's answer object

        Returns:
            Evaluation dictionary
        """
        message = AgentMessage(
            sender="orchestrator",
            receiver="answer_evaluator",
            content={
                "question": question,
                "student_answer": student_answer.answer_text if hasattr(student_answer, "answer_text") else str(student_answer),
            },
            message_type="request",
        )

        response = await self.agents["answer_evaluator"].process(message)

        if response.message_type == "error":
            raise Exception(f"Answer evaluation failed: {response.content.get('error', 'Unknown error')}")

        return response.content["evaluation"]

    async def _calculate_scores(self, evaluations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Send to Scoring Agent.

        Args:
            evaluations: List of evaluation dictionaries

        Returns:
            Scores dictionary
        """
        message = AgentMessage(
            sender="orchestrator",
            receiver="scoring_agent",
            content={"evaluations": evaluations},
            message_type="request",
        )

        response = await self.agents["scoring_agent"].process(message)

        if response.message_type == "error":
            raise Exception(f"Scoring failed: {response.content.get('error', 'Unknown error')}")

        return response.content["scores"]

    async def _generate_feedback(
        self, evaluations: List[Dict[str, Any]], scores: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send to Feedback Generator Agent.

        Args:
            evaluations: List of evaluation dictionaries
            scores: Scores dictionary

        Returns:
            Feedback dictionary
        """
        message = AgentMessage(
            sender="orchestrator",
            receiver="feedback_generator",
            content={"evaluations": evaluations, "scores": scores},
            message_type="request",
        )

        response = await self.agents["feedback_generator"].process(message)

        if response.message_type == "error":
            raise Exception(f"Feedback generation failed: {response.content.get('error', 'Unknown error')}")

        return response.content["feedback"]

    async def _qa_review(
        self,
        evaluations: List[Dict[str, Any]],
        scores: Dict[str, Any],
        feedback: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Send to QA Agent.

        Args:
            evaluations: List of evaluation dictionaries
            scores: Scores dictionary
            feedback: Feedback dictionary

        Returns:
            QA result dictionary
        """
        message = AgentMessage(
            sender="orchestrator",
            receiver="qa_agent",
            content={"evaluations": evaluations, "scores": scores, "feedback": feedback},
            message_type="request",
        )

        response = await self.agents["qa_agent"].process(message)

        if response.message_type == "error":
            raise Exception(f"QA review failed: {response.content.get('error', 'Unknown error')}")

        return response.content["qa_result"]

    async def _generate_report(
        self,
        answer_sheet: AnswerSheet,
        assessment_title: str,
        evaluations: List[Dict[str, Any]],
        scores: Dict[str, Any],
        feedback: Dict[str, Any],
        qa_result: Dict[str, Any],
    ) -> EvaluationReport:
        """Generate final evaluation report.

        Args:
            answer_sheet: The student's answer sheet
            assessment_title: Title of the assessment
            evaluations: List of evaluation dictionaries
            scores: Scores dictionary
            feedback: Feedback dictionary
            qa_result: QA result dictionary

        Returns:
            Complete EvaluationReport
        """
        # Convert dictionaries to Pydantic models
        question_evaluations = [AnswerEvaluation(**eval_data) for eval_data in evaluations]
        scoring_result = ScoringResult(**scores)
        feedback_report = FeedbackReport(**feedback)
        qa_result_obj = QAResult(**qa_result)

        # Determine if review is required and priority
        requires_review = qa_result_obj.requires_human_review
        review_priority = "low"

        if qa_result_obj.confidence_level == "low":
            review_priority = "high"
        elif qa_result_obj.confidence_level == "medium" or len(qa_result_obj.flags) > 0:
            review_priority = "medium"

        # Create evaluation report
        report = EvaluationReport(
            student_id=answer_sheet.student_id,
            assessment_title=assessment_title,
            assessment_date=answer_sheet.submission_time,
            scoring_result=scoring_result,
            question_evaluations=question_evaluations,
            feedback_report=feedback_report,
            qa_result=qa_result_obj,
            requires_review=requires_review,
            review_priority=review_priority,
        )

        return report


def create_orchestrator_agent(client, agents: Dict[str, BaseAgent]) -> OrchestratorAgent:
    """Factory function to create an Orchestrator Agent.

    Args:
        client: Anthropic client for Claude API
        agents: Dictionary of specialized agents

    Returns:
        Configured OrchestratorAgent instance
    """
    config = AgentConfig(
        name="orchestrator",
        system_prompt="You are the orchestrator agent.",  # Not used but required
    )
    return OrchestratorAgent(config=config, client=client, agents=agents)
