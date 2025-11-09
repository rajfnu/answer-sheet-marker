# Quick Test Feature - Design Document

## Overview

A "Quick Test" tab that allows users to instantly test the marking system with a single question and answer, without uploading PDFs. This is perfect for:
- **New users** understanding how the system works
- **Quick testing** of marking logic
- **Demo/sales** purposes
- **Development** and debugging
- **Saving tokens** - test before running on full assessments

---

## UI/UX Design

### Tab Name Options
Pick one:
- ✅ **"Quick Test"** (recommended - clear and concise)
- "Try Demo"
- "Test Marking"
- "Playground"
- "Live Test"

### Layout (Single Page, Split View)

```
┌─────────────────────────────────────────────────────────────┐
│  Quick Test - Try Marking Instantly! ℹ️                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────────┐  ┌────────────────────────────┐   │
│  │   Question Input    │  │   Marking Result           │   │
│  │     (Left 50%)      │  │   (Right 50%)              │   │
│  └─────────────────────┘  └────────────────────────────┘   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Left Panel: Question Input

### 1. Question Type Selector
```tsx
<Select label="Question Type">
  <Option value="short_answer">Short Answer ⭐ Recommended</Option>
  <Option value="essay">Essay/Long Answer</Option>
  <Option value="mcq">Multiple Choice (MCQ)</Option>
  <Option value="true_false">True/False</Option>
  <Option value="numerical">Numerical Answer</Option>
</Select>
```

### 2. Question Text
```tsx
<Textarea
  label="Question"
  placeholder="E.g., What is photosynthesis?"
  rows={3}
  required
/>
```

### 3. Maximum Marks
```tsx
<Input
  label="Maximum Marks"
  type="number"
  defaultValue={5}
  min={1}
  max={100}
/>
```

### 4. Marking Guide / Rubric
**With Smart Suggestions!**

```tsx
<div>
  <Label>
    Marking Guide
    <HelpIcon tooltip="Define what the ideal answer should contain" />
  </Label>

  {/* Quick Templates */}
  <ButtonGroup size="sm" variant="outline">
    <Button onClick={() => loadTemplate('key_concepts')}>
      💡 Key Concepts Template
    </Button>
    <Button onClick={() => loadTemplate('detailed')}>
      📋 Detailed Rubric
    </Button>
    <Button onClick={() => generateWithAI()}>
      🤖 Generate with AI
    </Button>
  </ButtonGroup>

  <Textarea
    value={markingGuide}
    onChange={setMarkingGuide}
    placeholder={getPlaceholderForQuestionType()}
    rows={8}
    className="mt-2"
  />

  {/* Character count */}
  <Text size="sm" color="muted">
    {markingGuide.length} characters
  </Text>
</div>
```

#### Smart Suggestions Based on Question Type:

**For Short Answer:**
```
Key Concepts (1 mark each):
1. [Concept 1]: Definition or explanation
2. [Concept 2]: Example or application
3. [Concept 3]: Related fact

Evaluation Criteria:
- Excellent (5/5): All concepts with examples
- Good (4/5): All concepts, missing examples
- Satisfactory (3/5): 2-3 concepts correct
- Poor (1-2/5): Only 1 concept or incomplete
```

**For Essay:**
```
Structure & Content (10 marks total):

Introduction (2 marks):
- Clear thesis statement
- Context provided

Body (6 marks):
- Argument 1 with evidence (2 marks)
- Argument 2 with evidence (2 marks)
- Argument 3 with evidence (2 marks)

Conclusion (2 marks):
- Summary of key points
- Final insight

Bonus: +1 for exceptional critical thinking
```

**For MCQ:**
```
Correct Answer: [B]

Explanation:
- Option A is incorrect because [reason]
- Option B is CORRECT because [reason]
- Option C is incorrect because [reason]
- Option D is incorrect because [reason]

Common Misconception: Students often choose A thinking [misconception]
```

### 5. Student Answer Input
```tsx
<Textarea
  label="Student Answer (to be marked)"
  placeholder="Enter the student's answer here..."
  rows={6}
  required
/>

{/* Helper text */}
<Text size="sm" color="muted">
  💡 Tip: Try different answers (correct, partially correct, incorrect)
  to see how the AI marks them!
</Text>
```

### 6. Optional: Student ID
```tsx
<Input
  label="Student ID (optional)"
  placeholder="e.g., 12345"
  defaultValue="TEST"
