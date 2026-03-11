"""
Machine Learning Feature Extraction for Steganography Detection
Handles numerical stability and prevents NaN values
"""
import numpy as np
from PIL import Image
from scipy.stats import entropy
from typing import Dict, List, Tuple
import warnings
import cv2
from scipy import stats

class MLFeatureExtractor:
    """Extract features from images for ML-based steganography detection with numerical stability"""
    
    def __init__(self):
        self.feature_names = self._generate_feature_names()
    
    def _generate_feature_names(self) -> List[str]:
        """Generate feature names for all features"""
        # Basic features
        basic_features = [
            'width', 'height', 'aspect_ratio', 'pixel_count', 
            'mode_length', 'file_size'
        ]
        
        # LSB features
        lsb_features = [
            'lsb_entropy', 'lsb_balance', 'lsb_std', 'lsb_mean', 
            'lsb_variance', 'lsb_correlation', 'lsb_homogeneity', 'lsb_energy'
        ]
        
        # Statistical features
        statistical_features = [
            'pixel_mean', 'pixel_std', 'pixel_variance', 'pixel_range',
            'rg_correlation', 'rb_correlation', 'gb_correlation',
            'h_diff_mean', 'h_diff_std', 'v_diff_mean', 'v_diff_std',
            'texture_complexity'
        ]
        
        # Histogram features (for each channel)
        channels = ['R', 'G', 'B', 'Gray']
        histogram_features = []
        for channel in channels:
            histogram_features.extend([
                f'{channel}_hist_entropy', f'{channel}_hist_mean', 
                f'{channel}_hist_std', f'{channel}_hist_skew'
            ])
        
        # Frequency features
        frequency_features = [
            'fft_mean', 'fft_std', 'fft_entropy', 'high_freq_energy', 
            'low_freq_energy', 'spectral_flatness'
        ]
        
        return basic_features + lsb_features + statistical_features + histogram_features + frequency_features
    
    def extract_features(self, image_path) -> Dict[str, float]:
        """
        Extract comprehensive feature vector from image with NaN handling
        Returns dictionary of feature name -> value with all NaNs replaced by 0
        """
        try:
            image = Image.open(image_path)
            features = {}
            
            # Basic information
            features.update(self._extract_basic_features(image, image_path))
            
            # Extract features with error handling
            feature_types = [
                (self._extract_lsb_features, "LSB"),
                (self._extract_histogram_features, "Histogram"),
                (self._extract_texture_features, "Texture"),
                (self._extract_frequency_features, "Frequency"),
                (self._extract_statistical_features, "Statistical")
            ]
            
            for extractor, feature_type in feature_types:
                try:
                    extracted = extractor(image)
                    features.update(extracted)
                except Exception as e:
                    print(f"Error extracting {feature_type} features from {image_path}: {str(e)}")
            
            # Replace any NaN or Inf values with 0
            for key in features:
                if np.isnan(features[key]) or np.isinf(features[key]):
                    features[key] = 0.0
            
            # Ensure all features exist with default values
            for feature_name in self.feature_names:
                if feature_name not in features:
                    features[feature_name] = 0.0
            
            # Validate features
            self._validate_features(features)
            
            return features
        except Exception as e:
            print(f"Critical error extracting features from {image_path}: {str(e)}")
            return {name: 0.0 for name in self.feature_names}
    
    def _validate_features(self, features: Dict[str, float]):
        """Validate features for numerical stability"""
        for key, value in features.items():
            if np.isnan(value) or np.isinf(value):
                features[key] = 0.0
                print(f"WARNING: {key} contained invalid value, replaced with 0")
    
    def _extract_basic_features(self, image: Image.Image, image_path: str) -> Dict[str, float]:
        """Basic image properties with file size"""
        features = {}
        features['width'] = float(image.width)
        features['height'] = float(image.height)
        features['aspect_ratio'] = max(image.width, 1) / max(image.height, 1)
        features['pixel_count'] = float(image.width * image.height)
        features['mode_length'] = float(len(image.mode))
        
        # File size
        try:
            features['file_size'] = float(image_path.stat().st_size)
        except:
            features['file_size'] = 0.0
            
        return features
    
    def _extract_lsb_features(self, image: Image.Image) -> Dict[str, float]:
        """Extract LSB-related features with numerical stability"""
        features = {}
        try:
            img_array = np.array(image)
            
            # Handle single-channel and multi-channel images
            if len(img_array.shape) == 3:
                # Convert to grayscale for LSB analysis
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_array
            
            # Extract LSB plane
            lsb_plane = gray & 1
            
            # LSB entropy
            try:
                counts = np.bincount(lsb_plane.ravel())
                if counts.sum() > 0:
                    probabilities = counts / counts.sum()
                    lsb_entropy = entropy(probabilities, base=2)
                    features['lsb_entropy'] = float(lsb_entropy)
                else:
                    features['lsb_entropy'] = 0.0
            except Exception as e:
                print(f"Error calculating LSB entropy: {e}")
                features['lsb_entropy'] = 0.0
            
            # LSB balance
            try:
                unique, counts = np.unique(lsb_plane, return_counts=True)
                if len(unique) == 2:
                    balance = min(counts[0], counts[1]) / max(counts[0], counts[1])
                else:
                    balance = 0.0
                features['lsb_balance'] = float(balance)
            except Exception as e:
                print(f"Error calculating LSB balance: {e}")
                features['lsb_balance'] = 0.0
            
            # Other LSB features
            try:
                features['lsb_mean'] = float(np.mean(lsb_plane))
                features['lsb_std'] = float(np.std(lsb_plane))
                features['lsb_variance'] = float(np.var(lsb_plane))
            except Exception as e:
                print(f"Error calculating LSB statistics: {e}")
                features.update({
                    'lsb_mean': 0.0,
                    'lsb_std': 0.0,
                    'lsb_variance': 0.0
                })
            
            # Additional LSB features
            try:
                # Correlation
                features['lsb_correlation'] = float(np.corrcoef(
                    lsb_plane[:, :-1].ravel(), 
                    lsb_plane[:, 1:].ravel()
                )[0, 1])
            except Exception as e:
                print(f"Error calculating LSB correlation: {e}")
                features['lsb_correlation'] = 0.0
            
            try:
                # Homogeneity and energy
                features['lsb_homogeneity'] = float(np.mean(
                    1 / (1 + np.diff(lsb_plane, axis=0)**2)
                ))
                features['lsb_energy'] = float(np.sum(lsb_plane**2) / lsb_plane.size)
            except Exception as e:
                print(f"Error calculating LSB texture features: {e}")
                features.update({
                    'lsb_homogeneity': 0.0,
                    'lsb_energy': 0.0
                })
            
        except Exception as e:
            print(f"Error in LSB feature extraction: {e}")
        
        return features
    
    def _extract_histogram_features(self, image: Image.Image) -> Dict[str, float]:
        """Extract histogram-based features with numerical stability"""
        features = {}
        try:
            img_array = np.array(image)
            
            # Determine number of channels
            if len(img_array.shape) == 2:
                channels = [(img_array, 'Gray')]
            else:
                channels = [
                    (img_array[:, :, i], channel) 
                    for i, channel in enumerate(['R', 'G', 'B'])
                ]
            
            for channel_data, channel_name in channels:
                try:
                    # Histogram
                    hist, _ = np.histogram(channel_data, bins=256, range=[0, 256])
                    total = float(hist.sum())
                    
                    if total == 0:
                        # Handle empty histogram
                        features[f'{channel_name}_hist_entropy'] = 0.0
                        features[f'{channel_name}_hist_mean'] = 0.0
                        features[f'{channel_name}_hist_std'] = 0.0
                        features[f'{channel_name}_hist_skew'] = 0.0
                        continue
                    
                    # Normalize histogram
                    hist = hist / total
                    
                    # Histogram entropy
                    valid_probs = hist[hist > 0]
                    hist_entropy = 0.0
                    if len(valid_probs) > 0:
                        hist_entropy = -np.sum(valid_probs * np.log2(valid_probs))
                    features[f'{channel_name}_hist_entropy'] = float(hist_entropy)
                    
                    # Histogram statistics
                    values = np.arange(256)
                    mean = np.sum(values * hist)
                    features[f'{channel_name}_hist_mean'] = float(mean)
                    
                    # Standard deviation
                    std = np.sqrt(np.sum(((values - mean) ** 2) * hist))
                    features[f'{channel_name}_hist_std'] = float(std)
                    
                    # Skewness
                    if std > 1e-10:
                        skew = np.sum(((values - mean) ** 3) * hist) / (std ** 3)
                        features[f'{channel_name}_hist_skew'] = float(skew)
                    else:
                        features[f'{channel_name}_hist_skew'] = 0.0
                    
                except Exception as e:
                    print(f"Error processing {channel_name} histogram: {e}")
                    # Set safe defaults
                    features[f'{channel_name}_hist_entropy'] = 0.0
                    features[f'{channel_name}_hist_mean'] = 0.0
                    features[f'{channel_name}_hist_std'] = 0.0
                    features[f'{channel_name}_hist_skew'] = 0.0
        
        except Exception as e:
            print(f"Error in histogram feature extraction: {e}")
        
        return features
    
    def _extract_texture_features(self, image: Image.Image) -> Dict[str, float]:
        """Extract texture-based features with numerical stability"""
        features = {}
        try:
            # Convert to grayscale for texture analysis
            if len(image.mode) != 'L':
                image = image.convert('L')
            
            img_array = np.array(image, dtype=np.float32)
            
            # Calculate differences between adjacent pixels
            try:
                h_diff = np.diff(img_array, axis=1)
                v_diff = np.diff(img_array, axis=0)
                
                # Handle empty arrays
                h_diff = h_diff if h_diff.size > 0 else np.array([0.0])
                v_diff = v_diff if v_diff.size > 0 else np.array([0.0])
                
                features['h_diff_mean'] = float(np.mean(h_diff))
                features['h_diff_std'] = float(np.std(h_diff))
                features['v_diff_mean'] = float(np.mean(v_diff))
                features['v_diff_std'] = float(np.std(v_diff))
                
                # Texture complexity
                features['texture_complexity'] = float(np.std(h_diff) + np.std(v_diff))
            except Exception as e:
                print(f"Error calculating texture features: {e}")
                features.update({
                    'h_diff_mean': 0.0,
                    'h_diff_std': 0.0,
                    'v_diff_mean': 0.0,
                    'v_diff_std': 0.0,
                    'texture_complexity': 0.0
                })
        
        except Exception as e:
            print(f"Error in texture feature extraction: {e}")
        
        return features
    
    def _extract_frequency_features(self, image: Image.Image) -> Dict[str, float]:
        """Extract frequency domain features with numerical stability"""
        features = {}
        try:
            # Convert to grayscale
            if len(image.mode) != 'L':
                image = image.convert('L')
            
            img_array = np.array(image, dtype=np.float32)
            
            # Perform FFT analysis
            try:
                # Add small epsilon to avoid log(0)
                fft = np.fft.fft2(img_array)
                fft_shifted = np.fft.fftshift(fft)
                magnitude_spectrum = np.log(np.abs(fft_shifted) + 1e-10)
                
                # Frequency domain statistics
                features['fft_mean'] = float(np.mean(magnitude_spectrum))
                features['fft_std'] = float(np.std(magnitude_spectrum))
                
                # Entropy calculation
                magnitude_flat = magnitude_spectrum.flatten()
                magnitude_flat = magnitude_flat / magnitude_flat.sum()
                features['fft_entropy'] = float(entropy(magnitude_flat, base=2))
                
                # High frequency energy
                h, w = magnitude_spectrum.shape
                center_h, center_w = h // 2, w // 2
                high_freq = magnitude_spectrum[center_h//2:3*center_h//2, center_w//2:3*center_w//2]
                features['high_freq_energy'] = float(np.mean(high_freq))
                
                # Low frequency energy
                low_freq = magnitude_spectrum[center_h//4:3*center_h//4, center_w//4:3*center_w//4]
                features['low_freq_energy'] = float(np.mean(low_freq))
                
                # Spectral flatness
                if np.min(magnitude_spectrum) > 0:
                    features['spectral_flatness'] = float(
                        np.exp(np.mean(np.log(magnitude_spectrum))) / np.mean(magnitude_spectrum)
                    )
                else:
                    features['spectral_flatness'] = 0.0
                    
            except Exception as e:
                print(f"Error in frequency analysis: {e}")
                # Set safe defaults
                features.update({
                    'fft_mean': 0.0,
                    'fft_std': 0.0,
                    'fft_entropy': 0.0,
                    'high_freq_energy': 0.0,
                    'low_freq_energy': 0.0,
                    'spectral_flatness': 0.0
                })
        
        except Exception as e:
            print(f"Error in frequency feature extraction: {e}")
        
        return features
    
    def _extract_statistical_features(self, image: Image.Image) -> Dict[str, float]:
        """Extract statistical features with numerical stability"""
        features = {}
        try:
            img_array = np.array(image, dtype=np.float32)
            
            # Overall statistics
            try:
                features['pixel_mean'] = float(np.mean(img_array))
                features['pixel_std'] = float(np.std(img_array))
                features['pixel_variance'] = float(np.var(img_array))
                features['pixel_range'] = float(np.max(img_array) - np.min(img_array))
            except Exception as e:
                print(f"Error calculating overall statistics: {e}")
                features.update({
                    'pixel_mean': 0.0,
                    'pixel_std': 0.0,
                    'pixel_variance': 0.0,
                    'pixel_range': 0.0
                })
            
            # Correlation between color channels
            try:
                if len(img_array.shape) == 3 and img_array.shape[2] >= 2:
                    features['rg_correlation'] = float(np.corrcoef(
                        img_array[:,:,0].ravel(), 
                        img_array[:,:,1].ravel()
                    )[0,1])
                else:
                    features['rg_correlation'] = 0.0
                
                if len(img_array.shape) == 3 and img_array.shape[2] >= 3:
                    features['rb_correlation'] = float(np.corrcoef(
                        img_array[:,:,0].ravel(), 
                        img_array[:,:,2].ravel()
                    )[0,1])
                    features['gb_correlation'] = float(np.corrcoef(
                        img_array[:,:,1].ravel(), 
                        img_array[:,:,2].ravel()
                    )[0,1])
                else:
                    features['rb_correlation'] = 0.0
                    features['gb_correlation'] = 0.0
            except Exception as e:
                print(f"Error calculating channel correlations: {e}")
                features.update({
                    'rg_correlation': 0.0,
                    'rb_correlation': 0.0,
                    'gb_correlation': 0.0
                })
        
        except Exception as e:
            print(f"Error in statistical feature extraction: {e}")
        
        return features
    
    def get_feature_names(self) -> List[str]:
        """Get list of all feature names"""
        return self.feature_names
    
    def features_to_vector(self, features: Dict[str, float]) -> List[float]:
        """Convert feature dictionary to vector (ordered) with NaN handling"""
        # Ensure all features exist
        for name in self.feature_names:
            if name not in features:
                features[name] = 0.0
        
        # Replace any NaN values
        vector = []
        for name in self.feature_names:
            value = features[name]
            if np.isnan(value) or np.isinf(value):
                value = 0.0
            vector.append(float(value))
        
        return vector
