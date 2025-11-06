# AI Answer Sheet Marker 🎓

> An intelligent, multi-agent AI system for automated answer sheet evaluation and grading

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Poetry](https://img.shields.io/badge/poetry-managed-blue.svg)](https://python-poetry.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## 🌟 Overview

The AI Answer Sheet Marker is a sophisticated system that automates the evaluation and grading of student answer sheets using advanced AI technology. Built with a multi-agent architecture powered by Anthropic's Claude, it provides consistent, fair, and detailed assessment with comprehensive feedback.

### Key Features

- 🤖 **Multi-Agent Architecture**: Specialized AI agents for different aspects of marking
- 📄 **Document Processing**: Supports PDFs, images, and scanned documents with OCR
- 📊 **Structured Evaluation**: Consistent marking using detailed rubrics
- 💡 **Intelligent Feedback**: Constructive, personalized feedback for students
- ✅ **Quality Assurance**: Built-in QA checks and human review flagging
- 📈 **Detailed Reports**: Comprehensive marking reports with analytics
- 🔄 **Batch Processing**: Efficiently process multiple answer sheets
- 🎯 **High Accuracy**: Designed for 90%+ agreement with human markers
- 🌐 **REST API**: Full FastAPI implementation for programmatic access
- ⚡ **Async Processing**: Background tasks and real-time progress tracking

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR AGENT                        │
│           (Workflow Management & Coordination)               │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  Question   │  │   Answer    │  │   Scoring   │
│  Analyzer   │─▶│  Evaluator  │─▶│    Agent    │
│   Agent     │  │   Agent     │  │             │
└─────────────┘  └─────────────┘  └──────┬──────┘
                                          │
                         ┌────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  Feedback   │  │  Quality    │  │   Report    │
│  Generator  │  │  Assurance  │  │  Generator  │
│   Agent     │  │   Agent     │  │             │
└─────────────┘  └─────────────┘  └─────────────┘
```

### Agent Responsibilities

| Agent | Purpose | Output |
|-------|---------|--------|
| **Orchestrator** | Coordinates workflow and manages agent communication | Workflow control |
| **Question Analyzer** | Analyzes marking guides and creates evaluation rubrics | Structured rubrics |
| **Answer Evaluator** | Evaluates student answers against rubrics | Detailed evaluations |
| **Scoring Agent** | Calculates marks and assigns grades | Scores and grades |
| **Feedback Generator** | Creates constructive student feedback | Personalized feedback |
| **QA Agent** | Reviews consistency and flags issues | Quality reports |
| **Report Generator** | Produces comprehensive marking reports | Final reports |

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- Poetry for dependency management
- Anthropic API key
- Tesseract OCR (for scanned documents)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/answer-sheet-marker.git
cd answer-sheet-marker

# Install dependencies using Poetry
poetry install

# Activate virtual environment
poetry shell

# Set up environment variables
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### Basic Usage

#### 1. Mark a Single Answer Sheet

```bash
poetry run answer-marker mark \
  --guide data/marking_guides/math_test.pdf \
  --answers data/answer_sheets/student_001.pdf \
  --output output/
```

#### 2. Batch Processing

```bash
poetry run answer-marker mark \
  --guide data/marking_guides/math_test.pdf \
  --answers data/answer_sheets/ \
  --output output/batch_results/
```

#### 3. Calibration Mode

```bash
poetry run answer-marker calibrate \
  --guide data/marking_guides/math_test.pdf \
  --sample data/samples/sample_answer.pdf \
  --score 85
```

### Python API Usage

```python
from pathlib import Path
from answer_marker.document_processing import DocumentProcessor
from answer_marker.core.orchestrator import OrchestratorAgent
from answer_marker.utils.claude_client import claude_client

async def mark_answer_sheet():
    # Initialize document processor
    doc_processor = DocumentProcessor(claude_client.get_client())
    
    # Process marking guide
    marking_guide = await doc_processor.process_marking_guide(
        Path("data/marking_guides/math_test.pdf")
    )
    
    # Process student answer sheet
    answer_sheet = await doc_processor.process_answer_sheet(
        Path("data/answer_sheets/student_001.pdf"),
        [q['id'] for q in marking_guide['questions']]
    )
    
    # Initialize orchestrator with all agents
    orchestrator = create_orchestrator()
    
    # Mark the answer sheet
    report = await orchestrator.mark_answer_sheet(marking_guide, answer_sheet)
    
    # Print results
    print(f"Student Score: {report['total_marks']}/{report['max_marks']}")
    print(f"Grade: {report['grade']}")
    print(f"Percentage: {report['percentage']:.1f}%")
    
    return report
```

### REST API Usage (NEW!)

```python
import httpx

async def mark_via_api():
    async with httpx.AsyncClient() as client:
        # Upload marking guide
        with open("marking_guide.pdf", "rb") as f:
            response = await client.post(
                "http://localhost:8000/api/v1/marking-guides/upload",
                files={"file": f},
                data={"title": "Math Test"},
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
                "student_id": "STU001"
            },
            headers={"X-API-Key": "your-api-key"}
        )
        
        job_id = response.json()["job_id"]
        print(f"Marking job created: {job_id}")
