# Data Models - Complete Reference

## Overview

This file provides complete data model definitions for the Answer Sheet Marker system. All models use Pydantic for validation and serialization.

## Implementation Files

Create these models in the following files:

### 1. Question Models (`src/answer_marker/models/question.py`)

```python
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from enum import Enum
from datetime import datetime

class QuestionType(str, Enum):
    """Types of questions supported"""
    MCQ = "mcq"
    SHORT_ANSWER = "short_answer"
    ESSAY = "essay"
    NUMERICAL = "numerical"
    TRUE_FALSE = "true_false"
    MIXED = "mixed"

class KeyConcept(BaseModel):
    """Key concept to evaluate in an answer"""
    concept: str = Field(..., description="The concept to look for")
    points: float = Field(..., ge=0, description="Points allocated to this concept")
    mandatory: bool = Field(default=False, description="Whether this concept is required")
    keywords: List[str] = Field(default=[], description="Keywords associated with this concept")
    description: Optional[str] = Field(None, description="Detailed description of the concept")
    
    class Config:
        json_schema_extra = {
            "example": {
                "concept": "Newton's First Law",
                "points": 2.0,
                "mandatory": True,
                "keywords": ["inertia", "force", "motion"],
                "description": "Must mention that objects maintain state of motion unless acted upon by force"
            }
        }

class EvaluationCriteria(BaseModel):
    """Criteria for different performance levels"""
    excellent: str = Field(..., description="Criteria for excellent performance")
    good: str = Field(..., description="Criteria for good performance")
    satisfactory: str = Field(..., description="Criteria for satisfactory performance")
    poor: str = Field(..., description="Criteria for poor performance")
    
    class Config:
        json_schema_extra = {
            "example": {
                "excellent": "All concepts clearly explained with examples",
                "good": "Most concepts present with minor gaps",
                "satisfactory": "Basic concepts present but incomplete",
                "poor": "Missing most key concepts"
            }
        }

class AnalyzedQuestion(BaseModel):
    """Question with complete analysis and rubric"""
    id: str = Field(..., description="Unique question identifier")
    question_text: str = Field(..., description="The question text")
    question_type: QuestionType
    max_marks: float = Field(..., ge=0, description="Maximum marks for this question")
    key_concepts: List[KeyConcept] = Field(..., description="Key concepts to evaluate")
    evaluation_criteria: EvaluationCriteria
    keywords: List[str] = Field(default=[], description="Important keywords")
    common_mistakes: List[str] = Field(default=[], description="Common mistakes to watch for")
    sample_answer: Optional[str] = Field(None, description="Sample correct answer")
    instructions: Optional[str] = Field(None, description="Special instructions for marking")
    metadata: dict = Field(default={}, description="Additional metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "Q1",
                "question_text": "Explain Newton's First Law of Motion",
                "question_type": "short_answer",
                "max_marks": 5.0,
                "key_concepts": [],
                "evaluation_criteria": {},
                "keywords": ["inertia", "force", "motion"]
            }
        }
```

### 2. Answer Models (`src/answer_marker/models/answer.py`)

```python
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class Answer(BaseModel):
    """Student answer for a single question"""
    question_id: str
    answer_text: str = Field(..., description="The student's answer")
    is_blank: bool = Field(default=False, description="Whether the answer is blank/unanswered")
    metadata: dict = Field(default={}, description="Additional metadata")

class AnswerSheet(BaseModel):
    """Complete answer sheet from a student"""
    student_id: Optional[str] = Field(None, description="Student identifier")
    student_name: Optional[str] = Field(None, description="Student name")
    answers: List[Answer] = Field(..., description="List of answers")
    submission_time: datetime = Field(default_factory=datetime.utcnow)
    source_file: Optional[str] = Field(None, description="Source file path")
    metadata: dict = Field(default={}, description="Additional metadata")
    
    def get_answer(self, question_id: str) -> Optional[Answer]:
        """Get answer for a specific question"""
        for answer in self.answers:
            if answer.question_id == question_id:
                return answer
        return None
    
    def get_answered_count(self) -> int:
        """Count non-blank answers"""
        return sum(1 for answer in self.answers if not answer.is_blank)
```

### 3. Marking Guide Models (`src/answer_marker/models/marking_guide.py`)

