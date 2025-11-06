"""Image processor for the Answer Sheet Marker system.

This module handles image processing operations including enhancement,
format conversion, and preparation for OCR.
"""

from pathlib import Path
from typing import Union, Tuple
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np
from loguru import logger


class ImageProcessor:
    """Process and enhance images for better OCR results.

    Provides various image processing operations to improve text recognition
    quality from scanned documents and photos.
    """

    @staticmethod
    def load_image(image_path: Union[str, Path]) -> Image.Image:
        """Load image from file.

        Args:
            image_path: Path to image file

        Returns:
            PIL Image object

        Raises:
            FileNotFoundError: If image file doesn't exist
            Exception: If image cannot be loaded
        """
        image_path = Path(image_path)

        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        try:
            logger.debug(f"Loading image: {image_path}")
            image = Image.open(image_path)
            return image
        except Exception as e:
            logger.error(f"Error loading image {image_path}: {e}")
            raise

    @staticmethod
    def save_image(image: Image.Image, output_path: Union[str, Path], quality: int = 95):
        """Save image to file.

        Args:
            image: PIL Image to save
            output_path: Output file path
            quality: JPEG quality (1-95), ignored for PNG
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            logger.debug(f"Saving image to: {output_path}")
            if output_path.suffix.lower() in [".jpg", ".jpeg"]:
                image.save(output_path, "JPEG", quality=quality)
            else:
                image.save(output_path)
        except Exception as e:
            logger.error(f"Error saving image: {e}")
            raise

    @staticmethod
    def to_grayscale(image: Image.Image) -> Image.Image:
        """Convert image to grayscale.

        Args:
            image: PIL Image

        Returns:
            Grayscale PIL Image
        """
        if image.mode == "L":
            return image
        logger.debug("Converting to grayscale")
        return image.convert("L")

    @staticmethod
    def enhance_contrast(
        image: Image.Image, factor: float = 2.0
    ) -> Image.Image:
        """Enhance image contrast.

        Args:
            image: PIL Image
            factor: Enhancement factor (1.0 = original, >1.0 = more contrast)

        Returns:
            Enhanced PIL Image
        """
        logger.debug(f"Enhancing contrast by factor {factor}")
        enhancer = ImageEnhance.Contrast(image)
        return enhancer.enhance(factor)

    @staticmethod
    def enhance_sharpness(
        image: Image.Image, factor: float = 2.0
    ) -> Image.Image:
        """Enhance image sharpness.

        Args:
            image: PIL Image
            factor: Enhancement factor (1.0 = original, >1.0 = sharper)

        Returns:
            Enhanced PIL Image
        """
        logger.debug(f"Enhancing sharpness by factor {factor}")
        enhancer = ImageEnhance.Sharpness(image)
        return enhancer.enhance(factor)

    @staticmethod
    def enhance_brightness(
        image: Image.Image, factor: float = 1.2
    ) -> Image.Image:
        """Enhance image brightness.

        Args:
            image: PIL Image
            factor: Enhancement factor (1.0 = original, >1.0 = brighter)

        Returns:
            Enhanced PIL Image
        """
        logger.debug(f"Enhancing brightness by factor {factor}")
        enhancer = ImageEnhance.Brightness(image)
        return enhancer.enhance(factor)

    @staticmethod
    def denoise(image: Image.Image) -> Image.Image:
        """Apply denoising filter to image.

        Args:
            image: PIL Image

        Returns:
            Denoised PIL Image
        """
        logger.debug("Applying denoise filter")
        return image.filter(ImageFilter.MedianFilter(size=3))

    @staticmethod
    def resize(
        image: Image.Image, scale: float = None, width: int = None, height: int = None
    ) -> Image.Image:
        """Resize image.

        Args:
            image: PIL Image
            scale: Scale factor (e.g., 0.5 for half size, 2.0 for double)
            width: Target width (maintains aspect ratio if height not provided)
            height: Target height (maintains aspect ratio if width not provided)

        Returns:
            Resized PIL Image
        """
        if scale:
            new_width = int(image.width * scale)
            new_height = int(image.height * scale)
        elif width and not height:
            new_width = width
            new_height = int(image.height * (width / image.width))
        elif height and not width:
            new_height = height
            new_width = int(image.width * (height / image.height))
        elif width and height:
            new_width = width
            new_height = height
        else:
            raise ValueError("Must provide scale, width, height, or both width and height")

        logger.debug(f"Resizing image from {image.size} to ({new_width}, {new_height})")
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    @staticmethod
    def rotate(image: Image.Image, angle: float, expand: bool = True) -> Image.Image:
        """Rotate image.

        Args:
            image: PIL Image
            angle: Rotation angle in degrees (counter-clockwise)
            expand: If True, expand output to fit entire rotated image

        Returns:
            Rotated PIL Image
        """
        logger.debug(f"Rotating image by {angle} degrees")
        return image.rotate(angle, expand=expand, fillcolor="white")

    @staticmethod
    def crop(
        image: Image.Image, left: int, top: int, right: int, bottom: int
    ) -> Image.Image:
        """Crop image to specified region.

        Args:
            image: PIL Image
            left: Left coordinate
            top: Top coordinate
            right: Right coordinate
            bottom: Bottom coordinate

        Returns:
            Cropped PIL Image
        """
        logger.debug(f"Cropping image to region ({left}, {top}, {right}, {bottom})")
        return image.crop((left, top, right, bottom))

    @staticmethod
    def auto_crop(image: Image.Image, border_color: Tuple[int, int, int] = (255, 255, 255)) -> Image.Image:
        """Automatically crop white borders from image.

        Args:
            image: PIL Image
            border_color: RGB color to remove (default: white)

        Returns:
            Auto-cropped PIL Image
        """
        logger.debug("Auto-cropping image borders")

        # Convert to RGB if needed
        if image.mode != "RGB":
            image = image.convert("RGB")

        # Get image as numpy array
        img_array = np.array(image)

        # Find non-border pixels
        mask = np.any(img_array != border_color, axis=-1)
        rows = np.any(mask, axis=1)
        cols = np.any(mask, axis=0)

        if not rows.any() or not cols.any():
            # No content found, return original
            return image

        # Find bounding box
        top = rows.argmax()
        bottom = len(rows) - rows[::-1].argmax()
        left = cols.argmax()
        right = len(cols) - cols[::-1].argmax()

        return image.crop((left, top, right, bottom))

    @staticmethod
    def binarize(image: Image.Image, threshold: int = 128) -> Image.Image:
        """Convert image to binary (black and white).

        Args:
            image: PIL Image
            threshold: Threshold value (0-255)

        Returns:
            Binary PIL Image
        """
        logger.debug(f"Binarizing image with threshold {threshold}")

        # Convert to grayscale first
        if image.mode != "L":
            image = image.convert("L")

        # Apply threshold
        return image.point(lambda x: 0 if x < threshold else 255, "1")

    @staticmethod
    def get_dimensions(image: Image.Image) -> Tuple[int, int]:
        """Get image dimensions.

        Args:
            image: PIL Image

        Returns:
            Tuple of (width, height)
        """
        return image.size

    @staticmethod
    def get_format(image: Image.Image) -> str:
        """Get image format.

        Args:
            image: PIL Image

        Returns:
            Format string (e.g., 'JPEG', 'PNG')
        """
        return image.format or "Unknown"

    @staticmethod
    def prepare_for_ocr(image: Image.Image) -> Image.Image:
        """Apply full preprocessing pipeline for OCR.

        Args:
            image: PIL Image

        Returns:
            Preprocessed PIL Image ready for OCR
        """
        logger.info("Preparing image for OCR")

        # Convert to grayscale
        image = ImageProcessor.to_grayscale(image)

        # Enhance contrast
        image = ImageProcessor.enhance_contrast(image, factor=2.0)

        # Enhance sharpness
        image = ImageProcessor.enhance_sharpness(image, factor=1.5)

        # Denoise
        image = ImageProcessor.denoise(image)

        return image
