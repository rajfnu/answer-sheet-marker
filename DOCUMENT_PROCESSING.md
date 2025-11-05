# Document Processing Guide - Answer Sheet Marker

## Overview

This guide covers document processing pipeline for handling various input formats including PDFs, images, and scanned documents.

## Document Processing Architecture

```
Input Documents
    ↓
PDF/Image Detection
    ↓
Text Extraction (pypdf/OCR)
    ↓
Structure Analysis
    ↓
Data Validation
    ↓
Structured Models
```

## Module 1: Document Parser

### Purpose
Unified interface for handling different document types.

### Implementation

```python
# src/answer_marker/document_processing/pdf_parser.py

from pathlib import Path
from typing import Union, Dict, List
import pypdf
from pdf2image import convert_from_path
from PIL import Image
from loguru import logger

class PDFParser:
    """
    Parse PDF documents and extract text
    """
    
    def __init__(self, use_ocr_fallback: bool = True):
        self.use_ocr_fallback = use_ocr_fallback
    
    async def parse(self, file_path: Union[str, Path]) -> Dict[str, any]:
        """
        Parse PDF and extract text
        
        Returns:
            {
                'text': str,
                'pages': List[str],
                'has_images': bool,
                'is_scanned': bool
            }
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"PDF not found: {file_path}")
        
        try:
            # Try direct text extraction first
            text, pages = self._extract_text_direct(file_path)
            is_scanned = self._is_likely_scanned(text)
            
            # If scanned or poor extraction, use OCR
            if is_scanned and self.use_ocr_fallback:
                logger.info(f"Using OCR for {file_path.name}")
                text, pages = await self._extract_text_ocr(file_path)
            
            return {
                'text': text,
                'pages': pages,
                'is_scanned': is_scanned,
                'page_count': len(pages),
                'source_file': str(file_path)
            }
            
        except Exception as e:
            logger.error(f"Error parsing PDF {file_path}: {e}")
            raise
    
    def _extract_text_direct(self, file_path: Path) -> tuple[str, List[str]]:
        """Extract text directly from PDF"""
        reader = pypdf.PdfReader(file_path)
        pages = []
        
        for page in reader.pages:
            page_text = page.extract_text()
            pages.append(page_text)
        
        full_text = "\n\n--- PAGE BREAK ---\n\n".join(pages)
        return full_text, pages
    
    def _is_likely_scanned(self, text: str) -> bool:
        """Detect if PDF is likely a scanned document"""
        # If very little text extracted, likely scanned
        if len(text.strip()) < 100:
            return True
        
        # Check for high ratio of non-alphanumeric characters
        alphanumeric = sum(c.isalnum() for c in text)
        if alphanumeric / len(text) < 0.5:
            return True
        
        return False
    
    async def _extract_text_ocr(self, file_path: Path) -> tuple[str, List[str]]:
        """Extract text using OCR"""
        from answer_marker.document_processing.ocr_handler import OCRHandler
        
        # Convert PDF to images
        images = convert_from_path(file_path, dpi=300)
        
        ocr_handler = OCRHandler()
        pages = []
        
        for i, image in enumerate(images):
            logger.info(f"OCR processing page {i+1}/{len(images)}")
            page_text = await ocr_handler.extract_text(image)
            pages.append(page_text)
        
        full_text = "\n\n--- PAGE BREAK ---\n\n".join(pages)
        return full_text, pages
```

## Module 2: OCR Handler

### Implementation

