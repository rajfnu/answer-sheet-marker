# Answer Sheet Marker - Backend API

AI-powered answer sheet marking system with REST API.

## Quick Start

```bash
# Install dependencies
poetry install

# Configure API key
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Start API server
poetry run uvicorn answer_marker.api.main:app --host 0.0.0.0 --port 8001

# Access interactive docs
open http://localhost:8001/docs
```

## API Endpoints

- `POST /api/v1/marking-guides/upload` - Upload assessment PDF
- `POST /api/v1/answer-sheets/mark` - Mark student answer sheet
- `GET /api/v1/reports/{id}` - Get marking report
- `GET /health` - Health check

See [START_API.md](START_API.md) for complete API documentation.

## Documentation

- [START_API.md](START_API.md) - API usage guide
- [COMPLETE_WORKFLOW_EXAMPLE.md](COMPLETE_WORKFLOW_EXAMPLE.md) - Workflow examples
- [QUICK_START.md](QUICK_START.md) - Getting started guide

## Development

```bash
# Run tests
poetry run pytest

# Format code
poetry run black .
poetry run isort .

# Type checking
poetry run mypy src
```
