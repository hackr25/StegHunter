# tests/create_test_images.py
from PIL import Image
import os
from pathlib import Path

def create_test_images():
    """Create test images for Windows environment"""
    test_dir = Path("test_images")
    test_dir.mkdir(exist_ok=True)
    
    # Create various test images
    # 1. Simple PNG
    img = Image.new('RGB', (100, 100), color='red')
    img.save(test_dir / "test_red.png")
    
    # 2. JPEG with different quality
    img = Image.new('RGB', (200, 150), color='blue')
    img.save(test_dir / "test_blue.jpg", quality=95)
    
    # 3. BMP format
    img = Image.new('L', (50, 50), color=128)  # Grayscale
    img.save(test_dir / "test_gray.bmp")
    
    # 4. Transparent PNG
    img = Image.new('RGBA', (80, 80), color=(255, 0, 0, 128))
    img.save(test_dir / "test_transparent.png")
    
    print(f"Test images created in {test_dir.absolute()}")

if __name__ == '__main__':
    create_test_images()
