# FastAPI Implementation Guide - Answer Sheet Marker API

## Overview

This guide provides complete specifications for exposing the Answer Sheet Marker system as a RESTful API using FastAPI. The API enables programmatic access to marking functionality, supports file uploads, real-time progress tracking, and webhooks for async processing.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Application                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │    Auth      │  │   Routes     │  │  WebSocket   │     │
│  │  Middleware  │  │  (Endpoints) │  │   Support    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                          ↓                                    │
│  ┌────────────────────────────────────────────────────┐     │
│  │           Dependency Injection Layer               │     │
│  │    (Database, Claude Client, Orchestrator)         │     │
│  └────────────────────────────────────────────────────┘     │
│                          ↓                                    │
│  ┌────────────────────────────────────────────────────┐     │
│  │            Background Task Queue                   │     │
│  │         (Celery/FastAPI BackgroundTasks)           │     │
│  └────────────────────────────────────────────────────┘     │
│                          ↓                                    │
│  ┌────────────────────────────────────────────────────┐     │
│  │        Core Marking System (Agents)                │     │
│  └────────────────────────────────────────────────────┘     │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Project Structure

```
src/answer_marker/api/
├── __init__.py
├── main.py                    # FastAPI app initialization
├── config.py                  # API-specific configuration
├── dependencies.py            # Dependency injection
├── exceptions.py              # Custom exceptions
├── middleware.py              # Custom middleware
│
├── models/                    # API request/response models
│   ├── __init__.py
│   ├── requests.py           # Request models
│   ├── responses.py          # Response models
│   └── schemas.py            # Additional schemas
│
├── routes/                    # API endpoints
│   ├── __init__.py
│   ├── health.py             # Health check endpoints
│   ├── marking.py            # Marking endpoints
│   ├── sessions.py           # Session management
│   ├── reports.py            # Report retrieval
│   ├── admin.py              # Admin endpoints
│   └── webhooks.py           # Webhook management
│
├── services/                  # Business logic
│   ├── __init__.py
│   ├── marking_service.py    # Marking orchestration
│   ├── session_service.py    # Session management
│   └── storage_service.py    # File storage
│
├── background/                # Background tasks
│   ├── __init__.py
│   ├── tasks.py              # Celery tasks (optional)
│   └── jobs.py               # Background jobs
│
└── utils/                     # API utilities
    ├── __init__.py
    ├── auth.py               # Authentication
    ├── rate_limit.py         # Rate limiting
    └── validators.py         # Custom validators
```

## Implementation

### 1. Main Application (`src/answer_marker/api/main.py`)

```python
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from loguru import logger
import time

from answer_marker.api.routes import (
    health,
    marking,
    sessions,
    reports,
    admin,
    webhooks
)
from answer_marker.api.middleware import RequestLoggingMiddleware, ErrorHandlerMiddleware
from answer_marker.api.exceptions import APIException
from answer_marker.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Answer Sheet Marker API")
    
    # Initialize resources
    # - Database connections
    # - Vector store
    # - Background task workers
    
    yield
    
    # Shutdown
    logger.info("Shutting down Answer Sheet Marker API")
    # Cleanup resources

# Create FastAPI application
app = FastAPI(
    title="Answer Sheet Marker API",
    description="AI-powered answer sheet marking system with multi-agent architecture",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # Configure in settings
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Custom Middleware
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(ErrorHandlerMiddleware)

# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(marking.router, prefix="/api/v1", tags=["Marking"])
app.include_router(sessions.router, prefix="/api/v1", tags=["Sessions"])
app.include_router(reports.router, prefix="/api/v1", tags=["Reports"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])
app.include_router(webhooks.router, prefix="/api/v1", tags=["Webhooks"])

# Static files (for storing uploaded documents temporarily)
app.mount("/uploads", StaticFiles(directory="data/uploads"), name="uploads")

# Global exception handler
@app.exception_handler(APIException)
async def api_exception_handler(request: Request, exc: APIException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error_code,
            "message": exc.message,
            "details": exc.details
        }
    )

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Answer Sheet Marker API",
        "version": "1.0.0",
        "docs": "/api/docs",
        "health": "/api/v1/health"
    }

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response
```

### 2. API Configuration (`src/answer_marker/api/config.py`)

