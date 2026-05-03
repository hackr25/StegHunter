"""
Hiding Location Analyzer - Identifies WHERE steganographic content is hidden
Analyzes specific image regions, channels, and methods to pinpoint hiding locations
"""

import numpy as np
from PIL import Image
import cv2
from typing import Dict, List, Tuple, Any
from pathlib import Path


class HidingLocationAnalyzer:
    """Analyzes and identifies potential hiding locations in images"""
    
    def __init__(self, window_size: int = 64, stride: int = 32):
        """
        Args:
            window_size: Size of sliding window for region analysis
            stride: Step size for sliding window
        """
        self.window_size = window_size
        self.stride = stride
    
    def analyze_hiding_locations(self, image_path: str) -> Dict[str, Any]:
        """
        Comprehensive analysis of potential hiding locations
        
        Returns:
            Dict with:
            - channel_analysis: Which color channels are suspicious
            - region_hotspots: Most suspicious image regions
            - frequency_analysis: Where in frequency domain anomalies exist
            - method_locations: Which methods flag which areas
        """
        image = Image.open(image_path)
        img_array = np.array(image)
        
        # Handle different image modes
        if len(img_array.shape) == 2:  # Grayscale
            img_array = cv2.cvtColor(img_array, cv2.COLOR_GRAY2RGB)
        elif img_array.shape[2] == 4:  # RGBA
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2RGB)
        
        results = {
            'image_path': str(image_path),
            'image_size': img_array.shape,
            'channel_analysis': self._analyze_channels(img_array),
            'region_hotspots': self._analyze_regions(img_array),
            'frequency_analysis': self._analyze_frequency(img_array),
            'lsb_analysis': self._analyze_lsb(img_array),
            'suspicious_areas': self._identify_suspicious_areas(img_array),
        }
        
        return results
    
    def _analyze_channels(self, img_array: np.ndarray) -> Dict[str, Any]:
        """
        Analyze which color channels are most suspicious
        
        Common hiding locations:
        - LSB (Least Significant Bit) plane
        - Cb/Cr channels in YCbCr (human eye less sensitive)
        - Alpha channel if present
        """
        analysis = {
            'rgb_lsb': self._analyze_rgb_lsb(img_array),
            'ycbcr_analysis': self._analyze_ycbcr(img_array),
            'alpha_channel': self._analyze_alpha(img_array) if img_array.shape[2] == 4 else None,
        }
        
        return analysis
    
    def _analyze_rgb_lsb(self, img_array: np.ndarray) -> Dict[str, Any]:
        """Analyze LSB patterns in each RGB channel"""
        results = {}
        
        for channel_name, channel_idx in [('Red', 0), ('Green', 1), ('Blue', 2)]:
            channel = img_array[:, :, channel_idx]
            lsb_plane = channel & 1  # Extract LSB
            
            # Calculate entropy and uniformity
            unique, counts = np.unique(lsb_plane, return_counts=True)
            entropy = -np.sum((counts / counts.sum()) * np.log2(counts / counts.sum() + 1e-10))
            uniformity = 1.0 - entropy  # 0 = random, 1 = uniform
            
            results[f'{channel_name}_LSB'] = {
                'entropy': float(entropy),
                'uniformity': float(uniformity),
                'suspicion_level': 'HIGH' if uniformity > 0.8 else 'MEDIUM' if uniformity > 0.6 else 'LOW',
                'likely_hiding': uniformity > 0.7,  # Too uniform = likely hiding spot
            }
        
        return results
    
    def _analyze_ycbcr(self, img_array: np.ndarray) -> Dict[str, Any]:
        """
        Analyze YCbCr color space
        Cb and Cr channels commonly used for steganography
        """
        # Convert RGB to YCbCr
        img_ycbcr = cv2.cvtColor(img_array, cv2.COLOR_RGB2YCrCb)
        
        results = {}
        for channel_name, channel_idx in [('Y (Luminance)', 0), ('Cr (Red)', 1), ('Cb (Blue)', 2)]:
            channel = img_ycbcr[:, :, channel_idx]
            
            # Calculate entropy
            hist = np.histogram(channel, bins=256, range=(0, 256))[0]
            entropy = -np.sum((hist / hist.sum()) * np.log2(hist / hist.sum() + 1e-10))
            
            # Low entropy = suspicious (data packed tightly)
            suspicion = 'HIGH' if entropy < 5.0 else 'MEDIUM' if entropy < 6.0 else 'LOW'
            
            results[channel_name] = {
                'entropy': float(entropy),
                'suspicion_level': suspicion,
                'likely_hiding': channel_name in ['Cr (Red)', 'Cb (Blue)'],  # These channels most used
            }
        
        return results
    
    def _analyze_alpha(self, img_array: np.ndarray) -> Dict[str, Any]:
        """Analyze alpha channel if present"""
        if img_array.shape[2] < 4:
            return None
        
        alpha = img_array[:, :, 3]
        unique_values = len(np.unique(alpha))
        
        return {
            'unique_values': int(unique_values),
            'suspicious': unique_values > 10,  # If many values, likely hiding data
            'likely_hiding': unique_values > 50,
        }
    
    def _analyze_regions(self, img_array: np.ndarray) -> Dict[str, Any]:
        """
        Analyze which image regions are most suspicious
        Uses sliding window to identify hotspots
        """
        h, w = img_array.shape[:2]
        heatmap = np.zeros((h, w), dtype=np.float32)
        
        # Sliding window analysis
        for i in range(0, h - self.window_size + 1, self.stride):
            for j in range(0, w - self.window_size + 1, self.stride):
                window = img_array[i:i+self.window_size, j:j+self.window_size]
                
                # Calculate multiple suspicion indicators
                lsb_uniformity = self._calculate_lsb_uniformity(window)
                entropy_anomaly = self._calculate_entropy_anomaly(window)
                noise_level = self._calculate_noise_level(window)
                
                # Combine indicators
                suspicion = (lsb_uniformity * 0.4 + entropy_anomaly * 0.3 + noise_level * 0.3)
                
                # Fill heatmap for this window
                end_i = min(i + self.window_size, h)
                end_j = min(j + self.window_size, w)
                heatmap[i:end_i, j:end_j] = np.maximum(heatmap[i:end_i, j:end_j], suspicion)
        
        # Normalize heatmap
        if heatmap.max() > 0:
            heatmap = heatmap / heatmap.max() * 100
        
        # Find hotspots
        threshold = np.percentile(heatmap[heatmap > 0], 75) if heatmap.max() > 0 else 0
        hotspots = np.where(heatmap > threshold)
        
        return {
            'heatmap': heatmap,
            'hotspot_count': len(hotspots[0]),
            'max_suspicion': float(heatmap.max()),
            'avg_suspicion': float(np.mean(heatmap[heatmap > 0])) if heatmap.max() > 0 else 0,
            'suspicious_regions': [
                {'x': int(x), 'y': int(y), 'suspicion': float(heatmap[y, x])}
                for x, y in zip(hotspots[1], hotspots[0])
            ][:10],  # Top 10 regions
        }
    
    def _analyze_frequency(self, img_array: np.ndarray) -> Dict[str, Any]:
        """
        Analyze frequency domain (FFT, DCT)
        Steganography often concentrated in specific frequencies
        """
        # Convert to grayscale for frequency analysis
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array
        
        # FFT analysis
        fft = np.fft.fft2(gray)
        fft_shift = np.fft.fftshift(fft)
        magnitude_spectrum = np.abs(fft_shift)
        
        # Log scale for visualization
        log_magnitude = np.log1p(magnitude_spectrum)
        
        # Analyze frequency distribution
        center_region = log_magnitude[
            log_magnitude.shape[0]//4:3*log_magnitude.shape[0]//4,
            log_magnitude.shape[1]//4:3*log_magnitude.shape[1]//4
        ]
        edge_region = np.concatenate([
            log_magnitude[:log_magnitude.shape[0]//4, :],
            log_magnitude[3*log_magnitude.shape[0]//4:, :],
        ])
        
        center_energy = np.sum(center_region ** 2)
        edge_energy = np.sum(edge_region ** 2)
        
        return {
            'fft_center_energy': float(center_energy),
            'fft_edge_energy': float(edge_energy),
            'energy_ratio': float(center_energy / (edge_energy + 1e-10)),
            'suspicious_frequencies': 'HIGH_FREQUENCY' if edge_energy > center_energy else 'LOW_FREQUENCY',
            'likely_hiding_location': 'High-frequency regions' if edge_energy > center_energy else 'Low-frequency regions',
        }
    
    def _analyze_lsb(self, img_array: np.ndarray) -> Dict[str, Any]:
        """
        Deep LSB analysis - most common hiding location
        """
        # Extract LSB planes for all channels
        lsb_planes = {}
        for ch in range(min(3, img_array.shape[2])):
            lsb = img_array[:, :, ch] & 1
            lsb_planes[f'Channel_{ch}_LSB'] = {
                'zeros': int(np.sum(lsb == 0)),
                'ones': int(np.sum(lsb == 1)),
                'ratio': float(np.sum(lsb == 0) / (lsb.size + 1e-10)),
                'suspicious': abs(np.sum(lsb == 0) / lsb.size - 0.5) > 0.15,
            }
        
        return {
            'lsb_planes': lsb_planes,
            'overall_lsb_suspicious': any(v['suspicious'] for v in lsb_planes.values()),
        }
    
    def _identify_suspicious_areas(self, img_array: np.ndarray) -> List[Dict[str, Any]]:
        """
        Identify and describe specific suspicious areas
        """
        suspicious_areas = []
        
        # Check corners (common hiding location)
        corner_size = min(50, img_array.shape[0]//4, img_array.shape[1]//4)
        corners = {
            'top-left': img_array[:corner_size, :corner_size],
            'top-right': img_array[:corner_size, -corner_size:],
            'bottom-left': img_array[-corner_size:, :corner_size],
            'bottom-right': img_array[-corner_size:, -corner_size:],
        }
        
        for corner_name, corner_data in corners.items():
            uniformity = self._calculate_lsb_uniformity(corner_data)
            if uniformity > 0.7:
                suspicious_areas.append({
                    'location': f'{corner_name} corner',
                    'suspicion_score': float(uniformity * 100),
                    'reason': 'LSB plane too uniform - likely hiding spot',
                    'method': 'LSB Analysis',
                })
        
        # Check if center is suspicious
        h, w = img_array.shape[:2]
        center_region = img_array[h//4:3*h//4, w//4:3*w//4]
        center_uniformity = self._calculate_lsb_uniformity(center_region)
        if center_uniformity > 0.6:
            suspicious_areas.append({
                'location': 'center region',
                'suspicion_score': float(center_uniformity * 100),
                'reason': 'LSB plane shows artificial uniformity',
                'method': 'LSB Analysis',
            })
        
        return suspicious_areas
    
    def _calculate_lsb_uniformity(self, window: np.ndarray) -> float:
        """Calculate LSB uniformity score (0-1, higher = more uniform)"""
        if window.shape[2] < 3:
            return 0.0
        
        lsb_bits = []
        for ch in range(min(3, window.shape[2])):
            lsb = window[:, :, ch] & 1
            lsb_bits.extend(lsb.flatten())
        
        lsb_bits = np.array(lsb_bits)
        if len(lsb_bits) == 0:
            return 0.0
        
        # Calculate uniformity (1 = all same, 0 = random)
        ratio = np.sum(lsb_bits == 0) / len(lsb_bits)
        uniformity = 1.0 - abs(ratio - 0.5) * 2  # Max when ratio=0 or 1
        
        return float(uniformity)
    
    def _calculate_entropy_anomaly(self, window: np.ndarray) -> float:
        """Calculate entropy anomaly score"""
        if window.shape[2] < 3:
            return 0.0
        
        entropies = []
        for ch in range(min(3, window.shape[2])):
            channel = window[:, :, ch].flatten()
            hist = np.histogram(channel, bins=256, range=(0, 256))[0]
            entropy = -np.sum((hist / hist.sum()) * np.log2(hist / hist.sum() + 1e-10))
            entropies.append(entropy)
        
        # Normal image entropy ~7.5, too low = suspicious
        avg_entropy = np.mean(entropies)
        anomaly = max(0, 7.5 - avg_entropy) / 7.5  # 0-1 scale
        
        return float(anomaly)
    
    def _calculate_noise_level(self, window: np.ndarray) -> float:
        """Calculate high-frequency noise level"""
        if window.shape[2] < 3:
            return 0.0
        
        # Convert to grayscale
        gray = cv2.cvtColor(window, cv2.COLOR_RGB2GRAY)
        
        # Apply Laplacian to detect edges/noise
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        variance = np.var(laplacian)
        
        # Normalize (typical range 0-100, scale to 0-1)
        noise_level = min(variance / 100, 1.0)
        
        return float(noise_level)
    
    
    def generate_location_heatmap(self, image_path: str) -> np.ndarray:
        """
        Generate heatmap showing WHERE steganography is likely hidden
        Returns only the heatmap array (no file saving)
        """
        analysis = self.analyze_hiding_locations(image_path)
        heatmap = analysis['region_hotspots']['heatmap']
        
        # Load original image for reference
        image = Image.open(image_path)
        img_array = np.array(image)
        if len(img_array.shape) == 2:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_GRAY2RGB)
        elif img_array.shape[2] == 4:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2RGB)
        
        # Resize heatmap to match image
        h, w = img_array.shape[:2]
        heatmap_resized = cv2.resize(heatmap, (w, h))
        
        # Convert heatmap to color (jet colormap)
        heatmap_uint8 = (heatmap_resized / 100 * 255).astype(np.uint8)
        heatmap_colored = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)
        
        # Blend with original image
        blended = cv2.addWeighted(img_array, 0.6, heatmap_colored, 0.4, 0)
        
        return blended