```

### CLI Usage

```bash
# Mark a single answer sheet
poetry run answer-marker mark \
  --guide data/marking_guides/math_test.pdf \
  --answers data/answer_sheets/student_001.pdf \
  --output output/

# Start API server
poetry run uvicorn answer_marker.api.main:app --reload
```

## 📁 Project Structure

```
answer-sheet-marker/
├── src/answer_marker/
│   ├── core/                  # Core business logic
│   │   ├── orchestrator.py    # Main workflow orchestrator
│   │   ├── agent_base.py      # Base agent class
│   │   └── workflow.py        # Marking workflow
│   │
│   ├── agents/                # Specialized agents
│   │   ├── question_analyzer.py
│   │   ├── answer_evaluator.py
│   │   ├── scoring_agent.py
│   │   ├── feedback_generator.py
│   │   └── qa_agent.py
│   │
│   ├── document_processing/   # Document handling
│   │   ├── pdf_parser.py
│   │   ├── ocr_handler.py
│   │   └── structure_analyzer.py
│   │
│   ├── models/                # Data models
│   │   ├── question.py
│   │   ├── answer.py
│   │   ├── evaluation.py
│   │   └── report.py
│   │
│   ├── utils/                 # Utilities
│   │   ├── logger.py
│   │   ├── claude_client.py
│   │   └── prompts.py
│   │
│   └── cli/                   # CLI interface
│       └── commands.py
│
├── tests/                     # Test suite
├── data/                      # Data directory
├── docs/                      # Documentation
├── pyproject.toml            # Poetry configuration
└── README.md                 # This file
```

## 🔧 Configuration

Configuration is managed through environment variables and the `config.py` file:

```python
# .env
ANTHROPIC_API_KEY=your_api_key_here
CLAUDE_MODEL=claude-sonnet-4-5-20250929
MAX_TOKENS=8192
TEMPERATURE=0.0

# Quality thresholds
MIN_CONFIDENCE_SCORE=0.7
REQUIRE_HUMAN_REVIEW_BELOW=0.6

# Processing
BATCH_SIZE=5
MAX_CONCURRENT_REQUESTS=3
```

## 📊 Evaluation Process

The system follows a structured evaluation process:

### 1. Document Processing
- Extract text from PDFs/images
- Apply OCR for scanned documents
- Structure document content
- Validate document quality

### 2. Question Analysis
- Parse marking guide
- Extract evaluation criteria
- Create detailed rubrics
- Identify key concepts and keywords

### 3. Answer Evaluation
- Compare answers with rubrics
- Identify present concepts
- Assess accuracy and completeness
- Detect misconceptions

### 4. Scoring
- Calculate marks per question
- Apply partial credit rules
- Compute total score
- Assign grade

### 5. Feedback Generation
- Highlight strengths
- Identify improvement areas
- Provide actionable suggestions
- Maintain encouraging tone

### 6. Quality Assurance
- Check evaluation consistency
- Flag low-confidence assessments
- Validate scoring logic
- Recommend human review when needed

## 🎯 Supported Question Types

- ✅ Multiple Choice Questions (MCQ)
- ✅ Short Answer Questions
- ✅ Essay Questions
- ✅ Numerical/Calculation Questions
- ✅ True/False Questions
- ✅ Mixed/Hybrid Questions

## 📈 Performance Metrics

Target performance indicators:

- **Accuracy**: >90% agreement with human markers
- **Consistency**: >95% inter-rater reliability
- **Efficiency**: 10x faster than manual marking
- **Coverage**: <10% requiring human review
- **Student Satisfaction**: High-quality feedback

## 🧪 Testing

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=src/answer_marker --cov-report=html

# Run specific test file
poetry run pytest tests/unit/test_scoring_agent.py

# Run integration tests only
poetry run pytest tests/integration/
```

