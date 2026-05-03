"""
Video forensics analyzer - Phase 4 implementation.
Extracts frames, analyzes LSB entropy, detects temporal anomalies.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
from PIL import Image

try:
    import imageio
    HAS_IMAGEIO = True
except ImportError:
    HAS_IMAGEIO = False

from .lsb_analyzer import lsb_analysis, lsb_entropy_score
from ..common.image_utils import validate_image_path


class VideoAnalyzer:
    """Analyze video files for steganographic content frame-by-frame."""

    def __init__(self, frame_sample_rate: int = 5):
        """
        Initialize video analyzer.
        
        Args:
            frame_sample_rate: Analyze every Nth frame (default: every 5th frame)
        """
        if not HAS_IMAGEIO:
            raise ImportError("imageio[ffmpeg] required for video analysis. Install with: pip install imageio[ffmpeg]")
        
        self.frame_sample_rate = frame_sample_rate

    def analyze_video(self, video_path: str) -> Dict[str, Any]:
        """
        Analyze video file for steganography.
        
        Args:
            video_path: Path to video file (.mp4, .mkv, .avi, etc.)
            
        Returns:
            Dict containing:
                - filename: Video filename
                - frame_count: Total frames extracted
                - analyzed_frames: Number of frames analyzed
                - lsb_entropy_timeline: List of entropy values per frame
                - temporal_anomalies: List of anomalous frames with scores
                - overall_score: Combined suspicion score (0-100)
                - analysis_time: Time taken in seconds
        """
        start = time.time()
        path = validate_image_path(video_path)
        
        # Extract frames
        frames = self._extract_frames(str(path))
        if not frames:
            return {
                'error': 'Could not extract frames from video',
                'filename': path.name,
                'overall_score': 0.0
            }
        
        # Analyze each frame for LSB entropy
        entropy_timeline = []
        frame_results = []
        
        for i, frame in enumerate(frames):
            try:
                lsb_result = lsb_analysis(frame)
                entropy = lsb_result.get('entropy', 0.5)
                entropy_timeline.append(entropy)
                frame_results.append({
                    'frame_index': i * self.frame_sample_rate,
                    'entropy': entropy,
                    'lsb_score': lsb_result.get('lsb_suspicion_score', 0.0)
                })
            except Exception as e:
                entropy_timeline.append(0.5)  # Default entropy on error
                frame_results.append({'frame_index': i * self.frame_sample_rate, 'error': str(e)})
        
        # Detect temporal anomalies
        anomalies = self._detect_temporal_anomalies(entropy_timeline)
        
        # Calculate overall score
        overall_score = self._calculate_overall_score(entropy_timeline, anomalies)
        
        return {
            'filename': path.name,
            'frame_count': len(frames),
            'analyzed_frames': len(frame_results),
            'sample_rate': self.frame_sample_rate,
            'lsb_entropy_timeline': entropy_timeline,
            'frame_results': frame_results,
            'temporal_anomalies': anomalies,
            'overall_score': round(overall_score, 2),
            'is_suspicious': overall_score > 50.0,
            'analysis_time': round(time.time() - start, 3)
        }

    def _extract_frames(self, video_path: str, max_frames: int = 300) -> List[Image.Image]:
        """
        Extract frames from video using imageio.
        
        Args:
            video_path: Path to video file
            max_frames: Maximum frames to extract (limit total analysis time)
            
        Returns:
            List of PIL Image objects
        """
        try:
            video = imageio.get_reader(video_path)
            frames = []
            
            for i, frame in enumerate(video):
                if i >= max_frames:
                    break
                
                # Sample frames at specified rate
                if i % self.frame_sample_rate == 0:
                    # Convert from numpy array to PIL Image
                    img = Image.fromarray(frame)
                    frames.append(img)
            
            return frames
        except Exception as e:
            raise ValueError(f"Failed to extract frames from {video_path}: {e}")

    def _detect_temporal_anomalies(self, entropy_timeline: List[float], z_threshold: float = 2.0) -> List[Dict[str, Any]]:
        """
        Detect anomalous frames using Z-score analysis.
        
        Args:
            entropy_timeline: List of entropy values per frame
            z_threshold: Z-score threshold for anomaly (default: 2.0 = 95% confidence)
            
        Returns:
            List of anomalous frames with scores
        """
        if len(entropy_timeline) < 3:
            return []
        
        entropy_array = np.array(entropy_timeline)
        mean_entropy = np.mean(entropy_array)
        std_entropy = np.std(entropy_array)
        
        if std_entropy == 0:
            return []  # No variation = no anomalies
        
        # Calculate Z-scores
        z_scores = (entropy_array - mean_entropy) / std_entropy
        
        # Detect anomalies (frames with high/low Z-scores)
        anomalies = []
        for i, z in enumerate(z_scores):
            if abs(z) > z_threshold:
                anomaly_score = min(100.0, abs(z) * 20.0)  # Convert Z-score to suspicion score
                anomalies.append({
                    'frame_index': i,
                    'z_score': round(float(z), 2),
                    'entropy': round(entropy_timeline[i], 3),
                    'anomaly_score': round(anomaly_score, 2),
                    'type': 'high_entropy' if z > 0 else 'low_entropy'
                })
        
        return anomalies

    def _calculate_overall_score(self, entropy_timeline: List[float], anomalies: List[Dict[str, Any]]) -> float:
        """
        Calculate overall suspicion score for video.
        
        Args:
            entropy_timeline: Per-frame entropy values
            anomalies: List of detected anomalies
            
        Returns:
            Suspicion score (0-100)
        """
        if not entropy_timeline:
            return 0.0
        
        entropy_array = np.array(entropy_timeline)
        
        # Base score from entropy variation
        entropy_std = np.std(entropy_array)
        entropy_score = min(100.0, entropy_std * 150.0)  # Normalized std to 0-100
        
        # Anomaly contribution
        anomaly_score = len(anomalies) * 5.0 if anomalies else 0.0
        anomaly_score = min(50.0, anomaly_score)
        
        # Entropy range (compression artifacts)
        entropy_min, entropy_max = np.min(entropy_array), np.max(entropy_array)
        range_score = (entropy_max - entropy_min) * 50.0 if entropy_max > entropy_min else 0.0
        range_score = min(30.0, range_score)
        
        # Weighted combination
        overall = (entropy_score * 0.5) + (anomaly_score * 0.3) + (range_score * 0.2)
        
        return min(100.0, overall)
