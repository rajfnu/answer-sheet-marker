"""Document processing package for the Answer Sheet Marker system.

This package provides a complete document processing pipeline for handling
PDFs, images, and scanned documents with OCR support.
"""

from pathlib import Path
from typing import Dict, List, Any
from .pdf_parser import PDFParser
from .ocr_handler import OCRHandler
from .image_processor import ImageProcessor
from .structure_analyzer import StructureAnalyzer, DocumentSection
from .validators import DocumentValidator, ValidationResult
from loguru import logger


class DocumentProcessor:
    """Main document processing pipeline.

    Integrates PDF parsing, OCR, structure analysis, and validation
    into a single unified interface.
    """

    def __init__(self, claude_client):
        """Initialize document processor.

        Args:
            claude_client: Anthropic client for Claude API
        """
        self.pdf_parser = PDFParser(use_ocr_fallback=True)
        self.ocr_handler = OCRHandler()
        self.structure_analyzer = StructureAnalyzer(claude_client)
        self.validator = DocumentValidator()
        self.image_processor = ImageProcessor()

        logger.info("DocumentProcessor initialized")

    async def process_marking_guide(self, file_path: Path) -> Dict[str, Any]:
        """Complete processing pipeline for marking guide.

        Args:
            file_path: Path to marking guide PDF

        Returns:
            Validated, structured marking guide with all metadata

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If validation fails
        """
        logger.info(f"Processing marking guide: {file_path}")

        try:
            # Step 1: Parse document
            parsed = await self.pdf_parser.parse(file_path)
            logger.info(
                f"Extracted {parsed['page_count']} pages "
                f"({'scanned' if parsed['is_scanned'] else 'native PDF'})"
            )

            # Step 1.5: Validate text extraction
            text_validation = self.validator.validate_text_extraction(parsed["text"])
            if not text_validation.is_valid:
                logger.error(f"Text extraction validation failed: {text_validation.errors}")
                raise ValueError("Poor text extraction quality")

            # Step 2: Analyze structure
            structured = await self.structure_analyzer.analyze_marking_guide(parsed["text"])
            logger.info(f"Found {len(structured.get('questions', []))} questions")

            # Step 3: Validate structure
            validation = self.validator.validate_marking_guide(structured)

            if not validation.is_valid:
                logger.error(f"Validation errors: {validation.errors}")
                raise ValueError(f"Invalid marking guide structure: {validation.errors}")

            if validation.warnings:
                logger.warning(f"Validation warnings: {validation.warnings}")

            logger.info(f"Document quality score: {validation.quality_score:.2f}")

            # Combine all results
            result = {
                **structured,
                "validation": validation.model_dump(),
                "source_file": str(file_path),
                "is_scanned": parsed["is_scanned"],
                "page_count": parsed["page_count"],
            }

            logger.info("Marking guide processing completed successfully")
            return result

        except Exception as e:
            logger.error(f"Error processing marking guide: {e}")
            raise

    async def process_answer_sheet(
        self, file_path: Path, expected_questions: List[str]
    ) -> Dict[str, Any]:
        """Complete processing pipeline for answer sheet.

        Args:
            file_path: Path to answer sheet PDF
            expected_questions: List of expected question IDs

        Returns:
            Validated, structured answer sheet with all answers

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If validation fails
        """
        logger.info(f"Processing answer sheet: {file_path}")

        try:
            # Step 1: Parse document
            parsed = await self.pdf_parser.parse(file_path)
            logger.info(
                f"Extracted {parsed['page_count']} pages "
                f"({'scanned' if parsed['is_scanned'] else 'native PDF'})"
            )

            # Step 1.5: Validate text extraction
            text_validation = self.validator.validate_text_extraction(parsed["text"])
            if not text_validation.is_valid:
                logger.error(f"Text extraction validation failed: {text_validation.errors}")
                raise ValueError("Poor text extraction quality")

            # Step 2: Analyze structure
            structured = await self.structure_analyzer.analyze_answer_sheet(
                parsed["text"], expected_questions
            )
            logger.info(f"Extracted {len(structured.get('answers', []))} answers")

            # Step 3: Validate structure
            validation = self.validator.validate_answer_sheet(structured, expected_questions)

            if not validation.is_valid:
                logger.error(f"Validation errors: {validation.errors}")
                raise ValueError(f"Invalid answer sheet structure: {validation.errors}")

            if validation.warnings:
                logger.warning(f"Validation warnings: {validation.warnings}")

            logger.info(f"Document quality score: {validation.quality_score:.2f}")

            # Combine all results
            result = {
                **structured,
                "validation": validation.model_dump(),
                "source_file": str(file_path),
                "is_scanned": parsed["is_scanned"],
                "page_count": parsed["page_count"],
            }

            logger.info("Answer sheet processing completed successfully")
            return result

        except Exception as e:
            logger.error(f"Error processing answer sheet: {e}")
            raise

    async def process_image(self, file_path: Path) -> Dict[str, Any]:
        """Process an image file using OCR.

        Args:
            file_path: Path to image file

        Returns:
            Dictionary with extracted text and metadata
        """
        logger.info(f"Processing image: {file_path}")

        try:
            # Load and preprocess image
            image = self.image_processor.load_image(file_path)
            processed_image = self.image_processor.prepare_for_ocr(image)

            # Extract text
            text = await self.ocr_handler.extract_text(processed_image)
            confidence = self.ocr_handler.get_confidence_score(processed_image)

            logger.info(f"Extracted {len(text)} characters (confidence: {confidence:.1f}%)")

            return {
                "text": text,
                "confidence": confidence,
                "source_file": str(file_path),
                "dimensions": self.image_processor.get_dimensions(image),
            }

        except Exception as e:
            logger.error(f"Error processing image: {e}")
            raise


# Export main classes
__all__ = [
    "DocumentProcessor",
    "PDFParser",
    "OCRHandler",
    "ImageProcessor",
    "StructureAnalyzer",
    "DocumentValidator",
    "DocumentSection",
    "ValidationResult",
]
