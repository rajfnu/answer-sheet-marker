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

## 🚀 Getting Started

This guide will help you set up and run the Answer Sheet Marker system locally in **under 10 minutes**.

### Prerequisites

Before you begin, make sure you have the following installed:

- **Python 3.11+** - [Download here](https://www.python.org/downloads/)
- **Node.js 18+** - [Download here](https://nodejs.org/)
- **Poetry** - Python dependency manager
  ```bash
  curl -sSL https://install.python-poetry.org | python3 -
  ```
- **Anthropic API Key** - [Get one here](https://console.anthropic.com/)

### Step-by-Step Setup

#### 1️⃣ Clone the Repository

```bash
git clone https://github.com/rajfnu/answer-sheet-marker.git
cd answer-sheet-marker
```

#### 2️⃣ Backend Setup

```bash
# Navigate to backend directory
cd backend

# Install dependencies (this may take 2-3 minutes)
poetry install

# Create environment file
cp .env.example .env

# Edit .env and add your Anthropic API key
# You can use nano, vim, or any text editor:
nano .env
```

**Important**: Update `.env` file with your API key:
```bash
# Required
ANTHROPIC_API_KEY=sk-ant-your-actual-key-here

# Optional (defaults are fine)
LLM_PROVIDER=anthropic
LLM_MODEL=claude-sonnet-4-5-20250929
API_HOST=0.0.0.0
API_PORT=8001
```

#### 3️⃣ Frontend Setup

```bash
# Navigate to frontend directory (from project root)
cd ../frontend

# Install dependencies (this may take 2-3 minutes)
npm install
```

#### 4️⃣ Start the Application

You'll need **two terminal windows**:

**Terminal 1 - Backend API:**
```bash
cd backend
poetry run uvicorn answer_marker.api.main:app --host 0.0.0.0 --port 8001 --reload
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8001
INFO:     Application startup complete.
```

**Terminal 2 - Frontend UI:**
```bash
cd frontend
npm run dev
```

You should see:
```
  VITE v5.x.x  ready in XXX ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: http://192.168.x.x:5173/
```

#### 5️⃣ Access the Application

Open your browser and go to:

- **Frontend UI**: http://localhost:5173
- **Backend API**: http://localhost:8001
- **API Documentation**: http://localhost:8001/docs

### 🎯 First Steps

Once the application is running:

1. **Upload an Assessment** (Marking Guide)
   - Click "Upload Assessment" in the sidebar
   - Upload your PDF marking guide (e.g., `example/Assessment.pdf`)
   - Wait for processing (~30-60 seconds)
   - You'll see all questions extracted with marks

2. **Mark Answer Sheets**
   - Click "Mark Answers" in the sidebar
   - Select the assessment you just uploaded
   - Enter student ID (e.g., "STUDENT001")
   - Upload student answer sheet PDF
   - Click "Submit for Marking"
   - Wait for evaluation (~1-2 minutes)

3. **View Results**
   - Click "Reports" in the sidebar
   - View detailed marking breakdown
   - See scores, grades, and feedback for each question

### 📁 Example Files

The repository includes sample files in `example/`:

```bash
example/
├── Assessment.pdf              # Sample marking guide
├── Student Answer Sheet 1.pdf  # Sample student answers
├── Student Answer Sheet 2.pdf
└── Student Answer Sheet 3.pdf
```

Use these to test the system before creating your own assessments.

### 🔧 Troubleshooting

**Issue**: `poetry: command not found`
```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Add to PATH (restart terminal after)
export PATH="$HOME/.local/bin:$PATH"
```

**Issue**: `Module not found` errors
```bash
# Reinstall dependencies
cd backend
poetry install --no-cache
```

**Issue**: Frontend won't start
```bash
# Clear cache and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
```

**Issue**: API returns 500 errors
- Check that your `ANTHROPIC_API_KEY` is correct in `backend/.env`
- Verify you have API credits: https://console.anthropic.com/
- Check backend logs in terminal for detailed error messages

**Issue**: "Failed to create assessment"
- Ensure storage directories exist:
  ```bash
  cd backend
  mkdir -p data/storage/marking_guides data/storage/reports data/storage/cache
  ```

### 🚀 Development Mode

For development with auto-reload:

**Backend** (already uses --reload):
```bash
cd backend
poetry run uvicorn answer_marker.api.main:app --host 0.0.0.0 --port 8001 --reload
```

**Frontend** (already has HMR):
```bash
cd frontend
npm run dev
```

Changes to code will automatically reload the servers.

### 🧪 Running Tests

```bash
# Backend tests
cd backend
poetry run pytest

# With coverage
poetry run pytest --cov=src/answer_marker --cov-report=html

# Specific test
poetry run pytest tests/unit/test_orchestrator.py -v
```

### 📖 Next Steps

After getting the system running:

1. **Read the TODO.md** - See planned features and roadmap
2. **Check docs/** - Additional documentation and guides
3. **Try the API docs** - http://localhost:8001/docs
4. **Explore the code** - Start with `backend/src/answer_marker/`

### 🎓 Understanding the System

```
┌─────────────────────────────────────────────────────┐
│  Frontend (React + TypeScript)                      │
│  http://localhost:5173                              │
│  - Upload assessments                               │
│  - Mark answer sheets                               │
│  - View reports                                     │
└──────────────────┬──────────────────────────────────┘
                   │ REST API calls
                   ▼
┌─────────────────────────────────────────────────────┐
│  Backend API (FastAPI + Python)                     │
│  http://localhost:8001                              │
│  - Document processing                              │
│  - Multi-agent marking system                       │
│  - Persistent storage                               │
└──────────────────┬──────────────────────────────────┘
                   │ API calls
                   ▼
┌─────────────────────────────────────────────────────┐
│  Anthropic Claude API                               │
│  - Question analysis                                │
│  - Answer evaluation                                │
│  - Feedback generation                              │
└─────────────────────────────────────────────────────┘
```

### 💡 Quick Commands Reference

```bash
# Start backend
cd backend && poetry run uvicorn answer_marker.api.main:app --host 0.0.0.0 --port 8001 --reload

# Start frontend
cd frontend && npm run dev

# Run tests
cd backend && poetry run pytest

# Check API health
curl http://localhost:8001/health

# Format code
cd backend && poetry run black src tests

# Build for production
cd frontend && npm run build
```

---

**Need help?** Check the [docs/](docs/) directory or [open an issue](https://github.com/rajfnu/answer-sheet-marker/issues).

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
- **QUICK_START.md** - Implementation roadmap
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

### Version 1.1 (Planned)
- [ ] Web-based UI
- [ ] REST API
- [ ] Multi-language support
- [ ] Advanced analytics dashboard

### Version 2.0 (Future)
- [ ] Machine learning from corrections
- [ ] Plagiarism detection
- [ ] LMS integration (Canvas, Moodle)
- [ ] Mobile app
- [ ] Real-time collaboration features

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
