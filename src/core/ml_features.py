"""
Machine Learning Feature Extraction for Steganography Detection
"""
import numpy as np
from PIL import Image
from scipy.stats import entropy
from typing import Dict, List
import cv2

class MLFeatureExtractor:
    """Extract features from images for ML-based steganography detection"""
    
    def __init__(self):
        self.feature_names = []
    
    def extract_features(self, image_path) -> Dict[str, float]:
        """
        Extract comprehensive feature vector from image
        Returns dictionary of feature name -> value
        """
        try:
            image = Image.open(image_path)
            features = {}
            
            # Basic features
            features.update(self._extract_basic_features(image))
            
            # LSB features
            features.update(self._extract_lsb_features(image))
            
            # Histogram features
            features.update(self._extract_histogram_features(image))
            
            # Texture features
            features.update(self._extract_texture_features(image))
            
            # Frequency features
            features.update(self._extract_frequency_features(image))
            
            # Statistical features
            features.update(self._extract_statistical_features(image))
            
            return features
        except Exception as e:
            print(f"Error extracting features from {image_path}: {e}")
            return {}
    
    def _extract_basic_features(self, image: Image.Image) -> Dict[str, float]:
        """Basic image properties"""
        features = {}
        features['width'] = float(image.width)
        features['height'] = float(image.height)
        features['aspect_ratio'] = image.width / max(image.height, 1)
        features['pixel_count'] = float(image.width * image.height)
        features['mode_length'] = float(len(image.mode))
        return features
    
    def _extract_lsb_features(self, image: Image.Image) -> Dict[str, float]:
        """Extract LSB-related features"""
        features = {}
        img_array = np.array(image)
        lsb_plane = img_array & 1
        
        # LSB entropy
        counts = np.bincount(lsb_plane.ravel())
        probabilities = counts / counts.sum()
        lsb_entropy = entropy(probabilities, base=2)
        features['lsb_entropy'] = float(lsb_entropy)
        
        # LSB balance
        unique, counts = np.unique(lsb_plane, return_counts=True)
        if len(unique) == 2:
            balance = min(counts[0], counts[1]) / max(counts[0], counts[1])
        else:
            balance = 0.0
        features['lsb_balance'] = float(balance)
        
        # LSB mean
        features['lsb_mean'] = float(np.mean(lsb_plane))
        
        # LSB standard deviation
        features['lsb_std'] = float(np.std(lsb_plane))
        
        return features
    
    def _extract_histogram_features(self, image: Image.Image) -> Dict[str, float]:
        """Extract histogram-based features"""
        features = {}
        img_array = np.array(image)
        
        # For each color channel
        for i, channel_name in enumerate(['R', 'G', 'B'][:len(img_array.shape)]):
            if len(img_array.shape) == 2:  # Grayscale
                channel = img_array
                channel_name = 'Gray'
            else:
                channel = img_array[:, :, i]
            
            # Histogram
            hist, _ = np.histogram(channel, bins=256, range=[0, 256])
            hist = hist / hist.sum()  # Normalize
            
            # Histogram entropy
            hist_entropy = entropy(hist, base=2)
            features[f'{channel_name}_hist_entropy'] = float(hist_entropy)
            
            # Histogram statistics
            features[f'{channel_name}_hist_mean'] = float(np.mean(hist))
            features[f'{channel_name}_hist_std'] = float(np.std(hist))
            
            # Fix skewness calculation to avoid division by zero
            hist_std = np.std(hist)
            if hist_std > 1e-10:  # Avoid division by zero
                hist_skew = float(float(np.mean((hist - np.mean(hist))**3)) / (hist_std ** 3))
            else:
                hist_skew = 0.0
            features[f'{channel_name}_hist_skew'] = hist_skew
        
        return features
    
    def _extract_texture_features(self, image: Image.Image) -> Dict[str, float]:
        """Extract texture-based features using GLCM"""
        features = {}
        try:
            # Convert to grayscale for texture analysis
            if len(image.mode) != 'L':
                image = image.convert('L')
            
            img_array = np.array(image)
            
            # Local Binary Pattern (LBP) approximation
            # Calculate differences between adjacent pixels
            h_diff = np.diff(img_array, axis=1)
            v_diff = np.diff(img_array, axis=0)
            
            features['h_diff_mean'] = float(np.mean(h_diff))
            features['h_diff_std'] = float(np.std(h_diff))
            features['v_diff_mean'] = float(np.mean(v_diff))
            features['v_diff_std'] = float(np.std(v_diff))
            
            # Texture complexity
            features['texture_complexity'] = float(np.std(h_diff) + np.std(v_diff))
            
        except Exception as e:
            print(f"Error extracting texture features: {e}")
        
        return features
    
    def _extract_frequency_features(self, image: Image.Image) -> Dict[str, float]:
        """Extract frequency domain features"""
        features = {}
        try:
            # Convert to grayscale
            if len(image.mode) != 'L':
                image = image.convert('L')
            
            img_array = np.array(image, dtype=np.float32)
            
            # FFT analysis
            fft = np.fft.fft2(img_array)
            fft_shifted = np.fft.fftshift(fft)
            magnitude_spectrum = np.log(np.abs(fft_shifted) + 1)
            
            # Frequency domain statistics
            features['fft_mean'] = float(np.mean(magnitude_spectrum))
            features['fft_std'] = float(np.std(magnitude_spectrum))
            features['fft_entropy'] = float(entropy(magnitude_spectrum.ravel(), base=2))
            
            # High frequency energy
            h, w = magnitude_spectrum.shape
            high_freq = magnitude_spectrum[h//4:3*h//4, w//4:3*w//4]
            features['high_freq_energy'] = float(np.mean(high_freq))
            
        except Exception as e:
            print(f"Error extracting frequency features: {e}")
        
        return features
    
    def _extract_statistical_features(self, image: Image.Image) -> Dict[str, float]:
        """Extract statistical features"""
        features = {}
        img_array = np.array(image)
        
        # Overall statistics
        features['pixel_mean'] = float(np.mean(img_array))
        features['pixel_std'] = float(np.std(img_array))
        features['pixel_variance'] = float(np.var(img_array))
        features['pixel_range'] = float(np.max(img_array) - np.min(img_array))
        
        # Correlation between color channels
        if len(img_array.shape) == 3 and img_array.shape[2] >= 2:
            features['rg_correlation'] = float(np.corrcoef(img_array[:,:,0].ravel(), 
                                                          img_array[:,:,1].ravel())[0,1])
        if len(img_array.shape) == 3 and img_array.shape[2] >= 3:
            features['rb_correlation'] = float(np.corrcoef(img_array[:,:,0].ravel(), 
                                                          img_array[:,:,2].ravel())[0,1])
            features['gb_correlation'] = float(np.corrcoef(img_array[:,:,1].ravel(), 
                                                          img_array[:,:,2].ravel())[0,1])
        
        return features
    
    def get_feature_names(self) -> List[str]:
        """Get list of all feature names"""
        if not self.feature_names:
            # Extract features from a dummy image to get names
            # Create a simple test image
            test_image = Image.new('RGB', (100, 100), color='red')
            temp_path = 'temp_test_image.png'
            test_image.save(temp_path)
            features = self.extract_features(temp_path)
            self.feature_names = list(features.keys())
            # Clean up
            import os
            if os.path.exists(temp_path):
                os.remove(temp_path)
        
        return self.feature_names
    
    def features_to_vector(self, features: Dict[str, float]) -> List[float]:
        """Convert feature dictionary to vector (ordered)"""
        feature_names = self.get_feature_names()
        return [features.get(name, 0.0) for name in feature_names]