```python
# src/answer_marker/document_processing/ocr_handler.py

import pytesseract
from PIL import Image
from typing import Union
import numpy as np
from loguru import logger

class OCRHandler:
    """
    Handle OCR operations for images and scanned documents
    """
    
    def __init__(self, language: str = 'eng', config: str = '--psm 6'):
        """
        Args:
            language: Tesseract language code (e.g., 'eng', 'fra', 'spa')
            config: Tesseract configuration (PSM modes)
                --psm 6: Assume a single uniform block of text
                --psm 3: Fully automatic page segmentation (default)
        """
        self.language = language
        self.config = config
    
    async def extract_text(self, image: Union[Image.Image, str, np.ndarray]) -> str:
        """
        Extract text from image using Tesseract OCR
        
        Args:
            image: PIL Image, file path, or numpy array
            
        Returns:
            Extracted text
        """
        try:
            # Convert to PIL Image if needed
            if isinstance(image, str):
                image = Image.open(image)
            elif isinstance(image, np.ndarray):
                image = Image.fromarray(image)
            
            # Preprocess image for better OCR
            processed_image = self._preprocess_image(image)
            
            # Extract text
            text = pytesseract.image_to_string(
                processed_image,
                lang=self.language,
                config=self.config
            )
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            raise
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocess image for better OCR results
        - Convert to grayscale
        - Increase contrast
        - Denoise
        """
        # Convert to grayscale
        if image.mode != 'L':
            image = image.convert('L')
        
        # Increase contrast
        from PIL import ImageEnhance
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)
        
        return image
    
    async def extract_with_layout(self, image: Union[Image.Image, str]) -> Dict:
        """
        Extract text with layout information (bounding boxes)
        Useful for structured documents
        """
        if isinstance(image, str):
            image = Image.open(image)
        
        # Get detailed OCR data
        data = pytesseract.image_to_data(
            image,
            lang=self.language,
            config=self.config,
            output_type=pytesseract.Output.DICT
        )
        
        # Group text by blocks/paragraphs
        blocks = self._group_by_blocks(data)
        
        return {
            'text': ' '.join(data['text']),
            'blocks': blocks,
            'raw_data': data
        }
    
    def _group_by_blocks(self, data: Dict) -> List[Dict]:
        """Group OCR data by text blocks"""
        blocks = []
        current_block = []
        current_block_num = None
        
        for i, block_num in enumerate(data['block_num']):
            if block_num != current_block_num:
                if current_block:
                    blocks.append({
                        'block_num': current_block_num,
                        'text': ' '.join(current_block)
                    })
                current_block = []
                current_block_num = block_num
            
            if data['text'][i].strip():
                current_block.append(data['text'][i])
        
        # Add last block
        if current_block:
            blocks.append({
                'block_num': current_block_num,
                'text': ' '.join(current_block)
            })
        
        return blocks
```

## Module 3: Structure Analyzer

### Purpose
Analyze document structure and extract questions, answers, and marking schemes.

### Implementation

```python
# src/answer_marker/document_processing/structure_analyzer.py

from typing import List, Dict, Optional
from pydantic import BaseModel
from anthropic import Anthropic
import re
from loguru import logger

class DocumentSection(BaseModel):
    """Represents a section of the document"""
    section_type: str  # 'question', 'answer', 'marking_scheme', 'header', 'footer'
    content: str
    question_number: Optional[str] = None
    marks: Optional[float] = None
    metadata: Dict = {}

class StructureAnalyzer:
    """
    Analyze document structure and extract structured information
    """
    
    def __init__(self, client: Anthropic):
        self.client = client
    
    async def analyze_marking_guide(self, document_text: str) -> Dict:
        """
        Analyze marking guide structure
        
        Returns structured marking guide with:
        - Questions
        - Marking schemes
        - Point allocations
        - Sample answers (if present)
        """
        
        # First, try pattern-based extraction
        sections = self._extract_sections_pattern(document_text)
        
        # Then use Claude for intelligent structuring
        structured = await self._structure_with_claude(document_text, sections)
        
        return structured
    
    def _extract_sections_pattern(self, text: str) -> List[DocumentSection]:
        """
        Extract sections using regex patterns
        Common patterns:
        - Q1. or Question 1: or 1)
        - [5 marks] or (5 points)
        """
        sections = []
        
        # Pattern for questions with marks
        question_pattern = r'(?:Q|Question)\.?\s*(\d+)\.?\s*(?:\[(\d+)\s*marks?\])?'
        
        lines = text.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            match = re.search(question_pattern, line, re.IGNORECASE)
            
            if match:
                # Save previous section
                if current_section:
                    current_section.content = '\n'.join(current_content)
                    sections.append(current_section)
                
                # Start new section
                question_num = match.group(1)
                marks = float(match.group(2)) if match.group(2) else None
                
                current_section = DocumentSection(
                    section_type='question',
                    content='',
                    question_number=question_num,
                    marks=marks
                )
                current_content = [line]
            else:
                current_content.append(line)
        
        # Add last section
        if current_section:
            current_section.content = '\n'.join(current_content)
            sections.append(current_section)
        
        return sections
    
    async def _structure_with_claude(
        self,
        document_text: str,
        pattern_sections: List[DocumentSection]
    ) -> Dict:
        """
        Use Claude to intelligently structure the document
        """
        
        structure_tool = {
            "name": "submit_structure",
            "description": "Submit the structured analysis of the marking guide",
            "input_schema": {
                "type": "object",
                "properties": {
                    "document_type": {
                        "type": "string",
                        "enum": ["marking_guide", "answer_sheet", "question_paper"]
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
                                    "enum": ["mcq", "short_answer", "essay", "numerical", "true_false"]
                                }
                            },
                            "required": ["id", "question_text", "marks"]
                        }
                    },
                    "total_marks": {"type": "number"},
                    "metadata": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "subject": {"type": "string"},
                            "date": {"type": "string"}
                        }
                    }
                },
                "required": ["document_type", "questions"]
            }
        }
        
        prompt = f"""
<document>
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
</guidelines>
"""
        
        response = self.client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=16000,
            system="You are an expert at analyzing educational documents and extracting structured information.",
            messages=[{"role": "user", "content": prompt}],
            tools=[structure_tool],
            tool_choice={"type": "tool", "name": "submit_structure"}
        )
        
        for block in response.content:
            if block.type == "tool_use":
                return block.input
        
        raise ValueError("Claude did not return structured output")
    
    def _format_pattern_sections(self, sections: List[DocumentSection]) -> str:
        """Format pattern-extracted sections for Claude"""
        if not sections:
            return "No clear patterns detected"
        
        formatted = []
        for i, section in enumerate(sections, 1):
            formatted.append(f"""
Section {i}:
Type: {section.section_type}
Question Number: {section.question_number or 'N/A'}
Marks: {section.marks or 'N/A'}
Content Preview: {section.content[:200]}...
""")
        return '\n'.join(formatted)
    
    async def analyze_answer_sheet(self, document_text: str, question_ids: List[str]) -> Dict:
        """
        Analyze answer sheet structure and map answers to questions
        
        Args:
            document_text: Extracted text from answer sheet
            question_ids: Expected question IDs
            
        Returns:
            Structured answers mapped to questions
        """
        
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
                                "is_blank": {"type": "boolean"}
                            },
                            "required": ["question_id", "answer_text"]
                        }
                    }
                },
                "required": ["answers"]
            }
        }
        
        prompt = f"""
<answer_sheet>
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
</guidelines>
"""
        
        response = self.client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=16000,
            system="You are an expert at reading and extracting student answers from answer sheets.",
            messages=[{"role": "user", "content": prompt}],
            tools=[answer_tool],
            tool_choice={"type": "tool", "name": "submit_answers"}
        )
        
        for block in response.content:
            if block.type == "tool_use":
                return block.input
        
        raise ValueError("Claude did not return structured answers")
```

