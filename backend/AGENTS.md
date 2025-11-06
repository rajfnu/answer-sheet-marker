# Agent Implementation Guide - Answer Sheet Marker

## Multi-Agent Architecture Deep Dive

This guide provides detailed implementation specifications for each agent in the system.

## Base Agent Design

### Abstract Agent Class

```python
# src/answer_marker/core/agent_base.py

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel
from anthropic import Anthropic
from loguru import logger

class AgentConfig(BaseModel):
    """Configuration for each agent"""
    name: str
    model: str = "claude-sonnet-4-5-20250929"
    max_tokens: int = 8192
    temperature: float = 0.0
    system_prompt: str
    tools: Optional[list] = None

class AgentMessage(BaseModel):
    """Standard message format between agents"""
    sender: str
    receiver: str
    content: Dict[str, Any]
    message_type: str  # request, response, error, info
    priority: int = 1
    metadata: Dict[str, Any] = {}

class BaseAgent(ABC):
    """Base class for all agents"""
    
    def __init__(self, config: AgentConfig, client: Anthropic):
        self.config = config
        self.client = client
        self.message_history: list[AgentMessage] = []
        
    @abstractmethod
    async def process(self, message: AgentMessage) -> AgentMessage:
        """Process incoming message and return response"""
        pass
    
    async def _call_claude(
        self,
        user_message: str,
        system_prompt: Optional[str] = None,
        tools: Optional[list] = None
    ) -> str:
        """Common Claude API call with error handling"""
        try:
            response = self.client.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                system=system_prompt or self.config.system_prompt,
                messages=[{"role": "user", "content": user_message}],
                tools=tools or self.config.tools
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"{self.config.name} API call failed: {e}")
            raise
    
    def log_message(self, message: AgentMessage):
        """Log agent communication"""
        self.message_history.append(message)
        logger.info(f"[{self.config.name}] {message.message_type}: {message.sender} -> {message.receiver}")
```

## Agent 1: Orchestrator Agent

### Purpose
Coordinates all agents, manages workflow, and handles the overall marking process.

### Implementation

```python
# src/answer_marker/core/orchestrator.py

from typing import List
from answer_marker.core.agent_base import BaseAgent, AgentMessage
from answer_marker.models.marking_guide import MarkingGuide
from answer_marker.models.answer import AnswerSheet
from answer_marker.models.evaluation import EvaluationReport

class OrchestratorAgent(BaseAgent):
    """
    Main orchestrator that coordinates the marking workflow
    """
    
    def __init__(self, config, client, agents: Dict[str, BaseAgent]):
        super().__init__(config, client)
        self.agents = agents  # Dictionary of specialized agents
        self.workflow_state = {}
        
    async def mark_answer_sheet(
        self,
        marking_guide: MarkingGuide,
        answer_sheet: AnswerSheet
    ) -> EvaluationReport:
        """
        Main entry point for marking process
        
        Workflow:
        1. Question analysis (parallel for all questions)
        2. Answer evaluation (for each question)
        3. Scoring (aggregate all evaluations)
        4. Feedback generation
        5. QA review
        6. Report generation
        """
        logger.info(f"Starting marking process for {answer_sheet.student_id}")
        
        # Step 1: Analyze all questions in marking guide
        analyzed_questions = await self._analyze_questions(marking_guide)
        
        # Step 2: Evaluate each answer
        evaluations = []
        for question in marking_guide.questions:
            student_answer = answer_sheet.get_answer(question.id)
            evaluation = await self._evaluate_answer(
                question=analyzed_questions[question.id],
                student_answer=student_answer
            )
            evaluations.append(evaluation)
        
        # Step 3: Calculate scores
        scores = await self._calculate_scores(evaluations)
        
        # Step 4: Generate feedback
        feedback = await self._generate_feedback(evaluations)
        
        # Step 5: QA Review
        qa_result = await self._qa_review(evaluations, scores, feedback)
        
        # Step 6: Generate final report
        report = await self._generate_report(
            answer_sheet=answer_sheet,
            evaluations=evaluations,
            scores=scores,
            feedback=feedback,
            qa_result=qa_result
        )
        
        return report
    
    async def _analyze_questions(self, marking_guide: MarkingGuide) -> Dict:
        """Send questions to Question Analyzer Agent"""
        message = AgentMessage(
            sender="orchestrator",
            receiver="question_analyzer",
            content={"marking_guide": marking_guide.model_dump()},
            message_type="request"
        )
        
        response = await self.agents["question_analyzer"].process(message)
        return response.content["analyzed_questions"]
    
    async def _evaluate_answer(self, question, student_answer):
        """Send to Answer Evaluator Agent"""
        message = AgentMessage(
            sender="orchestrator",
            receiver="answer_evaluator",
            content={
                "question": question,
                "student_answer": student_answer
            },
            message_type="request"
        )
        
        response = await self.agents["answer_evaluator"].process(message)
        return response.content["evaluation"]
    
    async def _calculate_scores(self, evaluations):
        """Send to Scoring Agent"""
        message = AgentMessage(
            sender="orchestrator",
            receiver="scoring_agent",
            content={"evaluations": evaluations},
            message_type="request"
        )
        
        response = await self.agents["scoring_agent"].process(message)
        return response.content["scores"]
    
    async def _generate_feedback(self, evaluations):
        """Send to Feedback Generator Agent"""
        message = AgentMessage(
            sender="orchestrator",
            receiver="feedback_generator",
            content={"evaluations": evaluations},
            message_type="request"
        )
        
        response = await self.agents["feedback_generator"].process(message)
        return response.content["feedback"]
    
    async def _qa_review(self, evaluations, scores, feedback):
        """Send to QA Agent"""
        message = AgentMessage(
            sender="orchestrator",
            receiver="qa_agent",
            content={
                "evaluations": evaluations,
                "scores": scores,
                "feedback": feedback
            },
            message_type="request"
        )
        
        response = await self.agents["qa_agent"].process(message)
        return response.content["qa_result"]
```

