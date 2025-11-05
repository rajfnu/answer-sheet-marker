# Quick Start Guide - Answer Sheet Marker

## Implementation Roadmap

This guide provides step-by-step instructions for implementing the Answer Sheet Marker system.

## Phase 0: Project Setup

### Step 1: Initialize Project

```bash
# Create project directory
mkdir answer-sheet-marker
cd answer-sheet-marker

# Initialize Poetry project (or copy the provided pyproject.toml)
poetry init

# Create directory structure
mkdir -p src/answer_marker/{core,agents,document_processing,models,storage,utils,output,api,cli}
mkdir -p tests/{unit,integration,fixtures}
mkdir -p data/{marking_guides,answer_sheets,sample_outputs,vector_db}
mkdir -p docs

# Create __init__.py files
find src -type d -exec touch {}/__init__.py \;
find tests -type d -exec touch {}/__init__.py \;
```

### Step 2: Install Dependencies

```bash
# Install all dependencies
poetry install

# Install with API support (optional)
poetry install -E api

# Activate virtual environment
poetry shell
```

### Step 3: Environment Configuration

Create `.env` file:

```bash
# .env
ANTHROPIC_API_KEY=your_api_key_here
CLAUDE_MODEL=claude-sonnet-4-5-20250929
MAX_TOKENS=8192
TEMPERATURE=0.0

# Processing Configuration
BATCH_SIZE=5
MAX_CONCURRENT_REQUESTS=3

# Quality Thresholds
MIN_CONFIDENCE_SCORE=0.7
REQUIRE_HUMAN_REVIEW_BELOW=0.6

# Storage
VECTOR_DB_PATH=./data/vector_db
CACHE_ENABLED=true

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/app.log
```

Create `.env.example`:
```bash
cp .env .env.example
# Edit .env.example and remove sensitive values
```

## Phase 1: Core Implementation (Week 1-2)

### Step 1: Configuration Management

**File:** `src/answer_marker/config.py`

```python
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application configuration"""
    
    # API Configuration
    anthropic_api_key: str
    claude_model: str = "claude-sonnet-4-5-20250929"
    max_tokens: int = 8192
    temperature: float = 0.0
    
    # Processing
    batch_size: int = 5
    max_concurrent_requests: int = 3
    
    # Quality Thresholds
    min_confidence_score: float = 0.7
    require_human_review_below: float = 0.6
    
    # Storage
    vector_db_path: str = "./data/vector_db"
    cache_enabled: bool = True
    
    # Logging
    log_level: str = "INFO"
    log_file: Optional[str] = "./logs/app.log"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()
```

### Step 2: Logger Setup

**File:** `src/answer_marker/utils/logger.py`

```python
from loguru import logger
import sys
from pathlib import Path
from answer_marker.config import settings

def setup_logger():
    """Configure application logger"""
    
    # Remove default handler
    logger.remove()
    
    # Console handler
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level=settings.log_level,
        colorize=True
    )
    
    # File handler
    if settings.log_file:
        log_path = Path(settings.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.add(
            settings.log_file,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}",
            level=settings.log_level,
            rotation="10 MB",
            retention="1 week",
            compression="zip"
        )
    
    return logger

# Initialize logger
setup_logger()
```

### Step 3: Claude Client Wrapper

**File:** `src/answer_marker/utils/claude_client.py`

```python
from anthropic import Anthropic
from tenacity import retry, stop_after_attempt, wait_exponential
from loguru import logger
from answer_marker.config import settings

class ClaudeClient:
    """Wrapper around Anthropic Claude API with retry logic"""
    
    def __init__(self):
        self.client = Anthropic(api_key=settings.anthropic_api_key)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def create_message(self, **kwargs):
        """Create message with retry logic"""
        try:
            return self.client.messages.create(**kwargs)
        except Exception as e:
            logger.error(f"Claude API call failed: {e}")
            raise
    
    def get_client(self):
        """Get underlying Anthropic client"""
        return self.client

# Global client instance
claude_client = ClaudeClient()
```