## Module 4: Document Validator

### Purpose
Validate document quality and completeness before processing.

### Implementation

```python
# src/answer_marker/document_processing/validators.py

from typing import Dict, List
from pydantic import BaseModel

class ValidationResult(BaseModel):
    """Result of document validation"""
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    quality_score: float  # 0-1

class DocumentValidator:
    """
    Validate documents before processing
    """
    
    def validate_marking_guide(self, structured_data: Dict) -> ValidationResult:
        """Validate marking guide structure"""
        errors = []
        warnings = []
        
        # Check required fields
        if 'questions' not in structured_data:
            errors.append("No questions found in marking guide")
        
        if 'questions' in structured_data:
            questions = structured_data['questions']
            
            # Check each question
            for i, q in enumerate(questions):
                if 'question_text' not in q or not q['question_text'].strip():
                    errors.append(f"Question {i+1} has no text")
                
                if 'marks' not in q:
                    warnings.append(f"Question {i+1} has no marks specified")
                
                if 'marking_scheme' not in q or not q['marking_scheme'].strip():
                    warnings.append(f"Question {i+1} has no marking scheme")
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(structured_data, errors, warnings)
        
        is_valid = len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            quality_score=quality_score
        )
    
    def validate_answer_sheet(
        self,
        structured_data: Dict,
        expected_questions: List[str]
    ) -> ValidationResult:
        """Validate answer sheet structure"""
        errors = []
        warnings = []
        
        if 'answers' not in structured_data:
            errors.append("No answers found in answer sheet")
        
        if 'answers' in structured_data:
            answers = structured_data['answers']
            answer_ids = [a['question_id'] for a in answers]
            
            # Check for missing questions
            missing = set(expected_questions) - set(answer_ids)
            if missing:
                warnings.append(f"Missing answers for questions: {missing}")
            
            # Check for unexpected questions
            unexpected = set(answer_ids) - set(expected_questions)
            if unexpected:
                warnings.append(f"Unexpected question IDs: {unexpected}")
            
            # Check blank answers
            blank_count = sum(1 for a in answers if a.get('is_blank', False))
            if blank_count > 0:
                warnings.append(f"{blank_count} unanswered questions")
        
        quality_score = self._calculate_quality_score(structured_data, errors, warnings)
        is_valid = len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            quality_score=quality_score
        )
    
    def _calculate_quality_score(
        self,
        data: Dict,
        errors: List[str],
        warnings: List[str]
    ) -> float:
        """Calculate overall quality score"""
        # Start with perfect score
        score = 1.0
        
        # Deduct for errors
        score -= len(errors) * 0.2
        
        # Deduct for warnings
        score -= len(warnings) * 0.05
        
        # Ensure score is between 0 and 1
        return max(0.0, min(1.0, score))
```