## Agent 2: Question Analyzer Agent

### Purpose
Analyzes marking guide, extracts evaluation criteria, identifies question types, and creates structured rubrics.

### System Prompt

```xml
<role>
You are an expert examiner and educational assessment specialist. Your role is to analyze 
marking guides and extract clear, structured evaluation criteria.
</role>

<task>
Analyze the provided marking guide and create a structured evaluation rubric for each question.
</task>

<instructions>
1. Identify the question type (MCQ, short answer, essay, numerical, etc.)
2. Extract all key concepts, keywords, and evaluation points
3. Determine the marking scheme and point allocation
4. Identify mandatory requirements vs. optional points
5. Create a clear rubric for consistent evaluation
6. Note any specific instructions or edge cases
</instructions>

<output_requirements>
For each question, provide:
- Question ID and type
- Maximum marks available
- List of key concepts (with point values)
- Required keywords or phrases
- Evaluation criteria (what constitutes full marks, partial marks, zero marks)
- Common mistakes to watch for
- Rubric tiers (excellent, good, satisfactory, poor)
</output_requirements>
```

### Implementation

```python
# src/answer_marker/agents/question_analyzer.py

from answer_marker.core.agent_base import BaseAgent, AgentMessage
from answer_marker.models.question import AnalyzedQuestion, QuestionType, EvaluationRubric
from typing import List, Dict
import json

class QuestionAnalyzerAgent(BaseAgent):
    """
    Analyzes marking guides and creates evaluation rubrics
    """
    
    async def process(self, message: AgentMessage) -> AgentMessage:
        """Process question analysis request"""
        marking_guide = message.content["marking_guide"]
        
        analyzed_questions = {}
        for question in marking_guide["questions"]:
            analysis = await self._analyze_single_question(question)
            analyzed_questions[question["id"]] = analysis
        
        return AgentMessage(
            sender="question_analyzer",
            receiver=message.sender,
            content={"analyzed_questions": analyzed_questions},
            message_type="response"
        )
    
    async def _analyze_single_question(self, question: Dict) -> AnalyzedQuestion:
        """Analyze a single question using Claude"""
        
        # Define structured output tool
        analysis_tool = {
            "name": "submit_question_analysis",
            "description": "Submit the structured analysis of a question",
            "input_schema": {
                "type": "object",
                "properties": {
                    "question_type": {
                        "type": "string",
                        "enum": ["mcq", "short_answer", "essay", "numerical", "true_false"]
                    },
                    "max_marks": {"type": "number"},
                    "key_concepts": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "concept": {"type": "string"},
                                "points": {"type": "number"},
                                "mandatory": {"type": "boolean"}
                            }
                        }
                    },
                    "evaluation_criteria": {
                        "type": "object",
                        "properties": {
                            "excellent": {"type": "string"},
                            "good": {"type": "string"},
                            "satisfactory": {"type": "string"},
                            "poor": {"type": "string"}
                        }
                    },
                    "keywords": {"type": "array", "items": {"type": "string"}},
                    "common_mistakes": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["question_type", "max_marks", "key_concepts", "evaluation_criteria"]
            }
        }
        
        prompt = f"""
<question>
{question['question_text']}
</question>

<marking_guide>
{question.get('marking_scheme', '')}
</marking_guide>

<sample_answer>
{question.get('sample_answer', '')}
</sample_answer>

Analyze this question thoroughly and use the submit_question_analysis tool to provide 
a structured evaluation rubric.
"""
        
        response = self.client.messages.create(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            system=self.config.system_prompt,
            messages=[{"role": "user", "content": prompt}],
            tools=[analysis_tool],
            tool_choice={"type": "tool", "name": "submit_question_analysis"}
        )
        
        # Extract tool use result
        for block in response.content:
            if block.type == "tool_use":
                analysis_data = block.input
                return AnalyzedQuestion(**analysis_data)
```