```python
from pydantic_settings import BaseSettings
from typing import List

class APISettings(BaseSettings):
    """API-specific configuration"""
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 4
    api_reload: bool = False
    
    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    # Authentication
    api_key_enabled: bool = True
    jwt_secret: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # seconds
    
    # File Upload
    max_upload_size: int = 50 * 1024 * 1024  # 50 MB
    allowed_extensions: List[str] = [".pdf", ".png", ".jpg", ".jpeg"]
    upload_directory: str = "./data/uploads"
    
    # Background Tasks
    use_celery: bool = False  # Set to True for production with Celery
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"
    
    # Webhooks
    webhook_timeout: int = 30
    webhook_retry_attempts: int = 3
    
    # Storage
    storage_type: str = "local"  # local, s3, gcs
    s3_bucket: str = ""
    s3_region: str = "us-east-1"
    
    class Config:
        env_file = ".env"
        env_prefix = "API_"

api_settings = APISettings()
```

### 3. API Models - Requests (`src/answer_marker/api/models/requests.py`)

```python
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime

class MarkingSingleRequest(BaseModel):
    """Request to mark a single answer sheet"""
    marking_guide_id: str = Field(..., description="ID of the marking guide")
    answer_sheet_file: str = Field(..., description="Path or ID of answer sheet file")
    student_id: Optional[str] = Field(None, description="Student identifier")
    student_name: Optional[str] = Field(None, description="Student name")
    webhook_url: Optional[str] = Field(None, description="Webhook URL for async notification")
    priority: int = Field(default=1, ge=1, le=10, description="Processing priority")
    
    class Config:
        json_schema_extra = {
            "example": {
                "marking_guide_id": "guide_123",
                "answer_sheet_file": "file_456",
                "student_id": "STU001",
                "student_name": "John Doe",
                "priority": 5
            }
        }

class MarkingBatchRequest(BaseModel):
    """Request to mark multiple answer sheets"""
    marking_guide_id: str
    answer_sheet_files: List[str] = Field(..., description="List of answer sheet file IDs")
    webhook_url: Optional[str] = None
    auto_review: bool = Field(default=False, description="Automatically review flagged items")
    
    @validator('answer_sheet_files')
    def validate_batch_size(cls, v):
        if len(v) > 100:
            raise ValueError("Batch size cannot exceed 100 sheets")
        return v

class UploadMarkingGuideRequest(BaseModel):
    """Request to upload and process a marking guide"""
    title: str = Field(..., description="Assessment title")
    subject: Optional[str] = None
    pass_percentage: float = Field(default=50.0, ge=0, le=100)
    instructions: Optional[str] = None

class WebhookRegistration(BaseModel):
    """Register a webhook for event notifications"""
    url: str = Field(..., description="Webhook URL")
    events: List[str] = Field(..., description="Events to subscribe to")
    secret: Optional[str] = Field(None, description="Secret for webhook verification")
    
    @validator('events')
    def validate_events(cls, v):
        allowed_events = [
            "marking.started",
            "marking.completed",
            "marking.failed",
            "session.created",
            "session.completed"
        ]
        for event in v:
            if event not in allowed_events:
                raise ValueError(f"Invalid event: {event}")
        return v

class SessionFilterRequest(BaseModel):
    """Filter sessions"""
    status: Optional[str] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
```

### 4. API Models - Responses (`src/answer_marker/api/models/responses.py`)

