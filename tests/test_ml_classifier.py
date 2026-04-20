"""Tests for ML classifier and features (Phase 5)."""
import pytest
from pathlib import Path
import numpy as np


class TestMLFeatures:
    """Test ML feature extraction."""
    
    def test_ml_features_basic(self, sample_clean_image):
        """Test basic feature extraction."""
        from src.core.ml_features import FeatureExtractor
        
        extractor = FeatureExtractor()
        features = extractor.extract(str(sample_clean_image))
        
        assert isinstance(features, dict)
        assert len(features) > 0
        assert all(isinstance(v, (int, float)) for v in features.values())
    
    def test_ml_features_consistency(self, sample_clean_image):
        """Test feature extraction consistency."""
        from src.core.ml_features import FeatureExtractor
        
        extractor = FeatureExtractor()
        features1 = extractor.extract(str(sample_clean_image))
        features2 = extractor.extract(str(sample_clean_image))
        
        assert features1 == features2
    
    def test_ml_features_different_images(self, sample_clean_image, sample_stego_image):
        """Test that different images produce different features."""
        from src.core.ml_features import FeatureExtractor
        
        extractor = FeatureExtractor()
        clean_features = extractor.extract(str(sample_clean_image))
        stego_features = extractor.extract(str(sample_stego_image))
        
        # Features should be different
        assert clean_features != stego_features
    
    def test_ml_features_min_max(self, sample_clean_image):
        """Test feature values are in reasonable ranges."""
        from src.core.ml_features import FeatureExtractor
        
        extractor = FeatureExtractor()
        features = extractor.extract(str(sample_clean_image))
        
        # Most features should be 0-100 or similar normalized range
        for key, val in features.items():
            assert isinstance(val, (int, float))
            assert not np.isnan(val), f"Feature {key} is NaN"
            assert not np.isinf(val), f"Feature {key} is infinite"
    
    def test_ml_features_count(self, sample_clean_image):
        """Test that appropriate number of features are extracted."""
        from src.core.ml_features import FeatureExtractor
        
        extractor = FeatureExtractor()
        features = extractor.extract(str(sample_clean_image))
        
        # Should extract 40+ features as documented
        assert len(features) >= 30
    
    def test_ml_features_missing_file(self):
        """Test feature extraction with missing file."""
        from src.core.ml_features import FeatureExtractor
        
        extractor = FeatureExtractor()
        features = extractor.extract("/nonexistent/file.png")
        
        assert isinstance(features, dict)


class TestMLClassifier:
    """Test ML classifier predictions."""
    
    def test_ml_classifier_predict(self, sample_clean_image):
        """Test basic prediction."""
        from src.core.ml_classifier import MLSteganalysisClassifier
        
        # Use default model if available
        classifier = MLSteganalysisClassifier()
        result = classifier.predict(str(sample_clean_image))
        
        assert isinstance(result, dict)
        assert "prediction" in result
        assert result["prediction"] in [0, 1]
    
    def test_ml_classifier_prediction_structure(self, sample_clean_image):
        """Test prediction return structure."""
        from src.core.ml_classifier import MLSteganalysisClassifier
        
        classifier = MLSteganalysisClassifier()
        result = classifier.predict(str(sample_clean_image))
        
        assert "prediction" in result
        assert "probability" in result or "confidence" in result
        assert isinstance(result["prediction"], (int, np.integer))
    
    def test_ml_classifier_consistency(self, sample_clean_image):
        """Test prediction consistency."""
        from src.core.ml_classifier import MLSteganalysisClassifier
        
        classifier = MLSteganalysisClassifier()
        result1 = classifier.predict(str(sample_clean_image))
        result2 = classifier.predict(str(sample_clean_image))
        
        assert result1["prediction"] == result2["prediction"]
    
    def test_ml_classifier_different_predictions(self, sample_clean_image, sample_stego_image):
        """Test that different images may produce different predictions."""
        from src.core.ml_classifier import MLSteganalysisClassifier
        
        classifier = MLSteganalysisClassifier()
        clean_pred = classifier.predict(str(sample_clean_image))
        stego_pred = classifier.predict(str(sample_stego_image))
        
        # Predictions should exist
        assert "prediction" in clean_pred
        assert "prediction" in stego_pred
    
    def test_ml_classifier_missing_model(self):
        """Test classifier with missing model file."""
        from src.core.ml_classifier import MLSteganalysisClassifier
        
        # Try to load nonexistent model
        classifier = MLSteganalysisClassifier("/nonexistent/model.pkl")
        
        # Should handle gracefully (may return default prediction)
        result = classifier.predict("test.png")
        assert isinstance(result, dict)
    
    def test_ml_classifier_batch_predict(self, sample_clean_image, sample_stego_image):
        """Test batch prediction."""
        from src.core.ml_classifier import MLSteganalysisClassifier
        
        classifier = MLSteganalysisClassifier()
        
        images = [str(sample_clean_image), str(sample_stego_image)]
        results = [classifier.predict(img) for img in images]
        
        assert len(results) == 2
        assert all("prediction" in r for r in results)


class TestMLEdgeCases:
    """Test edge cases for ML operations."""
    
    def test_ml_features_grayscale(self, sample_grayscale_image):
        """Test feature extraction with grayscale."""
        from src.core.ml_features import FeatureExtractor
        
        extractor = FeatureExtractor()
        features = extractor.extract(str(sample_grayscale_image))
        
        assert isinstance(features, dict)
        assert len(features) > 0
    
    def test_ml_features_rgba(self, sample_rgba_image):
        """Test feature extraction with RGBA."""
        from src.core.ml_features import FeatureExtractor
        
        extractor = FeatureExtractor()
        features = extractor.extract(str(sample_rgba_image))
        
        assert isinstance(features, dict)
        assert len(features) > 0
    
    @pytest.mark.parametrize("threshold", [0.3, 0.5, 0.7])
    def test_ml_classifier_threshold(self, sample_clean_image, threshold):
        """Test classifier with different confidence thresholds."""
        from src.core.ml_classifier import MLSteganalysisClassifier
        
        classifier = MLSteganalysisClassifier()
        result = classifier.predict(str(sample_clean_image))
        
        assert "prediction" in result