## Agent 3: Answer Evaluator Agent

### Purpose
Compares student answers with marking rubrics and identifies correct concepts, errors, and gaps.

### System Prompt

```xml
<role>
You are a fair, consistent, and expert examiner. You evaluate student answers against 
marking rubrics with precision and objectivity.
</role>

<principles>
- Be fair and unbiased
- Look for what students know, not just what they don't know
- Award partial credit appropriately
- Identify both strengths and weaknesses
- Be consistent across all evaluations
- Recognize different ways of expressing correct concepts
</principles>

<task>
Evaluate student answers by comparing them with the provided marking rubric and 
identify all concepts present and missing.
</task>

<evaluation_process>
1. Read the question and marking rubric carefully
2. Read the student's answer thoroughly
3. Identify each key concept from the rubric
4. Check if the concept is present in the student's answer (with variations in wording)
5. Assess the accuracy and completeness of each identified concept
6. Note any misconceptions or errors
7. Determine partial credit eligibility
8. Provide a confidence score for your evaluation
</evaluation_process>
```

### Implementation

```python
# src/answer_marker/agents/answer_evaluator.py

from answer_marker.core.agent_base import BaseAgent, AgentMessage
from answer_marker.models.evaluation import ConceptEvaluation, AnswerEvaluation

class AnswerEvaluatorAgent(BaseAgent):
    """
    Evaluates student answers against marking rubrics
    """
    
    async def process(self, message: AgentMessage) -> AgentMessage:
        """Process answer evaluation request"""
        question = message.content["question"]
        student_answer = message.content["student_answer"]
        
        evaluation = await self._evaluate_answer(question, student_answer)
        
        return AgentMessage(
            sender="answer_evaluator",
            receiver=message.sender,
            content={"evaluation": evaluation.model_dump()},
            message_type="response"
        )
    
    async def _evaluate_answer(self, question, student_answer) -> AnswerEvaluation:
        """Perform detailed evaluation"""
        
        evaluation_tool = {
            "name": "submit_evaluation",
            "description": "Submit the evaluation of a student answer",
            "input_schema": {
                "type": "object",
                "properties": {
                    "concepts_identified": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "concept": {"type": "string"},
                                "present": {"type": "boolean"},
                                "accuracy": {
                                    "type": "string",
                                    "enum": ["fully_correct", "partially_correct", "incorrect", "not_present"]
                                },
                                "evidence": {"type": "string"},
                                "points_earned": {"type": "number"}
                            }
                        }
                    },
                    "overall_quality": {
                        "type": "string",
                        "enum": ["excellent", "good", "satisfactory", "poor", "inadequate"]
                    },
                    "strengths": {"type": "array", "items": {"type": "string"}},
                    "weaknesses": {"type": "array", "items": {"type": "string"}},
                    "misconceptions": {"type": "array", "items": {"type": "string"}},
                    "confidence_score": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 1
                    },
                    "requires_human_review": {"type": "boolean"},
                    "review_reason": {"type": "string"}
                },
                "required": ["concepts_identified", "overall_quality", "confidence_score"]
            }
        }
        
        prompt = f"""
<question>
{question['question_text']}
</question>

<marking_rubric>
Question Type: {question['question_type']}
Maximum Marks: {question['max_marks']}

Key Concepts to Look For:
{self._format_key_concepts(question['key_concepts'])}

Evaluation Criteria:
- Excellent: {question['evaluation_criteria']['excellent']}
- Good: {question['evaluation_criteria']['good']}
- Satisfactory: {question['evaluation_criteria']['satisfactory']}
- Poor: {question['evaluation_criteria']['poor']}

Keywords: {', '.join(question.get('keywords', []))}
</marking_rubric>

<student_answer>
{student_answer}
</student_answer>

<instructions>
Evaluate this answer carefully:
1. Check for each key concept in the rubric
2. Assess accuracy of concepts present
3. Identify strengths and weaknesses
4. Note any misconceptions
5. Determine your confidence in this evaluation
6. Flag for human review if confidence is low or answer is ambiguous

Use the submit_evaluation tool to provide your structured evaluation.
</instructions>
"""
        
        response = self.client.messages.create(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            system=self.config.system_prompt,
            messages=[{"role": "user", "content": prompt}],
            tools=[evaluation_tool],
            tool_choice={"type": "tool", "name": "submit_evaluation"}
        )
        
        # Extract and return evaluation
        for block in response.content:
            if block.type == "tool_use":
                return AnswerEvaluation(**block.input, question_id=question['id'])
    
    def _format_key_concepts(self, concepts: List[Dict]) -> str:
        """Format key concepts for prompt"""
        formatted = []
        for i, concept in enumerate(concepts, 1):
            mandatory = "MANDATORY" if concept['mandatory'] else "Optional"
            formatted.append(
                f"{i}. {concept['concept']} - {concept['points']} marks [{mandatory}]"
            )
        return "\n".join(formatted)
```

