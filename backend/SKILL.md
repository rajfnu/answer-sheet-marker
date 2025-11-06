# AI Answer Sheet Marker - Project Skill Guide

## Project Overview

An intelligent, agentic AI system that automatically evaluates and grades answer sheets based on provided marking guides. The system uses multi-agent architecture with Claude API to ensure accurate, consistent, and fair assessment.

## Architecture Design

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Answer Sheet Marker System                │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Document Processing Pipeline                  │  │
│  │  (PDF/Image → Text Extraction → Structure Analysis)  │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ↓                                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Multi-Agent Orchestrator                 │  │
│  │         (Coordinates specialized agents)              │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ↓                                    │
│  ┌─────────────┬──────────────┬───────────────┬─────────┐  │
│  │  Question   │   Answer     │   Scoring     │ Quality │  │
│  │  Analyzer   │  Evaluator   │   Agent       │ Assurer │  │
│  │   Agent     │   Agent      │               │  Agent  │  │
│  └─────────────┴──────────────┴───────────────┴─────────┘  │
│                          ↓                                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Feedback & Report Generation                  │  │
│  │    (Detailed marks, feedback, improvement areas)      │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Component Architecture

#### 1. **Document Processing Layer**
- **PDF/Image Parser**: Extract text from various formats
- **Structure Analyzer**: Identify questions, answers, marking schemes
- **OCR Engine**: Handle handwritten or scanned documents
- **Document Validator**: Ensure document quality and completeness

#### 2. **Agent Layer** (Multi-Agent System)

**Orchestrator Agent**: Coordinates all agents and manages workflow

**Specialized Agents**:
- **Question Analyzer Agent**: 
  - Parses marking guide
  - Extracts key concepts, keywords, and evaluation criteria
  - Identifies question types (MCQ, short answer, essay, numerical)
  - Creates structured evaluation rubrics

- **Answer Evaluator Agent**:
  - Compares student answers with marking guide
  - Identifies correct concepts and knowledge gaps
  - Handles partial credit scenarios
  - Manages different answer formats

- **Scoring Agent**:
  - Applies marking rubric consistently
  - Calculates marks based on evaluation
  - Handles edge cases and partial marks
  - Maintains scoring transparency

- **Feedback Generator Agent**:
  - Creates constructive feedback
  - Highlights strengths and areas for improvement
  - Suggests learning resources
  - Maintains encouraging tone

- **Quality Assurance Agent**:
  - Reviews marking consistency
  - Flags uncertain evaluations for human review
  - Validates score distribution
  - Ensures fairness across all submissions

#### 3. **Data Management Layer**
- **Vector Store**: RAG for marking guide reference
- **Session Manager**: Track marking sessions
- **Audit Logger**: Complete audit trail
- **Cache Manager**: Optimize repeated evaluations

#### 4. **Output Layer**
- **Report Generator**: PDF/HTML reports
- **Analytics Dashboard**: Statistics and insights
- **Export Module**: Various output formats

## Technology Stack

### Core Technologies
```toml
python = "^3.11"
anthropic = "^0.40.0"          # Claude API
pydantic = "^2.9"              # Data validation
pydantic-settings = "^2.6"     # Configuration management
```

### Document Processing
```toml
pypdf = "^5.0"                 # PDF text extraction
pdf2image = "^1.17"            # PDF to image conversion
pillow = "^10.4"               # Image processing
pytesseract = "^0.3"           # OCR capabilities
python-doctr = "^0.8"          # Advanced document OCR
```

### AI & Vector Operations
```toml
chromadb = "^0.5.0"            # Vector database for RAG
sentence-transformers = "^3.0" # Embeddings
tiktoken = "^0.8"              # Token counting
```

### API & Web (Optional)
```toml
fastapi = "^0.115"             # REST API
uvicorn = "^0.32"              # ASGI server
python-multipart = "^0.0.12"   # File uploads
```

### Utilities
```toml
rich = "^13.9"                 # Beautiful CLI output
loguru = "^0.7"                # Advanced logging
tenacity = "^9.0"              # Retry logic
python-dotenv = "^1.0"         # Environment management
```

### Development
```toml
[tool.poetry.group.dev.dependencies]
pytest = "^8.3"
pytest-asyncio = "^0.24"
pytest-cov = "^6.0"
black = "^24.10"
ruff = "^0.7"
mypy = "^1.13"
```

## Project Structure