```python
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from answer_marker.models.question import AnalyzedQuestion

class MarkingGuide(BaseModel):
    """Complete marking guide for an assessment"""
    title: str = Field(..., description="Assessment title")
    subject: Optional[str] = Field(None, description="Subject/course")
    date: Optional[datetime] = Field(None, description="Assessment date")
    total_marks: float = Field(..., ge=0, description="Total marks available")
    questions: List[AnalyzedQuestion] = Field(..., description="List of questions")
    instructions: Optional[str] = Field(None, description="General marking instructions")
    pass_percentage: float = Field(default=50.0, description="Pass percentage")
    time_limit: Optional[int] = Field(None, description="Time limit in minutes")
    metadata: dict = Field(default={}, description="Additional metadata")
    source_file: Optional[str] = Field(None, description="Source file path")
    
    def get_question(self, question_id: str) -> Optional[AnalyzedQuestion]:
        """Get a specific question by ID"""
        for question in self.questions:
            if question.id == question_id:
                return question
        return None
    
    def validate_total_marks(self) -> bool:
        """Validate that question marks sum to total"""
        sum_marks = sum(q.max_marks for q in self.questions)
        return abs(sum_marks - self.total_marks) < 0.01
```

### 4. Evaluation Models (`src/answer_marker/models/evaluation.py`)

```python
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime

class ConceptEvaluation(BaseModel):
    """Evaluation of a single concept"""
    concept: str
    present: bool = Field(..., description="Whether the concept is present")
    accuracy: Literal["fully_correct", "partially_correct", "incorrect", "not_present"]
    evidence: str = Field(..., description="Evidence from the answer")
    points_earned: float = Field(..., ge=0, description="Points earned for this concept")
    points_possible: float = Field(..., ge=0, description="Maximum points for this concept")
    feedback: Optional[str] = Field(None, description="Specific feedback for this concept")

class AnswerEvaluation(BaseModel):
    """Complete evaluation of a student answer"""
    question_id: str
    student_id: Optional[str] = None
    concepts_identified: List[ConceptEvaluation] = Field(..., description="Concept evaluations")
    overall_quality: Literal["excellent", "good", "satisfactory", "poor", "inadequate"]
    strengths: List[str] = Field(default=[], description="Answer strengths")
    weaknesses: List[str] = Field(default=[], description="Answer weaknesses")
    misconceptions: List[str] = Field(default=[], description="Identified misconceptions")
    confidence_score: float = Field(..., ge=0, le=1, description="Confidence in evaluation")
    requires_human_review: bool = Field(default=False, description="Whether human review needed")
    review_reason: Optional[str] = Field(None, description="Reason for human review")
    marks_awarded: float = Field(..., ge=0, description="Total marks awarded")
    max_marks: float = Field(..., ge=0, description="Maximum marks possible")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict = Field(default={}, description="Additional metadata")
    
    @property
    def percentage(self) -> float:
        """Calculate percentage score"""
        if self.max_marks == 0:
            return 0.0
        return (self.marks_awarded / self.max_marks) * 100

class QuestionScore(BaseModel):
    """Score for a single question"""
    question_id: str
    marks_awarded: float = Field(..., ge=0)
    max_marks: float = Field(..., ge=0)
    percentage: float = Field(..., ge=0, le=100)
    quality: Optional[str] = None

class ScoringResult(BaseModel):
    """Final scoring result for an answer sheet"""
    student_id: Optional[str] = None
    total_marks: float = Field(..., ge=0, description="Total marks awarded")
    max_marks: float = Field(..., ge=0, description="Maximum marks possible")
    percentage: float = Field(..., ge=0, le=100, description="Percentage score")
    grade: str = Field(..., description="Letter grade")
    question_scores: List[QuestionScore] = Field(..., description="Scores per question")
    passed: bool = Field(..., description="Whether the student passed")
    rank: Optional[str] = Field(None, description="Performance rank")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    @property
    def questions_passed(self) -> int:
        """Count questions with >50% score"""
        return sum(1 for q in self.question_scores if q.percentage >= 50)

class QAFlag(BaseModel):
    """Flag raised by QA agent"""
    question_id: str
    reason: str
    severity: Literal["low", "medium", "high"]
    details: dict = {}

class QAResult(BaseModel):
    """Quality assurance result"""
    passed: bool = Field(..., description="Whether QA checks passed")
    requires_human_review: bool = Field(..., description="Whether human review needed")
    flags: List[QAFlag] = Field(default=[], description="QA flags raised")
    issues: List[dict] = Field(default=[], description="Issues found")
    confidence_level: Literal["high", "medium", "low"]
    consistency_score: float = Field(default=1.0, ge=0, le=1, description="Consistency score")
    recommendations: List[str] = Field(default=[], description="QA recommendations")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
```

### 5. Feedback Models (`src/answer_marker/models/feedback.py`)

