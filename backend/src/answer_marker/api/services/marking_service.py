"""Marking service for API operations.

This service integrates the existing marking components with the API layer.
"""

import asyncio
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List
from loguru import logger

from answer_marker.config import settings
from answer_marker.llm.factory import create_llm_client_from_config
from answer_marker.llm.compat import LLMClientCompat
from answer_marker.document_processing import DocumentProcessor
from answer_marker.agents.question_analyzer import create_question_analyzer_agent
from answer_marker.agents.answer_evaluator import create_answer_evaluator_agent
from answer_marker.agents.scoring_agent import create_scoring_agent
from answer_marker.agents.feedback_generator import create_feedback_generator_agent
from answer_marker.agents.qa_agent import create_qa_agent
from answer_marker.core.orchestrator import create_orchestrator_agent
from answer_marker.models.marking_guide import MarkingGuide
from answer_marker.models.answer import AnswerSheet, Answer
from answer_marker.models.report import EvaluationReport

from ..exceptions import (
    ResourceNotFoundError,
    ProcessingError,
    FileUploadError,
)


class MarkingService:
    """Service for handling marking operations via API."""

    def __init__(self):
        """Initialize the marking service."""
        self.llm_client = None
        self.doc_processor = None
        self.agents = {}
        self.orchestrator = None
        self.marking_guides: Dict[str, MarkingGuide] = {}
        self.reports: Dict[str, EvaluationReport] = {}
        self.jobs: Dict[str, dict] = {}
        self.initialized = False

        # Initialize persistent storage
        from answer_marker.storage import PersistentStorage
        storage_dir = Path(settings.data_dir) / "storage"
        self.storage = PersistentStorage(storage_dir)
        logger.info(f"Initialized persistent storage at {storage_dir}")

        # Initialize cost tracker
        from answer_marker.observability.cost_tracker import cost_tracker
        self.cost_tracker = cost_tracker

    async def initialize(self):
        """Initialize LLM client and agents.

        This is called lazily on first use to avoid initialization during import.
        """
        if self.initialized:
            return

        logger.info("Initializing marking service...")

        # Initialize LLM client
        llm_client = create_llm_client_from_config(settings)
        self.llm_client = LLMClientCompat(llm_client)

        # Initialize document processor
        self.doc_processor = DocumentProcessor(self.llm_client)

        # Create specialized agents
        self.agents = {
            "question_analyzer": create_question_analyzer_agent(self.llm_client),
            "answer_evaluator": create_answer_evaluator_agent(self.llm_client),
            "scoring_agent": create_scoring_agent(self.llm_client),
            "feedback_generator": create_feedback_generator_agent(self.llm_client),
            "qa_agent": create_qa_agent(self.llm_client),
        }

        # Create orchestrator
        self.orchestrator = create_orchestrator_agent(self.llm_client, self.agents)

        # Load existing data from persistent storage
        self.marking_guides, self.reports = self.storage.load_all_to_memory()
        logger.info(
            f"Loaded {len(self.marking_guides)} guides and {len(self.reports)} reports from storage"
        )

        self.initialized = True
        logger.info("Marking service initialized successfully")

    async def upload_marking_guide(
        self, file_path: Path, filename: str, job_id: Optional[str] = None
    ) -> tuple[str, MarkingGuide, bool]:
        """Process and store an uploaded marking guide.

        Args:
            file_path: Path to the uploaded file
            filename: Original filename
            job_id: Optional job ID for progress tracking

        Returns:
            Tuple of (guide_id, MarkingGuide, cached)
            cached=True if loaded from cache (0 API calls)

        Raises:
            FileUploadError: If file processing fails
        """
        await self.initialize()

        try:
            # Check cache first - MAJOR OPTIMIZATION!
            cached_guide_id = self.storage.check_cache(file_path)
            if cached_guide_id and cached_guide_id in self.marking_guides:
                logger.info(
                    f"⚡ CACHE HIT: Using cached marking guide {cached_guide_id} "
                    f"(0 API calls, $0.00 cost)"
                )
                return cached_guide_id, self.marking_guides[cached_guide_id], True

            logger.info(f"Processing NEW marking guide: {filename}")

            # Process marking guide
            marking_guide_data = await self.doc_processor.process_marking_guide(file_path)

            # Analyze questions with Question Analyzer agent
            analyzed_questions = []
            total_questions = len(marking_guide_data.get("questions", []))

            for i, q in enumerate(marking_guide_data.get("questions", []), 1):
                # Emit progress update if job_id provided
                if job_id:
                    from answer_marker.api.progress_tracker import progress_tracker
                    await progress_tracker.update_progress(
                        job_id,
                        current_step=i,
                        message=f"Analyzing question {i} of {total_questions}...",
                        status="processing"
                    )

                analyzed_q = await self.agents["question_analyzer"]._analyze_single_question(q)
                analyzed_questions.append(analyzed_q)

                # Record token usage (if available from Claude response)
                # Note: This requires instrumenting the agent to return token counts
                logger.debug(f"Analyzed question {i}/{total_questions}")

            # Create MarkingGuide
            guide_id = f"guide_{uuid.uuid4().hex[:8]}"
            marking_guide = MarkingGuide(
                title=marking_guide_data.get("title", filename),
                total_marks=sum(q.max_marks for q in analyzed_questions),
                questions=analyzed_questions,
                source_file=str(file_path),
            )

            # Store in memory
            self.marking_guides[guide_id] = marking_guide

            # Save to persistent storage with cache entry
            self.storage.save_marking_guide(guide_id, marking_guide, file_path)

            logger.info(
                f"✅ Marking guide {guide_id} created with {len(analyzed_questions)} questions, "
                f"total marks: {marking_guide.total_marks}"
            )

            return guide_id, marking_guide, False

        except Exception as e:
            logger.error(f"Failed to process marking guide: {e}")
            raise FileUploadError(f"Failed to process marking guide: {str(e)}")

    async def mark_answer_sheet(
        self,
        marking_guide_id: str,
        student_id: str,
        answer_sheet_path: Path,
        job_id: Optional[str] = None,
    ) -> tuple[str, EvaluationReport, bool]:
        """Mark a single answer sheet.

        Args:
            marking_guide_id: ID of the marking guide to use
            student_id: Student identifier
            answer_sheet_path: Path to the answer sheet PDF
            job_id: Optional job ID for progress tracking

        Returns:
            Tuple of (report_id, EvaluationReport, cached)
            cached=True if loaded from cache (0 API calls)

        Raises:
            ResourceNotFoundError: If marking guide not found
            ProcessingError: If marking fails
        """
        await self.initialize()

        # Get marking guide
        marking_guide = self.marking_guides.get(marking_guide_id)
        if not marking_guide:
            raise ResourceNotFoundError("Marking guide", marking_guide_id)

        try:
            # Check answer sheet cache first - MAJOR OPTIMIZATION!
            cached_report_id = self.storage.check_answer_sheet_cache(
                marking_guide_id, student_id, answer_sheet_path
            )
            if cached_report_id and cached_report_id in self.reports:
                logger.info(
                    f"⚡ CACHE HIT: Using cached report {cached_report_id} for {student_id} "
                    f"(0 API calls, $0.00 cost)"
                )
                return cached_report_id, self.reports[cached_report_id], True

            logger.info(f"Marking NEW answer sheet for student {student_id}")

            # Emit progress: Starting
            if job_id:
                from answer_marker.api.progress_tracker import progress_tracker
                await progress_tracker.update_progress(
                    job_id,
                    current_step=1,
                    message="Processing answer sheet...",
                    status="processing"
                )

            # Process answer sheet
            expected_questions = [q.id for q in marking_guide.questions]
            answer_sheet_data = await self.doc_processor.process_answer_sheet(
                answer_sheet_path, expected_questions
            )

            # Convert to AnswerSheet model
            answers = [
                Answer(
                    question_id=ans["question_id"],
                    answer_text=ans.get("answer_text", ""),
                    is_blank=ans.get("is_blank", False),
                )
                for ans in answer_sheet_data.get("answers", [])
            ]

            answer_sheet = AnswerSheet(
                student_id=student_id,
                answers=answers,
            )

            # Emit progress: Evaluating answers
            if job_id:
                await progress_tracker.update_progress(
                    job_id,
                    current_step=2,
                    message=f"Evaluating {len(marking_guide.questions)} answers...",
                    status="processing"
                )

            # Mark the answer sheet
            report = await self.orchestrator.mark_answer_sheet(
                marking_guide=marking_guide,
                answer_sheet=answer_sheet,
                assessment_title=marking_guide.title,
            )

            # Generate report ID and store
            report_id = f"report_{uuid.uuid4().hex[:8]}"
            self.reports[report_id] = report

            # Save to persistent storage
            self.storage.save_report(report_id, report, marking_guide_id)

            # Register answer sheet in cache
            self.storage.register_answer_sheet(
                marking_guide_id, student_id, answer_sheet_path, report_id
            )

            logger.info(
                f"✅ Marking complete for {student_id}: "
                f"{report.scoring_result.total_marks}/{report.scoring_result.max_marks}"
            )

            return report_id, report, False

        except Exception as e:
            logger.error(f"Failed to mark answer sheet: {e}")
            raise ProcessingError(f"Failed to mark answer sheet: {str(e)}")

    async def get_marking_guide(self, guide_id: str) -> MarkingGuide:
        """Get a marking guide by ID.

        Args:
            guide_id: Marking guide ID

        Returns:
            MarkingGuide

        Raises:
            ResourceNotFoundError: If not found
        """
        await self.initialize()
        guide = self.marking_guides.get(guide_id)
        if not guide:
            raise ResourceNotFoundError("Marking guide", guide_id)
        return guide

    async def get_report(self, report_id: str) -> EvaluationReport:
        """Get a marking report by ID.

        Args:
            report_id: Report ID

        Returns:
            EvaluationReport

        Raises:
            ResourceNotFoundError: If not found
        """
        await self.initialize()
        report = self.reports.get(report_id)
        if not report:
            raise ResourceNotFoundError("Report", report_id)
        return report

    async def list_marking_guides(self) -> List[str]:
        """List all available marking guide IDs."""
        await self.initialize()
        return list(self.marking_guides.keys())

    async def list_reports(self) -> List[str]:
        """List all available report IDs."""
        await self.initialize()
        return list(self.reports.keys())


# Global service instance
marking_service = MarkingService()
