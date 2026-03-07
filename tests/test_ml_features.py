import warnings
warnings.filterwarnings('ignore', category=RuntimeWarning)

import unittest
from pathlib import Path
from src.core.ml_features import MLFeatureExtractor
from PIL import Image

class TestMLFeatures(unittest.TestCase):
    def setUp(self):
        self.extractor = MLFeatureExtractor()
        self.test_dir = Path("test_images")
        self.test_dir.mkdir(exist_ok=True)
        
        # Create test image
        self.test_image_path = self.test_dir / "test_ml_features.png"
        img = Image.new('RGB', (100, 100), color='red')
        img.save(self.test_image_path)
    
    def tearDown(self):
        if self.test_image_path.exists():
            self.test_image_path.unlink()
    
    def test_basic_features(self):
        """Test basic feature extraction"""
        features = self.extractor.extract_features(self.test_image_path)
        self.assertIn('width', features)
        self.assertIn('height', features)
        self.assertIn('aspect_ratio', features)
        self.assertEqual(features['width'], 100.0)
        self.assertEqual(features['height'], 100.0)
    
    def test_lsb_features(self):
        """Test LSB feature extraction"""
        features = self.extractor.extract_features(self.test_image_path)
        self.assertIn('lsb_entropy', features)
        self.assertIn('lsb_balance', features)
        self.assertIn('lsb_mean', features)
        self.assertGreaterEqual(features['lsb_entropy'], 0.0)
        self.assertLessEqual(features['lsb_balance'], 1.0)
    
    def test_histogram_features(self):
        """Test histogram feature extraction"""
        features = self.extractor.extract_features(self.test_image_path)
        # Check for color channel features
        self.assertIn('R_hist_entropy', features)
        self.assertIn('G_hist_entropy', features)
        self.assertIn('B_hist_entropy', features)
    
    def test_frequency_features(self):
        """Test frequency feature extraction"""
        features = self.extractor.extract_features(self.test_image_path)
        self.assertIn('fft_mean', features)
        self.assertIn('fft_std', features)
        self.assertIn('fft_entropy', features)
        self.assertIn('high_freq_energy', features)
    
    def test_features_to_vector(self):
        """Test converting features to vector"""
        features = self.extractor.extract_features(self.test_image_path)
        vector = self.extractor.features_to_vector(features)
        self.assertIsInstance(vector, list)
        self.assertTrue(all(isinstance(x, (int, float)) for x in vector))
        self.assertTrue(len(vector) > 0)

if __name__ == '__main__':
    unittest.main()
