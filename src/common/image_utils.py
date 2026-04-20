"""
Common image utility functions for StegHunter
"""

from PIL import Image
from pathlib import Path
from typing import Optional, Dict, Any
from .constants import SUPPORTED_FORMATS
from .exceptions import InvalidImageError


def validate_image_path(image_path: str) -> Path:
    """Validate that the path exists and is a supported image format.
    
    Args:
        image_path: Path to image file
        
    Returns:
        Validated Path object
        
    Raises:
        InvalidImageError: If file doesn't exist or format not supported
    """
    path = Path(image_path)
    
    if not path.exists():
        raise InvalidImageError(f"Image file not found: {image_path}")
    
    if not path.is_file():
        raise InvalidImageError(f"Path is not a file: {image_path}")
    
    if path.suffix.lower() not in SUPPORTED_FORMATS:
        raise InvalidImageError(
            f"Unsupported image format: {path.suffix}. "
            f"Supported: {', '.join(sorted(SUPPORTED_FORMATS))}"
        )
    
    return path


def get_image_info(image_path: str) -> Dict[str, Any]:
    """Get basic information about an image file.
    
    Args:
        image_path: Path to image file
        
    Returns:
        Dictionary with image metadata
        
    Raises:
        InvalidImageError: If image cannot be opened or analyzed
    """
    path = validate_image_path(image_path)
    
    try:
        with Image.open(path) as img:
            info = {
                'Filename': path.name,
                'Full Path': str(path.resolve()),
                'File Size': f"{path.stat().st_size} bytes",
                'Format': img.format,
                'Dimensions': f"{img.width} x {img.height}",
                'Mode': img.mode,
                'Supported': 'Yes'
            }
    except Exception as e:
        raise InvalidImageError(f"Failed to open image file {image_path}: {e}")
    
    return info


def load_image(image_path: str) -> Image.Image:
    """Load an image and return PIL Image object.
    
    Args:
        image_path: Path to image file
        
    Returns:
        PIL Image object
        
    Raises:
        InvalidImageError: If image cannot be loaded
    """
    path = validate_image_path(image_path)
    try:
        return Image.open(path)
    except Exception as e:
        raise InvalidImageError(f"Failed to load image {image_path}: {e}")