```python
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class QuestionFeedback(BaseModel):
    """Feedback for a single question"""
    question_id: str
    feedback: str = Field(..., description="Main feedback text")
    strengths: List[str] = Field(default=[], description="Specific strengths")
    improvement_areas: List[str] = Field(default=[], description="Areas for improvement")
    suggestions: List[str] = Field(default=[], description="Actionable suggestions")
    resources: List[str] = Field(default=[], description="Recommended learning resources")

class FeedbackReport(BaseModel):
    """Complete feedback report"""
    student_id: Optional[str] = None
    overall_feedback: str = Field(..., description="Overall feedback summary")
    question_feedback: List[QuestionFeedback] = Field(..., description="Per-question feedback")
    key_strengths: List[str] = Field(default=[], description="Overall strengths")
    key_improvements: List[str] = Field(default=[], description="Key areas to improve")
    study_recommendations: List[str] = Field(default=[], description="Study recommendations")
    encouragement: str = Field(default="", description="Encouraging message")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
```

### 6. Report Models (`src/answer_marker/models/report.py`)

```python
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from answer_marker.models.evaluation import AnswerEvaluation, ScoringResult, QAResult
from answer_marker.models.feedback import FeedbackReport

class EvaluationReport(BaseModel):
    """Complete evaluation report for an answer sheet"""
    # Student Information
    student_id: Optional[str] = None
    student_name: Optional[str] = None
    
    # Assessment Information
    assessment_title: str
    assessment_date: Optional[datetime] = None
    
    # Scoring
    scoring_result: ScoringResult
    
    # Evaluations
    question_evaluations: List[AnswerEvaluation] = Field(..., description="All question evaluations")
    
    # Feedback
    feedback_report: FeedbackReport
    
    # Quality Assurance
    qa_result: QAResult
    
    # Metadata
    marked_by: str = Field(default="AI Marker", description="Marker identifier")
    marked_at: datetime = Field(default_factory=datetime.utcnow)
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")
    version: str = Field(default="1.0.0", description="System version")
    
    # Flags
    requires_review: bool = Field(default=False)
    review_priority: Literal["low", "medium", "high"] = Field(default="low")
    
    class Config:
        json_schema_extra = {
            "example": {
                "student_id": "STU001",
                "assessment_title": "Mathematics Final Exam",
                "scoring_result": {},
                "question_evaluations": [],
                "feedback_report": {},
                "qa_result": {}
            }
        }
    
    def to_json_file(self, filepath: str):
        """Save report to JSON file"""
        import json
        from pathlib import Path
        
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(self.model_dump(), f, indent=2, default=str)
    
    @classmethod
    def from_json_file(cls, filepath: str):
        """Load report from JSON file"""
        import json
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls(**data)

class BatchReport(BaseModel):
    """Report for batch processing"""
    batch_id: str
    assessment_title: str
    total_sheets: int
    processed_sheets: int
    failed_sheets: int
    reports: List[EvaluationReport] = []
    
    # Statistics
    average_score: float
    median_score: float
    highest_score: float
    lowest_score: float
    pass_rate: float
    
    # Timing
    started_at: datetime
    completed_at: Optional[datetime] = None
    total_processing_time: Optional[float] = None
    
    # Flags
    sheets_requiring_review: int = 0
    
    def generate_summary(self) -> dict:
        """Generate summary statistics"""
        return {
            "total_sheets": self.total_sheets,
            "processed": self.processed_sheets,
            "failed": self.failed_sheets,
            "success_rate": (self.processed_sheets / self.total_sheets * 100) if self.total_sheets > 0 else 0,
            "average_score": self.average_score,
            "pass_rate": self.pass_rate,
            "requiring_review": self.sheets_requiring_review
        }
```

### 7. Session Models (`src/answer_marker/models/session.py`)

```python
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime
from pathlib import Path

class MarkingSession(BaseModel):
    """Marking session tracking"""
    session_id: str = Field(..., description="Unique session identifier")
    marking_guide_path: str
    answer_sheets_path: str
    output_path: str
    
    # Status
    status: Literal["initialized", "processing", "completed", "failed"] = "initialized"
    
    # Progress
    total_sheets: int = 0
    processed_sheets: int = 0
    failed_sheets: int = 0
    
    # Timing
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    # Results
    reports: List[str] = Field(default=[], description="Paths to generated reports")
    
    # Configuration
    config: dict = Field(default={}, description="Session configuration")
    
    def update_progress(self, processed: int, failed: int = 0):
        """Update session progress"""
        self.processed_sheets = processed
        self.failed_sheets = failed
        
        if self.processed_sheets + self.failed_sheets >= self.total_sheets:
            self.status = "completed"
            self.completed_at = datetime.utcnow()
    
    def get_progress_percentage(self) -> float:
        """Get progress as percentage"""
        if self.total_sheets == 0:
            return 0.0
        return (self.processed_sheets + self.failed_sheets) / self.total_sheets * 100
```