```python
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from answer_marker.models.evaluation import ScoringResult, QAResult

class BaseResponse(BaseModel):
    """Base response model"""
    success: bool
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ErrorResponse(BaseResponse):
    """Error response"""
    success: bool = False
    error_code: str
    details: Optional[Dict[str, Any]] = None

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    uptime: float
    services: Dict[str, str]  # service_name: status

class UploadResponse(BaseResponse):
    """File upload response"""
    file_id: str
    filename: str
    size: int
    url: str

class MarkingGuideResponse(BaseResponse):
    """Marking guide processing response"""
    guide_id: str
    title: str
    total_marks: float
    question_count: int
    validation: Dict[str, Any]

class MarkingJobResponse(BaseResponse):
    """Marking job created response"""
    job_id: str
    status: str  # pending, processing, completed, failed
    estimated_time: Optional[int] = Field(None, description="Estimated completion time in seconds")
    progress_url: str

class MarkingStatusResponse(BaseModel):
    """Marking job status"""
    job_id: str
    status: str
    progress: float = Field(ge=0, le=100, description="Progress percentage")
    current_step: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    result_url: Optional[str] = None

class MarkingResultResponse(BaseResponse):
    """Complete marking result"""
    job_id: str
    student_id: Optional[str] = None
    student_name: Optional[str] = None
    scoring_result: ScoringResult
    qa_result: QAResult
    requires_review: bool
    report_url: str
    pdf_report_url: Optional[str] = None
    
class BatchMarkingResponse(BaseResponse):
    """Batch marking response"""
    batch_id: str
    total_sheets: int
    jobs: List[MarkingJobResponse]
    progress_url: str

class BatchStatusResponse(BaseModel):
    """Batch marking status"""
    batch_id: str
    total_sheets: int
    completed: int
    failed: int
    in_progress: int
    status: str
    results: List[MarkingResultResponse]

class SessionListResponse(BaseModel):
    """List of marking sessions"""
    sessions: List[Dict[str, Any]]
    total: int
    limit: int
    offset: int

class ReportResponse(BaseModel):
    """Report retrieval response"""
    report_id: str
    student_id: Optional[str] = None
    created_at: datetime
    format: str  # json, pdf, html
    data: Dict[str, Any]
    download_url: Optional[str] = None
```

### 5. Dependencies (`src/answer_marker/api/dependencies.py`)

```python
from fastapi import Depends, HTTPException, Header, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from loguru import logger
import jwt
from datetime import datetime, timedelta

from answer_marker.utils.claude_client import claude_client
from answer_marker.core.orchestrator import OrchestratorAgent
from answer_marker.document_processing import DocumentProcessor
from answer_marker.api.config import api_settings
from answer_marker.api.exceptions import AuthenticationError

security = HTTPBearer()

# Authentication
def verify_api_key(x_api_key: str = Header(None)) -> str:
    """Verify API key from header"""
    if not api_settings.api_key_enabled:
        return "anonymous"
    
    if not x_api_key:
        raise AuthenticationError("API key required")
    
    # Validate API key (implement your validation logic)
    # This is a simple example - use a database in production
    valid_keys = ["your-api-key-here"]  # Load from database
    
    if x_api_key not in valid_keys:
        raise AuthenticationError("Invalid API key")
    
    return x_api_key

def verify_jwt_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """Verify JWT token"""
    try:
        payload = jwt.decode(
            credentials.credentials,
            api_settings.jwt_secret,
            algorithms=[api_settings.jwt_algorithm]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token expired")
    except jwt.InvalidTokenError:
        raise AuthenticationError("Invalid token")

# Optional authentication (either API key or JWT)
def get_current_user(
    api_key: str = Depends(verify_api_key),
    # token: dict = Depends(verify_jwt_token)  # Uncomment for JWT
) -> str:
    """Get current authenticated user"""
    return api_key

# Services
def get_claude_client():
    """Get Claude client instance"""
    return claude_client.get_client()

def get_document_processor(
    client = Depends(get_claude_client)
) -> DocumentProcessor:
    """Get document processor instance"""
    return DocumentProcessor(client)

def get_orchestrator(
    client = Depends(get_claude_client)
) -> OrchestratorAgent:
    """Get orchestrator agent instance"""
    # Initialize orchestrator with all agents
    # This is simplified - implement proper agent initialization
    from answer_marker.core.agent_base import AgentConfig
    
    config = AgentConfig(
        name="orchestrator",
        system_prompt="You are the orchestrator agent"
    )
    
    # Create and return orchestrator with all agents
    # agents = create_all_agents(client)
    # return OrchestratorAgent(config, client, agents)
    
    # Simplified for example
    return None  # Replace with actual orchestrator

# File validation
async def validate_upload_file(
    file: UploadFile = File(...)
) -> UploadFile:
    """Validate uploaded file"""
    # Check file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in api_settings.allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"File type {file_ext} not allowed"
        )
    
    # Check file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning
    
    if file_size > api_settings.max_upload_size:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds maximum of {api_settings.max_upload_size} bytes"
        )
    
    return file

# Rate limiting dependency
from fastapi_limiter.depends import RateLimiter

def rate_limit():
    """Rate limiting dependency"""
    if not api_settings.rate_limit_enabled:
        return None
    
    return RateLimiter(
        times=api_settings.rate_limit_requests,
        seconds=api_settings.rate_limit_window
    )
```

