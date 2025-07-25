"""
Text Extraction Utility for VisuaLens
Handles OCR and text preprocessing for better document analysis
"""

import base64
import io
from typing import Dict, Any, Optional, List
from PIL import Image, ImageEnhance, ImageFilter
import logging
from pathlib import Path
import sys

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from loguru import logger

class TextExtractor:
    """Handles text extraction and image preprocessing for OCR"""
    
    def __init__(self):
        """Initialize the text extractor"""
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging for text extraction"""
        logger.info("Initialized TextExtractor")
    
    def preprocess_image_for_ocr(self, image_data: bytes) -> Image.Image:
        """
        Preprocess image to improve OCR accuracy
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            Preprocessed PIL Image
        """
        try:
            # Load image
            image = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Enhance image for better OCR
            # Increase contrast
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.5)
            
            # Increase sharpness
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(2.0)
            
            # Convert to grayscale for better text recognition
            image = image.convert('L')
            
            # Apply threshold to make text more prominent
            # Convert to binary (black and white)
            threshold = 128
            image = image.point(lambda x: 255 if x > threshold else 0, mode='1')
            
            logger.debug("Image preprocessed for OCR")
            return image
            
        except Exception as e:
            logger.error(f"Failed to preprocess image: {e}")
            # Return original image if preprocessing fails
            return Image.open(io.BytesIO(image_data))
    
    def extract_text_simple(self, image_data: bytes) -> Dict[str, Any]:
        """
        Simple text extraction without OCR - analyze image structure
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            Dictionary with text analysis results
        """
        try:
            # Preprocess image
            processed_image = self.preprocess_image_for_ocr(image_data)
            
            # Analyze image characteristics for document detection
            width, height = processed_image.size
            aspect_ratio = width / height
            
            # Basic document detection heuristics
            is_document = self._detect_document_type(processed_image)
            
            result = {
                'success': True,
                'extracted_text': '',  # We'll rely on vision model for now
                'is_document': is_document,
                'document_type': self._classify_document(processed_image),
                'preprocessing_applied': True,
                'image_characteristics': {
                    'width': width,
                    'height': height,
                    'aspect_ratio': aspect_ratio,
                    'mode': processed_image.mode
                }
            }
            
            logger.info(f"Text extraction analysis completed - Document detected: {is_document}")
            return result
            
        except Exception as e:
            logger.error(f"Text extraction failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'extracted_text': '',
                'is_document': False,
                'preprocessing_applied': False
            }
    
    def _detect_document_type(self, image: Image.Image) -> bool:
        """
        Detect if image contains a document
        
        Args:
            image: PIL Image object
            
        Returns:
            True if image appears to be a document
        """
        try:
            # Convert to numpy array for analysis
            import numpy as np
            img_array = np.array(image)
            
            # Check for text-like patterns
            # Documents typically have:
            # - High contrast areas (text)
            # - Horizontal lines (text lines)
            # - Regular spacing
            
            # Simple heuristic: check for horizontal line patterns
            height, width = img_array.shape
            
            # Sample horizontal lines to detect text patterns
            line_samples = []
            for i in range(0, height, height // 20):  # Sample 20 lines
                if i < height:
                    line = img_array[i, :]
                    # Count transitions (text creates many black-white transitions)
                    transitions = np.sum(np.diff(line.astype(int)) != 0)
                    line_samples.append(transitions)
            
            # Documents typically have many transitions due to text
            avg_transitions = np.mean(line_samples) if line_samples else 0
            
            # If average transitions per line > threshold, likely a document
            is_document = avg_transitions > (width * 0.1)  # 10% of width
            
            logger.debug(f"Document detection: avg_transitions={avg_transitions}, threshold={width * 0.1}, is_document={is_document}")
            return is_document
            
        except Exception as e:
            logger.warning(f"Document detection failed: {e}")
            return True  # Default to assuming it's a document
    
    def _classify_document(self, image: Image.Image) -> str:
        """
        Classify the type of document
        
        Args:
            image: PIL Image object
            
        Returns:
            Document type classification
        """
        try:
            width, height = image.size
            aspect_ratio = width / height
            
            # Basic classification based on dimensions and layout
            if 0.7 <= aspect_ratio <= 0.8:
                return "resume_cv"  # Typical resume format
            elif aspect_ratio > 1.2:
                return "landscape_document"
            elif aspect_ratio < 0.6:
                return "portrait_document"
            else:
                return "standard_document"
                
        except Exception:
            return "unknown"
    
    def enhance_image_for_vision(self, image_data: bytes) -> bytes:
        """
        Enhance image specifically for vision model processing
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            Enhanced image bytes
        """
        try:
            image = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Enhance for vision models
            # Increase contrast moderately
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.3)
            
            # Slight sharpness boost
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.2)
            
            # Resize if too large (vision models have limits)
            max_size = 1024
            if max(image.size) > max_size:
                ratio = max_size / max(image.size)
                new_size = tuple(int(dim * ratio) for dim in image.size)
                image = image.resize(new_size, Image.Resampling.LANCZOS)
            
            # Convert back to bytes
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=95)
            enhanced_data = output.getvalue()
            
            logger.debug(f"Image enhanced for vision model - Original: {len(image_data)} bytes, Enhanced: {len(enhanced_data)} bytes")
            return enhanced_data
            
        except Exception as e:
            logger.error(f"Image enhancement failed: {e}")
            return image_data  # Return original if enhancement fails


# Global instance
text_extractor = TextExtractor()
