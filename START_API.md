# Answer Sheet Marker API - Quick Start Guide

## Starting the API Server

### Option 1: Using Uvicorn (Recommended for Development)
```bash
# Start with auto-reload (recommended during development)
poetry run uvicorn answer_marker.api.main:app --reload --host 0.0.0.0 --port 8000

# Or without auto-reload (for production)
poetry run uvicorn answer_marker.api.main:app --host 0.0.0.0 --port 8000
```

### Option 2: Using Python Module
```bash
poetry run python -m answer_marker.api.main
```

### Access Points
- **API Base URL**: `http://localhost:8000`
- **Interactive API Docs (Swagger UI)**: `http://localhost:8000/docs`
- **Alternative Docs (ReDoc)**: `http://localhost:8000/redoc`
- **OpenAPI Schema**: `http://localhost:8000/openapi.json`

---

## Available API Endpoints

### 1. Health & Info
- `GET /` - API root information
- `GET /health` - Health check with system status

### 2. Marking Guides
- `POST /api/v1/marking-guides/upload` - Upload marking guide PDF
- `GET /api/v1/marking-guides` - List all uploaded marking guides
- `GET /api/v1/marking-guides/{guide_id}` - Get specific marking guide details

### 3. Answer Sheet Marking
- `POST /api/v1/answer-sheets/mark` - Mark a single student's answer sheet

### 4. Reports
- `GET /api/v1/reports` - List all generated marking reports
- `GET /api/v1/reports/{report_id}` - Get specific marking report

---

## API Usage Examples

### 1. Check API Health
```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-11-06T14:43:04.115279",
  "llm_provider": "anthropic",
  "llm_model": "claude-sonnet-4-5-20250929"
}
```

---

### 2. Upload Marking Guide (Questions + Rubric)

**Upload the assessment PDF containing:**
- Question descriptions
- Mark allocation
- Marking criteria/rubric
- Evaluation guidelines

```bash
curl -X POST "http://localhost:8000/api/v1/marking-guides/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@example/Assessment.pdf"
```

**Response:**
```json
{
  "guide_id": "guide_abc123",
  "title": "Financial Accounting Assessment",
  "total_marks": 118.0,
  "num_questions": 10,
  "questions": [
    {
      "question_id": "Q1",
      "question_number": "1",
      "max_marks": 10.0,
      "question_type": "short_answer",
      "has_rubric": true
    },
    ...
  ],
  "analyzed": true,
  "created_at": "2025-11-06T10:30:00"
}
```

**Save the `guide_id` - you'll need it for marking!**

---

### 3. List All Marking Guides

```bash
curl http://localhost:8000/api/v1/marking-guides
```

**Response:**
```json
["guide_abc123", "guide_def456"]
```

---

### 4. Get Marking Guide Details

```bash
curl http://localhost:8000/api/v1/marking-guides/guide_abc123
```

**Response:**
```json
{
  "guide_id": "guide_abc123",
  "title": "Financial Accounting Assessment",
  "total_marks": 118.0,
  "num_questions": 10,
  "questions": [...],
  "analyzed": true,
  "created_at": "2025-11-06T10:30:00"
}
```

---

### 5. Mark a Student's Answer Sheet

**Upload student answer sheet PDF for marking:**

```bash
curl -X POST "http://localhost:8000/api/v1/answer-sheets/mark" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "marking_guide_id=guide_abc123" \
  -F "student_id=student_001" \
  -F "file=@example/Student Answer Sheet 1.pdf"
```

**Response:**
```json
{
  "report_id": "report_xyz789",
  "student_id": "student_001",
  "marking_guide_id": "guide_abc123",
  "assessment_title": "Financial Accounting Assessment",
  "score": {
    "total_marks": 85.5,
    "max_marks": 118.0,
    "percentage": 72.5,
    "grade": "B",
    "passed": true
  },
  "num_questions": 10,
  "requires_review": false,
  "processing_time": 45.2,
  "marked_at": "2025-11-06T10:35:00"
}
```

**Note:** This endpoint takes ~30-60 seconds per student because it uses AI to:
1. Extract answers from the PDF
2. Analyze each answer against the marking guide
3. Calculate scores and generate feedback

---

### 6. List All Reports

```bash
curl http://localhost:8000/api/v1/reports
```

**Response:**
```json
["report_xyz789", "report_abc456"]
```

---

### 7. Get Specific Report

```bash
curl http://localhost:8000/api/v1/reports/report_xyz789
```

**Response:**
```json
{
  "report_id": "report_xyz789",
  "student_id": "student_001",
  "assessment_title": "Financial Accounting Assessment",
  "score": {
    "total_marks": 85.5,
    "max_marks": 118.0,
    "percentage": 72.5,
    "grade": "B",
    "passed": true
  },
  "num_questions": 10,
  "requires_review": false,
  "processing_time": 45.2,
  "marked_at": "2025-11-06T10:35:00"
}
```

---

## Complete Workflow Example

### Step 1: Start the API Server
```bash
poetry run uvicorn answer_marker.api.main:app --reload
```

