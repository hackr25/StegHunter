"""
Video heatmap generation - frame-by-frame LSB entropy visualization.
"""
from pathlib import Path
from typing import List, Optional
import numpy as np
from PIL import Image, ImageDraw, ImageFont


class VideoHeatmapGenerator:
    """Generate heatmap visualization of LSB entropy over video frames."""
    
    def __init__(self, width: int = 1200, height: int = 300):
        """
        Initialize heatmap generator.
        
        Args:
            width: Heatmap image width in pixels
            height: Heatmap image height in pixels
        """
        self.width = width
        self.height = height
    
    def generate(
        self, 
        entropy_timeline: List[float], 
        anomalies: Optional[List[dict]] = None,
        output_path: Optional[str] = None
    ) -> Image.Image:
        """
        Generate heatmap from entropy timeline.
        
        Args:
            entropy_timeline: List of entropy values (one per frame)
            anomalies: Optional list of anomalous frames
            output_path: Optional path to save PNG
            
        Returns:
            PIL Image object with heatmap
        """
        if not entropy_timeline:
            raise ValueError("entropy_timeline cannot be empty")
        
        # Normalize entropy to 0-1 range
        entropy_array = np.array(entropy_timeline)
        min_entropy = np.min(entropy_array)
        max_entropy = np.max(entropy_array)
        
        if max_entropy > min_entropy:
            normalized = (entropy_array - min_entropy) / (max_entropy - min_entropy)
        else:
            normalized = np.ones_like(entropy_array) * 0.5
        
        # Create heatmap image
        img = Image.new('RGB', (self.width, self.height), color='white')
        pixels = img.load()
        
        frame_width = self.width // len(entropy_timeline)
        
        # Draw gradient for each frame
        for i, norm_entropy in enumerate(normalized):
            color = self._entropy_to_color(norm_entropy)
            x_start = i * frame_width
            x_end = (i + 1) * frame_width
            
            for x in range(int(x_start), int(x_end)):
                if x < self.width:
                    for y in range(self.height):
                        pixels[x, y] = color
        
        # Overlay anomalies if provided
        if anomalies:
            img = self._overlay_anomalies(img, anomalies, len(entropy_timeline))
        
        # Add timeline labels
        img = self._add_timeline_labels(img, len(entropy_timeline))
        
        # Save if path provided
        if output_path:
            img.save(output_path)
            print(f"Heatmap saved to {output_path}")
        
        return img
    
    @staticmethod
    def _entropy_to_color(norm_entropy: float) -> tuple[int, int, int]:
        """
        Convert normalized entropy (0-1) to RGB color (blue to red gradient).
        
        Args:
            norm_entropy: Normalized entropy value (0-1)
            
        Returns:
            RGB tuple
        """
        # Cool (blue) = low entropy, Hot (red) = high entropy
        if norm_entropy < 0.5:
            # Blue to Green
            t = norm_entropy * 2  # 0 to 1
            r = int(0)
            g = int(255 * t)
            b = int(255 * (1 - t))
        else:
            # Green to Red
            t = (norm_entropy - 0.5) * 2  # 0 to 1
            r = int(255 * t)
            g = int(255 * (1 - t))
            b = int(0)
        
        return (r, g, b)
    
    @staticmethod
    def _overlay_anomalies(
        img: Image.Image, 
        anomalies: List[dict], 
        frame_count: int
    ) -> Image.Image:
        """
        Overlay anomaly markers on heatmap.
        
        Args:
            img: Base heatmap image
            anomalies: List of anomaly dicts with 'frame_index'
            frame_count: Total frame count
            
        Returns:
            Image with overlays
        """
        draw = ImageDraw.Draw(img)
        frame_width = img.width // frame_count
        
        for anomaly in anomalies:
            frame_idx = anomaly.get('frame_index', 0)
            x = (frame_idx + 0.5) * frame_width
            
            # Draw red marker line
            draw.line([(x, 0), (x, img.height)], fill='red', width=2)
        
        return img
    
    @staticmethod
    def _add_timeline_labels(img: Image.Image, frame_count: int) -> Image.Image:
        """
        Add frame number labels to heatmap.
        
        Args:
            img: Base image
            frame_count: Total frames
            
        Returns:
            Image with labels
        """
        # Create image with extra space for labels
        labeled_img = Image.new('RGB', (img.width, img.height + 30), color='white')
        labeled_img.paste(img, (0, 0))
        
        draw = ImageDraw.Draw(labeled_img)
        frame_width = img.width // frame_count
        
        # Draw labels for every 10th frame or fewer
        step = max(1, frame_count // 10)
        for i in range(0, frame_count, step):
            x = i * frame_width + frame_width // 2
            label = str(i)
            try:
                draw.text((x - 10, img.height + 5), label, fill='black')
            except:
                # Fallback if font unavailable
                pass
        
        return labeled_img
