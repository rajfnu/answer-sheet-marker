# Complete Workflow: Upload Assessments & Mark Answer Sheets

## Scenario: You have 3 students taking "Financial Accounting Assessment"

### Step 1: Upload the Assessment (Marking Guide)

```bash
# Upload assessment PDF with questions and rubric
curl -X POST "http://localhost:8001/api/v1/marking-guides/upload" \
  -F "file=@example/Assessment.pdf"
```

**Response:**
```json
{
  "guide_id": "guide_abc123",
  "title": "Financial Accounting Assessment",
  "total_marks": 118.0,
  "num_questions": 10,
  "analyzed": true
}
```

**💾 SAVE THIS:** `guide_id = "guide_abc123"` - You'll need it for marking!

---

### Step 2: Mark Student 1's Answer Sheet

```bash
# Mark student 1 using the guide_id from Step 1
curl -X POST "http://localhost:8001/api/v1/answer-sheets/mark" \
  -F "marking_guide_id=guide_abc123" \
  -F "student_id=student_001" \
  -F "file=@example/Student Answer Sheet 1.pdf"
```

**Response:**
```json
{
  "report_id": "report_001",
  "student_id": "student_001",
  "marking_guide_id": "guide_abc123",  ← Linked to assessment!
  "assessment_title": "Financial Accounting Assessment",
  "score": {
    "total_marks": 85.5,
    "max_marks": 118.0,
    "percentage": 72.5,
    "grade": "B",
    "passed": true
  },
  "processing_time": 45.2
}
```

---

### Step 3: Mark Student 2's Answer Sheet (Same Assessment)

```bash
# Use SAME guide_id for same assessment
curl -X POST "http://localhost:8001/api/v1/answer-sheets/mark" \
  -F "marking_guide_id=guide_abc123" \
  -F "student_id=student_002" \
  -F "file=@example/Student Answer Sheet 2.pdf"
```

**Response:**
```json
{
  "report_id": "report_002",
  "student_id": "student_002",
  "marking_guide_id": "guide_abc123",  ← Same assessment!
  "assessment_title": "Financial Accounting Assessment",
  "score": {
    "total_marks": 92.0,
    "max_marks": 118.0,
    "percentage": 78.0,
    "grade": "B+",
    "passed": true
  }
}
```

---

### Step 4: Mark Student 3's Answer Sheet (Same Assessment)

```bash
# Use SAME guide_id again
curl -X POST "http://localhost:8001/api/v1/answer-sheets/mark" \
  -F "marking_guide_id=guide_abc123" \
  -F "student_id=student_003" \
  -F "file=@example/Student Answer Sheet 3.pdf"
```

---

## Multiple Assessments Example

### Scenario: You have 3 different assessments

#### Assessment 1: Midterm Exam

```bash
# Step 1: Upload midterm assessment
curl -X POST "http://localhost:8001/api/v1/marking-guides/upload" \
  -F "file=@assessments/Midterm_Exam.pdf"

# Response: guide_id = "guide_midterm_123"

# Step 2: Mark students for midterm
curl -X POST "http://localhost:8001/api/v1/answer-sheets/mark" \
  -F "marking_guide_id=guide_midterm_123" \
  -F "student_id=student_001" \
  -F "file=@answers/student_001_midterm.pdf"
```

#### Assessment 2: Final Exam (Different Assessment!)

```bash
# Step 1: Upload final exam assessment
curl -X POST "http://localhost:8001/api/v1/marking-guides/upload" \
  -F "file=@assessments/Final_Exam.pdf"

# Response: guide_id = "guide_final_456"  ← Different guide_id!

# Step 2: Mark students for final exam
curl -X POST "http://localhost:8001/api/v1/answer-sheets/mark" \
  -F "marking_guide_id=guide_final_456" \  ← Different guide_id!
  -F "student_id=student_001" \
  -F "file=@answers/student_001_final.pdf"
```

#### Assessment 3: Quiz 1 (Yet Another Assessment!)

```bash
# Step 1: Upload quiz assessment
curl -X POST "http://localhost:8001/api/v1/marking-guides/upload" \
  -F "file=@assessments/Quiz_1.pdf"

# Response: guide_id = "guide_quiz1_789"  ← Another unique guide_id!

# Step 2: Mark students for quiz
curl -X POST "http://localhost:8001/api/v1/answer-sheets/mark" \
  -F "marking_guide_id=guide_quiz1_789" \  ← Quiz guide_id!
  -F "student_id=student_001" \
  -F "file=@answers/student_001_quiz1.pdf"
```

---

## How the System Tracks Everything

### Database Structure (Conceptual)