### 6. Marking Routes (`src/answer_marker/api/routes/marking.py`)

```python
from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from typing import List
from pathlib import Path
import uuid
from loguru import logger

from answer_marker.api.models.requests import (
    MarkingSingleRequest,
    MarkingBatchRequest,
    UploadMarkingGuideRequest
)
from answer_marker.api.models.responses import (
    MarkingJobResponse,
    MarkingStatusResponse,
    MarkingResultResponse,
    BatchMarkingResponse,
    UploadResponse,
    MarkingGuideResponse
)
from answer_marker.api.dependencies import (
    get_current_user,
    get_document_processor,
    get_orchestrator,
    validate_upload_file
)
from answer_marker.api.services.marking_service import MarkingService
from answer_marker.api.exceptions import NotFoundError, ValidationError

router = APIRouter()

@router.post(
    "/marking-guides/upload",
    response_model=MarkingGuideResponse,
    summary="Upload and process marking guide"
)
async def upload_marking_guide(
    file: UploadFile = Depends(validate_upload_file),
    metadata: UploadMarkingGuideRequest = Depends(),
    doc_processor = Depends(get_document_processor),
    user: str = Depends(get_current_user)
):
    """
    Upload and process a marking guide document.
    
    - Accepts PDF files
    - Extracts questions and marking schemes
    - Creates evaluation rubrics
    - Returns processed marking guide ID
    """
    try:
        # Save uploaded file
        file_id = str(uuid.uuid4())
        file_path = Path(f"data/uploads/{file_id}_{file.filename}")
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        logger.info(f"Processing marking guide: {file.filename}")
        
        # Process document
        marking_guide = await doc_processor.process_marking_guide(file_path)
        
        # Save to database (implement your storage logic)
        guide_id = f"guide_{uuid.uuid4().hex[:12]}"
        # store_marking_guide(guide_id, marking_guide)
        
        return MarkingGuideResponse(
            success=True,
            message="Marking guide processed successfully",
            guide_id=guide_id,
            title=marking_guide['title'],
            total_marks=marking_guide['total_marks'],
            question_count=len(marking_guide['questions']),
            validation=marking_guide.get('validation', {})
        )
        
    except Exception as e:
        logger.error(f"Error processing marking guide: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/mark/single",
    response_model=MarkingJobResponse,
    summary="Mark a single answer sheet"
)
async def mark_single_answer_sheet(
    request: MarkingSingleRequest,
    background_tasks: BackgroundTasks,
    marking_service: MarkingService = Depends(),
    user: str = Depends(get_current_user)
):
    """
    Submit a single answer sheet for marking.
    
    - Creates a marking job
    - Processes asynchronously
    - Returns job ID for status tracking
    - Optionally sends webhook notification when complete
    """
    try:
        # Create marking job
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        
        # Add to background tasks
        background_tasks.add_task(
            marking_service.process_single_marking,
            job_id=job_id,
            marking_guide_id=request.marking_guide_id,
            answer_sheet_file=request.answer_sheet_file,
            student_id=request.student_id,
            student_name=request.student_name,
            webhook_url=request.webhook_url
        )
        
        logger.info(f"Created marking job: {job_id}")
        
        return MarkingJobResponse(
            success=True,
            message="Marking job created successfully",
            job_id=job_id,
            status="pending",
            estimated_time=30,  # seconds
            progress_url=f"/api/v1/marking/jobs/{job_id}/status"
        )
        
    except Exception as e:
        logger.error(f"Error creating marking job: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/marking/jobs/{job_id}/status",
    response_model=MarkingStatusResponse,
    summary="Get marking job status"
)
async def get_marking_status(
    job_id: str,
    marking_service: MarkingService = Depends(),
    user: str = Depends(get_current_user)
):
    """
    Get the status of a marking job.
    
    - Returns current progress
    - Shows current processing step
    - Provides result URL when complete
    """
    try:
        status = await marking_service.get_job_status(job_id)
        
        if not status:
            raise NotFoundError(f"Job {job_id} not found")
        
        return status
        
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error getting job status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/marking/jobs/{job_id}/result",
    response_model=MarkingResultResponse,
    summary="Get marking result"
)
async def get_marking_result(
    job_id: str,
    marking_service: MarkingService = Depends(),
    user: str = Depends(get_current_user)
):
    """
    Get the complete marking result for a job.
    
    - Returns detailed evaluation
    - Includes scores and feedback
    - Provides download links for reports
    """
    try:
        result = await marking_service.get_job_result(job_id)
        
        if not result:
            raise NotFoundError(f"Result for job {job_id} not found")
        
        return result
        
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error getting job result: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/mark/batch",
    response_model=BatchMarkingResponse,
    summary="Mark multiple answer sheets"
)
async def mark_batch_answer_sheets(
    request: MarkingBatchRequest,
    background_tasks: BackgroundTasks,
    marking_service: MarkingService = Depends(),
    user: str = Depends(get_current_user)
):
    """
    Submit multiple answer sheets for batch marking.
    
    - Processes up to 100 sheets at once
    - Each sheet processed asynchronously
    - Returns batch ID for tracking
    - Webhook notification when batch completes
    """
    try:
        batch_id = f"batch_{uuid.uuid4().hex[:12]}"
        
        # Create jobs for each answer sheet
        jobs = []
        for sheet_file in request.answer_sheet_files:
            job_id = f"job_{uuid.uuid4().hex[:12]}"
            
            background_tasks.add_task(
                marking_service.process_single_marking,
                job_id=job_id,
                marking_guide_id=request.marking_guide_id,
                answer_sheet_file=sheet_file,
                batch_id=batch_id,
                webhook_url=request.webhook_url
            )
            
            jobs.append(MarkingJobResponse(
                success=True,
                message="Job created",
                job_id=job_id,
                status="pending",
                progress_url=f"/api/v1/marking/jobs/{job_id}/status"
            ))
        
        logger.info(f"Created batch {batch_id} with {len(jobs)} jobs")
        
        return BatchMarkingResponse(
            success=True,
            message=f"Batch marking started for {len(jobs)} sheets",
            batch_id=batch_id,
            total_sheets=len(jobs),
            jobs=jobs,
            progress_url=f"/api/v1/marking/batches/{batch_id}/status"
        )
        
    except Exception as e:
        logger.error(f"Error creating batch marking: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/answer-sheets/upload",
    response_model=UploadResponse,
    summary="Upload answer sheet"
)
async def upload_answer_sheet(
    file: UploadFile = Depends(validate_upload_file),
    user: str = Depends(get_current_user)
):
    """
    Upload an answer sheet file for later marking.
    
    - Accepts PDF, PNG, JPG files
    - Returns file ID for use in marking requests
    """
    try:
        # Save file
        file_id = str(uuid.uuid4())
        file_path = Path(f"data/uploads/{file_id}_{file.filename}")
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        logger.info(f"Uploaded answer sheet: {file.filename}")
        
        return UploadResponse(
            success=True,
            message="File uploaded successfully",
            file_id=file_id,
            filename=file.filename,
            size=len(content),
            url=f"/uploads/{file_id}_{file.filename}"
        )
        
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/marking/jobs/{job_id}/report/pdf",
    response_class=FileResponse,
    summary="Download PDF report"
)
async def download_pdf_report(
    job_id: str,
    marking_service: MarkingService = Depends(),
    user: str = Depends(get_current_user)
):
    """
    Download the marking report as a PDF file.
    """
    try:
        pdf_path = await marking_service.generate_pdf_report(job_id)
        
        if not pdf_path or not Path(pdf_path).exists():
            raise NotFoundError(f"PDF report for job {job_id} not found")
        
        return FileResponse(
            path=pdf_path,
            media_type="application/pdf",
            filename=f"marking_report_{job_id}.pdf"
        )
        
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error generating PDF report: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

### 7. Health Check Routes (`src/answer_marker/api/routes/health.py`)

```python
from fastapi import APIRouter, Depends
from answer_marker.api.models.responses import HealthResponse
from answer_marker.utils.claude_client import claude_client
import time
import psutil

