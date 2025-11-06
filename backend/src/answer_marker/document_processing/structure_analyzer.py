"""Structure analyzer for the Answer Sheet Marker system.

This module analyzes document structure and extracts structured information
using pattern matching and AI-powered analysis with Claude.
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from anthropic import Anthropic
import re
from loguru import logger
from answer_marker.config import settings


class DocumentSection(BaseModel):
    """Represents a section of the document."""

    section_type: str  # 'question', 'answer', 'marking_scheme', 'header', 'footer'
    content: str
    question_number: Optional[str] = None
    marks: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class StructureAnalyzer:
    """Analyze document structure and extract structured information.

    Uses both pattern-based extraction and AI-powered analysis to convert
    unstructured document text into structured data models.
    """

    def __init__(self, client: Anthropic):
        """Initialize structure analyzer.

        Args:
            client: Anthropic client for Claude API
        """
        self.client = client

    async def analyze_marking_guide(self, document_text: str) -> Dict[str, Any]:
        """Analyze marking guide structure.

        Args:
            document_text: Extracted text from marking guide

        Returns:
            Structured marking guide with questions, marking schemes,
            point allocations, and sample answers
        """
        logger.info("Analyzing marking guide structure")

        # First, try pattern-based extraction
        sections = self._extract_sections_pattern(document_text)
        logger.debug(f"Pattern extraction found {len(sections)} sections")

        # Then use Claude for intelligent structuring
        structured = await self._structure_with_claude(document_text, sections)

        logger.info(
            f"Structured marking guide: {len(structured.get('questions', []))} questions"
        )
        return structured

    def _extract_sections_pattern(self, text: str) -> List[DocumentSection]:
        """Extract sections using regex patterns.

        Common patterns:
        - Q1. or Question 1: or 1)
        - [5 marks] or (5 points)

        Args:
            text: Document text

        Returns:
            List of DocumentSection objects
        """
        sections = []

        # Pattern for questions with marks
        # Matches: Q1, Question 1, 1), etc. with optional marks
        question_pattern = r"(?:Q|Question)\.?\s*(\d+)\.?\s*(?:\[(\d+)\s*marks?\]|\((\d+)\s*(?:marks?|points?)\))?"

        lines = text.split("\n")
        current_section = None
        current_content = []

        for line in lines:
            match = re.search(question_pattern, line, re.IGNORECASE)

            if match:
                # Save previous section
                if current_section:
                    current_section.content = "\n".join(current_content)
                    sections.append(current_section)

                # Start new section
                question_num = match.group(1)
                marks = float(match.group(2) or match.group(3) or 0) or None

                current_section = DocumentSection(
                    section_type="question",
                    content="",
                    question_number=question_num,
                    marks=marks,
                )
                current_content = [line]
            else:
                current_content.append(line)

        # Add last section
        if current_section:
            current_section.content = "\n".join(current_content)
            sections.append(current_section)

        return sections

    async def _structure_with_claude(
        self, document_text: str, pattern_sections: List[DocumentSection]
    ) -> Dict[str, Any]:
        """Use Claude to intelligently structure the document.

        Args:
            document_text: Full document text
            pattern_sections: Pre-extracted sections from pattern matching

        Returns:
            Structured document data
        """
        structure_tool = {
            "name": "submit_structure",
            "description": "Submit the structured analysis of the marking guide",
            "input_schema": {
                "type": "object",
                "properties": {
                    "document_type": {
                        "type": "string",
                        "enum": ["marking_guide", "answer_sheet", "question_paper"],
                    },
                    "questions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "question_text": {"type": "string"},
                                "marks": {"type": "number"},
                                "marking_scheme": {"type": "string"},
                                "sample_answer": {"type": "string"},
                                "question_type": {
                                    "type": "string",
                                    "enum": [
                                        "mcq",
                                        "short_answer",
                                        "essay",
                                        "numerical",
                                        "true_false",
                                    ],
                                },
                            },
                            "required": ["id", "question_text", "marks"],
                        },
                    },
                    "total_marks": {"type": "number"},
                    "metadata": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "subject": {"type": "string"},
                            "date": {"type": "string"},
                        },
                    },
                },
                "required": ["document_type", "questions"],
            },
        }

        prompt = f"""<document>
{document_text}
</document>