/>
```

### 7. Advanced Options (Collapsible)
```tsx
<Collapsible title="Advanced Options">
  <Select label="Confidence Threshold">
    <Option value="0.7">Normal (0.7)</Option>
    <Option value="0.8">High (0.8)</Option>
    <Option value="0.6">Low (0.6)</Option>
  </Select>

  <Checkbox>
    Show detailed concept breakdown
  </Checkbox>

  <Checkbox checked>
    Include AI reasoning
  </Checkbox>
</Collapsible>
```

### 8. Action Button
```tsx
<Button
  size="lg"
  fullWidth
  onClick={handleMarkAnswer}
  loading={isMarking}
  disabled={!questionText || !studentAnswer}
>
  {isMarking ? (
    <>
      <Spinner /> Marking...
      <Text size="sm">(~3-5 seconds)</Text>
    </>
  ) : (
    <>🎯 Mark Answer Now</>
  )}
</Button>

{/* Estimate */}
<Text size="sm" color="muted" className="text-center mt-2">
  Estimated tokens: ~500 | Cost: ~$0.001 (FREE with Gemini!)
</Text>
```

---

## Right Panel: Marking Result

### Loading State
```tsx
{isMarking && (
  <Card className="h-full flex items-center justify-center">
    <Spinner size="lg" />
    <Text>Analyzing answer...</Text>
    <Progress value={progress} className="w-64 mt-4" />
  </Card>
)}
```

### Result Display
```tsx
{result && (
  <Card className="h-full overflow-auto">
    {/* Score Banner */}
    <div className="bg-gradient-to-r from-blue-500 to-purple-500 text-white p-6 rounded-t-lg">
      <Text size="sm" className="opacity-80">SCORE</Text>
      <div className="flex items-baseline gap-2">
        <Text size="4xl" weight="bold">{result.marks_awarded}</Text>
        <Text size="xl">/ {result.max_marks}</Text>
      </div>
      <Progress value={result.percentage} className="mt-2" />
      <Text size="sm">{result.percentage}% | Grade: {result.grade}</Text>
    </div>

    {/* Overall Quality */}
    <div className="p-4 border-b">
      <Badge variant={getQualityBadgeVariant(result.overall_quality)}>
        {result.overall_quality}
      </Badge>
      <Text className="mt-2">
        Confidence: {(result.confidence_score * 100).toFixed(0)}%
      </Text>
    </div>

    {/* Concept Breakdown */}
    <div className="p-4">
      <Heading size="md" className="mb-3">
        📊 Concept Breakdown
      </Heading>

      {result.concepts_identified.map((concept, i) => (
        <Card key={i} className="mb-3 p-3">
          <div className="flex justify-between items-start">
            <div className="flex-1">
              <div className="flex items-center gap-2">
                {concept.present ? (
                  <CheckIcon className="text-green-500" />
                ) : (
                  <XIcon className="text-red-500" />
                )}
                <Text weight="semibold">{concept.concept}</Text>
              </div>

              <Badge
                variant={getAccuracyBadgeVariant(concept.accuracy)}
                size="sm"
                className="mt-1"
              >
                {concept.accuracy.replace('_', ' ')}
              </Badge>

              {concept.evidence && (
                <blockquote className="mt-2 pl-3 border-l-2 border-gray-300 text-sm italic text-gray-600">
                  "{concept.evidence}"
                </blockquote>
              )}

              {concept.feedback && (
                <Text size="sm" className="mt-2 text-gray-700">
                  💬 {concept.feedback}
                </Text>
              )}
            </div>

            <div className="text-right ml-4">
              <Text weight="bold" color={concept.points_earned > 0 ? 'success' : 'muted'}>
                {concept.points_earned} / {concept.points_possible}
              </Text>
            </div>
          </div>
        </Card>
      ))}
    </div>

    {/* Strengths */}
    {result.strengths?.length > 0 && (
      <div className="p-4 bg-green-50 border-t">
        <Heading size="sm" className="text-green-800 mb-2">
          ✅ Strengths
        </Heading>
        <ul className="list-disc list-inside space-y-1">
          {result.strengths.map((strength, i) => (
            <li key={i} className="text-green-700 text-sm">{strength}</li>
          ))}
        </ul>
      </div>
    )}

    {/* Weaknesses */}
    {result.weaknesses?.length > 0 && (
      <div className="p-4 bg-orange-50 border-t">
        <Heading size="sm" className="text-orange-800 mb-2">
          ⚠️ Areas for Improvement
        </Heading>
        <ul className="list-disc list-inside space-y-1">
          {result.weaknesses.map((weakness, i) => (
            <li key={i} className="text-orange-700 text-sm">{weakness}</li>
          ))}
        </ul>
      </div>
    )}

    {/* Misconceptions */}
    {result.misconceptions?.length > 0 && (
      <div className="p-4 bg-red-50 border-t">
        <Heading size="sm" className="text-red-800 mb-2">
          ❌ Misconceptions
        </Heading>
        <ul className="list-disc list-inside space-y-1">
          {result.misconceptions.map((misc, i) => (
            <li key={i} className="text-red-700 text-sm">{misc}</li>
          ))}
        </ul>
      </div>
    )}

    {/* Action Buttons */}
    <div className="p-4 border-t flex gap-2">
      <Button variant="outline" onClick={handleReset}>
        🔄 Test Another
      </Button>
      <Button variant="outline" onClick={handleCopyResults}>
        📋 Copy Results
      </Button>
      <Button variant="outline" onClick={handleExportJSON}>
        💾 Export JSON
      </Button>
    </div>
  </Card>
)}
```

---

## Backend API Endpoint

### New Route: POST `/api/v1/quick-test/mark`

```python
# backend/src/answer_marker/api/routes/quick_test.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Literal