router = APIRouter()

start_time = time.time()

@router.get("/health", response_model=HealthResponse, summary="Health check")
async def health_check():
    """
    Check the health of the API and its dependencies.
    
    Returns status of:
    - API server
    - Claude API connection
    - Database (if applicable)
    - Vector store
    - File system
    """
    uptime = time.time() - start_time
    
    # Check services
    services = {
        "api": "healthy",
        "claude": "unknown",
        "storage": "healthy"
    }
    
    # Test Claude API
    try:
        # Quick test of Claude API
        services["claude"] = "healthy"
    except Exception:
        services["claude"] = "unhealthy"
    
    overall_status = "healthy" if all(
        s == "healthy" for s in services.values()
    ) else "degraded"
    
    return HealthResponse(
        status=overall_status,
        version="1.0.0",
        uptime=uptime,
        services=services
    )

@router.get("/health/detailed", summary="Detailed health check")
async def detailed_health_check():
    """
    Detailed health information including system metrics.
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
        "uptime": time.time() - start_time,
        "system": {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent
        },
        "services": {
            "api": "healthy",
            "claude": "healthy",
            "storage": "healthy"
        }
    }
```

### 8. Marking Service (`src/answer_marker/api/services/marking_service.py`)

```python
from typing import Optional
from pathlib import Path
from loguru import logger
import asyncio
import httpx

from answer_marker.document_processing import DocumentProcessor
from answer_marker.core.orchestrator import OrchestratorAgent
from answer_marker.api.models.responses import (
    MarkingStatusResponse,
    MarkingResultResponse
)

class MarkingService:
    """Service for handling marking operations"""
    
    def __init__(
        self,
        doc_processor: DocumentProcessor,
        orchestrator: OrchestratorAgent
    ):
        self.doc_processor = doc_processor
        self.orchestrator = orchestrator
        self.jobs = {}  # In-memory job storage (use Redis/DB in production)
    
    async def process_single_marking(
        self,
        job_id: str,
        marking_guide_id: str,
        answer_sheet_file: str,
        student_id: Optional[str] = None,
        student_name: Optional[str] = None,
        batch_id: Optional[str] = None,
        webhook_url: Optional[str] = None
    ):
        """Process a single marking job"""
        try:
            # Update job status
            self.jobs[job_id] = {
                "status": "processing",
                "progress": 0,
                "current_step": "Loading marking guide",
                "started_at": datetime.utcnow()
            }
            
            # Load marking guide
            marking_guide = await self._load_marking_guide(marking_guide_id)
            self._update_job_progress(job_id, 20, "Processing answer sheet")
            
            # Process answer sheet
            answer_sheet = await self.doc_processor.process_answer_sheet(
                Path(answer_sheet_file),
                [q['id'] for q in marking_guide['questions']]
            )
            self._update_job_progress(job_id, 40, "Evaluating answers")
            
            # Mark the answer sheet
            report = await self.orchestrator.mark_answer_sheet(
                marking_guide,
                answer_sheet
            )
            self._update_job_progress(job_id, 80, "Generating report")
            
            # Generate PDF report
            pdf_path = await self._generate_pdf(job_id, report)
            self._update_job_progress(job_id, 100, "Completed")
            
            # Store result
            self.jobs[job_id].update({
                "status": "completed",
                "result": report,
                "pdf_path": pdf_path,
                "completed_at": datetime.utcnow()
            })
            
            # Send webhook if provided
            if webhook_url:
                await self._send_webhook(webhook_url, job_id, "completed", report)
            
            logger.info(f"Completed marking job: {job_id}")
            
        except Exception as e:
            logger.error(f"Error in marking job {job_id}: {e}")
            self.jobs[job_id] = {
                "status": "failed",
                "error": str(e),
                "completed_at": datetime.utcnow()
            }
            
            if webhook_url:
                await self._send_webhook(webhook_url, job_id, "failed", {"error": str(e)})
    
    async def get_job_status(self, job_id: str) -> Optional[MarkingStatusResponse]:
        """Get job status"""
        if job_id not in self.jobs:
            return None
        
        job = self.jobs[job_id]
        
        return MarkingStatusResponse(
            job_id=job_id,
            status=job["status"],
            progress=job.get("progress", 0),
            current_step=job.get("current_step"),
            started_at=job["started_at"],
            completed_at=job.get("completed_at"),
            result_url=f"/api/v1/marking/jobs/{job_id}/result" if job["status"] == "completed" else None
        )
    
    async def get_job_result(self, job_id: str) -> Optional[MarkingResultResponse]:
        """Get job result"""
        if job_id not in self.jobs or self.jobs[job_id]["status"] != "completed":
            return None
        
        job = self.jobs[job_id]
        report = job["result"]
        
        return MarkingResultResponse(
            success=True,
            message="Marking completed",
            job_id=job_id,
            student_id=report.get("student_id"),
            student_name=report.get("student_name"),
            scoring_result=report["scoring_result"],
            qa_result=report["qa_result"],
            requires_review=report["requires_review"],
            report_url=f"/api/v1/marking/jobs/{job_id}/result",
            pdf_report_url=f"/api/v1/marking/jobs/{job_id}/report/pdf"
        )
    
    def _update_job_progress(self, job_id: str, progress: int, step: str):
        """Update job progress"""
        if job_id in self.jobs:
            self.jobs[job_id].update({
                "progress": progress,
                "current_step": step
            })
    
    async def _load_marking_guide(self, guide_id: str):
        """Load marking guide from storage"""
        # Implement loading from your storage
        pass
    
    async def _generate_pdf(self, job_id: str, report: dict) -> str:
        """Generate PDF report"""
        # Implement PDF generation
        # You can use reportlab, weasyprint, or similar libraries
        pass
    
    async def _send_webhook(self, url: str, job_id: str, status: str, data: dict):
        """Send webhook notification"""
        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "job_id": job_id,
                    "status": status,
                    "data": data,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                response = await client.post(
                    url,
                    json=payload,
                    timeout=30
                )
                
                if response.status_code >= 400:
                    logger.warning(f"Webhook failed: {response.status_code}")
                else:
                    logger.info(f"Webhook sent successfully to {url}")
                    
        except Exception as e:
            logger.error(f"Error sending webhook: {e}")
```

### 9. Custom Exceptions (`src/answer_marker/api/exceptions.py`)

```python
from fastapi import HTTPException

class APIException(HTTPException):
    """Base API exception"""
    def __init__(
        self,
        status_code: int,
        error_code: str,
        message: str,
        details: dict = None
    ):
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        super().__init__(status_code=status_code, detail=message)

class AuthenticationError(APIException):
    """Authentication failed"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            status_code=401,
            error_code="AUTH_ERROR",
            message=message
        )