### Step 4: Data Models

**File:** `src/answer_marker/models/question.py`

```python
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from enum import Enum

class QuestionType(str, Enum):
    MCQ = "mcq"
    SHORT_ANSWER = "short_answer"
    ESSAY = "essay"
    NUMERICAL = "numerical"
    TRUE_FALSE = "true_false"

class KeyConcept(BaseModel):
    """Key concept to look for in answers"""
    concept: str
    points: float
    mandatory: bool = False
    keywords: List[str] = []

class EvaluationCriteria(BaseModel):
    """Evaluation criteria for different performance levels"""
    excellent: str
    good: str
    satisfactory: str
    poor: str

class AnalyzedQuestion(BaseModel):
    """Question with analysis and rubric"""
    id: str
    question_text: str
    question_type: QuestionType
    max_marks: float
    key_concepts: List[KeyConcept]
    evaluation_criteria: EvaluationCriteria
    keywords: List[str] = []
    common_mistakes: List[str] = []
    sample_answer: Optional[str] = None
```

**File:** `src/answer_marker/models/evaluation.py`

```python
from pydantic import BaseModel, Field
from typing import List, Literal
from datetime import datetime

class ConceptEvaluation(BaseModel):
    """Evaluation of a single concept"""
    concept: str
    present: bool
    accuracy: Literal["fully_correct", "partially_correct", "incorrect", "not_present"]
    evidence: str
    points_earned: float

class AnswerEvaluation(BaseModel):
    """Complete evaluation of a student answer"""
    question_id: str
    concepts_identified: List[ConceptEvaluation]
    overall_quality: Literal["excellent", "good", "satisfactory", "poor", "inadequate"]
    strengths: List[str]
    weaknesses: List[str]
    misconceptions: List[str] = []
    confidence_score: float = Field(ge=0, le=1)
    requires_human_review: bool = False
    review_reason: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ScoringResult(BaseModel):
    """Final scoring result"""
    total_marks: float
    max_marks: float
    percentage: float
    grade: str
    question_scores: List[dict]

class QAResult(BaseModel):
    """Quality assurance result"""
    passed: bool
    requires_human_review: bool
    flags: List[dict] = []
    issues: List[dict] = []
    confidence_level: Literal["high", "medium", "low"]
```

## Phase 2: Document Processing (Week 2-3)

Follow the implementation details in `DOCUMENT_PROCESSING.md`.

Key files to implement:
1. `src/answer_marker/document_processing/pdf_parser.py`
2. `src/answer_marker/document_processing/ocr_handler.py`
3. `src/answer_marker/document_processing/structure_analyzer.py`
4. `src/answer_marker/document_processing/validators.py`

## Phase 3: Agent Implementation (Week 3-5)

Follow the implementation details in `AGENTS.md`.

Implementation order:
1. Base Agent (`src/answer_marker/core/agent_base.py`)
2. Question Analyzer Agent
3. Answer Evaluator Agent
4. Scoring Agent
5. Feedback Generator Agent
6. QA Agent
7. Orchestrator Agent

## Phase 4: CLI Interface (Week 5)

**File:** `src/answer_marker/cli/commands.py`