## Agent 4: Scoring Agent

### Purpose
Aggregates evaluations and calculates final marks based on rubrics and partial credit rules.

### Implementation

```python
# src/answer_marker/agents/scoring_agent.py

from answer_marker.core.agent_base import BaseAgent, AgentMessage
from answer_marker.models.evaluation import ScoringResult
from typing import List

class ScoringAgent(BaseAgent):
    """
    Calculates final scores from evaluations
    """
    
    async def process(self, message: AgentMessage) -> AgentMessage:
        """Process scoring request"""
        evaluations = message.content["evaluations"]
        
        scores = await self._calculate_scores(evaluations)
        
        return AgentMessage(
            sender="scoring_agent",
            receiver=message.sender,
            content={"scores": scores.model_dump()},
            message_type="response"
        )
    
    async def _calculate_scores(self, evaluations: List[Dict]) -> ScoringResult:
        """Calculate scores with validation"""
        
        total_marks = 0
        max_marks = 0
        question_scores = []
        
        for eval_data in evaluations:
            question_score = sum(
                concept['points_earned'] 
                for concept in eval_data['concepts_identified']
            )
            
            question_max = eval_data.get('max_marks', 0)
            
            # Ensure score doesn't exceed maximum
            question_score = min(question_score, question_max)
            
            total_marks += question_score
            max_marks += question_max
            
            question_scores.append({
                "question_id": eval_data['question_id'],
                "marks_awarded": question_score,
                "max_marks": question_max,
                "percentage": (question_score / question_max * 100) if question_max > 0 else 0
            })
        
        percentage = (total_marks / max_marks * 100) if max_marks > 0 else 0
        
        return ScoringResult(
            total_marks=total_marks,
            max_marks=max_marks,
            percentage=percentage,
            question_scores=question_scores,
            grade=self._calculate_grade(percentage)
        )
    
    def _calculate_grade(self, percentage: float) -> str:
        """Convert percentage to grade"""
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
        else:
            return "F"
```

## Agent 5: Feedback Generator Agent

### Purpose
Creates constructive, personalized feedback for students.

### System Prompt

