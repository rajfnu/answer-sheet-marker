"""PDF parser for the Answer Sheet Marker system.

This module handles PDF document parsing with automatic OCR fallback for scanned documents.
"""

from pathlib import Path
from typing import Union, Dict, List, Any
import pypdf
from pdf2image import convert_from_path
from PIL import Image
from loguru import logger
from answer_marker.config import settings


class PDFParser:
    """Parse PDF documents and extract text with OCR fallback.

    Handles both native PDF text extraction and OCR for scanned documents.
    Automatically detects scanned documents and applies appropriate extraction method.
    """

    def __init__(self, use_ocr_fallback: bool = True):
        """Initialize PDF parser.

        Args:
            use_ocr_fallback: Enable OCR fallback for scanned documents
        """
        self.use_ocr_fallback = use_ocr_fallback

    async def parse(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Parse PDF and extract text.

        Args:
            file_path: Path to PDF file

        Returns:
            Dictionary containing:
                - text: Full extracted text
                - pages: List of text per page
                - is_scanned: Whether document appears to be scanned
                - page_count: Number of pages
                - source_file: Source file path

        Raises:
            FileNotFoundError: If PDF file doesn't exist
            Exception: For other parsing errors
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"PDF not found: {file_path}")

        if not file_path.suffix.lower() == ".pdf":
            raise ValueError(f"File is not a PDF: {file_path}")

        try:
            # Try direct text extraction first
            logger.debug(f"Attempting direct text extraction from {file_path.name}")
            text, pages = self._extract_text_direct(file_path)
            is_scanned = self._is_likely_scanned(text)

            # If scanned or poor extraction, use OCR
            if is_scanned and self.use_ocr_fallback and settings.ocr_enabled:
                logger.info(f"Document appears scanned, using OCR for {file_path.name}")
                text, pages = await self._extract_text_ocr(file_path)
            elif is_scanned and not self.use_ocr_fallback:
                logger.warning(
                    f"Document appears scanned but OCR is disabled for {file_path.name}"
                )

            logger.info(
                f"Successfully parsed {file_path.name}: "
                f"{len(pages)} pages, {len(text)} characters"
            )

            return {
                "text": text,
                "pages": pages,
                "is_scanned": is_scanned,
                "page_count": len(pages),
                "source_file": str(file_path),
            }

        except Exception as e:
            logger.error(f"Error parsing PDF {file_path}: {e}")
            raise

    def _extract_text_direct(self, file_path: Path) -> tuple[str, List[str]]:
        """Extract text directly from PDF using pypdf.

        Args:
            file_path: Path to PDF file

        Returns:
            Tuple of (full_text, pages_list)
        """
        try:
            reader = pypdf.PdfReader(str(file_path))
            pages = []

            for i, page in enumerate(reader.pages):
                logger.debug(f"Extracting text from page {i + 1}/{len(reader.pages)}")
                page_text = page.extract_text()
                pages.append(page_text)

            full_text = "\n\n--- PAGE BREAK ---\n\n".join(pages)
            return full_text, pages

        except Exception as e:
            logger.error(f"Direct text extraction failed: {e}")
            # Return empty if extraction fails - OCR will be attempted
            return "", []

    def _is_likely_scanned(self, text: str) -> bool:
        """Detect if PDF is likely a scanned document.

        Uses heuristics:
        - Very little text extracted
        - High ratio of non-alphanumeric characters
        - Low character density

        Args:
            text: Extracted text

        Returns:
            True if document appears to be scanned
        """
        if not text or len(text.strip()) < 100:
            logger.debug("Document has <100 characters, likely scanned")
            return True

        # Check for high ratio of non-alphanumeric characters
        alphanumeric = sum(c.isalnum() for c in text)
        if len(text) > 0 and alphanumeric / len(text) < 0.5:
            logger.debug(
                f"Low alphanumeric ratio ({alphanumeric}/{len(text)}), likely scanned"
            )
            return True

        return False

    async def _extract_text_ocr(self, file_path: Path) -> tuple[str, List[str]]:
        """Extract text using OCR.

        Converts PDF pages to images and applies OCR to each page.

        Args:
            file_path: Path to PDF file

        Returns:
            Tuple of (full_text, pages_list)
        """
        from answer_marker.document_processing.ocr_handler import OCRHandler

        try:
            # Convert PDF to images
            logger.info(f"Converting PDF to images at {settings.pdf_dpi} DPI")
            images = convert_from_path(str(file_path), dpi=settings.pdf_dpi)

            ocr_handler = OCRHandler()
            pages = []

            for i, image in enumerate(images):
                logger.info(f"OCR processing page {i + 1}/{len(images)}")
                page_text = await ocr_handler.extract_text(image)
                pages.append(page_text)

            full_text = "\n\n--- PAGE BREAK ---\n\n".join(pages)
            return full_text, pages

        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            raise

    def get_page_count(self, file_path: Union[str, Path]) -> int:
        """Get number of pages in PDF without full parsing.

        Args:
            file_path: Path to PDF file

        Returns:
            Number of pages
        """
        file_path = Path(file_path)
        try:
            reader = pypdf.PdfReader(str(file_path))
            return len(reader.pages)
        except Exception as e:
            logger.error(f"Error getting page count: {e}")
            raise

    def extract_page(self, file_path: Union[str, Path], page_number: int) -> str:
        """Extract text from a specific page.

        Args:
            file_path: Path to PDF file
            page_number: Page number (0-indexed)

        Returns:
            Text from the specified page
        """
        file_path = Path(file_path)
        try:
            reader = pypdf.PdfReader(str(file_path))
            if page_number < 0 or page_number >= len(reader.pages):
                raise ValueError(f"Invalid page number: {page_number}")

            page = reader.pages[page_number]
            return page.extract_text()
        except Exception as e:
            logger.error(f"Error extracting page {page_number}: {e}")
            raise
