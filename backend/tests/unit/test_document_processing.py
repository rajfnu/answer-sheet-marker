"""Unit tests for document processing components."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
import numpy as np

from answer_marker.document_processing import (
    PDFParser,
    OCRHandler,
    ImageProcessor,
    DocumentValidator,
    ValidationResult,
)
from answer_marker.document_processing.structure_analyzer import DocumentSection


class TestPDFParser:
    """Test cases for PDFParser."""

    def test_pdf_parser_initialization(self):
        """Test PDFParser initialization."""
        parser = PDFParser(use_ocr_fallback=True)
        assert parser.use_ocr_fallback is True

        parser = PDFParser(use_ocr_fallback=False)
        assert parser.use_ocr_fallback is False

    def test_is_likely_scanned_with_short_text(self):
        """Test scanned document detection with short text."""
        parser = PDFParser()
        result = parser._is_likely_scanned("Short")
        assert result is True

    def test_is_likely_scanned_with_long_text(self):
        """Test scanned document detection with normal text."""
        parser = PDFParser()
        long_text = "This is a long enough text with many characters " * 10
        result = parser._is_likely_scanned(long_text)
        assert result is False

    def test_is_likely_scanned_with_garbled_text(self):
        """Test scanned document detection with garbled text."""
        parser = PDFParser()
        garbled = "@@##$$%%^^&&**" * 20  # High ratio of non-alphanumeric
        result = parser._is_likely_scanned(garbled)
        assert result is True


class TestOCRHandler:
    """Test cases for OCRHandler."""

    def test_ocr_handler_initialization(self):
        """Test OCRHandler initialization."""
        handler = OCRHandler(language="eng", config="--psm 6")
        assert handler.language == "eng"
        assert handler.config == "--psm 6"

    def test_ocr_handler_defaults(self):
        """Test OCRHandler with default values."""
        handler = OCRHandler()
        assert handler.language is not None
        assert handler.config is not None

    def test_group_by_blocks_empty(self):
        """Test grouping empty OCR data."""
        handler = OCRHandler()
        data = {"block_num": [], "text": []}
        result = handler._group_by_blocks(data)
        assert result == []

    def test_group_by_blocks_single_block(self):
        """Test grouping single block."""
        handler = OCRHandler()
        data = {
            "block_num": [1, 1, 1],
            "text": ["Hello", "world", "test"],
        }
        result = handler._group_by_blocks(data)
        assert len(result) == 1
        assert result[0]["block_num"] == 1
        assert result[0]["text"] == "Hello world test"

    def test_group_by_blocks_multiple_blocks(self):
        """Test grouping multiple blocks."""
        handler = OCRHandler()
        data = {
            "block_num": [1, 1, 2, 2, 3],
            "text": ["Hello", "world", "test", "data", "final"],
        }
        result = handler._group_by_blocks(data)
        assert len(result) == 3
        assert result[0]["text"] == "Hello world"
        assert result[1]["text"] == "test data"
        assert result[2]["text"] == "final"


class TestImageProcessor:
    """Test cases for ImageProcessor."""

    @pytest.fixture
    def sample_image(self):
        """Create a sample PIL Image for testing."""
        # Create a simple 100x100 RGB image
        return Image.new("RGB", (100, 100), color="white")

    def test_to_grayscale(self, sample_image):
        """Test grayscale conversion."""
        result = ImageProcessor.to_grayscale(sample_image)
        assert result.mode == "L"

    def test_to_grayscale_already_gray(self):
        """Test grayscale conversion on already gray image."""
        gray_image = Image.new("L", (100, 100))
        result = ImageProcessor.to_grayscale(gray_image)
        assert result.mode == "L"
        assert result is gray_image

    def test_enhance_contrast(self, sample_image):
        """Test contrast enhancement."""
        result = ImageProcessor.enhance_contrast(sample_image, factor=2.0)
        assert isinstance(result, Image.Image)

    def test_enhance_sharpness(self, sample_image):
        """Test sharpness enhancement."""
        result = ImageProcessor.enhance_sharpness(sample_image, factor=2.0)
        assert isinstance(result, Image.Image)

    def test_enhance_brightness(self, sample_image):
        """Test brightness enhancement."""
        result = ImageProcessor.enhance_brightness(sample_image, factor=1.5)
        assert isinstance(result, Image.Image)

    def test_denoise(self, sample_image):
        """Test denoising."""
        result = ImageProcessor.denoise(sample_image)
        assert isinstance(result, Image.Image)

    def test_resize_with_scale(self, sample_image):
        """Test resizing with scale factor."""
        result = ImageProcessor.resize(sample_image, scale=0.5)
        assert result.size == (50, 50)

    def test_resize_with_width(self, sample_image):
        """Test resizing with width only."""
        result = ImageProcessor.resize(sample_image, width=200)
        assert result.size == (200, 200)  # Maintains aspect ratio

    def test_resize_with_height(self, sample_image):
        """Test resizing with height only."""
        result = ImageProcessor.resize(sample_image, height=50)
        assert result.size == (50, 50)  # Maintains aspect ratio

    def test_resize_with_width_and_height(self, sample_image):
        """Test resizing with both dimensions."""
        result = ImageProcessor.resize(sample_image, width=150, height=200)
        assert result.size == (150, 200)

    def test_resize_no_parameters(self, sample_image):
        """Test that resize raises error with no parameters."""
        with pytest.raises(ValueError):
            ImageProcessor.resize(sample_image)

    def test_rotate(self, sample_image):
        """Test rotation."""
        result = ImageProcessor.rotate(sample_image, angle=90)
        assert isinstance(result, Image.Image)

    def test_crop(self, sample_image):
        """Test cropping."""
        result = ImageProcessor.crop(sample_image, 10, 10, 90, 90)
        assert result.size == (80, 80)

    def test_get_dimensions(self, sample_image):
        """Test getting dimensions."""
        width, height = ImageProcessor.get_dimensions(sample_image)
        assert width == 100
        assert height == 100

    def test_prepare_for_ocr(self, sample_image):
        """Test OCR preparation pipeline."""
        result = ImageProcessor.prepare_for_ocr(sample_image)
        assert isinstance(result, Image.Image)
        assert result.mode == "L"  # Should be grayscale


class TestDocumentValidator:
    """Test cases for DocumentValidator."""

    def test_validate_marking_guide_valid(self):
        """Test validation of valid marking guide."""
        validator = DocumentValidator()
        data = {
            "questions": [
                {
                    "id": "Q1",
                    "question_text": "What is 2+2?",
                    "marks": 5.0,
                    "marking_scheme": "Answer should be 4",
                    "question_type": "short_answer",
                }
            ],
            "total_marks": 5.0,
        }

        result = validator.validate_marking_guide(data)
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validate_marking_guide_no_questions(self):
        """Test validation with no questions."""
        validator = DocumentValidator()
        data = {}

        result = validator.validate_marking_guide(data)
        assert result.is_valid is False
        assert any("No questions found" in error for error in result.errors)

    def test_validate_marking_guide_empty_questions(self):
        """Test validation with empty questions list."""
        validator = DocumentValidator()
        data = {"questions": []}

        result = validator.validate_marking_guide(data)
        assert result.is_valid is False
        assert any("no questions" in error.lower() for error in result.errors)

    def test_validate_marking_guide_missing_question_text(self):
        """Test validation with missing question text."""
        validator = DocumentValidator()
        data = {"questions": [{"id": "Q1", "marks": 5.0}]}

        result = validator.validate_marking_guide(data)
        assert result.is_valid is False
        assert any("no text" in error.lower() for error in result.errors)

    def test_validate_answer_sheet_valid(self):
        """Test validation of valid answer sheet."""
        validator = DocumentValidator()
        data = {
            "answers": [
                {"question_id": "Q1", "answer_text": "The answer is 4", "is_blank": False}
            ]
        }
        expected = ["Q1"]

        result = validator.validate_answer_sheet(data, expected)
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validate_answer_sheet_no_answers(self):
        """Test validation with no answers."""
        validator = DocumentValidator()
        data = {}
        expected = ["Q1", "Q2"]

        result = validator.validate_answer_sheet(data, expected)
        assert result.is_valid is False
        assert any("No answers found" in error for error in result.errors)

    def test_validate_answer_sheet_missing_questions(self):
        """Test validation with missing question answers."""
        validator = DocumentValidator()
        data = {"answers": [{"question_id": "Q1", "answer_text": "Answer 1"}]}
        expected = ["Q1", "Q2", "Q3"]

        result = validator.validate_answer_sheet(data, expected)
        assert result.is_valid is True  # Just warnings, not errors
        assert len(result.warnings) > 0
        assert any("Missing answers" in warning for warning in result.warnings)

    def test_validate_text_extraction_valid(self):
        """Test text extraction validation with valid text."""
        validator = DocumentValidator()
        text = "This is a long enough text with plenty of alphanumeric characters " * 5

        result = validator.validate_text_extraction(text)
        assert result.is_valid is True

    def test_validate_text_extraction_too_short(self):
        """Test text extraction validation with short text."""
        validator = DocumentValidator()
        text = "Short"

        result = validator.validate_text_extraction(text, min_length=50)
        assert result.is_valid is False
        assert any("too short" in error.lower() for error in result.errors)

    def test_calculate_quality_score(self):
        """Test quality score calculation."""
        validator = DocumentValidator()

        # Perfect score
        score = validator._calculate_quality_score({}, [], [])
        assert score == 1.0

        # With errors
        score = validator._calculate_quality_score({}, ["error1"], [])
        assert score < 1.0

        # With warnings
        score = validator._calculate_quality_score({}, [], ["warning1"])
        assert score < 1.0


class TestDocumentSection:
    """Test cases for DocumentSection model."""

    def test_document_section_creation(self):
        """Test creating DocumentSection."""
        section = DocumentSection(
            section_type="question",
            content="What is 2+2?",
            question_number="1",
            marks=5.0,
        )

        assert section.section_type == "question"
        assert section.content == "What is 2+2?"
        assert section.question_number == "1"
        assert section.marks == 5.0

    def test_document_section_defaults(self):
        """Test DocumentSection with default values."""
        section = DocumentSection(section_type="header", content="Header text")

        assert section.question_number is None
        assert section.marks is None
        assert section.metadata == {}


class TestValidationResult:
    """Test cases for ValidationResult model."""

    def test_validation_result_creation(self):
        """Test creating ValidationResult."""
        result = ValidationResult(
            is_valid=True, errors=[], warnings=["warning1"], quality_score=0.95
        )

        assert result.is_valid is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 1
        assert result.quality_score == 0.95

    def test_validation_result_with_errors(self):
        """Test ValidationResult with errors."""
        result = ValidationResult(
            is_valid=False, errors=["error1", "error2"], warnings=[], quality_score=0.5
        )

        assert result.is_valid is False
        assert len(result.errors) == 2
        assert result.quality_score == 0.5