<pattern_extraction_results>
{self._format_pattern_sections(pattern_sections)}
</pattern_extraction_results>

<task>
Analyze this marking guide document and extract structured information:

1. Identify all questions (number, text, marks)
2. Extract marking schemes for each question
3. Identify sample answers if present
4. Determine question types
5. Extract any metadata (title, subject, date)

Use the submit_structure tool to provide the structured output.
</task>

<guidelines>
- Be thorough - extract all questions completely
- Preserve the exact wording of questions and marking schemes
- Identify implicit marking schemes from sample answers
- Handle multi-part questions appropriately
- Extract all numerical marks accurately
</guidelines>"""

        logger.debug("Calling Claude for structure analysis")
        response = self.client.messages.create(
            model=settings.claude_model,
            max_tokens=settings.max_tokens * 2,  # Allow more tokens for structure
            system="You are an expert at analyzing educational documents and extracting structured information.",
            messages=[{"role": "user", "content": prompt}],
            tools=[structure_tool],
            tool_choice={"type": "tool", "name": "submit_structure"},
        )

        for block in response.content:
            if block.type == "tool_use":
                logger.debug("Received structured output from Claude")
                return block.input

        raise ValueError("Claude did not return structured output")

    def _format_pattern_sections(self, sections: List[DocumentSection]) -> str:
        """Format pattern-extracted sections for Claude.

        Args:
            sections: List of DocumentSection objects

        Returns:
            Formatted string for prompt
        """
        if not sections:
            return "No clear patterns detected"

        formatted = []
        for i, section in enumerate(sections, 1):
            formatted.append(
                f"""Section {i}:
Type: {section.section_type}
Question Number: {section.question_number or 'N/A'}
Marks: {section.marks or 'N/A'}
Content Preview: {section.content[:200]}..."""
            )
        return "\n".join(formatted)

    async def analyze_answer_sheet(
        self, document_text: str, question_ids: List[str]
    ) -> Dict[str, Any]:
        """Analyze answer sheet structure and map answers to questions.

        Args:
            document_text: Extracted text from answer sheet
            question_ids: Expected question IDs

        Returns:
            Structured answers mapped to questions
        """
        logger.info(f"Analyzing answer sheet for {len(question_ids)} questions")

        answer_tool = {
            "name": "submit_answers",
            "description": "Submit structured student answers",
            "input_schema": {
                "type": "object",
                "properties": {
                    "student_id": {"type": "string"},
                    "answers": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "question_id": {"type": "string"},
                                "answer_text": {"type": "string"},
                                "is_blank": {"type": "boolean"},
                            },
                            "required": ["question_id", "answer_text"],
                        },
                    },
                },
                "required": ["answers"],
            },
        }

        prompt = f"""<answer_sheet>
{document_text}
</answer_sheet>

<expected_questions>
{', '.join(question_ids)}
</expected_questions>

<task>
Extract student answers from this answer sheet:

1. Identify the student ID if present
2. Map each answer to its corresponding question ID
3. Extract the complete answer text for each question
4. Mark blank/unanswered questions

Use the submit_answers tool to provide structured output.
</task>

<guidelines>
- Extract complete answers - don't truncate
- Preserve formatting where relevant (equations, bullet points)
- If a question is unanswered, set is_blank to true
- Be careful with question numbering - match to expected question IDs
</guidelines>"""

        logger.debug("Calling Claude for answer extraction")
        response = self.client.messages.create(
            model=settings.claude_model,
            max_tokens=settings.max_tokens * 2,
            system="You are an expert at reading and extracting student answers from answer sheets.",
            messages=[{"role": "user", "content": prompt}],
            tools=[answer_tool],
            tool_choice={"type": "tool", "name": "submit_answers"},
        )

        for block in response.content:
            if block.type == "tool_use":
                logger.debug("Received structured answers from Claude")
                return block.input

        raise ValueError("Claude did not return structured answers")
