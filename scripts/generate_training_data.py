"""
Generate training data for ML model
Creates stego images using LSB embedding
"""
import os
import sys
from pathlib import Path
from PIL import Image
import numpy as np
import random
from typing import List

class TrainingDataGenerator:
    """Generate synthetic stego images for training"""
    
    def __init__(self):
        pass
    
    def generate_lsb_stego(self, image_path: str, output_path: str, 
                          embedding_rate: float = 1.0) -> bool:
        """
        Generate LSB stego image by embedding random data
        Args:
            image_path: Path to clean image
            output_path: Path to save stego image
            embedding_rate: Fraction of pixels to embed in (0.0 to 1.0)
        """
        try:
            # Load image
            image = Image.open(image_path)
            img_array = np.array(image, dtype=np.uint8)
            
            # Generate random message bits
            h, w = img_array.shape[:2]
            total_pixels = h * w * len(img_array.shape) if len(img_array.shape) == 3 else h * w
            message_length = int(total_pixels * embedding_rate)
            
            # Generate random bits
            message_bits = np.random.randint(0, 2, message_length)
            
            # Embed using LSB substitution (FIXED)
            idx = 0
            for i in range(h):
                for j in range(w):
                    if len(img_array.shape) == 3:
                        for channel in range(img_array.shape[2]):
                            if idx < len(message_bits):
                                # Clear LSB using 254 (0xFE) instead of ~1
                                # Then set LSB using message bit
                                pixel_value = img_array[i, j, channel]
                                pixel_value = (pixel_value & 0xFE) | message_bits[idx]
                                img_array[i, j, channel] = pixel_value
                                idx += 1
                    else:
                        if idx < len(message_bits):
                            # Clear LSB using 254 (0xFE) instead of ~1
                            # Then set LSB using message bit
                            pixel_value = img_array[i, j]
                            pixel_value = (pixel_value & 0xFE) | message_bits[idx]
                            img_array[i, j] = pixel_value
                            idx += 1
            
            # Save stego image
            stego_image = Image.fromarray(img_array)
            stego_image.save(output_path)
            return True
            
        except Exception as e:
            print(f"Error generating stego image: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def generate_dataset(self, clean_dir: str, stego_dir: str, 
                        num_samples: int = 100, embedding_rate: float = 1.0):
        """
        Generate training dataset
        Args:
            clean_dir: Directory containing clean images
            stego_dir: Directory to save stego images
            num_samples: Number of stego images to generate
            embedding_rate: Embedding rate for stego images
        """
        clean_path = Path(clean_dir)
        stego_path = Path(stego_dir)
        stego_path.mkdir(parents=True, exist_ok=True)
        
        # Get clean images
        supported = {'.jpg', '.jpeg', '.png', '.bmp'}
        clean_images = [p for p in clean_path.rglob('*') if p.is_file() and p.suffix.lower() in supported]
        
        if len(clean_images) == 0:
            print(f"No images found in {clean_dir}")
            return
        
        print(f"Found {len(clean_images)} clean images")
        print(f"Generating {num_samples} stego images...")
        
        generated = 0
        for i in range(num_samples):
            # Randomly select clean image
            clean_img = random.choice(clean_images)
            
            # Generate output path
            output_name = f"stego_{i:04d}_{clean_img.stem}{clean_img.suffix}"
            output_path = stego_path / output_name
            
            # Generate stego image
            success = self.generate_lsb_stego(str(clean_img), str(output_path), embedding_rate)
            
            if success:
                generated += 1
                if generated % 10 == 0:
                    print(f"Generated {generated}/{num_samples} stego images")
        
        print(f"✅ Successfully generated {generated}/{num_samples} stego images")

def main():
    """Main function for CLI usage"""
    if len(sys.argv) < 3:
        print("Usage: python generate_training_data.py <clean_dir> <stego_dir> [num_samples] [embedding_rate]")
        print("Example: python generate_training_data.py clean_images stego_images 100 1.0")
        sys.exit(1)
    
    clean_dir = sys.argv[1]
    stego_dir = sys.argv[2]
    num_samples = int(sys.argv[3]) if len(sys.argv) > 3 else 100
    embedding_rate = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0
    
    generator = TrainingDataGenerator()
    generator.generate_dataset(clean_dir, stego_dir, num_samples, embedding_rate)

if __name__ == '__main__':
    main()
