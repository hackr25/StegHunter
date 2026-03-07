"""
Frequency Domain Analysis for Steganography Detection
"""
import numpy as np
from PIL import Image
from scipy import fftpack
from typing import Dict, Tuple

class FrequencyAnalyzer:
    """Analyze images in frequency domain to detect steganography"""
    
    def __init__(self):
        pass
    
    def fft_analysis(self, image: Image.Image) -> Dict:
        """
        Perform FFT analysis on image
        Returns frequency domain statistics
        """
        # Convert to grayscale
        if len(image.mode) != 'L':
            image = image.convert('L')
        
        img_array = np.array(image, dtype=np.float32)
        
        # 2D FFT
        fft_result = fftpack.fft2(img_array)
        fft_shifted = fftpack.fftshift(fft_result)
        magnitude_spectrum = np.log(np.abs(fft_shifted) + 1)
        
        # Phase spectrum
        phase_spectrum = np.angle(fft_shifted)
        
        # Statistical features
        features = {
            'fft_mean': float(np.mean(magnitude_spectrum)),
            'fft_std': float(np.std(magnitude_spectrum)),
            'fft_variance': float(np.var(magnitude_spectrum)),
            'fft_max': float(np.max(magnitude_spectrum)),
            'fft_min': float(np.min(magnitude_spectrum)),
            'fft_range': float(np.max(magnitude_spectrum) - np.min(magnitude_spectrum)),
            
            # Phase features
            'phase_mean': float(np.mean(phase_spectrum)),
            'phase_std': float(np.std(phase_spectrum)),
            
            # High frequency energy
            'high_freq_energy': self._calculate_high_freq_energy(magnitude_spectrum),
            'low_freq_energy': self._calculate_low_freq_energy(magnitude_spectrum),
            
            # Spectral flatness
            'spectral_flatness': self._spectral_flatness(magnitude_spectrum)
        }
        
        return features
    
    def dct_analysis(self, image: Image.Image) -> Dict:
        """
        Perform DCT analysis (for JPEG images)
        Returns DCT coefficient statistics
        """
        # Convert to grayscale
        if len(image.mode) != 'L':
            image = image.convert('L')
        
        img_array = np.array(image, dtype=np.float32)
        
        # Block-based DCT (8x8 blocks)
        h, w = img_array.shape
        block_size = 8
        
        dct_coeffs = []
        for i in range(0, h, block_size):
            for j in range(0, w, block_size):
                block = img_array[i:i+block_size, j:j+block_size]
                if block.shape != (block_size, block_size):
                    continue
                dct_block = fftpack.dct(fftpack.dct(block, axis=0, norm='ortho'), axis=1, norm='ortho')
                dct_coeffs.extend(dct_block.flatten())
        
        dct_coeffs = np.array(dct_coeffs)
        
        features = {
            'dct_mean': float(np.mean(dct_coeffs)),
            'dct_std': float(np.std(dct_coeffs)),
            'dct_variance': float(np.var(dct_coeffs)),
            'dct_skewness': self._calculate_skewness(dct_coeffs),
            'dct_kurtosis': self._calculate_kurtosis(dct_coeffs),
            'dct_zeros': float(np.sum(dct_coeffs == 0)),
            'dct_zero_ratio': float(np.sum(dct_coeffs == 0) / len(dct_coeffs))
        }
        
        return features
    
    def detect_frequency_anomalies(self, image: Image.Image, threshold: float = 3.0) -> Dict:
        """
        Detect anomalies in frequency domain
        Returns suspicious regions and anomaly scores
        """
        # Convert to grayscale
        if len(image.mode) != 'L':
            image = image.convert('L')
        
        img_array = np.array(image, dtype=np.float32)
        
        # Sliding window FFT
        window_size = 64
        stride = 32
        h, w = img_array.shape
        
        anomaly_map = np.zeros((h, w))
        count_map = np.zeros((h, w))
        
        for i in range(0, h - window_size + 1, stride):
            for j in range(0, w - window_size + 1, stride):
                window = img_array[i:i+window_size, j:j+window_size]
                
                # FFT of window
                fft_result = fftpack.fft2(window)
                fft_shifted = fftpack.fftshift(fft_result)
                magnitude = np.abs(fft_shifted)
                
                # Calculate anomaly score
                anomaly_score = self._calculate_anomaly_score(magnitude)
                
                # Add to anomaly map
                anomaly_map[i:i+window_size, j:j+window_size] += anomaly_score
                count_map[i:i+window_size, j:j+window_size] += 1
        
        # Average overlapping regions
        anomaly_map = np.divide(anomaly_map, count_map, out=np.zeros_like(anomaly_map), where=count_map!=0)
        
        # Calculate overall anomaly score
        mean_anomaly = np.mean(anomaly_map)
        std_anomaly = np.std(anomaly_map)
        global_anomaly_score = mean_anomaly / (std_anomaly + 1e-10)
        
        return {
            'global_anomaly_score': float(global_anomaly_score),
            'mean_anomaly': float(mean_anomaly),
            'std_anomaly': float(std_anomaly),
            'max_anomaly': float(np.max(anomaly_map)),
            'anomaly_map': anomaly_map,
            'is_anomalous': global_anomaly_score > threshold
        }
    
    def _calculate_high_freq_energy(self, magnitude_spectrum: np.ndarray) -> float:
        """Calculate energy in high frequency components"""
        h, w = magnitude_spectrum.shape
        center_h, center_w = h // 2, w // 2
        
        # High frequency region (edges of spectrum)
        high_freq_region = np.concatenate([
            magnitude_spectrum[0:center_h//2, :],
            magnitude_spectrum[center_h + center_h//2:, :],
            magnitude_spectrum[:, 0:center_w//2],
            magnitude_spectrum[:, center_w + center_w//2:]
        ])
        
        return float(np.mean(high_freq_region))
    
    def _calculate_low_freq_energy(self, magnitude_spectrum: np.ndarray) -> float:
        """Calculate energy in low frequency components"""
        h, w = magnitude_spectrum.shape
        center_h, center_w = h // 2, w // 2
        
        # Low frequency region (center of spectrum)
        low_freq_region = magnitude_spectrum[center_h//2:center_h + center_h//2, 
                                            center_w//2:center_w + center_w//2]
        
        return float(np.mean(low_freq_region))
    
    def _spectral_flatness(self, magnitude_spectrum: np.ndarray) -> float:
        """Calculate spectral flatness (ratio of geometric mean to arithmetic mean)"""
        magnitude_flat = magnitude_spectrum.flatten()
        
        geometric_mean = np.exp(np.mean(np.log(magnitude_flat + 1e-10)))
        arithmetic_mean = np.mean(magnitude_flat)
        
        return float(geometric_mean / (arithmetic_mean + 1e-10))
    
    def _calculate_anomaly_score(self, magnitude: np.ndarray) -> float:
        """Calculate anomaly score based on magnitude spectrum"""
        # Z-score based anomaly detection
        mean = np.mean(magnitude)
        std = np.std(magnitude)
        z_score = (magnitude - mean) / (std + 1e-10)
        
        # Use sum of absolute z-scores as anomaly score
        return float(np.sum(np.abs(z_score)))
    
    def _calculate_skewness(self, data: np.ndarray) -> float:
        """Calculate skewness of data"""
        mean = np.mean(data)
        std = np.std(data)
        if std == 0:
            return 0.0
        return float(np.mean(((data - mean) / std) ** 3))
    
    def _calculate_kurtosis(self, data: np.ndarray) -> float:
        """Calculate kurtosis of data"""
        mean = np.mean(data)
        std = np.std(data)
        if std == 0:
            return 0.0
        return float(np.mean(((data - mean) / std) ** 4) - 3)