```
answer-sheet-marker/
├── pyproject.toml                 # Poetry configuration
├── README.md                      # Project documentation
├── .env.example                   # Environment variables template
├── .gitignore
│
├── src/
│   └── answer_marker/
│       ├── __init__.py
│       │
│       ├── core/                  # Core business logic
│       │   ├── __init__.py
│       │   ├── orchestrator.py    # Main orchestrator
│       │   ├── agent_base.py      # Base agent class
│       │   └── workflow.py        # Marking workflow
│       │
│       ├── agents/                # Specialized agents
│       │   ├── __init__.py
│       │   ├── question_analyzer.py
│       │   ├── answer_evaluator.py
│       │   ├── scoring_agent.py
│       │   ├── feedback_generator.py
│       │   └── qa_agent.py
│       │
│       ├── document_processing/   # Document handling
│       │   ├── __init__.py
│       │   ├── pdf_parser.py
│       │   ├── image_processor.py
│       │   ├── ocr_handler.py
│       │   └── structure_analyzer.py
│       │
│       ├── models/                # Data models
│       │   ├── __init__.py
│       │   ├── question.py        # Question models
│       │   ├── answer.py          # Answer models
│       │   ├── marking_guide.py   # Marking guide models
│       │   ├── evaluation.py      # Evaluation results
│       │   └── report.py          # Report models
│       │
│       ├── storage/               # Data persistence
│       │   ├── __init__.py
│       │   ├── vector_store.py    # ChromaDB integration
│       │   ├── session_manager.py
│       │   └── cache_manager.py
│       │
│       ├── utils/                 # Utilities
│       │   ├── __init__.py
│       │   ├── logger.py          # Logging configuration
│       │   ├── claude_client.py   # Claude API wrapper
│       │   ├── prompts.py         # Prompt templates
│       │   └── validators.py      # Input validators
│       │
│       ├── output/                # Output generation
│       │   ├── __init__.py
│       │   ├── report_generator.py
│       │   ├── templates/         # Report templates
│       │   └── exporters.py
│       │
│       ├── api/                   # Optional REST API
│       │   ├── __init__.py
│       │   ├── main.py
│       │   ├── routes/
│       │   └── dependencies.py
│       │
│       └── cli/                   # Command-line interface
│           ├── __init__.py
│           └── commands.py
│
├── tests/                         # Test suite
│   ├── __init__.py
│   ├── unit/
│   ├── integration/
│   └── fixtures/
│
├── data/                          # Data directory
│   ├── marking_guides/
│   ├── answer_sheets/
│   ├── sample_outputs/
│   └── vector_db/
│
└── docs/                          # Documentation
    ├── architecture.md
    ├── agent_design.md
    ├── api_reference.md
    └── user_guide.md
```

## Best Practices & Design Principles

### 1. **Multi-Agent Design Patterns**

#### Agent Communication Protocol
```python
class AgentMessage(BaseModel):
    """Standard message format between agents"""
    sender: str
    receiver: str
    content: dict
    message_type: str
    priority: int
    timestamp: datetime
```

#### Agent Responsibilities (Single Responsibility Principle)
- Each agent has ONE clear purpose
- Agents communicate through structured messages
- Orchestrator manages workflow, not business logic

### 2. **Robust Error Handling**

```python
# Use tenacity for retries with exponential backoff
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type(APIError)
)
async def call_claude_api(...):
    pass
```

### 3. **Structured Outputs with Pydantic**

```python
class EvaluationResult(BaseModel):
    """Ensures consistent evaluation format"""
    question_id: str
    marks_awarded: float
    max_marks: float
    evaluation_rationale: str
    key_points_identified: List[str]
    missing_concepts: List[str]
    confidence_score: float  # 0-1 scale
    requires_human_review: bool
```

### 4. **Prompt Engineering Excellence**

**Key Principles**:
- Use XML tags for structured prompts
- Provide clear examples (few-shot learning)
- Separate instructions from context
- Use chain-of-thought reasoning
- Include error handling instructions

Example prompt structure:
```xml
<task>
You are an expert examiner evaluating student answers.
</task>

<marking_guide>
{{marking_guide_content}}
</marking_guide>

<student_answer>
{{student_answer}}
</student_answer>

<instructions>
1. Identify key concepts in the marking guide
2. Check which concepts are present in the student answer
3. Assess accuracy and completeness
4. Provide specific, constructive feedback
</instructions>

<output_format>
Return your evaluation in JSON format...
</output_format>
```

### 5. **RAG Implementation for Marking Guides**

```python
# Chunk marking guide into semantic sections
# Store in vector database
# Retrieve relevant sections for each question
# Context-aware evaluation
```

### 6. **Quality Assurance Mechanisms**

- **Confidence Scoring**: Each evaluation includes confidence level
- **Human Review Flagging**: Low confidence → human review
- **Consistency Checks**: Compare similar answers across students
- **Calibration Mode**: Initial calibration with sample answers
- **Audit Trail**: Complete logging of all decisions

### 7. **Handling Different Question Types**

#### MCQ (Multiple Choice)
- Direct answer matching
- Automatic scoring
- No subjective evaluation needed