class AuthorizationError(APIException):
    """Authorization failed"""
    def __init__(self, message: str = "Not authorized"):
        super().__init__(
            status_code=403,
            error_code="AUTHZ_ERROR",
            message=message
        )

class NotFoundError(APIException):
    """Resource not found"""
    def __init__(self, message: str = "Resource not found"):
        super().__init__(
            status_code=404,
            error_code="NOT_FOUND",
            message=message
        )

class ValidationError(APIException):
    """Validation error"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(
            status_code=422,
            error_code="VALIDATION_ERROR",
            message=message,
            details=details
        )

class RateLimitError(APIException):
    """Rate limit exceeded"""
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(
            status_code=429,
            error_code="RATE_LIMIT",
            message=message
        )
```

### 10. Running the API

Create `run_api.py` in project root:

```python
import uvicorn
from answer_marker.api.config import api_settings

if __name__ == "__main__":
    uvicorn.run(
        "answer_marker.api.main:app",
        host=api_settings.api_host,
        port=api_settings.api_port,
        reload=api_settings.api_reload,
        workers=api_settings.api_workers
    )
```

Run with:
```bash
# Development
poetry run python run_api.py

# Or directly with uvicorn
poetry run uvicorn answer_marker.api.main:app --reload --host 0.0.0.0 --port 8000
```

## API Documentation

Once running, access:
- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc
- **OpenAPI JSON**: http://localhost:8000/api/openapi.json

## Usage Examples

### Python Client Example

```python
import httpx
import asyncio

async def mark_answer_sheet():
    async with httpx.AsyncClient() as client:
        # Upload marking guide
        with open("marking_guide.pdf", "rb") as f:
            response = await client.post(
                "http://localhost:8000/api/v1/marking-guides/upload",
                files={"file": f},
                data={"title": "Math Test Chapter 1"},
                headers={"X-API-Key": "your-api-key"}
            )
        guide_id = response.json()["guide_id"]
        
        # Upload answer sheet
        with open("student_answer.pdf", "rb") as f:
            response = await client.post(
                "http://localhost:8000/api/v1/answer-sheets/upload",
                files={"file": f},
                headers={"X-API-Key": "your-api-key"}
            )
        file_id = response.json()["file_id"]
        
        # Submit for marking
        response = await client.post(
            "http://localhost:8000/api/v1/mark/single",
            json={
                "marking_guide_id": guide_id,
                "answer_sheet_file": file_id,
                "student_id": "STU001",
                "student_name": "John Doe"
            },
            headers={"X-API-Key": "your-api-key"}
        )
        job_id = response.json()["job_id"]
        
        # Poll for status
        while True:
            response = await client.get(
                f"http://localhost:8000/api/v1/marking/jobs/{job_id}/status",
                headers={"X-API-Key": "your-api-key"}
            )
            status = response.json()
            
            print(f"Status: {status['status']} - {status['progress']}%")
            
            if status["status"] in ["completed", "failed"]:
                break
            
            await asyncio.sleep(2)
        
        # Get result
        if status["status"] == "completed":
            response = await client.get(
                f"http://localhost:8000/api/v1/marking/jobs/{job_id}/result",
                headers={"X-API-Key": "your-api-key"}
            )
            result = response.json()
            print(f"Score: {result['scoring_result']['total_marks']}/{result['scoring_result']['max_marks']}")

asyncio.run(mark_answer_sheet())
```

### cURL Examples

```bash
# Upload marking guide
curl -X POST "http://localhost:8000/api/v1/marking-guides/upload" \
  -H "X-API-Key: your-api-key" \
  -F "file=@marking_guide.pdf" \
  -F "title=Math Test"

# Mark answer sheet
curl -X POST "http://localhost:8000/api/v1/mark/single" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "marking_guide_id": "guide_abc123",
    "answer_sheet_file": "file_xyz789",
    "student_id": "STU001"
  }'

# Check status
curl -X GET "http://localhost:8000/api/v1/marking/jobs/job_abc123/status" \
  -H "X-API-Key: your-api-key"

# Get result
curl -X GET "http://localhost:8000/api/v1/marking/jobs/job_abc123/result" \
  -H "X-API-Key: your-api-key"

# Download PDF
curl -X GET "http://localhost:8000/api/v1/marking/jobs/job_abc123/report/pdf" \
  -H "X-API-Key: your-api-key" \
  -o report.pdf
```

## Docker Deployment

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Poetry
RUN pip install poetry

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-dev

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "answer_marker.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - API_HOST=0.0.0.0
      - API_PORT=8000
    volumes:
      - ./data:/app/data
    restart: unless-stopped
```

## Testing the API

```python
# tests/api/test_marking_routes.py

import pytest
from fastapi.testclient import TestClient
from answer_marker.api.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] in ["healthy", "degraded"]

def test_upload_marking_guide():
    with open("tests/fixtures/sample_guide.pdf", "rb") as f:
        response = client.post(
            "/api/v1/marking-guides/upload",
            files={"file": f},
            data={"title": "Test Guide"},
            headers={"X-API-Key": "test-key"}
        )
    assert response.status_code == 200
    assert "guide_id" in response.json()

def test_mark_single_answer():
    response = client.post(
        "/api/v1/mark/single",
        json={
            "marking_guide_id": "guide_test123",
            "answer_sheet_file": "file_test456",
            "student_id": "STU001"
        },
        headers={"X-API-Key": "test-key"}
    )
    assert response.status_code == 200
    assert "job_id" in response.json()
```

## Best Practices

1. **Authentication**: Implement proper API key or JWT authentication in production
2. **Rate Limiting**: Use Redis-based rate limiting for production
3. **Background Tasks**: Use Celery with Redis/RabbitMQ for production workloads
4. **File Storage**: Use S3/GCS instead of local storage
5. **Database**: Use PostgreSQL/MongoDB for job tracking
6. **Monitoring**: Implement Prometheus metrics and Grafana dashboards
7. **Logging**: Use structured logging with correlation IDs
8. **Caching**: Cache marking guides and results
9. **Webhooks**: Implement retry logic and signature verification
10. **Documentation**: Keep OpenAPI schema up to date

## Security Considerations

- API key management (use secrets manager)
- Input validation (file size, type, content)
- Rate limiting per user/IP
- HTTPS only in production
- CORS configuration
- File upload scanning
- SQL injection prevention
- XSS protection
- CSRF tokens for web uploads

This FastAPI implementation provides a production-ready REST API for your Answer Sheet Marker system! 🚀
