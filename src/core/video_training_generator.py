"""
Video Training Data Generator for ML Models
Generates training data from both images and videos with steganographic embedding.
Supports frame extraction and temporal stego creation.
"""

import os
import cv2
import numpy as np
from pathlib import Path
from PIL import Image
import random
from typing import List, Tuple, Optional
import tempfile


class VideoTrainingDataGenerator:
    """Generate training data from videos and images with LSB steganography"""
    
    def __init__(self):
        self.supported_image_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
        self.supported_video_formats = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv'}
    
    def generate_lsb_stego_image(self, image_array: np.ndarray, 
                                  embedding_rate: float = 1.0) -> np.ndarray:
        """
        Generate LSB stego for image array
        
        Args:
            image_array: Input image as numpy array
            embedding_rate: Fraction of pixels to embed (0.0 to 1.0)
            
        Returns:
            np.ndarray: Stego image array
        """
        img = image_array.copy()
        h, w = img.shape[:2]
        
        total_channels = img.shape[2] if len(img.shape) == 3 else 1
        total_pixels = h * w * total_channels
        message_length = int(total_pixels * embedding_rate)
        
        # Generate random message bits
        message_bits = np.random.randint(0, 2, message_length)
        
        # Embed using LSB substitution
        idx = 0
        for i in range(h):
            for j in range(w):
                if len(img.shape) == 3:
                    for channel in range(img.shape[2]):
                        if idx < len(message_bits):
                            pixel_value = img[i, j, channel]
                            pixel_value = (pixel_value & 0xFE) | message_bits[idx]
                            img[i, j, channel] = pixel_value
                            idx += 1
                else:
                    if idx < len(message_bits):
                        pixel_value = img[i, j]
                        pixel_value = (pixel_value & 0xFE) | message_bits[idx]
                        img[i, j] = pixel_value
                        idx += 1
        
        return img
    
    def extract_frames_from_video(self, video_path: str, 
                                   output_dir: str,
                                   frame_interval: int = 1,
                                   max_frames: Optional[int] = None) -> int:
        """
        Extract frames from video file
        
        Args:
            video_path: Path to video file
            output_dir: Directory to save extracted frames
            frame_interval: Extract every Nth frame (1=all frames)
            max_frames: Maximum frames to extract (None=all)
            
        Returns:
            int: Number of frames extracted
        """
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                print(f"❌ Cannot open video: {video_path}")
                return 0
            
            frame_count = 0
            extracted = 0
            video_name = Path(video_path).stem
            
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                if frame_count % frame_interval == 0:
                    if max_frames and extracted >= max_frames:
                        break
                    
                    # Save frame as image
                    frame_path = os.path.join(
                        output_dir,
                        f"{video_name}_frame_{extracted:06d}.png"
                    )
                    cv2.imwrite(frame_path, frame)
                    extracted += 1
                
                frame_count += 1
            
            cap.release()
            return extracted
        
        except Exception as e:
            print(f"❌ Error extracting frames: {e}")
            return 0
    
    def generate_stego_video(self, video_path: str,
                            output_path: str,
                            embedding_rate: float = 1.0) -> bool:
        """
        Create stego video by embedding LSB in all frames
        
        Args:
            video_path: Path to clean video
            output_path: Path to save stego video
            embedding_rate: Embedding rate for LSB (0.0-1.0)
            
        Returns:
            bool: True if successful
        """
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                print(f"❌ Cannot open video: {video_path}")
                return False
            
            # Get video properties
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            
            # Create output video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            frame_count = 0
            processed = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Apply LSB steganography
                stego_frame = self.generate_lsb_stego_image(frame, embedding_rate)
                
                # Write stego frame to output video
                out.write(stego_frame.astype(np.uint8))
                processed += 1
                frame_count += 1
                
                if frame_count % 30 == 0:
                    print(f"  Processed {processed} frames...")
            
            cap.release()
            out.release()
            
            print(f"✅ Stego video created: {output_path} ({processed} frames)")
            return True
        
        except Exception as e:
            print(f"❌ Error generating stego video: {e}")
            return False
    
    def generate_mixed_dataset(self, clean_image_dir: str,
                              stego_image_dir: str,
                              clean_video_dir: Optional[str] = None,
                              stego_video_dir: Optional[str] = None,
                              output_image_dir: str = None,
                              num_image_samples: int = 100,
                              num_video_samples: int = 50,
                              embedding_rate: float = 1.0,
                              frames_per_video: int = 10) -> dict:
        """
        Generate training dataset from both images and videos
        
        Args:
            clean_image_dir: Directory with clean images
            stego_image_dir: Directory with stego images
            clean_video_dir: Directory with clean videos (optional)
            stego_video_dir: Directory with stego videos (optional)
            output_image_dir: Directory to save extracted frames from videos
            num_image_samples: Number of image samples to use
            num_video_samples: Number of videos to process
            embedding_rate: LSB embedding rate
            frames_per_video: Frames to extract per video
            
        Returns:
            dict: Summary of generated training data
        """
        stats = {
            'images_clean': 0,
            'images_stego': 0,
            'videos_clean': 0,
            'videos_stego': 0,
            'frames_extracted': 0,
            'stego_videos_created': 0
        }
        
        # Process images (existing approach)
        print("\n📸 Processing Images...")
        clean_images = [p for p in Path(clean_image_dir).rglob('*') 
                       if p.suffix.lower() in self.supported_image_formats]
        stego_images = [p for p in Path(stego_image_dir).rglob('*') 
                       if p.suffix.lower() in self.supported_image_formats]
        
        stats['images_clean'] = min(len(clean_images), num_image_samples)
        stats['images_stego'] = min(len(stego_images), num_image_samples)
        print(f"  ✓ {stats['images_clean']} clean images")
        print(f"  ✓ {stats['images_stego']} stego images")
        
        # Process videos if directories provided
        if clean_video_dir or stego_video_dir:
            if output_image_dir is None:
                output_image_dir = os.path.join(Path(clean_image_dir).parent, "video_frames")
            
            print("\n🎬 Processing Videos...")
            
            # Extract frames from clean videos
            if clean_video_dir and os.path.exists(clean_video_dir):
                clean_videos = [p for p in Path(clean_video_dir).rglob('*') 
                              if p.suffix.lower() in self.supported_video_formats]
                
                clean_frames_dir = os.path.join(output_image_dir, "clean_frames")
                
                for video in clean_videos[:num_video_samples]:
                    print(f"  Extracting frames from: {video.name}")
                    frames = self.extract_frames_from_video(
                        str(video),
                        clean_frames_dir,
                        frame_interval=1,
                        max_frames=frames_per_video
                    )
                    stats['frames_extracted'] += frames
                    stats['videos_clean'] += 1
            
            # Extract frames from stego videos or create them
            if stego_video_dir and os.path.exists(stego_video_dir):
                stego_videos = [p for p in Path(stego_video_dir).rglob('*') 
                              if p.suffix.lower() in self.supported_video_formats]
                
                stego_frames_dir = os.path.join(output_image_dir, "stego_frames")
                
                for video in stego_videos[:num_video_samples]:
                    print(f"  Extracting frames from: {video.name}")
                    frames = self.extract_frames_from_video(
                        str(video),
                        stego_frames_dir,
                        frame_interval=1,
                        max_frames=frames_per_video
                    )
                    stats['frames_extracted'] += frames
                    stats['videos_stego'] += 1
            
            # Create stego videos from clean videos
            if clean_video_dir and os.path.exists(clean_video_dir):
                clean_videos = [p for p in Path(clean_video_dir).rglob('*') 
                              if p.suffix.lower() in self.supported_video_formats]
                
                stego_output_dir = os.path.join(
                    Path(clean_video_dir).parent,
                    "stego_videos_generated"
                )
                Path(stego_output_dir).mkdir(parents=True, exist_ok=True)
                
                for video in clean_videos[:min(num_video_samples // 2, 5)]:
                    print(f"  Creating stego video from: {video.name}")
                    output_path = os.path.join(stego_output_dir, f"stego_{video.name}")
                    success = self.generate_stego_video(
                        str(video),
                        output_path,
                        embedding_rate
                    )
                    if success:
                        stats['stego_videos_created'] += 1
        
        return stats
    
    def generate_training_dataset(self, clean_dir: str, stego_dir: str, 
                                 num_samples: int = 100,
                                 embedding_rate: float = 1.0):
        """
        Generate training dataset (backward compatible with image-only approach)
        
        Args:
            clean_dir: Directory with clean images
            stego_dir: Directory to save stego images
            num_samples: Number of samples to generate
            embedding_rate: LSB embedding rate
        """
        clean_path = Path(clean_dir)
        stego_path = Path(stego_dir)
        stego_path.mkdir(parents=True, exist_ok=True)
        
        # Get clean images
        clean_images = [p for p in clean_path.rglob('*') 
                       if p.suffix.lower() in self.supported_image_formats]
        
        if len(clean_images) == 0:
            print(f"No images found in {clean_dir}")
            return
        
        print(f"Found {len(clean_images)} clean images")
        print(f"Generating {num_samples} stego images...")
        
        generated = 0
        for i in range(num_samples):
            clean_img = random.choice(clean_images)
            
            try:
                image = Image.open(clean_img)
                img_array = np.array(image, dtype=np.uint8)
                
                # Generate stego
                stego_array = self.generate_lsb_stego_image(img_array, embedding_rate)
                stego_image = Image.fromarray(stego_array)
                
                # Save
                output_name = f"stego_{i:04d}_{clean_img.stem}{clean_img.suffix}"
                output_path = stego_path / output_name
                stego_image.save(output_path)
                
                generated += 1
                if generated % 10 == 0:
                    print(f"  Generated {generated}/{num_samples}")
            
            except Exception as e:
                print(f"  ⚠️  Error processing {clean_img}: {e}")
        
        print(f"✅ Generated {generated}/{num_samples} stego images")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python video_training_generator.py <clean_dir> <stego_dir> [num_samples] [embedding_rate]")
        print("       python video_training_generator.py --video <clean_video_dir> <stego_video_dir>")
        sys.exit(1)
    
    generator = VideoTrainingDataGenerator()
    
    if sys.argv[1] == '--video':
        # Video mode
        clean_dir = sys.argv[2]
        stego_dir = sys.argv[3] if len(sys.argv) > 3 else None
        
        stats = generator.generate_mixed_dataset(
            clean_image_dir=clean_dir,
            stego_image_dir=stego_dir or clean_dir,
            clean_video_dir=clean_dir,
            stego_video_dir=stego_dir,
            num_video_samples=10,
            frames_per_video=15
        )
        
        print("\n" + "="*50)
        print("TRAINING DATA GENERATION SUMMARY")
        print("="*50)
        for key, val in stats.items():
            print(f"  {key}: {val}")
    else:
        # Image mode (backward compatible)
        clean_dir = sys.argv[1]
        stego_dir = sys.argv[2]
        num_samples = int(sys.argv[3]) if len(sys.argv) > 3 else 100
        embedding_rate = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0
        
        generator.generate_training_dataset(clean_dir, stego_dir, num_samples, embedding_rate)
