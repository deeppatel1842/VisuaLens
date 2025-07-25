"""
Image Processing Pipeline for VisuaLens
Handles image validation, resize, optimization, and format conversion
"""

import io
import base64
import time
from typing import Dict, Any, Tuple, Optional
from pathlib import Path
import sys

# Image processing imports
from PIL import Image, ImageOps, ExifTags
import hashlib

# Logging
from loguru import logger

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from config.settings import settings
from src.models.schemas import ImageProcessingInfo


class ImageProcessor:
    """Image processing utilities for VisuaLens"""
    
    SUPPORTED_FORMATS = ['JPEG', 'PNG', 'WebP', 'JPG']
    MAX_DIMENSION = 1024
    QUALITY = 85
    
    def __init__(self):
        self.max_dimension = getattr(settings, 'max_image_dimension', self.MAX_DIMENSION)
        self.quality = getattr(settings, 'image_quality', self.QUALITY)
        logger.info(f"ImageProcessor initialized (max_dim: {self.max_dimension}, quality: {self.quality})")
    
    def validate_image(self, image_data: bytes, filename: str, content_type: str) -> Tuple[bool, str]:
        """
        Validate image data and metadata
        
        Args:
            image_data: Raw image bytes
            filename: Original filename
            content_type: MIME type
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check if data can be opened as image
            img = Image.open(io.BytesIO(image_data))
            
            # Verify format
            if img.format not in self.SUPPORTED_FORMATS:
                return False, f"Unsupported format: {img.format}. Supported: {self.SUPPORTED_FORMATS}"
            
            # Check dimensions
            width, height = img.size
            if width < 32 or height < 32:
                return False, f"Image too small: {width}x{height}. Minimum: 32x32"
            
            if width > 8192 or height > 8192:
                return False, f"Image too large: {width}x{height}. Maximum: 8192x8192"
            
            # Check for corrupted image
            img.verify()
            
            return True, "Valid image"
            
        except Exception as e:
            return False, f"Invalid image data: {str(e)}"
    
    def fix_image_orientation(self, img: Image.Image) -> Image.Image:
        """
        Fix image orientation based on EXIF data
        
        Args:
            img: PIL Image object
            
        Returns:
            Image with corrected orientation
        """
        try:
            # Get EXIF data
            exif = img._getexif()
            if exif is not None:
                # Find orientation tag
                for tag, value in exif.items():
                    if tag in ExifTags.TAGS and ExifTags.TAGS[tag] == 'Orientation':
                        # Rotate based on orientation
                        if value == 3:
                            img = img.rotate(180, expand=True)
                        elif value == 6:
                            img = img.rotate(270, expand=True)
                        elif value == 8:
                            img = img.rotate(90, expand=True)
                        break
        except (AttributeError, KeyError, TypeError):
            # No EXIF data or orientation info
            pass
        
        return img
    
    def resize_image(self, img: Image.Image, max_dimension: int = None) -> Image.Image:
        """
        Resize image while maintaining aspect ratio
        
        Args:
            img: PIL Image object
            max_dimension: Maximum width or height
            
        Returns:
            Resized image
        """
        max_dim = max_dimension or self.max_dimension
        width, height = img.size
        
        # Check if resize is needed
        if width <= max_dim and height <= max_dim:
            return img
        
        # Calculate new dimensions
        if width > height:
            new_width = max_dim
            new_height = int((height * max_dim) / width)
        else:
            new_height = max_dim
            new_width = int((width * max_dim) / height)
        
        # Resize with high-quality resampling
        resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        logger.debug(f"Resized image from {width}x{height} to {new_width}x{new_height}")
        return resized
    
    def optimize_image(self, img: Image.Image, format: str = 'JPEG') -> Image.Image:
        """
        Optimize image for web usage
        
        Args:
            img: PIL Image object
            format: Target format
            
        Returns:
            Optimized image
        """
        # Convert to RGB if necessary (for JPEG)
        if format.upper() == 'JPEG' and img.mode in ('RGBA', 'LA', 'P'):
            # Create white background for transparent images
            bg = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            bg.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = bg
        elif format.upper() == 'PNG' and img.mode not in ('RGBA', 'LA', 'P'):
            img = img.convert('RGBA')
        
        return img
    
    def encode_to_base64(self, img: Image.Image, format: str = 'JPEG') -> str:
        """
        Encode image to base64 string
        
        Args:
            img: PIL Image object
            format: Image format
            
        Returns:
            Base64 encoded string
        """
        buffer = io.BytesIO()
        
        save_kwargs = {}
        if format.upper() == 'JPEG':
            save_kwargs = {
                'quality': self.quality,
                'optimize': True,
                'progressive': True
            }
        elif format.upper() == 'PNG':
            save_kwargs = {
                'optimize': True,
                'compress_level': 6
            }
        
        img.save(buffer, format=format.upper(), **save_kwargs)
        
        encoded = base64.b64encode(buffer.getvalue()).decode('utf-8')
        return encoded
    
    def get_image_hash(self, image_data: bytes) -> str:
        """
        Generate hash for image data (for deduplication)
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            SHA256 hash string
        """
        return hashlib.sha256(image_data).hexdigest()
    
    def process_image(
        self,
        image_data: bytes,
        filename: str,
        content_type: str,
        target_format: str = 'JPEG',
        max_dimension: int = None
    ) -> Dict[str, Any]:
        """
        Complete image processing pipeline
        
        Args:
            image_data: Raw image bytes
            filename: Original filename
            content_type: MIME type
            target_format: Target format for output
            max_dimension: Maximum dimension for resize
            
        Returns:
            Processing result dictionary
        """
        start_time = time.time()
        
        try:
            # Validate image
            is_valid, validation_msg = self.validate_image(image_data, filename, content_type)
            if not is_valid:
                return {
                    'success': False,
                    'error': 'Image validation failed',
                    'details': validation_msg
                }
            
            # Open and get original info
            original_img = Image.open(io.BytesIO(image_data))
            original_size = len(image_data)
            original_dimensions = original_img.size
            original_format = original_img.format
            
            logger.debug(f"Processing image: {original_dimensions} {original_format} ({original_size} bytes)")
            
            # Fix orientation
            img = self.fix_image_orientation(original_img)
            
            # Resize if needed
            img = self.resize_image(img, max_dimension)
            
            # Optimize for target format
            img = self.optimize_image(img, target_format)
            
            # Convert to bytes
            buffer = io.BytesIO()
            save_kwargs = {}
            if target_format.upper() == 'JPEG':
                save_kwargs = {
                    'quality': self.quality,
                    'optimize': True,
                    'progressive': True
                }
            elif target_format.upper() == 'PNG':
                save_kwargs = {
                    'optimize': True,
                    'compress_level': 6
                }
            
            img.save(buffer, format=target_format.upper(), **save_kwargs)
            processed_data = buffer.getvalue()
            
            # Encode to base64
            base64_encoded = self.encode_to_base64(img, target_format)
            
            # Calculate processing info
            processed_size = len(processed_data)
            processed_dimensions = img.size
            processing_time = time.time() - start_time
            
            # Generate hash
            image_hash = self.get_image_hash(processed_data)
            
            processing_info = ImageProcessingInfo(
                original_size=original_size,
                processed_size=processed_size,
                original_dimensions=original_dimensions,
                processed_dimensions=processed_dimensions,
                format=target_format.upper(),
                processing_time=processing_time
            )
            
            logger.info(f"Image processed successfully in {processing_time:.2f}s")
            logger.debug(f"Size: {original_size} -> {processed_size} bytes")
            logger.debug(f"Dimensions: {original_dimensions} -> {processed_dimensions}")
            
            return {
                'success': True,
                'processed_data': processed_data,
                'base64_encoded': base64_encoded,
                'processing_info': processing_info,
                'image_hash': image_hash,
                'filename': f"processed_{int(time.time())}.{target_format.lower()}"
            }
            
        except Exception as e:
            logger.error(f"Image processing failed: {e}")
            return {
                'success': False,
                'error': 'Image processing failed',
                'details': str(e)
            }


# Global processor instance
processor = ImageProcessor()


async def process_uploaded_image(
    image_data: bytes,
    filename: str,
    content_type: str,
    image_id: str,
    target_format: str = 'JPEG'
) -> Dict[str, Any]:
    """
    Process uploaded image (async wrapper)
    
    Args:
        image_data: Raw image bytes
        filename: Original filename
        content_type: MIME type
        image_id: Unique image identifier
        target_format: Target format for processing
        
    Returns:
        Processing result dictionary
    """
    try:
        # Process the image
        result = processor.process_image(
            image_data=image_data,
            filename=filename,
            content_type=content_type,
            target_format=target_format
        )
        
        if result['success']:
            # Store processed image temporarily (in a real app, you might use Redis, database, etc.)
            temp_storage_path = Path(settings.temp_dir) / f"{image_id}.{target_format.lower()}"
            temp_storage_path.parent.mkdir(exist_ok=True)
            
            with open(temp_storage_path, 'wb') as f:
                f.write(result['processed_data'])
            
            logger.info(f"Stored processed image: {temp_storage_path}")
            
            # Add storage info to result
            result['storage_path'] = str(temp_storage_path)
            result['image_id'] = image_id
        
        return result
        
    except Exception as e:
        logger.error(f"Image upload processing failed: {e}")
        return {
            'success': False,
            'error': 'Upload processing failed',
            'details': str(e)
        }


def get_processed_image(image_id: str) -> Optional[bytes]:
    """
    Retrieve processed image data by ID
    
    Args:
        image_id: Image identifier
        
    Returns:
        Image data or None if not found
    """
    try:
        # Look for the image in temp storage
        for ext in ['jpg', 'jpeg', 'png', 'webp']:
            temp_path = Path(settings.temp_dir) / f"{image_id}.{ext}"
            if temp_path.exists():
                with open(temp_path, 'rb') as f:
                    return f.read()
        
        logger.warning(f"Processed image not found: {image_id}")
        return None
        
    except Exception as e:
        logger.error(f"Failed to retrieve processed image {image_id}: {e}")
        return None


def cleanup_processed_image(image_id: str) -> bool:
    """
    Clean up processed image files
    
    Args:
        image_id: Image identifier
        
    Returns:
        True if cleanup successful
    """
    try:
        cleaned = False
        for ext in ['jpg', 'jpeg', 'png', 'webp']:
            temp_path = Path(settings.temp_dir) / f"{image_id}.{ext}"
            if temp_path.exists():
                temp_path.unlink()
                cleaned = True
                logger.debug(f"Cleaned up: {temp_path}")
        
        return cleaned
        
    except Exception as e:
        logger.error(f"Failed to cleanup image {image_id}: {e}")
        return False


# Utility functions for testing
def create_test_image(width: int = 100, height: int = 100, color: str = 'red') -> bytes:
    """Create a test image for development/testing"""
    img = Image.new('RGB', (width, height), color)
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=85)
    return buffer.getvalue()


if __name__ == "__main__":
    # Test the image processor
    print("Testing ImageProcessor...")
    
    # Create test image
    test_data = create_test_image(800, 600, 'blue')
    print(f"Created test image: {len(test_data)} bytes")
    
    # Process test image
    result = processor.process_image(
        image_data=test_data,
        filename="test.jpg",
        content_type="image/jpeg"
    )
    
    if result['success']:
        print("Image processing successful")
        print(f"Original size: {result['processing_info'].original_size}")
        print(f"Processed size: {result['processing_info'].processed_size}")
        print(f"Dimensions: {result['processing_info'].original_dimensions} -> {result['processing_info'].processed_dimensions}")
        print(f"Processing time: {result['processing_info'].processing_time:.2f}s")
    else:
        print(f"Processing failed: {result['error']}")
        print(f"Details: {result['details']}")
