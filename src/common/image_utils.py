"""
Common image utility functions for StegHunter
"""

from PIL import Image
from pathlib import Path

SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}

def validate_image_path(image_path):
    """Validate that the path exists and is a supported image format"""
    path = Path(image_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")
    
    if path.suffix.lower() not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported image format: {path.suffix}. Supported: {SUPPORTED_FORMATS}")
    
    return path

def get_image_info(image_path):
    """Get basic information about an image file"""
    path = validate_image_path(image_path)
    
    with Image.open(path) as img:
        info = {
            'Filename': path.name,
            'Full Path': str(path.resolve()),
            'File Size': f"{path.stat().st_size} bytes",
            'Format': img.format,
            'Dimensions': f"{img.width} x {img.height}",
            'Mode': img.mode,
            'Supported': 'Yes' if path.suffix.lower() in SUPPORTED_FORMATS else 'No'
        }
    
    return info

def load_image(image_path):
    """Load an image and return PIL Image object"""
    path = validate_image_path(image_path)
    return Image.open(path)