router = APIRouter(prefix="/api/v1/quick-test", tags=["quick-test"])


class QuickTestRequest(BaseModel):
    """Request model for quick test marking."""

    question_text: str = Field(..., min_length=10, max_length=5000)
    question_type: Literal["short_answer", "essay", "mcq", "true_false", "numerical"] = "short_answer"
    max_marks: float = Field(..., gt=0, le=100)
    marking_guide: str = Field(..., min_length=20, max_length=10000)
    student_answer: str = Field(..., min_length=1, max_length=10000)
    student_id: Optional[str] = Field(default="TEST", max_length=50)

    # Optional MCQ-specific fields
    options: Optional[List[dict]] = None
    correct_answer: Optional[str] = None

    # Advanced options
    confidence_threshold: float = Field(default=0.7, ge=0, le=1)
    show_detailed_breakdown: bool = True


@router.post("/mark")
async def mark_quick_test(request: QuickTestRequest):
    """Mark a single question instantly without uploading files.

    This endpoint:
    1. Creates a temporary AnalyzedQuestion from the marking guide
    2. Evaluates the student answer
    3. Returns detailed results

    Perfect for testing, demos, and learning how the system works!
    """

    # Import marking service
    from answer_marker.api.services.marking_service import marking_service
    from answer_marker.models.marking_guide import AnalyzedQuestion
    from answer_marker.models.answer import Answer

    # Initialize service
    await marking_service.initialize()

    # Parse marking guide into key concepts
    # This is simplified - you could use LLM to extract concepts from freeform text
    key_concepts = _parse_marking_guide(request.marking_guide, request.max_marks)

    # Create temporary AnalyzedQuestion
    question = AnalyzedQuestion(
        id="Q1",
        question_number="1",
        question_text=request.question_text,
        question_type=request.question_type,
        max_marks=request.max_marks,
        key_concepts=key_concepts,
        evaluation_criteria=_generate_evaluation_criteria(request.marking_guide),
        keywords=_extract_keywords(request.question_text, request.marking_guide),
        options=request.options or [],
        correct_answer=request.correct_answer,
    )

    # Create answer object
    student_answer = Answer(
        question_id="Q1",
        answer_text=request.student_answer,
        is_blank=len(request.student_answer.strip()) == 0,
    )

    # Evaluate using answer_evaluator agent
    from answer_marker.core.agent_base import AgentMessage

    eval_message = AgentMessage(
        sender="quick_test",
        receiver="answer_evaluator",
        content={
            "question": question.model_dump(),
            "student_answer": student_answer.answer_text,
        },
        message_type="request",
    )

    try:
        eval_response = await marking_service.agents["answer_evaluator"].process(eval_message)

        if eval_response.message_type == "error":
            raise HTTPException(status_code=500, detail=eval_response.content.get("error"))

        evaluation = eval_response.content.get("evaluation")

        # Add grade based on percentage
        percentage = (evaluation["marks_awarded"] / evaluation["max_marks"]) * 100
        grade = _calculate_grade(percentage)

        return {
            "success": True,
            "result": {
                **evaluation,
                "percentage": percentage,
                "grade": grade,
            },
            "metadata": {
                "student_id": request.student_id,
                "question_type": request.question_type,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        }

    except Exception as e:
        logger.error(f"Quick test marking failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Marking failed: {str(e)}"
        )


def _parse_marking_guide(guide_text: str, max_marks: float) -> List[dict]:
    """Parse marking guide text into key concepts.

    Simple heuristic parsing. Could be enhanced with LLM.
    """
    concepts = []
    lines = guide_text.strip().split('\n')

    # Try to detect numbered/bulleted concepts
    concept_markers = ['1.', '2.', '3.', '-', '•', '*']

    for line in lines:
        line = line.strip()
        if any(line.startswith(marker) for marker in concept_markers):
            # Remove marker
            for marker in concept_markers:
                line = line.replace(marker, '', 1).strip()

            if line and len(line) > 5:  # Minimum concept length
                concepts.append({
                    "concept": line,
                    "marks": max_marks / max(3, len([l for l in lines if any(l.strip().startswith(m) for m in concept_markers)])),
                    "required": True,
                })

    # If no concepts found, create default
    if not concepts:
        concepts = [{
            "concept": "Complete and accurate answer",
            "marks": max_marks,
            "required": True,
        }]

    return concepts


def _generate_evaluation_criteria(guide_text: str) -> dict:
    """Generate evaluation criteria from marking guide."""
    return {
        "excellent": "Comprehensive answer covering all key concepts with examples",
        "good": "Most key concepts covered with good understanding",
        "satisfactory": "Basic concepts present but incomplete or unclear",
        "poor": "Minimal understanding, major concepts missing",
    }


def _extract_keywords(question_text: str, guide_text: str) -> List[str]:
    """Extract important keywords from question and guide."""
    import re

    # Simple keyword extraction (could use NLP)
    text = f"{question_text} {guide_text}".lower()
    words = re.findall(r'\b[a-z]{4,}\b', text)  # Words 4+ chars

    # Count frequency
    from collections import Counter
    word_freq = Counter(words)

    # Return top 10 most common
    return [word for word, _ in word_freq.most_common(10)]


def _calculate_grade(percentage: float) -> str:
    """Calculate letter grade from percentage."""
    if percentage >= 90:
        return "A+"
    elif percentage >= 85:
        return "A"
    elif percentage >= 80:
        return "A-"
    elif percentage >= 75:
        return "B+"
    elif percentage >= 70:
        return "B"
    elif percentage >= 65:
        return "B-"
    elif percentage >= 60:
        return "C+"
    elif percentage >= 55:
        return "C"
    elif percentage >= 50:
        return "C-"
    elif percentage >= 40:
        return "D"
    else:
        return "F"
```

---

## Frontend Implementation

### File Structure
```
frontend/src/
├── pages/
│   └── QuickTest.tsx          # Main page component
├── components/
│   └── quick-test/
│       ├── QuestionInput.tsx   # Left panel
│       ├── MarkingResult.tsx   # Right panel
│       ├── TemplateSelector.tsx
│       └── ConceptBreakdown.tsx
└── api/
    └── quickTest.ts            # API client
```

### API Client
```typescript
// frontend/src/api/quickTest.ts

export interface QuickTestRequest {
  question_text: string;
  question_type: 'short_answer' | 'essay' | 'mcq' | 'true_false' | 'numerical';
  max_marks: number;
  marking_guide: string;
  student_answer: string;
  student_id?: string;
  options?: Array<{label: string; text: string; is_correct?: boolean}>;
  correct_answer?: string;
  confidence_threshold?: number;
  show_detailed_breakdown?: boolean;
}

export interface QuickTestResult {
  success: boolean;
  result: {
    question_id: string;
    marks_awarded: number;
    max_marks: number;
    percentage: number;
    grade: string;
    overall_quality: string;
    confidence_score: number;
    concepts_identified: Array<{
      concept: string;
      present: boolean;
      accuracy: string;
      evidence: string;
      points_earned: number;
      points_possible: number;
      feedback?: string;
    }>;
    strengths: string[];
    weaknesses: string[];
    misconceptions: string[];
  };
  metadata: {
    student_id: string;
    question_type: string;
    timestamp: string;
  };
}

export async function markQuickTest(request: QuickTestRequest): Promise<QuickTestResult> {
  const response = await fetch(`${API_BASE_URL}/api/v1/quick-test/mark`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`Marking failed: ${response.statusText}`);
  }

  return response.json();
}
```

---

## Pre-filled Examples

Provide 3-4 example questions users can load instantly:

### Example 1: Biology - Photosynthesis
```typescript
{
  question_text: "What is photosynthesis and why is it important?",
  question_type: "short_answer",
  max_marks: 5,
  marking_guide: `Key Concepts (1.5 marks each):
1. Definition: Process by which plants convert light energy to chemical energy
2. Chemical equation: 6CO2 + 6H2O + light → C6H12O6 + 6O2
3. Importance: Produces oxygen and food for living organisms

Bonus (0.5): Mention of chlorophyll or chloroplasts`,

  // Good answer
  student_answer: "Photosynthesis is the process where plants use sunlight to convert carbon dioxide and water into glucose and oxygen. It's important because it provides oxygen for animals to breathe and produces food that supports the food chain."
}
```

### Example 2: Math - Quadratic Formula
```typescript
{
  question_text: "Solve the equation: x² - 5x + 6 = 0",
  question_type: "numerical",
  max_marks: 4,
  marking_guide: `Solution Steps (1 mark each):
1. Identify a=1, b=-5, c=6
2. Apply quadratic formula or factoring
3. Show work: (x-2)(x-3) = 0
4. Final answer: x = 2 or x = 3`,

  student_answer: "(x-2)(x-3) = 0, so x = 2 or x = 3"
}
```

### Example 3: History - MCQ
```typescript
{
  question_text: "When did World War II end?",
  question_type: "mcq",
  max_marks: 1,
  options: [
    {label: "A", text: "1943", is_correct: false},
    {label: "B", text: "1945", is_correct: true},
    {label: "C", text: "1947", is_correct: false},
    {label: "D", text: "1950", is_correct: false},
  ],
  correct_answer: "B",
  marking_guide: `Correct Answer: B (1945)

Explanation: World War II ended in 1945 with:
- Germany surrendering in May 1945
- Japan surrendering in August 1945 after atomic bombs

Common mistakes:
- A (1943): This is when the tide turned, not the end
- C (1947): This is after the war
- D (1950): This is the Korean War start`,

  student_answer: "B"
}
```

---

## Benefits Summary

### For Users:
- ✅ **Instant feedback** - see results in 3-5 seconds
- ✅ **No PDF uploads** - just type and test
- ✅ **Learn the system** - understand how marking works
- ✅ **Save tokens** - test concepts before running full assessments
- ✅ **Iterate quickly** - try different answers

### For Development:
- ✅ **Easy debugging** - test marking logic quickly
- ✅ **Demo tool** - showcase to stakeholders
- ✅ **User onboarding** - helps new users understand the system

### For Sales/Marketing:
- ✅ **Live demos** - show potential customers immediately
- ✅ **No setup required** - works instantly
- ✅ **Impressive** - real-time AI marking

---

## Implementation Checklist

### Backend (2-3 hours)
- [ ] Create `quick_test.py` route
- [ ] Implement `_parse_marking_guide()` helper
- [ ] Add validation for input
- [ ] Test with various question types

### Frontend (4-5 hours)
- [ ] Create `QuickTest.tsx` page
- [ ] Build `QuestionInput` component
- [ ] Build `MarkingResult` component
- [ ] Add template system
- [ ] Style with TailwindCSS
- [ ] Add loading states
- [ ] Add error handling

### Testing (1-2 hours)
- [ ] Test with all question types
- [ ] Test edge cases (empty answers, very long answers)
- [ ] Test with Gemini 2.0 Flash
- [ ] Mobile responsiveness

### Documentation (30 mins)
- [ ] Add user guide
- [ ] Add tooltips/help text
- [ ] Record demo video

---

## Future Enhancements

1. **AI-Generated Marking Guides**
   - User enters question, AI generates suggested rubric
   - Uses Gemini to analyze question and create marking guide

2. **Answer Variations**
   - Show multiple example answers (excellent, good, poor)
   - Let user compare how each is marked

3. **Batch Testing**
   - Test 5-10 student answers at once
   - See consistency of marking

4. **Export to Full Assessment**
   - "Add to Assessment" button
   - Saves tested question to a new/existing assessment

5. **Community Templates**
   - Share marking guides with other users
   - Browse example questions by subject

---

## Mockup URLs

Once implemented, the flow would be:
1. User clicks "Quick Test" tab
2. Selects question type → loads template
3. Fills in question, guide, and answer
4. Clicks "Mark Answer Now"
5. Sees detailed results in 3-5 seconds
6. Can test variations or start a new test

This feature would significantly improve UX and help users understand the value of your product immediately!