#### Short Answer
- Keyword/concept matching
- Partial credit based on concept coverage
- Moderate subjectivity

#### Essay/Long Answer
- Comprehensive concept analysis
- Structure and coherence evaluation
- High subjectivity - higher confidence thresholds

#### Numerical/Calculation
- Answer accuracy check
- Method/working validation
- Partial marks for correct methodology

### 8. **Performance Optimization**

- **Batch Processing**: Process multiple answers in parallel
- **Caching**: Cache marking guide analysis
- **Async Operations**: Use asyncio for I/O operations
- **Rate Limiting**: Respect Claude API rate limits
- **Token Optimization**: Minimize token usage in prompts

### 9. **Security & Privacy**

- **Data Encryption**: Encrypt sensitive student data
- **Access Control**: Role-based access
- **Audit Logging**: Complete audit trail
- **Data Retention**: Clear retention policies
- **GDPR Compliance**: Student data protection

### 10. **Extensibility**

- **Plugin Architecture**: Easy to add new question types
- **Custom Rubrics**: Support custom marking schemes
- **Integration Ready**: API for LMS integration
- **Export Formats**: Multiple output formats

## Implementation Workflow

### Phase 1: Document Processing
1. Upload question sheet with marking guide
2. Upload answer sheets
3. Extract and structure all documents
4. Validate document completeness

### Phase 2: Calibration (Optional but Recommended)
1. Process sample answer with known score
2. Adjust evaluation parameters
3. Validate consistency

### Phase 3: Evaluation
1. Question Analyzer processes marking guide
2. For each answer sheet:
   - Answer Evaluator compares with guide
   - Scoring Agent calculates marks
   - Feedback Generator creates feedback
   - QA Agent validates evaluation
3. Generate reports

### Phase 4: Review & Export
1. Human review of flagged items
2. Generate final reports
3. Export in required format
4. Archive for audit

## Configuration Management

```python
# config.py using pydantic-settings
class Settings(BaseSettings):
    # API Configuration
    anthropic_api_key: str
    claude_model: str = "claude-sonnet-4-5-20250929"
    max_tokens: int = 8192
    temperature: float = 0.0  # Deterministic for marking
    
    # Processing
    batch_size: int = 5
    max_concurrent_requests: int = 3
    
    # Quality Thresholds
    min_confidence_score: float = 0.7
    require_human_review_below: float = 0.6
    
    # Storage
    vector_db_path: str = "./data/vector_db"
    cache_enabled: bool = True
    
    class Config:
        env_file = ".env"
```

## Testing Strategy

### Unit Tests
- Test each agent independently
- Mock Claude API responses
- Test document parsing

### Integration Tests
- Test agent communication
- Test end-to-end workflows
- Test with sample documents

### Performance Tests
- Test with large batches
- Measure response times
- Test concurrent processing

## Monitoring & Observability

```python
# Key metrics to track
- Documents processed per hour
- Average confidence scores
- Human review rate
- API token usage
- Error rates by component
- Processing time per answer
```

## Claude API Best Practices

### 1. **Structured Outputs**
```python
# Use tools/function calling for structured outputs
tools = [{
    "name": "submit_evaluation",
    "description": "Submit the evaluation results",
    "input_schema": {
        "type": "object",
        "properties": {
            "marks_awarded": {"type": "number"},
            "rationale": {"type": "string"},
            # ... more fields
        }
    }
}]
```

### 2. **Context Management**
- Keep prompts focused and concise
- Use extended thinking for complex evaluations
- Manage token limits effectively

### 3. **Error Handling**
- Handle rate limits gracefully
- Implement retry logic
- Validate all API responses

## Success Metrics

- **Accuracy**: Agreement with human markers (target: >90%)
- **Consistency**: Inter-rater reliability
- **Efficiency**: Time saved vs manual marking
- **Coverage**: % of submissions requiring human review (target: <10%)
- **Student Satisfaction**: Quality of feedback

## Future Enhancements

1. **Machine Learning Integration**: Learn from human corrections
2. **Multi-language Support**: Support for multiple languages
3. **Plagiarism Detection**: Integrate plagiarism checking
4. **LMS Integration**: Direct integration with Canvas, Moodle, etc.
5. **Mobile App**: Mobile interface for teachers
6. **Real-time Collaboration**: Multiple markers working together
7. **Advanced Analytics**: Deep insights into student performance

## Getting Started

See the detailed implementation guides in:
- `ARCHITECTURE.md` - Detailed architecture decisions
- `AGENTS.md` - Agent implementation guide
- `DOCUMENT_PROCESSING.md` - Document processing guide
- `API_GUIDE.md` - API development guide
- `DEPLOYMENT.md` - Deployment instructions

## Support & Contributing

For issues and contributions, refer to CONTRIBUTING.md
