"""Marking routes."""

import uuid
import shutil
from pathlib import Path
from typing import List
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from loguru import logger

from ..config import api_settings
from ..models.requests import MarkingSingleRequest
from ..models.responses import (
    UploadResponse,
    MarkingGuideResponse,
    MarkingReportResponse,
    QuestionSummary,
    ScoreSummary,
)
from ..exceptions import FileUploadError, ResourceNotFoundError
from ..services.marking_service import marking_service

router = APIRouter(prefix="/api/v1", tags=["Marking"])


@router.post(
    "/marking-guides/upload",
    response_model=MarkingGuideResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload Marking Guide",
    description="Upload a marking guide PDF for processing and analysis",
)
async def upload_marking_guide(
    file: UploadFile = File(..., description="Marking guide PDF file"),
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

        # Process marking guide
        guide_id, marking_guide = await marking_service.upload_marking_guide(
            file_path, file.filename
        )

        # Build response
        question_summaries = [
            QuestionSummary(
                question_id=q.id,
                question_number=q.id,  # Use id as question_number
                max_marks=q.max_marks,
                question_type=q.question_type,
                has_rubric=bool(q.evaluation_criteria),
            )
            for q in marking_guide.questions
        ]

        return MarkingGuideResponse(
            guide_id=guide_id,
            title=marking_guide.title,
            total_marks=marking_guide.total_marks,
            num_questions=len(marking_guide.questions),
            questions=question_summaries,
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
    return marking_service.list_marking_guides()


@router.get(
    "/marking-guides/{guide_id}",
    response_model=MarkingGuideResponse,
    summary="Get Marking Guide",
    description="Get details of a specific marking guide",
)
async def get_marking_guide(guide_id: str) -> MarkingGuideResponse:
    """Get marking guide details."""
    try:
        marking_guide = marking_service.get_marking_guide(guide_id)

        question_summaries = [
            QuestionSummary(
                question_id=q.id,
                question_number=q.id,  # Use id as question_number
                max_marks=q.max_marks,
                question_type=q.question_type,
                has_rubric=bool(q.evaluation_criteria),
            )
            for q in marking_guide.questions
        ]

        return MarkingGuideResponse(
            guide_id=guide_id,
            title=marking_guide.title,
            total_marks=marking_guide.total_marks,
            num_questions=len(marking_guide.questions),
            questions=question_summaries,
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

        # Mark the answer sheet
        report = await marking_service.mark_answer_sheet(
            marking_guide_id, student_id, file_path
        )

        # Build response
        report_id = f"report_{uuid.uuid4().hex[:8]}"
        marking_service.reports[report_id] = report

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
            num_questions=len(report.question_results),
            requires_review=report.requires_review,
            processing_time=report.processing_time,
            marked_at=datetime.now(),
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
    return marking_service.list_reports()


@router.get(
    "/reports/{report_id}",
    response_model=MarkingReportResponse,
    summary="Get Report",
    description="Get a specific marking report",
)
async def get_report(report_id: str) -> MarkingReportResponse:
    """Get marking report details."""
    try:
        report = marking_service.get_report(report_id)

        return MarkingReportResponse(
            report_id=report_id,
            student_id=report.student_id,
            marking_guide_id="",  # Not stored in report currently
            assessment_title=report.assessment_title,
            score=ScoreSummary(
                total_marks=report.scoring_result.total_marks,
                max_marks=report.scoring_result.max_marks,
                percentage=report.scoring_result.percentage,
                grade=report.scoring_result.grade,
                passed=report.scoring_result.passed,
            ),
            num_questions=len(report.question_results),
            requires_review=report.requires_review,
            processing_time=report.processing_time,
            marked_at=datetime.now(),
        )

    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report {report_id} not found",
        )