## 🔍 Development

### Code Quality

```bash
# Format code
poetry run black src tests

# Lint
poetry run ruff src tests

# Type checking
poetry run mypy src
```

### Pre-commit Hooks

```bash
# Install pre-commit hooks
poetry run pre-commit install

# Run manually
poetry run pre-commit run --all-files
```

## 📖 Documentation

Comprehensive documentation is available in the `docs/` directory and SKILL.md files:

- **SKILL.md** - Main project architecture and design
- **AGENTS.md** - Detailed agent implementation guide
- **DOCUMENT_PROCESSING.md** - Document processing guide
- **MODELS.md** - Complete data models reference
- **QUICK_START.md** - Implementation roadmap
- **API_IMPLEMENTATION.md** - FastAPI REST API guide (NEW!)
- **API_REFERENCE.md** - API documentation
- **USER_GUIDE.md** - End-user guide

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please ensure:
- Code passes all tests
- Code is formatted with Black
- Code passes linting (Ruff)
- Type hints are provided
- Documentation is updated

## 🔐 Security & Privacy

- All student data is processed securely
- API keys are stored in environment variables
- No data is retained after processing
- Complete audit trail for transparency
- GDPR compliant data handling

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Anthropic Claude](https://www.anthropic.com/)
- Document processing powered by [PyPDF](https://pypdf.readthedocs.io/) and [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
- Vector operations using [ChromaDB](https://www.trychroma.com/)

## 📧 Contact

- **Project Maintainer**: Your Name
- **Email**: your.email@example.com
- **Issues**: [GitHub Issues](https://github.com/yourusername/answer-sheet-marker/issues)

## 🗺️ Roadmap

### Version 1.0 (Current)
- ✅ Multi-agent architecture
- ✅ Document processing pipeline
- ✅ Basic evaluation and scoring
- ✅ CLI interface
- ✅ REST API with FastAPI
- ✅ Background task processing
- ✅ File upload handling

### Version 1.1 (Planned)
- [ ] Web-based UI
- [ ] WebSocket for real-time updates
- [ ] Multi-language support
- [ ] Advanced analytics dashboard
- [ ] Mobile app

### Version 2.0 (Future)
- [ ] Machine learning from corrections
- [ ] Plagiarism detection
- [ ] LMS integration (Canvas, Moodle)
- [ ] Real-time collaboration features
- [ ] Advanced reporting with charts

## 💡 Use Cases

1. **Educational Institutions**
   - Automate grading for standardized tests
   - Reduce teacher workload
   - Ensure consistent marking

2. **Online Learning Platforms**
   - Scale assessment capabilities
   - Provide instant feedback
   - Support large student cohorts

3. **Corporate Training**
   - Evaluate employee assessments
   - Track learning progress
   - Generate analytics

4. **Tutoring Services**
   - Quick assessment of practice tests
   - Detailed performance analysis
   - Personalized learning recommendations

## ⚠️ Limitations

- Works best with typed or clearly handwritten text
- May require human review for highly subjective essays
- Accuracy depends on marking guide quality
- Limited to languages supported by OCR
- Requires clear question numbering in answer sheets

## 🆘 Troubleshooting

### Common Issues

**Issue**: OCR not working
```bash
# Install Tesseract OCR
# macOS
brew install tesseract

# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# Windows
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
```

**Issue**: API rate limits
```
Solution: Adjust MAX_CONCURRENT_REQUESTS in .env
Reduce batch size or add delays between requests
```

**Issue**: Low confidence scores
```
Solution: Improve marking guide detail
Provide sample answers
Calibrate system with known samples
```

## 📚 Resources

- [Anthropic Documentation](https://docs.anthropic.com/)
- [Prompt Engineering Guide](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering)
- [Poetry Documentation](https://python-poetry.org/docs/)
- [Pydantic Documentation](https://docs.pydantic.dev/)

---

**Built with ❤️ using Claude 4 Sonnet**

*Making education more efficient, one answer sheet at a time.*