```xml
<role>
You are an experienced, encouraging teacher who provides constructive feedback 
to help students learn and improve.
</role>

<principles>
- Be constructive and encouraging
- Highlight strengths before weaknesses
- Provide specific, actionable suggestions
- Maintain a positive tone
- Focus on learning and improvement
- Be specific about what was good and what needs work
</principles>

<feedback_structure>
1. Overall performance summary
2. Strengths (what the student did well)
3. Areas for improvement (specific gaps)
4. Actionable suggestions (how to improve)
5. Encouragement (motivational closing)
</feedback_structure>
```

### Implementation

```python
# src/answer_marker/agents/feedback_generator.py

from answer_marker.core.agent_base import BaseAgent, AgentMessage
from answer_marker.models.evaluation import FeedbackReport

class FeedbackGeneratorAgent(BaseAgent):
    """
    Generates constructive feedback for students
    """
    
    async def process(self, message: AgentMessage) -> AgentMessage:
        """Process feedback generation request"""
        evaluations = message.content["evaluations"]
        
        feedback = await self._generate_feedback(evaluations)
        
        return AgentMessage(
            sender="feedback_generator",
            receiver=message.sender,
            content={"feedback": feedback.model_dump()},
            message_type="response"
        )
    
    async def _generate_feedback(self, evaluations: List[Dict]) -> FeedbackReport:
        """Generate comprehensive feedback"""
        
        question_feedback = []
        
        for evaluation in evaluations:
            prompt = f"""
<evaluation_summary>
Question Type: {evaluation.get('question_type', 'unknown')}
Overall Quality: {evaluation['overall_quality']}
Marks: {sum(c['points_earned'] for c in evaluation['concepts_identified'])} / {evaluation.get('max_marks', 0)}

Strengths Identified:
{self._format_list(evaluation.get('strengths', []))}

Weaknesses Identified:
{self._format_list(evaluation.get('weaknesses', []))}

Misconceptions:
{self._format_list(evaluation.get('misconceptions', []))}
</evaluation_summary>

Generate constructive, encouraging feedback for this question following these guidelines:
1. Start with positive aspects (strengths)
2. Address areas for improvement specifically
3. Provide actionable suggestions
4. Maintain an encouraging tone
5. Keep it concise (3-5 sentences)

Return only the feedback text, no additional formatting.
"""
            
            feedback_text = await self._call_claude(prompt)
            
            question_feedback.append({
                "question_id": evaluation['question_id'],
                "feedback": feedback_text,
                "strengths": evaluation.get('strengths', []),
                "improvement_areas": evaluation.get('weaknesses', [])
            })
        
        # Generate overall summary feedback
        overall_feedback = await self._generate_overall_feedback(evaluations)
        
        return FeedbackReport(
            overall_feedback=overall_feedback,
            question_feedback=question_feedback
        )
    
    def _format_list(self, items: List[str]) -> str:
        """Format list for prompt"""
        if not items:
            return "None"
        return "\n".join(f"- {item}" for item in items)
```

## Agent 6: QA Agent

### Purpose
Reviews evaluations for consistency, fairness, and flags items requiring human review.

### Implementation