```python
import typer
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from answer_marker.core.orchestrator import OrchestratorAgent
from answer_marker.document_processing import DocumentProcessor
from answer_marker.utils.claude_client import claude_client
from loguru import logger

app = typer.Typer(
    name="answer-marker",
    help="AI-powered answer sheet marking system"
)
console = Console()

@app.command()
def mark(
    marking_guide: Path = typer.Option(..., "--guide", "-g", help="Path to marking guide PDF"),
    answer_sheets: Path = typer.Option(..., "--answers", "-a", help="Path to answer sheets directory"),
    output_dir: Path = typer.Option("./output", "--output", "-o", help="Output directory for reports"),
):
    """Mark answer sheets using AI"""
    
    console.print("[bold blue]Answer Sheet Marker[/bold blue]")
    console.print(f"Marking Guide: {marking_guide}")
    console.print(f"Answer Sheets: {answer_sheets}")
    console.print(f"Output Directory: {output_dir}")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        
        # Process marking guide
        task1 = progress.add_task("Processing marking guide...", total=None)
        doc_processor = DocumentProcessor(claude_client.get_client())
        marking_guide_data = await doc_processor.process_marking_guide(marking_guide)
        progress.update(task1, completed=True)
        
        # Process answer sheets
        answer_sheet_files = list(answer_sheets.glob("*.pdf"))
        task2 = progress.add_task(
            f"Processing {len(answer_sheet_files)} answer sheets...",
            total=len(answer_sheet_files)
        )
        
        # Mark each answer sheet
        # Implementation here...
        
    console.print("[bold green]✓[/bold green] Marking completed!")

@app.command()
def calibrate(
    marking_guide: Path = typer.Option(..., "--guide", "-g"),
    sample_answer: Path = typer.Option(..., "--sample", "-s"),
    expected_score: float = typer.Option(..., "--score", "-sc"),
):
    """Calibrate the system with a sample answer"""
    console.print("[bold blue]Calibration Mode[/bold blue]")
    # Implementation here...

@app.command()
def report(
    session_id: str = typer.Argument(..., help="Session ID to generate report for"),
):
    """Generate detailed report for a marking session"""
    console.print(f"Generating report for session: {session_id}")
    # Implementation here...

if __name__ == "__main__":
    app()
```

## Phase 5: Testing (Ongoing)

### Unit Tests Example

**File:** `tests/unit/test_scoring_agent.py`

```python
import pytest
from unittest.mock import Mock, AsyncMock
from answer_marker.agents.scoring_agent import ScoringAgent
from answer_marker.core.agent_base import AgentConfig, AgentMessage

@pytest.fixture
def mock_claude_client():
    return Mock()

@pytest.fixture
def scoring_agent(mock_claude_client):
    config = AgentConfig(
        name="scoring_agent",
        system_prompt="You are a scoring agent"
    )
    return ScoringAgent(config, mock_claude_client)

@pytest.mark.asyncio
async def test_calculate_scores(scoring_agent):
    evaluations = [
        {
            'question_id': 'Q1',
            'concepts_identified': [
                {'points_earned': 3.0},
                {'points_earned': 2.0}
            ],
            'max_marks': 5.0
        },
        {
            'question_id': 'Q2',
            'concepts_identified': [
                {'points_earned': 5.0}
            ],
            'max_marks': 5.0
        }
    ]
    
    message = AgentMessage(
        sender="test",
        receiver="scoring_agent",
        content={"evaluations": evaluations},
        message_type="request"
    )
    
    response = await scoring_agent.process(message)
    
    assert response.message_type == "response"
    scores = response.content['scores']
    assert scores['total_marks'] == 10.0
    assert scores['max_marks'] == 10.0
    assert scores['percentage'] == 100.0
```

### Integration Test Example

**File:** `tests/integration/test_end_to_end.py`

```python
import pytest
from pathlib import Path
from answer_marker.document_processing import DocumentProcessor
from answer_marker.core.orchestrator import OrchestratorAgent

@pytest.mark.asyncio
async def test_end_to_end_marking(
    sample_marking_guide,
    sample_answer_sheet,
    claude_client
):
    """Test complete marking workflow"""
    
    # Process documents
    doc_processor = DocumentProcessor(claude_client)
    marking_guide = await doc_processor.process_marking_guide(sample_marking_guide)
    answer_sheet = await doc_processor.process_answer_sheet(
        sample_answer_sheet,
        [q['id'] for q in marking_guide['questions']]
    )
    
    # Create orchestrator
    orchestrator = OrchestratorAgent(config, claude_client, agents)
    
    # Mark answer sheet
    report = await orchestrator.mark_answer_sheet(marking_guide, answer_sheet)
    
    # Assertions
    assert report is not None
    assert report['total_marks'] > 0
    assert len(report['question_evaluations']) == len(marking_guide['questions'])
```

