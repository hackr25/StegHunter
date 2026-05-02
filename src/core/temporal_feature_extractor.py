"""
Temporal Feature Extractor for Video Analysis
Extracts temporal and sequence-based features from video frames for ML training
"""

import cv2
import numpy as np
from pathlib import Path
from typing import List, Tuple, Dict, Optional
from PIL import Image


class TemporalFeatureExtractor:
    """Extract temporal features from video sequences"""
    
    def __init__(self, frame_batch_size: int = 5):
        """
        Initialize temporal feature extractor
        
        Args:
            frame_batch_size: Number of consecutive frames to analyze
        """
        self.frame_batch_size = frame_batch_size
    
    def extract_frame_from_video(self, video_path: str, frame_index: int) -> Optional[np.ndarray]:
        """
        Extract single frame from video
        
        Args:
            video_path: Path to video file
            frame_index: Frame number to extract (0-indexed)
            
        Returns:
            np.ndarray: Frame array or None if failed
        """
        try:
            cap = cv2.VideoCapture(video_path)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
            ret, frame = cap.read()
            cap.release()
            return frame if ret else None
        except Exception as e:
            print(f"Error extracting frame {frame_index}: {e}")
            return None
    
    def calculate_optical_flow(self, frame1: np.ndarray, frame2: np.ndarray) -> np.ndarray:
        """
        Calculate optical flow between two frames
        Detects motion patterns between frames
        
        Args:
            frame1: First frame
            frame2: Second frame
            
        Returns:
            np.ndarray: Optical flow magnitude and angle
        """
        try:
            gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
            
            flow = cv2.calcOpticalFlowFarneback(gray1, gray2, None, 0.5, 3, 15, 3, 5, 1.2, 0)
            mag, ang = cv2.cartToPolar(flow[..., 0], flow[..., 1])
            
            return {
                'magnitude': mag,
                'angle': ang,
                'mean_magnitude': np.mean(mag),
                'std_magnitude': np.std(mag),
                'mean_angle': np.mean(ang),
                'std_angle': np.std(ang)
            }
        except Exception as e:
            print(f"Error calculating optical flow: {e}")
            return None
    
    def calculate_frame_difference(self, frame1: np.ndarray, frame2: np.ndarray) -> Dict:
        """
        Calculate pixel-level differences between frames
        
        Args:
            frame1: First frame
            frame2: Second frame
            
        Returns:
            dict: Difference metrics
        """
        try:
            diff = cv2.absdiff(frame1, frame2)
            
            return {
                'mean_diff': np.mean(diff),
                'std_diff': np.std(diff),
                'max_diff': np.max(diff),
                'min_diff': np.min(diff),
                'median_diff': np.median(diff),
                'percentile_95': np.percentile(diff, 95),
                'percentile_05': np.percentile(diff, 5)
            }
        except Exception as e:
            print(f"Error calculating frame difference: {e}")
            return None
    
    def calculate_histogram_difference(self, frame1: np.ndarray, frame2: np.ndarray) -> Dict:
        """
        Calculate histogram differences between frames
        
        Args:
            frame1: First frame
            frame2: Second frame
            
        Returns:
            dict: Histogram difference metrics
        """
        try:
            gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
            
            hist1 = cv2.calcHist([gray1], [0], None, [256], [0, 256])
            hist2 = cv2.calcHist([gray2], [0], None, [256], [0, 256])
            
            hist1 = cv2.normalize(hist1, hist1).flatten()
            hist2 = cv2.normalize(hist2, hist2).flatten()
            
            bhattacharyya = cv2.compareHist(hist1, hist2, cv2.HISTCMP_BHATTACHARYYA)
            correlation = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
            chi_square = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CHISQR)
            
            return {
                'bhattacharyya': bhattacharyya,
                'correlation': correlation,
                'chi_square': chi_square
            }
        except Exception as e:
            print(f"Error calculating histogram difference: {e}")
            return None
    
    def extract_temporal_features_from_batch(self, frames: List[np.ndarray]) -> Dict:
        """
        Extract temporal features from a batch of consecutive frames
        
        Args:
            frames: List of frame arrays (at least 2 frames)
            
        Returns:
            dict: Temporal features
        """
        if len(frames) < 2:
            return {}
        
        temporal_features = {}
        
        # Calculate frame-to-frame differences
        for i in range(len(frames) - 1):
            frame_diff = self.calculate_frame_difference(frames[i], frames[i + 1])
            for key, val in frame_diff.items():
                feature_name = f"frame_diff_{i}_{key}"
                temporal_features[feature_name] = val
            
            # Optical flow
            opt_flow = self.calculate_optical_flow(frames[i], frames[i + 1])
            for key, val in opt_flow.items():
                if key not in ['magnitude', 'angle']:  # Skip full arrays
                    feature_name = f"optical_flow_{i}_{key}"
                    temporal_features[feature_name] = val
            
            # Histogram difference
            hist_diff = self.calculate_histogram_difference(frames[i], frames[i + 1])
            for key, val in hist_diff.items():
                feature_name = f"hist_diff_{i}_{key}"
                temporal_features[feature_name] = val
        
        # Calculate consistency metrics
        temporal_features['frame_consistency'] = self._calculate_frame_consistency(frames)
        temporal_features['motion_pattern_entropy'] = self._calculate_motion_entropy(frames)
        
        return temporal_features
    
    def _calculate_frame_consistency(self, frames: List[np.ndarray]) -> float:
        """
        Calculate how consistent frames are (lower = more consistent)
        
        Args:
            frames: List of frame arrays
            
        Returns:
            float: Consistency metric
        """
        if len(frames) < 2:
            return 0.0
        
        diffs = []
        for i in range(len(frames) - 1):
            frame_diff = self.calculate_frame_difference(frames[i], frames[i + 1])
            diffs.append(frame_diff['mean_diff'])
        
        return float(np.std(diffs))  # Higher variance = less consistent
    
    def _calculate_motion_entropy(self, frames: List[np.ndarray]) -> float:
        """
        Calculate entropy of motion patterns
        
        Args:
            frames: List of frame arrays
            
        Returns:
            float: Motion entropy
        """
        if len(frames) < 2:
            return 0.0
        
        motion_magnitudes = []
        
        for i in range(len(frames) - 1):
            opt_flow = self.calculate_optical_flow(frames[i], frames[i + 1])
            motion_magnitudes.append(opt_flow['mean_magnitude'])
        
        # Calculate entropy from motion magnitudes
        if len(motion_magnitudes) == 0:
            return 0.0
        
        # Normalize to 0-255
        motion_array = np.array(motion_magnitudes)
        motion_array = ((motion_array - np.min(motion_array)) / 
                       (np.max(motion_array) - np.min(motion_array) + 1e-8) * 255).astype(np.uint8)
        
        # Calculate histogram entropy
        hist = np.histogram(motion_array, bins=256, range=(0, 256))[0]
        hist = hist / np.sum(hist)
        entropy = -np.sum(hist[hist > 0] * np.log2(hist[hist > 0]))
        
        return float(entropy)
    
    def extract_video_temporal_features(self, video_path: str, 
                                       num_batches: int = 5) -> Dict:
        """
        Extract temporal features from entire video
        
        Args:
            video_path: Path to video file
            num_batches: Number of frame batches to analyze
            
        Returns:
            dict: Aggregated temporal features
        """
        try:
            cap = cv2.VideoCapture(video_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            if total_frames < self.frame_batch_size:
                print(f"⚠️ Video has fewer frames ({total_frames}) than batch size ({self.frame_batch_size})")
                return {}
            
            # Calculate frame indices to sample
            batch_indices = np.linspace(0, total_frames - self.frame_batch_size,
                                       num_batches, dtype=int)
            
            all_temporal_features = {}
            batch_count = 0
            
            for start_idx in batch_indices:
                frames = []
                
                # Extract frame batch
                for frame_idx in range(start_idx, start_idx + self.frame_batch_size):
                    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                    ret, frame = cap.read()
                    if ret:
                        frames.append(frame)
                
                if len(frames) < 2:
                    continue
                
                # Extract features from this batch
                batch_features = self.extract_temporal_features_from_batch(frames)
                
                # Aggregate with prefix
                for key, val in batch_features.items():
                    agg_key = f"batch_{batch_count}_{key}"
                    all_temporal_features[agg_key] = val
                
                batch_count += 1
            
            cap.release()
            
            # Calculate overall statistics
            if all_temporal_features:
                all_temporal_features['total_batches_analyzed'] = batch_count
            
            return all_temporal_features
        
        except Exception as e:
            print(f"Error extracting video temporal features: {e}")
            return {}


if __name__ == '__main__':
    # Test usage
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python temporal_feature_extractor.py <video_path>")
        sys.exit(1)
    
    video_path = sys.argv[1]
    extractor = TemporalFeatureExtractor(frame_batch_size=5)
    
    features = extractor.extract_video_temporal_features(video_path, num_batches=5)
    
    print(f"\nExtracted {len(features)} temporal features:")
    for key, val in list(features.items())[:10]:
        print(f"  {key}: {val}")