```
MARKING GUIDES (Assessments)
┌──────────────────┬─────────────────────────────┬──────────┐
│ guide_id         │ title                       │ marks    │
├──────────────────┼─────────────────────────────┼──────────┤
│ guide_midterm_123│ Midterm Exam                │ 100      │
│ guide_final_456  │ Final Exam                  │ 150      │
│ guide_quiz1_789  │ Quiz 1                      │ 25       │
└──────────────────┴─────────────────────────────┴──────────┘

MARKING REPORTS (Answer Sheets)
┌────────────┬─────────────┬──────────────────┬────────┬───────┐
│ report_id  │ student_id  │ marking_guide_id │ score  │ grade │
├────────────┼─────────────┼──────────────────┼────────┼───────┤
│ report_001 │ student_001 │ guide_midterm_123│ 85.5   │ B     │
│ report_002 │ student_002 │ guide_midterm_123│ 92.0   │ A-    │
│ report_003 │ student_001 │ guide_final_456  │ 120.5  │ A     │
│ report_004 │ student_001 │ guide_quiz1_789  │ 23.0   │ A+    │
└────────────┴─────────────┴──────────────────┴────────┴───────┘
                              ↑
                              This links answer sheet to assessment!
```

### Query Examples

**Get all reports for Midterm Exam:**
```
Filter by: marking_guide_id = "guide_midterm_123"
Result: report_001, report_002
```

**Get all of student_001's reports:**
```
Filter by: student_id = "student_001"
Result: report_001, report_003, report_004
```

**Get student_001's midterm result:**
```
Filter by: student_id = "student_001" AND marking_guide_id = "guide_midterm_123"
Result: report_001 (score: 85.5, grade: B)
```

---

## Frontend Implementation Example

### JavaScript/TypeScript

```javascript
// Component: MarkStudentAnswers.tsx

async function markStudents(assessmentId: string, students: File[]) {
  const results = [];

  for (const studentFile of students) {
    // Extract student ID from filename or form
    const studentId = extractStudentId(studentFile.name);

    // Mark this student's answer sheet for THIS assessment
    const formData = new FormData();
    formData.append('marking_guide_id', assessmentId);  // Links to assessment!
    formData.append('student_id', studentId);
    formData.append('file', studentFile);

    const response = await fetch('http://localhost:8001/api/v1/answer-sheets/mark', {
      method: 'POST',
      body: formData
    });

    const report = await response.json();
    results.push(report);
  }

  return results;
}

// Usage:
const midtermAssessmentId = "guide_midterm_123";
const studentFiles = [student1.pdf, student2.pdf, student3.pdf];

const reports = await markStudents(midtermAssessmentId, studentFiles);
console.log(`Marked ${reports.length} students for midterm exam`);
```

---

## Key Points

1. **One Assessment = One guide_id**
   - Upload assessment once
   - Get unique guide_id
   - Use for ALL students taking that assessment

2. **Answer Sheets Linked via guide_id**
   - Each marking request includes marking_guide_id
   - System knows which rubric to use
   - Report shows which assessment it belongs to

3. **Multiple Assessments = Multiple guide_ids**
   - Each assessment gets unique guide_id
   - Answer sheets use corresponding guide_id
   - Reports grouped by guide_id

4. **Same Student, Multiple Assessments**
   - One student can have multiple reports
   - Each report linked to different guide_id
   - Easy to query: "Show all of student X's results"

5. **File Storage**
   - Assessment PDFs → `data/uploads/file_{id}_{Assessment_name}.pdf`
   - Answer Sheet PDFs → `data/uploads/file_{id}_{student_answer}.pdf`
   - All identified by unique file IDs
   - Linked via guide_id in database/memory

---

## API Endpoints Reference

```
Upload Assessment:
POST /api/v1/marking-guides/upload
  → Returns: guide_id

Mark Answer Sheet:
POST /api/v1/answer-sheets/mark
  → Requires: marking_guide_id, student_id, file
  → Returns: report with marking_guide_id reference

List Assessments:
GET /api/v1/marking-guides
  → Returns: Array of guide_ids

Get Assessment Details:
GET /api/v1/marking-guides/{guide_id}
  → Returns: Assessment info

Get Report:
GET /api/v1/reports/{report_id}
  → Returns: Student's marking report
```

---

## Best Practices

1. **Store guide_id in your database**
   ```sql
   CREATE TABLE assessments (
     id SERIAL PRIMARY KEY,
     guide_id VARCHAR(50) UNIQUE,  -- From API
     title VARCHAR(200),
     created_at TIMESTAMP
   );
   ```

2. **Store report_id with student records**
   ```sql
   CREATE TABLE student_results (
     id SERIAL PRIMARY KEY,
     student_id VARCHAR(50),
     assessment_id INTEGER,  -- References assessments table
     report_id VARCHAR(50),  -- From API
     guide_id VARCHAR(50),   -- For quick filtering
     score DECIMAL,
     grade VARCHAR(5)
   );
   ```

3. **Frontend State Management**
   ```typescript
   interface Assessment {
     guideId: string;
     title: string;
     totalMarks: number;
   }

   interface StudentReport {
     reportId: string;
     studentId: string;
     assessmentGuideId: string;  // Links to Assessment
     score: number;
     grade: string;
   }
   ```

The **marking_guide_id** is the key that connects everything! 🔑
