"""Marking routes."""

import uuid
import shutil
import asyncio
from pathlib import Path
from typing import List
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status, BackgroundTasks
from fastapi.responses import StreamingResponse
from loguru import logger

from ..config import api_settings
from ..models.requests import MarkingSingleRequest
from ..models.responses import (
    UploadResponse,
    MarkingGuideResponse,
    MarkingReportResponse,
    QuestionSummary,
    QuestionDetailResponse,
    KeyConceptResponse,
    EvaluationCriteriaResponse,
    ScoreSummary,
    QuestionEvaluationResponse,
)
from ..exceptions import FileUploadError, ResourceNotFoundError
from ..services.marking_service import marking_service
from ..progress_tracker import progress_tracker

router = APIRouter(prefix="/api/v1", tags=["Marking"])


@router.post(
    "/marking-guides/upload",
    response_model=MarkingGuideResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Assessment",
    description="Create a new assessment with marking guide PDF and metadata",
)
async def upload_marking_guide(
    title: str = Form(..., description="Assessment name/title"),
    file: UploadFile = File(..., description="Marking guide PDF file"),
    description: str = Form(None, description="Assessment description"),
    subject: str = Form(None, description="Subject/course name"),
    grade: str = Form(None, description="Grade level"),
) -> MarkingGuideResponse:
    """Upload and process a marking guide.

    The marking guide is analyzed to extract questions, marking schemes,
    and evaluation criteria.
    """
    # Validate file type
    if not file.filename.endswith(".pdf"):
        raise FileUploadError("Only PDF files are supported")

    # Create upload directory
    upload_dir = Path(api_settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Save uploaded file
    file_id = f"file_{uuid.uuid4().hex[:8]}"
    file_path = upload_dir / f"{file_id}_{file.filename}"

    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        logger.info(f"Saved uploaded file: {file_path}")

        # Process marking guide (with caching!)
        guide_id, marking_guide, cached = await marking_service.upload_marking_guide(
            file_path=file_path,
            filename=file.filename,
            title=title,
            description=description,
            subject=subject,
            grade=grade,
        )

        if cached:
            logger.info(f"⚡ Returned cached guide {guide_id} - 0 API calls!")

        # Build response with full question details
        question_details = [
            QuestionDetailResponse(
                question_id=q.id,
                question_number=q.question_number,  # Use actual question number
                question_text=q.question_text,
                question_type=q.question_type.value if hasattr(q.question_type, 'value') else str(q.question_type),
                max_marks=q.max_marks,
                key_concepts=[
                    KeyConceptResponse(
                        concept=kc.concept,
                        points=kc.points,
                        mandatory=kc.mandatory,
                        keywords=kc.keywords,
                        description=kc.description,
                    )
                    for kc in q.key_concepts
                ],
                evaluation_criteria=EvaluationCriteriaResponse(
                    excellent=q.evaluation_criteria.excellent,
                    good=q.evaluation_criteria.good,
                    satisfactory=q.evaluation_criteria.satisfactory,
                    poor=q.evaluation_criteria.poor,
                ),
                keywords=q.keywords,
                common_mistakes=q.common_mistakes,
                sample_answer=q.sample_answer,
                instructions=q.instructions,
            )
            for q in marking_guide.questions
        ]

        return MarkingGuideResponse(
            guide_id=guide_id,
            title=marking_guide.title,
            description=getattr(marking_guide, 'description', None),
            subject=getattr(marking_guide, 'subject', None),
            grade=getattr(marking_guide, 'grade', None),
            total_marks=marking_guide.total_marks,
            num_questions=len(marking_guide.questions),
            questions=question_details,
            analyzed=True,
            created_at=datetime.now(),
        )

    except FileUploadError:
        raise
    except Exception as e:
        logger.error(f"Failed to process marking guide: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process marking guide: {str(e)}",
        )
    finally:
        await file.close()


@router.get(
    "/marking-guides",
    response_model=List[str],
    summary="List Marking Guides",
    description="List all available marking guide IDs",
)
async def list_marking_guides() -> List[str]:
    """List all uploaded marking guides."""
    return await marking_service.list_marking_guides()


@router.get(
    "/progress/{job_id}",
    summary="Get Upload Progress (SSE)",
    description="Stream real-time progress updates for marking guide upload",
)
async def get_upload_progress(job_id: str):
    """Stream Server-Sent Events for upload progress."""
    return StreamingResponse(
        progress_tracker.get_progress_stream(job_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


@router.get(
    "/marking-guides/{guide_id}",
    response_model=MarkingGuideResponse,
    summary="Get Marking Guide",
    description="Get details of a specific marking guide",
)
async def get_marking_guide(guide_id: str) -> MarkingGuideResponse:
    """Get marking guide details."""
    try:
        marking_guide = await marking_service.get_marking_guide(guide_id)

        # Build response with full question details
        question_details = [
            QuestionDetailResponse(
                question_id=q.id,
                question_number=q.question_number,  # Use actual question number
                question_text=q.question_text,
                question_type=q.question_type.value if hasattr(q.question_type, 'value') else str(q.question_type),
                max_marks=q.max_marks,
                key_concepts=[
                    KeyConceptResponse(
                        concept=kc.concept,
                        points=kc.points,
                        mandatory=kc.mandatory,
                        keywords=kc.keywords,
                        description=kc.description,
                    )
                    for kc in q.key_concepts
                ],
                evaluation_criteria=EvaluationCriteriaResponse(
                    excellent=q.evaluation_criteria.excellent,
                    good=q.evaluation_criteria.good,
                    satisfactory=q.evaluation_criteria.satisfactory,
                    poor=q.evaluation_criteria.poor,
                ),
                keywords=q.keywords,
                common_mistakes=q.common_mistakes,
                sample_answer=q.sample_answer,
                instructions=q.instructions,
            )
            for q in marking_guide.questions
        ]

        return MarkingGuideResponse(
            guide_id=guide_id,
            title=marking_guide.title,
            description=getattr(marking_guide, 'description', None),
            subject=getattr(marking_guide, 'subject', None),
            grade=getattr(marking_guide, 'grade', None),
            total_marks=marking_guide.total_marks,
            num_questions=len(marking_guide.questions),
            questions=question_details,
            analyzed=True,
            created_at=datetime.now(),
        )

    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Marking guide {guide_id} not found",
        )


@router.post(
    "/answer-sheets/mark",
    response_model=MarkingReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Mark Answer Sheet",
    description="Mark a single student's answer sheet",
)
async def mark_answer_sheet(
    marking_guide_id: str = Form(..., description="Marking guide ID"),
    student_id: str = Form(..., description="Student identifier"),
    file: UploadFile = File(..., description="Answer sheet PDF"),
) -> MarkingReportResponse:
    """Mark a single answer sheet.

    The answer sheet is processed, answers are extracted, and each answer
    is evaluated against the marking guide using AI agents.
    """
    # Validate file type
    if not file.filename.endswith(".pdf"):
        raise FileUploadError("Only PDF files are supported")

    # Create upload directory
    upload_dir = Path(api_settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Save uploaded file
    file_id = f"file_{uuid.uuid4().hex[:8]}"
    file_path = upload_dir / f"{file_id}_{file.filename}"

    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        logger.info(f"Saved uploaded answer sheet: {file_path}")

        # Mark the answer sheet (with caching!)
        report_id, report, cached = await marking_service.mark_answer_sheet(
            marking_guide_id, student_id, file_path
        )

        if cached:
            logger.info(f"⚡ Returned cached report {report_id} - 0 API calls!")

        # Map question evaluations to response models
        question_evaluations = [
            QuestionEvaluationResponse(
                question_id=qe.question_id,
                question_number=qe.question_number,  # Preserve question number for display
                marks_awarded=qe.marks_awarded,
                max_marks=qe.max_marks,
                percentage=qe.percentage,
                overall_quality=qe.overall_quality,
                strengths=qe.strengths,
                weaknesses=qe.weaknesses,
                requires_human_review=qe.requires_human_review,
            )
            for qe in report.question_evaluations
        ]

        return MarkingReportResponse(
            report_id=report_id,
            student_id=report.student_id,
            marking_guide_id=marking_guide_id,
            assessment_title=report.assessment_title,
            score=ScoreSummary(
                total_marks=report.scoring_result.total_marks,
                max_marks=report.scoring_result.max_marks,
                percentage=report.scoring_result.percentage,
                grade=report.scoring_result.grade,
                passed=report.scoring_result.passed,
            ),
            num_questions=len(report.question_evaluations),
            requires_review=report.requires_review,
            processing_time=report.processing_time,
            marked_at=datetime.now(),
            question_evaluations=question_evaluations,
        )

    except ResourceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e.message),
        )
    except Exception as e:
        logger.error(f"Failed to mark answer sheet: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark answer sheet: {str(e)}",
        )
    finally:
        await file.close()


@router.get(
    "/reports",
    response_model=List[str],
    summary="List Reports",
    description="List all available marking report IDs",
)
async def list_reports() -> List[str]:
    """List all generated marking reports."""
    return await marking_service.list_reports()


@router.get(
    "/reports/{report_id}",
    response_model=MarkingReportResponse,
    summary="Get Report",
    description="Get a specific marking report",
)
async def get_report(report_id: str) -> MarkingReportResponse:
    """Get marking report details."""
    try:
        report = await marking_service.get_report(report_id)

        # Get marking_guide_id from storage metadata
        marking_guide_id = marking_service.storage.metadata.get("reports", {}).get(report_id, {}).get("marking_guide_id", "")

        # Map question evaluations to response models
        question_evaluations = [
            QuestionEvaluationResponse(
                question_id=qe.question_id,
                question_number=qe.question_number,  # Preserve question number for display
                marks_awarded=qe.marks_awarded,
                max_marks=qe.max_marks,
                percentage=qe.percentage,
                overall_quality=qe.overall_quality,
                strengths=qe.strengths,
                weaknesses=qe.weaknesses,
                requires_human_review=qe.requires_human_review,
            )
            for qe in report.question_evaluations
        ]

        return MarkingReportResponse(
            report_id=report_id,
            student_id=report.student_id,
            marking_guide_id=marking_guide_id,
            assessment_title=report.assessment_title,
            score=ScoreSummary(
                total_marks=report.scoring_result.total_marks,
                max_marks=report.scoring_result.max_marks,
                percentage=report.scoring_result.percentage,
                grade=report.scoring_result.grade,
                passed=report.scoring_result.passed,
            ),
            num_questions=len(report.question_evaluations),
            requires_review=report.requires_review,
            processing_time=report.processing_time,
            marked_at=datetime.now(),
            question_evaluations=question_evaluations,
        )

    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report {report_id} not found",
        )