```python
# src/answer_marker/agents/qa_agent.py

from answer_marker.core.agent_base import BaseAgent, AgentMessage
from answer_marker.models.evaluation import QAResult

class QAAgent(BaseAgent):
    """
    Quality assurance - reviews marking consistency and flags issues
    """
    
    async def process(self, message: AgentMessage) -> AgentMessage:
        """Process QA review request"""
        evaluations = message.content["evaluations"]
        scores = message.content["scores"]
        feedback = message.content["feedback"]
        
        qa_result = await self._perform_qa_check(evaluations, scores, feedback)
        
        return AgentMessage(
            sender="qa_agent",
            receiver=message.sender,
            content={"qa_result": qa_result.model_dump()},
            message_type="response"
        )
    
    async def _perform_qa_check(self, evaluations, scores, feedback) -> QAResult:
        """Perform quality assurance checks"""
        
        issues = []
        flags_for_review = []
        
        # Check 1: Low confidence evaluations
        for eval_data in evaluations:
            if eval_data['confidence_score'] < 0.6:
                flags_for_review.append({
                    "question_id": eval_data['question_id'],
                    "reason": "Low confidence score",
                    "confidence": eval_data['confidence_score']
                })
        
        # Check 2: Inconsistent scoring
        for eval_data in evaluations:
            total_concept_points = sum(
                c['points_earned'] for c in eval_data['concepts_identified']
            )
            expected_max = eval_data.get('max_marks', 0)
            
            if total_concept_points > expected_max:
                issues.append({
                    "question_id": eval_data['question_id'],
                    "issue": "Score exceeds maximum",
                    "details": f"Awarded {total_concept_points} but max is {expected_max}"
                })
        
        # Check 3: Missing mandatory concepts but high scores
        for eval_data in evaluations:
            mandatory_concepts = [
                c for c in eval_data['concepts_identified'] 
                if c.get('mandatory', False)
            ]
            missing_mandatory = [
                c for c in mandatory_concepts 
                if c.get('accuracy') == 'not_present'
            ]
            
            if missing_mandatory and eval_data.get('overall_quality') in ['excellent', 'good']:
                flags_for_review.append({
                    "question_id": eval_data['question_id'],
                    "reason": "High score despite missing mandatory concepts",
                    "missing_concepts": [c['concept'] for c in missing_mandatory]
                })
        
        # Determine overall QA status
        requires_review = len(flags_for_review) > 0
        has_issues = len(issues) > 0
        
        return QAResult(
            passed=not has_issues,
            requires_human_review=requires_review,
            flags=flags_for_review,
            issues=issues,
            confidence_level="high" if not requires_review else "medium"
        )
```

## Agent Communication Flow Example

```python
# Example flow for marking one answer sheet

# 1. Orchestrator receives request
orchestrator.mark_answer_sheet(marking_guide, answer_sheet)

# 2. Orchestrator -> Question Analyzer
message = AgentMessage(
    sender="orchestrator",
    receiver="question_analyzer",
    content={"marking_guide": marking_guide},
    message_type="request"
)
analyzed = await question_analyzer.process(message)

# 3. For each question: Orchestrator -> Answer Evaluator
for question in questions:
    message = AgentMessage(
        sender="orchestrator",
        receiver="answer_evaluator",
        content={"question": question, "student_answer": answer},
        message_type="request"
    )
    evaluation = await answer_evaluator.process(message)

# 4. Orchestrator -> Scoring Agent
message = AgentMessage(
    sender="orchestrator",
    receiver="scoring_agent",
    content={"evaluations": all_evaluations},
    message_type="request"
)
scores = await scoring_agent.process(message)

# 5. Orchestrator -> Feedback Generator
# 6. Orchestrator -> QA Agent
# 7. Orchestrator generates final report
```

## Best Practices for Agent Development

1. **Separation of Concerns**: Each agent has ONE clear responsibility
2. **Structured Communication**: Always use AgentMessage for inter-agent communication
3. **Error Handling**: Each agent handles its own errors and returns error messages
4. **Logging**: Comprehensive logging at each step
5. **Testing**: Unit test each agent independently with mock responses
6. **Versioning**: Version agent prompts and track changes
7. **Monitoring**: Track agent performance metrics
8. **Async Operations**: Use async/await for concurrent processing

## Testing Agents

```python
# tests/unit/test_question_analyzer.py

import pytest
from unittest.mock import Mock, AsyncMock
from answer_marker.agents.question_analyzer import QuestionAnalyzerAgent

@pytest.mark.asyncio
async def test_question_analyzer():
    # Mock Claude client
    mock_client = Mock()
    mock_client.messages.create = AsyncMock(return_value=mock_response)
    
    # Create agent
    config = AgentConfig(name="test_analyzer", system_prompt="test")
    agent = QuestionAnalyzerAgent(config, mock_client)
    
    # Test
    message = AgentMessage(
        sender="test",
        receiver="question_analyzer",
        content={"marking_guide": test_marking_guide},
        message_type="request"
    )
    
    response = await agent.process(message)
    
    assert response.message_type == "response"
    assert "analyzed_questions" in response.content
```

This multi-agent architecture ensures:
- **Modularity**: Easy to update individual agents
- **Scalability**: Can process multiple submissions in parallel
- **Maintainability**: Clear separation of concerns
- **Testability**: Each agent can be tested independently
- **Extensibility**: Easy to add new agent types