### Step 2: Upload Marking Guide
```bash
# Upload the assessment with questions and marking rubric
GUIDE_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/marking-guides/upload" \
  -F "file=@example/Assessment.pdf")

# Extract the guide_id
GUIDE_ID=$(echo $GUIDE_RESPONSE | python -c "import sys, json; print(json.load(sys.stdin)['guide_id'])")

echo "Marking Guide ID: $GUIDE_ID"
```

### Step 3: Mark Student Answer Sheets
```bash
# Mark student 1
curl -X POST "http://localhost:8000/api/v1/answer-sheets/mark" \
  -F "marking_guide_id=$GUIDE_ID" \
  -F "student_id=student_001" \
  -F "file=@example/Student Answer Sheet 1.pdf" \
  | python -m json.tool

# Mark student 2
curl -X POST "http://localhost:8000/api/v1/answer-sheets/mark" \
  -F "marking_guide_id=$GUIDE_ID" \
  -F "student_id=student_002" \
  -F "file=@example/Student Answer Sheet 2.pdf" \
  | python -m json.tool

# Mark student 3
curl -X POST "http://localhost:8000/api/v1/answer-sheets/mark" \
  -F "marking_guide_id=$GUIDE_ID" \
  -F "student_id=student_003" \
  -F "file=@example/Student Answer Sheet 3.pdf" \
  | python -m json.tool
```

### Step 4: View All Reports
```bash
curl http://localhost:8000/api/v1/reports | python -m json.tool
```

---

## Using Postman or Insomnia

### Import OpenAPI Schema
1. Start the API server
2. Go to `http://localhost:8000/openapi.json`
3. Copy the JSON
4. Import into Postman/Insomnia as "OpenAPI 3.0"
5. All endpoints will be auto-configured!

### Or Use Interactive Docs
1. Go to `http://localhost:8000/docs`
2. Click "Try it out" on any endpoint
3. Fill in parameters and upload files
4. Click "Execute"
5. View responses directly in the browser!

---

## Python Client Example

```python
import requests

# Base URL
BASE_URL = "http://localhost:8000"

# 1. Check health
response = requests.get(f"{BASE_URL}/health")
print(response.json())

# 2. Upload marking guide
with open("example/Assessment.pdf", "rb") as f:
    response = requests.post(
        f"{BASE_URL}/api/v1/marking-guides/upload",
        files={"file": f}
    )
    guide_data = response.json()
    guide_id = guide_data["guide_id"]
    print(f"Uploaded guide: {guide_id}")

# 3. Mark answer sheet
with open("example/Student Answer Sheet 1.pdf", "rb") as f:
    response = requests.post(
        f"{BASE_URL}/api/v1/answer-sheets/mark",
        data={
            "marking_guide_id": guide_id,
            "student_id": "student_001"
        },
        files={"file": f}
    )
    report = response.json()
    print(f"Score: {report['score']['total_marks']}/{report['score']['max_marks']}")
    print(f"Grade: {report['score']['grade']}")
```

---

## JavaScript/TypeScript Client Example

```javascript
// Using fetch API
const BASE_URL = 'http://localhost:8000';

// 1. Check health
const health = await fetch(`${BASE_URL}/health`);
console.log(await health.json());

// 2. Upload marking guide
const formData = new FormData();
formData.append('file', markingGuideFile); // File object from input

const uploadResponse = await fetch(`${BASE_URL}/api/v1/marking-guides/upload`, {
  method: 'POST',
  body: formData
});
const guideData = await uploadResponse.json();
const guideId = guideData.guide_id;

// 3. Mark answer sheet
const markingFormData = new FormData();
markingFormData.append('marking_guide_id', guideId);
markingFormData.append('student_id', 'student_001');
markingFormData.append('file', answerSheetFile); // File object from input

const markResponse = await fetch(`${BASE_URL}/api/v1/answer-sheets/mark`, {
  method: 'POST',
  body: markingFormData
});
const report = await markResponse.json();
console.log(`Score: ${report.score.total_marks}/${report.score.max_marks}`);
console.log(`Grade: ${report.score.grade}`);
```

---

## Important Notes

### File Requirements
- **Format**: PDF only
- **Size**: Max 10 MB per file
- **Marking Guide**: Must contain questions, marks, and evaluation criteria
- **Answer Sheets**: Must have clear question numbers and student responses

### Processing Time
- **Marking Guide Upload**: ~10-30 seconds (analyzes all questions)
- **Answer Sheet Marking**: ~30-60 seconds per student (AI evaluation)

### Data Storage
- Currently stored **in-memory** (lost when server restarts)
- For production, you'll want to add database persistence

### CORS Configuration
- Allowed origins: `http://localhost:3000`, `http://localhost:8000`
- Can be configured in `src/answer_marker/api/config.py`

### Error Responses
All errors follow this format:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": {}
  }
}
```

---

## Next Steps for Frontend/Mobile Development

1. **Start the API server** (see above)
2. **Test endpoints** using the interactive docs at `/docs`
3. **Build your frontend** using the examples above
4. **Handle file uploads** for PDFs
5. **Show progress indicators** during marking (takes 30-60s)
6. **Display results** with scores, grades, and feedback

The API is fully ready for integration with React, Vue, Angular, React Native, Flutter, etc.!