## Phase 6: Deployment Preparation

### Create Docker Support (Optional)

**File:** `Dockerfile`

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
    && poetry install --no-interaction --no-ansi

# Copy application
COPY . .

# Run
CMD ["poetry", "run", "answer-marker", "--help"]
```

### Create GitHub Actions CI/CD

**File:** `.github/workflows/ci.yml`

```yaml
name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install Poetry
      run: |
        curl -sSL https://install.python-poetry.org | python3 -
        echo "$HOME/.local/bin" >> $GITHUB_PATH
    
    - name: Install dependencies
      run: poetry install
    
    - name: Run linters
      run: |
        poetry run black --check src tests
        poetry run ruff src tests
        poetry run mypy src
    
    - name: Run tests
      run: poetry run pytest --cov=src --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

## Development Workflow

### Daily Development

```bash
# Activate environment
poetry shell

# Run tests
poetry run pytest

# Run with coverage
poetry run pytest --cov

# Format code
poetry run black src tests

# Lint
poetry run ruff src tests

# Type check
poetry run mypy src

# Run CLI
poetry run answer-marker --help
```

### Pre-commit Hooks

**File:** `.pre-commit-config.yaml`

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 24.10.0
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.7.0
    hooks:
      - id: ruff
        args: [--fix]

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
```

Install pre-commit:
```bash
poetry run pre-commit install
```

## Usage Examples

### Example 1: Mark Single Answer Sheet

```python
from pathlib import Path
from answer_marker.document_processing import DocumentProcessor
from answer_marker.core.orchestrator import OrchestratorAgent
from answer_marker.utils.claude_client import claude_client

async def mark_single():
    # Setup
    doc_processor = DocumentProcessor(claude_client.get_client())
    
    # Process marking guide
    marking_guide = await doc_processor.process_marking_guide(
        Path("data/marking_guides/math_test_guide.pdf")
    )
    
    # Process answer sheet
    answer_sheet = await doc_processor.process_answer_sheet(
        Path("data/answer_sheets/student_001.pdf"),
        [q['id'] for q in marking_guide['questions']]
    )
    
    # Mark
    orchestrator = create_orchestrator()
    report = await orchestrator.mark_answer_sheet(marking_guide, answer_sheet)
    
    print(f"Total Score: {report['total_marks']}/{report['max_marks']}")
    print(f"Grade: {report['grade']}")
```

### Example 2: Batch Processing

```python
from pathlib import Path
import asyncio

async def mark_batch():
    marking_guide = await process_marking_guide(...)
    
    answer_sheets = Path("data/answer_sheets").glob("*.pdf")
    
    tasks = [
        mark_single_sheet(marking_guide, sheet)
        for sheet in answer_sheets
    ]
    
    results = await asyncio.gather(*tasks)
    
    # Generate summary report
    generate_summary(results)
```

## Next Steps

1. **Week 1-2**: Setup project, implement core classes and configuration
2. **Week 2-3**: Implement document processing pipeline
3. **Week 3-5**: Implement all agents
4. **Week 5**: Create CLI interface
5. **Week 6**: Testing and refinement
6. **Week 7**: Documentation and examples
7. **Week 8**: Deployment preparation

## Resources

- **Anthropic Documentation**: https://docs.anthropic.com
- **Claude API Reference**: https://docs.anthropic.com/en/api
- **Poetry Documentation**: https://python-poetry.org/docs/
- **Pydantic Documentation**: https://docs.pydantic.dev/

## Support

For issues and questions:
1. Check the documentation in `docs/`
2. Review the SKILL.md files
3. Open an issue on GitHub
4. Contact the development team

## License

MIT License - See LICENSE file for details
