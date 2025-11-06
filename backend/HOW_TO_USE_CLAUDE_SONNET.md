# How to Use with Claude Sonnet

## Quick Setup

### 1. Get API Key
- Go to https://console.anthropic.com/
- Create an API key (starts with `sk-ant-...`)

### 2. Configure `.env` File
Create or edit `.env` in the project root:

```bash
LLM_PROVIDER=anthropic
LLM_MODEL=claude-sonnet-4-5-20250929
LLM_API_KEY=sk-ant-your-api-key-here
MAX_TOKENS=8192
TEMPERATURE=0.0
```

### 3. Install Dependencies
```bash
poetry install
poetry shell
```

### 4. Run Marking
```bash
poetry run answer-marker mark \
  --guide path/to/marking_guide.pdf \
  --answers path/to/answer_sheets/ \
  --output ./output
```

## Command Options

```bash
poetry run answer-marker mark \
  --guide <marking_guide.pdf>     # Required: Path to marking guide PDF
  --answers <answer_sheets/>       # Required: Path to answer sheet(s) or directory
  --output <directory>            # Optional: Output directory (default: ./output)
  --assessment-title <title>      # Optional: Assessment title (default: "Assessment")
```

## Examples

**Single answer sheet:**
```bash
poetry run answer-marker mark \
  -g marking_guide.pdf \
  -a student_001.pdf \
  -o ./output
```

**Multiple answer sheets:**
```bash
poetry run answer-marker mark \
  -g marking_guide.pdf \
  -a ./answer_sheets/ \
  -o ./output \
  --assessment-title "Final Exam"
```

## Output

Reports are saved as JSON files in the output directory:
- Format: `{student_id}_report.json`
- Contains: Scores, grades, feedback, and evaluation details

## That's It!

The system will:
1. Process the marking guide
2. Extract answers from PDFs
3. Evaluate each answer using Claude Sonnet
4. Generate scores and feedback
5. Save reports to the output directory

