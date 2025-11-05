"""OCR handler for the Answer Sheet Marker system.

This module handles Optical Character Recognition (OCR) operations for images
and scanned documents using Tesseract.
"""

import pytesseract
from PIL import Image, ImageEnhance
from typing import Union, Dict, List, Any
import numpy as np
from loguru import logger
from answer_marker.config import settings


class OCRHandler:
    """Handle OCR operations for images and scanned documents.

    Uses Tesseract OCR engine to extract text from images with preprocessing
    for improved accuracy.
    """

    def __init__(self, language: str = None, config: str = None):
        """Initialize OCR handler.

        Args:
            language: Tesseract language code (e.g., 'eng', 'fra', 'spa')
                     Defaults to settings.ocr_language
            config: Tesseract configuration string
                    Defaults to '--psm 6' (single uniform block of text)
                    PSM modes:
                      --psm 3: Fully automatic page segmentation (default)
                      --psm 6: Assume a single uniform block of text
                      --psm 11: Sparse text. Find as much text as possible
        """
        self.language = language or settings.ocr_language
        self.config = config or "--psm 6"
        logger.debug(f"Initialized OCR handler: language={self.language}, config={self.config}")

    async def extract_text(self, image: Union[Image.Image, str, np.ndarray]) -> str:
        """Extract text from image using Tesseract OCR.

        Args:
            image: PIL Image, file path, or numpy array

        Returns:
            Extracted text (stripped of leading/trailing whitespace)

        Raises:
            Exception: If OCR extraction fails
        """
        try:
            # Convert to PIL Image if needed
            if isinstance(image, str):
                logger.debug(f"Loading image from path: {image}")
                image = Image.open(image)
            elif isinstance(image, np.ndarray):
                logger.debug("Converting numpy array to PIL Image")
                image = Image.fromarray(image)

            # Preprocess image for better OCR
            processed_image = self._preprocess_image(image)

            # Extract text
            logger.debug("Extracting text with Tesseract")
            text = pytesseract.image_to_string(
                processed_image, lang=self.language, config=self.config
            )

            return text.strip()

        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            raise

    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess image for better OCR results.

        Applies:
        - Grayscale conversion
        - Contrast enhancement
        - Optional sharpening

        Args:
            image: PIL Image to preprocess

        Returns:
            Preprocessed PIL Image
        """
        # Convert to grayscale
        if image.mode != "L":
            logger.debug("Converting image to grayscale")
            image = image.convert("L")

        # Increase contrast
        logger.debug("Enhancing image contrast")
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)

        # Optional: Increase sharpness slightly
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(1.5)

        return image

    async def extract_with_layout(
        self, image: Union[Image.Image, str]
    ) -> Dict[str, Any]:
        """Extract text with layout information (bounding boxes).

        Useful for structured documents where position matters.

        Args:
            image: PIL Image or file path

        Returns:
            Dictionary containing:
                - text: Full extracted text
                - blocks: List of text blocks with metadata
                - raw_data: Raw OCR data from Tesseract
        """
        try:
            if isinstance(image, str):
                image = Image.open(image)

            logger.debug("Extracting text with layout information")

            # Get detailed OCR data
            data = pytesseract.image_to_data(
                image,
                lang=self.language,
                config=self.config,
                output_type=pytesseract.Output.DICT,
            )

            # Group text by blocks/paragraphs
            blocks = self._group_by_blocks(data)

            # Combine all text
            full_text = " ".join([word for word in data["text"] if word.strip()])

            return {"text": full_text, "blocks": blocks, "raw_data": data}

        except Exception as e:
            logger.error(f"Layout extraction failed: {e}")
            raise

    def _group_by_blocks(self, data: Dict) -> List[Dict[str, Any]]:
        """Group OCR data by text blocks.

        Args:
            data: Raw OCR data dictionary from Tesseract

        Returns:
            List of text blocks with metadata
        """
        blocks = []
        current_block = []
        current_block_num = None

        for i, block_num in enumerate(data["block_num"]):
            if block_num != current_block_num:
                # Save previous block
                if current_block:
                    blocks.append(
                        {"block_num": current_block_num, "text": " ".join(current_block)}
                    )
                current_block = []
                current_block_num = block_num

            # Add text if not empty
            if data["text"][i].strip():
                current_block.append(data["text"][i])

        # Add last block
        if current_block:
            blocks.append({"block_num": current_block_num, "text": " ".join(current_block)})

        logger.debug(f"Grouped text into {len(blocks)} blocks")
        return blocks

    def get_confidence_score(self, image: Union[Image.Image, str]) -> float:
        """Get OCR confidence score for an image.

        Args:
            image: PIL Image or file path

        Returns:
            Average confidence score (0-100)
        """
        try:
            if isinstance(image, str):
                image = Image.open(image)

            # Get OCR data with confidence scores
            data = pytesseract.image_to_data(
                image,
                lang=self.language,
                config=self.config,
                output_type=pytesseract.Output.DICT,
            )

            # Calculate average confidence (excluding -1 values)
            confidences = [int(conf) for conf in data["conf"] if int(conf) != -1]

            if not confidences:
                return 0.0

            avg_confidence = sum(confidences) / len(confidences)
            logger.debug(f"OCR confidence score: {avg_confidence:.2f}")
            return avg_confidence

        except Exception as e:
            logger.error(f"Error calculating confidence: {e}")
            return 0.0

    def is_tesseract_installed(self) -> bool:
        """Check if Tesseract is installed and accessible.

        Returns:
            True if Tesseract is available, False otherwise
        """
        try:
            version = pytesseract.get_tesseract_version()
            logger.info(f"Tesseract version: {version}")
            return True
        except Exception as e:
            logger.error(f"Tesseract not found: {e}")
            return False