## Integration Example

### Complete Document Processing Pipeline

```python
# src/answer_marker/document_processing/__init__.py

from pathlib import Path
from typing import Dict
from .pdf_parser import PDFParser
from .structure_analyzer import StructureAnalyzer
from .validators import DocumentValidator
from loguru import logger

class DocumentProcessor:
    """
    Main document processing pipeline
    """
    
    def __init__(self, claude_client):
        self.pdf_parser = PDFParser(use_ocr_fallback=True)
        self.structure_analyzer = StructureAnalyzer(claude_client)
        self.validator = DocumentValidator()
    
    async def process_marking_guide(self, file_path: Path) -> Dict:
        """
        Complete processing pipeline for marking guide
        
        Returns:
            Validated, structured marking guide
        """
        logger.info(f"Processing marking guide: {file_path}")
        
        # Step 1: Parse document
        parsed = await self.pdf_parser.parse(file_path)
        logger.info(f"Extracted {parsed['page_count']} pages")
        
        # Step 2: Analyze structure
        structured = await self.structure_analyzer.analyze_marking_guide(
            parsed['text']
        )
        logger.info(f"Found {len(structured['questions'])} questions")
        
        # Step 3: Validate
        validation = self.validator.validate_marking_guide(structured)
        
        if not validation.is_valid:
            logger.error(f"Validation errors: {validation.errors}")
            raise ValueError("Invalid marking guide structure")
        
        if validation.warnings:
            logger.warning(f"Validation warnings: {validation.warnings}")
        
        logger.info(f"Document quality score: {validation.quality_score:.2f}")
        
        return {
            **structured,
            'validation': validation.model_dump(),
            'source_file': str(file_path)
        }
    
    async def process_answer_sheet(
        self,
        file_path: Path,
        expected_questions: List[str]
    ) -> Dict:
        """
        Complete processing pipeline for answer sheet
        """
        logger.info(f"Processing answer sheet: {file_path}")
        
        # Step 1: Parse
        parsed = await self.pdf_parser.parse(file_path)
        
        # Step 2: Analyze
        structured = await self.structure_analyzer.analyze_answer_sheet(
            parsed['text'],
            expected_questions
        )
        
        # Step 3: Validate
        validation = self.validator.validate_answer_sheet(
            structured,
            expected_questions
        )
        
        if not validation.is_valid:
            logger.error(f"Validation errors: {validation.errors}")
            raise ValueError("Invalid answer sheet structure")
        
        return {
            **structured,
            'validation': validation.model_dump(),
            'source_file': str(file_path)
        }
```

## Best Practices

1. **Always Use OCR Fallback**: Many answer sheets are scanned documents
2. **Preprocess Images**: Enhance contrast and denoise for better OCR
3. **Validate Early**: Catch issues before expensive AI processing
4. **Preserve Original**: Keep original text for human review
5. **Handle Errors Gracefully**: Log issues but continue processing
6. **Cache Results**: Save parsed results to avoid reprocessing
7. **Support Multiple Formats**: PDF, DOCX, images, etc.
8. **Track Quality**: Monitor OCR accuracy and validation scores

## Testing Document Processing

```python
# tests/integration/test_document_processing.py

import pytest
from pathlib import Path
from answer_marker.document_processing import DocumentProcessor

@pytest.mark.asyncio
async def test_process_marking_guide(mock_claude_client, sample_marking_guide_pdf):
    processor = DocumentProcessor(mock_claude_client)
    
    result = await processor.process_marking_guide(sample_marking_guide_pdf)
    
    assert result['document_type'] == 'marking_guide'
    assert len(result['questions']) > 0
    assert result['validation']['is_valid'] == True
    
@pytest.mark.asyncio
async def test_process_scanned_document(mock_claude_client, scanned_pdf):
    processor = DocumentProcessor(mock_claude_client)
    
    result = await processor.process_marking_guide(scanned_pdf)
    
    # Should successfully process scanned documents
    assert result['validation']['quality_score'] > 0.5
```

This document processing pipeline ensures:
- **Robustness**: Handles various document formats
- **Accuracy**: Uses OCR when needed
- **Validation**: Catches issues early
- **Structure**: Converts unstructured text to structured data
- **Quality**: Monitors and reports quality metrics
