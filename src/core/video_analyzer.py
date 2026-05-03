"""
Video forensics analyzer - Phase 4 implementation.
Comprehensive frame-by-frame analysis using all detection techniques.
Applies image analysis methods (ELA, JPEG Ghost, LSB, Noise, etc.) per frame
and aggregates results with temporal anomaly detection.
"""
from __future__ import annotations

import json
import time
import logging
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
from .ela_analyzer import ELAAnalyzer
from .jpeg_ghost_analyzer import JPEGGhostAnalyzer
from .noise_analyzer import NoiseAnalyzer
from .color_space_analyzer import ColorSpaceAnalyzer
from .statistical_tests import chi_square_test, pixel_value_differencing
from ..common.image_utils import validate_video_path

logger = logging.getLogger(__name__)


class VideoAnalyzer:
    """Analyze video files for steganographic content using comprehensive frame-by-frame techniques."""

    def __init__(self, frame_sample_rate: int = 5):
        """
        Initialize video analyzer.
        
        Args:
            frame_sample_rate: Analyze every Nth frame (default: every 5th frame)
        """
        if not HAS_IMAGEIO:
            raise ImportError("imageio[ffmpeg] required for video analysis. Install with: pip install imageio[ffmpeg]")
        
        self.frame_sample_rate = frame_sample_rate
        self.ela_analyzer = ELAAnalyzer()
        self.jpeg_ghost_analyzer = JPEGGhostAnalyzer()
        self.noise_analyzer = NoiseAnalyzer()
        self.color_space_analyzer = ColorSpaceAnalyzer()

    def analyze_video(self, video_path: str) -> Dict[str, Any]:
        """
        Analyze video file for steganography using comprehensive frame-by-frame techniques.
        
        Args:
            video_path: Path to video file (.mp4, .mkv, .avi, etc.)
            
        Returns:
            Dict containing per-frame technique scores, temporal analysis, and overall score
        """
        start = time.time()
        path = validate_video_path(video_path)
        
        # Extract frames
        frames = self._extract_frames(str(path))
        if not frames:
            return {
                'error': 'Could not extract frames from video',
                'filename': path.name,
                'final_suspicion_score': 0.0
            }
        
        # Analyze each frame with all techniques
        frame_results = []
        technique_timelines = {
            'lsb': [], 'ela': [], 'jpeg_ghost': [], 'noise': [],
            'color_space': [], 'chi_square': [], 'pixel_differencing': []
        }
        
        for i, frame in enumerate(frames):
            frame_idx = i * self.frame_sample_rate
            frame_analysis = self._analyze_frame_comprehensive(frame, frame_idx)
            frame_results.append(frame_analysis)
            
            # Build timelines for each technique
            for technique in technique_timelines:
                score = frame_analysis.get('techniques', {}).get(technique, {}).get('suspicion_score', 0.0)
                technique_timelines[technique].append(score)
        
        # Detect temporal anomalies for each technique
        temporal_analysis = {}
        for technique, timeline in technique_timelines.items():
            if timeline:
                anomalies = self._detect_temporal_anomalies(timeline, technique_name=technique)
                temporal_analysis[technique] = anomalies
        
        # Calculate overall score (weighted aggregate)
        overall_score = self._calculate_overall_score(frame_results, temporal_analysis)
        
        return {
            'filename': path.name,
            'frame_count': len(frames),
            'analyzed_frames': len(frame_results),
            'sample_rate': self.frame_sample_rate,
            'frame_results': frame_results,
            'technique_timelines': technique_timelines,
            'temporal_anomalies': temporal_analysis,
            'final_suspicion_score': round(overall_score, 2),
            'is_suspicious': overall_score > 50.0,
            'analysis_time': round(time.time() - start, 3)
        }
    
    def _analyze_frame_comprehensive(self, frame: Image.Image, frame_idx: int) -> Dict[str, Any]:
        """
        Analyze single frame using all available techniques.
        
        Args:
            frame: PIL Image object
            frame_idx: Frame index in video
            
        Returns:
            Dict with per-technique scores
        """
        techniques = {}
        temp_paths = []  # Track temp files for cleanup
        
        try:
            # LSB Analysis
            try:
                lsb_result = lsb_analysis(frame)
                techniques['lsb'] = {
                    'suspicion_score': lsb_result.get('lsb_suspicion_score', 0.0),
                    'entropy': lsb_result.get('entropy', 0.5)
                }
            except Exception as e:
                logger.warning(f"LSB analysis failed for frame {frame_idx}: {e}")
                techniques['lsb'] = {'suspicion_score': 0.0, 'error': str(e)}
            
            # Chi-Square Test
            try:
                chi_result = chi_square_test(frame)
                techniques['chi_square'] = {
                    'suspicion_score': chi_result.get('suspicion_score', 0.0),
                    'chi_square_value': chi_result.get('chi_square_value', 0.0)
                }
            except Exception as e:
                logger.warning(f"Chi-square analysis failed for frame {frame_idx}: {e}")
                techniques['chi_square'] = {'suspicion_score': 0.0, 'error': str(e)}
            
            # Pixel Differencing
            try:
                pd_result = pixel_value_differencing(frame)
                techniques['pixel_differencing'] = {
                    'suspicion_score': pd_result.get('suspicion_score', 0.0),
                    'mean_difference': pd_result.get('mean_difference', 0.0)
                }
            except Exception as e:
                logger.warning(f"Pixel differencing analysis failed for frame {frame_idx}: {e}")
                techniques['pixel_differencing'] = {'suspicion_score': 0.0, 'error': str(e)}
            
            # ELA & Noise & Color Space (need temp PNG file)
            try:
                import tempfile
                temp_png = Path(tempfile.gettempdir()) / f"frame_{frame_idx}_{int(time.time() * 1000)}.png"
                frame.save(str(temp_png))
                temp_paths.append(temp_png)
                
                # ELA Analysis
                try:
                    ela_result = self.ela_analyzer.analyze(str(temp_png))
                    techniques['ela'] = {
                        'suspicion_score': ela_result.get('suspicion_score', 0.0),
                        'error_level_mean': ela_result.get('error_level_mean', 0.0)
                    }
                except Exception as e:
                    logger.warning(f"ELA analysis failed for frame {frame_idx}: {e}")
                    techniques['ela'] = {'suspicion_score': 0.0, 'error': str(e)}
                
                # Noise Analysis
                try:
                    noise_result = self.noise_analyzer.analyze(str(temp_png))
                    techniques['noise'] = {
                        'suspicion_score': noise_result.get('suspicion_score', 0.0),
                        'noise_variance': noise_result.get('noise_variance', 0.0)
                    }
                except Exception as e:
                    logger.warning(f"Noise analysis failed for frame {frame_idx}: {e}")
                    techniques['noise'] = {'suspicion_score': 0.0, 'error': str(e)}
                
                # Color Space Analysis
                try:
                    cs_result = self.color_space_analyzer.analyze(str(temp_png))
                    techniques['color_space'] = {
                        'suspicion_score': cs_result.get('suspicion_score', 0.0),
                        'dominant_colors': cs_result.get('dominant_colors', 0)
                    }
                except Exception as e:
                    logger.warning(f"Color space analysis failed for frame {frame_idx}: {e}")
                    techniques['color_space'] = {'suspicion_score': 0.0, 'error': str(e)}
            except Exception as e:
                logger.warning(f"Temp PNG creation failed for frame {frame_idx}: {e}")
                techniques['ela'] = {'suspicion_score': 0.0, 'error': 'Temp file creation failed'}
                techniques['noise'] = {'suspicion_score': 0.0, 'error': 'Temp file creation failed'}
                techniques['color_space'] = {'suspicion_score': 0.0, 'error': 'Temp file creation failed'}
            
            # JPEG Ghost (need temp JPEG file)
            try:
                import tempfile
                temp_jpg = Path(tempfile.gettempdir()) / f"frame_{frame_idx}_{int(time.time() * 1000)}.jpg"
                frame.convert('RGB').save(str(temp_jpg), 'JPEG', quality=95)
                temp_paths.append(temp_jpg)
                
                try:
                    jpeg_result = self.jpeg_ghost_analyzer.analyze(str(temp_jpg))
                    techniques['jpeg_ghost'] = {
                        'suspicion_score': jpeg_result.get('suspicion_score', 0.0),
                        'ghost_artifacts': jpeg_result.get('ghost_artifacts', 0)
                    }
                except Exception as e:
                    logger.warning(f"JPEG Ghost analysis failed for frame {frame_idx}: {e}")
                    techniques['jpeg_ghost'] = {'suspicion_score': 0.0, 'error': str(e)}
            except Exception as e:
                logger.warning(f"Temp JPEG creation failed for frame {frame_idx}: {e}")
                techniques['jpeg_ghost'] = {'suspicion_score': 0.0, 'error': 'Temp file creation failed'}
            
            # Calculate frame-level score (average of all techniques)
            technique_scores = [v.get('suspicion_score', 0.0) for v in techniques.values()]
            frame_score = np.mean(technique_scores) if technique_scores else 0.0
            
            return {
                'frame_index': frame_idx,
                'techniques': techniques,
                'frame_suspicion_score': round(float(frame_score), 2)
            }
        finally:
            # Clean up temporary files
            for temp_path in temp_paths:
                try:
                    if temp_path.exists():
                        temp_path.unlink()
                except Exception as e:
                    logger.warning(f"Failed to clean up temp file {temp_path}: {e}")

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

    def _detect_temporal_anomalies(self, scores_timeline: List[float], technique_name: str = "general", z_threshold: float = 2.0) -> List[Dict[str, Any]]:
        """
        Detect anomalous frames using Z-score analysis on technique scores.
        
        Args:
            scores_timeline: List of suspicion scores per frame
            technique_name: Name of the technique being analyzed
            z_threshold: Z-score threshold for anomaly (default: 2.0 = 95% confidence)
            
        Returns:
            List of anomalous frames with scores
        """
        if len(scores_timeline) < 3:
            return []
        
        scores_array = np.array(scores_timeline)
        mean_score = np.mean(scores_array)
        std_score = np.std(scores_array)
        
        if std_score == 0:
            return []  # No variation = no anomalies
        
        # Calculate Z-scores
        z_scores = (scores_array - mean_score) / std_score
        
        # Detect anomalies
        anomalies = []
        for i, z in enumerate(z_scores):
            if abs(z) > z_threshold:
                anomaly_score = min(100.0, abs(z) * 20.0)
                anomalies.append({
                    'frame_index': i,
                    'z_score': round(float(z), 2),
                    'score': round(scores_timeline[i], 2),
                    'anomaly_score': round(anomaly_score, 2),
                    'type': 'high_suspicion' if z > 0 else 'low_suspicion'
                })
        
        return anomalies
    
    def _calculate_overall_score(self, frame_results: List[Dict[str, Any]], temporal_analysis: Dict[str, Any]) -> float:
        """
        Calculate overall suspicion score for entire video.
        
        Args:
            frame_results: Per-frame analysis results
            temporal_analysis: Temporal anomaly detections for each technique
            
        Returns:
            Suspicion score (0-100)
        """
        if not frame_results:
            return 0.0
        
        # Extract frame-level scores
        frame_scores = [f.get('frame_suspicion_score', 0.0) for f in frame_results]
        if not frame_scores:
            return 0.0
        
        frame_scores_array = np.array(frame_scores)
        
        # Component 1: Average frame suspicion score (50% weight)
        avg_frame_score = np.mean(frame_scores_array)
        
        # Component 2: Variance (temporal inconsistency) (20% weight)
        variance_score = min(100.0, np.std(frame_scores_array) * 80.0)
        
        # Component 3: Max score (indicates at least one suspicious frame) (15% weight)
        max_frame_score = np.max(frame_scores_array)
        
        # Component 4: Anomaly severity (15% weight)
        total_anomaly_score = 0.0
        anomaly_count = 0
        for technique, anomalies in temporal_analysis.items():
            if anomalies:
                avg_anomaly = np.mean([a.get('anomaly_score', 0.0) for a in anomalies])
                total_anomaly_score += avg_anomaly
                anomaly_count += len(anomalies)
        
        anomaly_severity = min(100.0, total_anomaly_score / max(1, len(temporal_analysis)))
        
        # Weighted combination
        overall = (
            avg_frame_score * 0.50 +
            variance_score * 0.20 +
            max_frame_score * 0.15 +
            anomaly_severity * 0.15
        )
        
        return min(100.0, overall)