## Usage Examples

### Creating a Marking Guide

```python
from answer_marker.models.marking_guide import MarkingGuide
from answer_marker.models.question import AnalyzedQuestion, KeyConcept, EvaluationCriteria

marking_guide = MarkingGuide(
    title="Physics Test - Chapter 1",
    subject="Physics",
    total_marks=50.0,
    questions=[
        AnalyzedQuestion(
            id="Q1",
            question_text="Explain Newton's First Law",
            question_type="short_answer",
            max_marks=5.0,
            key_concepts=[
                KeyConcept(
                    concept="Inertia",
                    points=2.0,
                    mandatory=True,
                    keywords=["inertia", "rest", "motion"]
                ),
                KeyConcept(
                    concept="Force required to change motion",
                    points=3.0,
                    mandatory=True,
                    keywords=["force", "change", "motion"]
                )
            ],
            evaluation_criteria=EvaluationCriteria(
                excellent="Clear explanation with both concepts and examples",
                good="Both concepts present, minor gaps",
                satisfactory="Basic understanding shown",
                poor="Missing key concepts"
            )
        )
    ]
)
```

### Creating an Answer Sheet

```python
from answer_marker.models.answer import AnswerSheet, Answer

answer_sheet = AnswerSheet(
    student_id="STU001",
    student_name="John Doe",
    answers=[
        Answer(
            question_id="Q1",
            answer_text="Newton's First Law states that an object at rest stays at rest..."
        ),
        Answer(
            question_id="Q2",
            answer_text="F = ma means...",
            is_blank=False
        )
    ]
)
```

### Creating an Evaluation

```python
from answer_marker.models.evaluation import AnswerEvaluation, ConceptEvaluation

evaluation = AnswerEvaluation(
    question_id="Q1",
    concepts_identified=[
        ConceptEvaluation(
            concept="Inertia",
            present=True,
            accuracy="fully_correct",
            evidence="Student mentioned 'object at rest stays at rest'",
            points_earned=2.0,
            points_possible=2.0
        )
    ],
    overall_quality="good",
    strengths=["Clear explanation", "Good use of terminology"],
    weaknesses=["Could include more examples"],
    confidence_score=0.85,
    marks_awarded=4.5,
    max_marks=5.0
)
```

## Model Validation

All models include built-in validation:

```python
from pydantic import ValidationError

try:
    # This will raise ValidationError
    invalid_score = ScoringResult(
        total_marks=-5.0,  # Cannot be negative
        max_marks=10.0,
        percentage=150.0,  # Cannot exceed 100
        grade="A"
    )
except ValidationError as e:
    print(e)
```

## Serialization

Models can be easily serialized:

```python
# To dictionary
report_dict = report.model_dump()

# To JSON
report_json = report.model_dump_json(indent=2)

# From dictionary
report = EvaluationReport(**report_dict)

# From JSON
import json
report = EvaluationReport(**json.loads(report_json))
```

## Best Practices

1. **Always validate**: Use Pydantic's validation features
2. **Type hints**: Provide proper type hints for all fields
3. **Descriptions**: Add field descriptions for clarity
4. **Defaults**: Provide sensible defaults where appropriate
5. **Methods**: Add helper methods for common operations
6. **Examples**: Include examples in Config for documentation
7. **Immutability**: Consider using `frozen=True` for immutable models

## Testing Models

```python
import pytest
from answer_marker.models.evaluation import AnswerEvaluation

def test_answer_evaluation_percentage():
    eval = AnswerEvaluation(
        question_id="Q1",
        concepts_identified=[],
        overall_quality="good",
        confidence_score=0.8,
        marks_awarded=7.5,
        max_marks=10.0
    )
    
    assert eval.percentage == 75.0

def test_invalid_confidence_score():
    with pytest.raises(ValidationError):
        AnswerEvaluation(
            question_id="Q1",
            concepts_identified=[],
            overall_quality="good",
            confidence_score=1.5,  # Invalid: > 1.0
            marks_awarded=5.0,
            max_marks=10.0
        )
```

This comprehensive model structure ensures:
- **Type Safety**: Strong typing with Pydantic
- **Validation**: Automatic validation of all fields
- **Documentation**: Self-documenting with descriptions
- **Serialization**: Easy JSON/dict conversion
- **Maintainability**: Clear structure and organization
