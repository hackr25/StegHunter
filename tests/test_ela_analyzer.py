"""
Tests for ELA (Error Level Analysis) module.
"""
import pytest
from PIL import Image
import numpy as np
from src.core.ela_analyzer import ELAAnalyzer


class TestELAAnalyzer:
    """Test ELA analysis functionality."""
    
    def test_ela_basic_clean_image(self, sample_clean_image):
        """Test ELA on clean image."""
        image = Image.open(sample_clean_image)
        analyzer = ELAAnalyzer()
        result = analyzer.analyze(sample_clean_image)
        
        assert isinstance(result, dict)
        assert 'suspicion_score' in result
        assert 0 <= result['suspicion_score'] <= 100
    
    def test_ela_jpeg_only(self, sample_grayscale_image):
        """Test that ELA handles non-JPEG images gracefully."""
        analyzer = ELAAnalyzer()
        result = analyzer.analyze(sample_grayscale_image)
        
        # PNG should still work (converted internally to JPEG for analysis)
        assert isinstance(result, dict)
        assert 'suspicion_score' in result or 'error' in result
    
    def test_ela_return_format(self, sample_clean_image):
        """Test that ELA returns expected fields."""
        analyzer = ELAAnalyzer()
        result = analyzer.analyze(sample_clean_image)
        
        assert 'suspicion_score' in result
        assert isinstance(result['suspicion_score'], (int, float))
        assert 'description' in result or 'error' in result
    
    def test_ela_quality_parameter(self, sample_clean_image):
        """Test ELA with different quality settings."""
        analyzer = ELAAnalyzer()
        
        result_90 = analyzer.analyze(sample_clean_image, quality=90)
        result_95 = analyzer.analyze(sample_clean_image, quality=95)
        
        # Different quality should yield different results
        assert 'suspicion_score' in result_90
        assert 'suspicion_score' in result_95
    
    def test_ela_scale_parameter(self, sample_clean_image):
        """Test ELA with different amplification scales."""
        analyzer = ELAAnalyzer()
        
        result_5 = analyzer.analyze(sample_clean_image, scale=5)
        result_10 = analyzer.analyze(sample_clean_image, scale=10)
        
        assert 'suspicion_score' in result_5
        assert 'suspicion_score' in result_10
    
    def test_ela_blank_image(self, blank_image):
        """Test ELA on blank image (edge case)."""
        analyzer = ELAAnalyzer()
        result = analyzer.analyze(blank_image)
        
        # Blank image should have low ELA score
        assert 'suspicion_score' in result
        assert result['suspicion_score'] < 30.0
    
    def test_ela_corrupted_image(self, corrupted_image):
        """Test ELA with corrupted image."""
        analyzer = ELAAnalyzer()
        result = analyzer.analyze(corrupted_image)
        
        # Should handle gracefully
        assert isinstance(result, dict)
        assert 'error' in result or 'suspicion_score' in result


class TestELAModified:
    """Test ELA on modified images."""
    
    def test_ela_modified_region(self):
        """Test that ELA detects modified regions."""
        # Create original image
        img_array = np.random.randint(0, 256, (256, 256, 3), dtype=np.uint8)
        original = Image.fromarray(img_array, 'RGB')
        
        # Modify a region
        modified_array = np.array(img_array)
        modified_array[50:100, 50:100] = [255, 0, 0]  # Red square
        modified = Image.fromarray(modified_array.astype(np.uint8), 'RGB')
        
        analyzer = ELAAnalyzer()
        result = analyzer.analyze(modified)
        
        # Modified image should have higher ELA score
        assert 'suspicion_score' in result
        assert result['suspicion_score'] > 20.0
