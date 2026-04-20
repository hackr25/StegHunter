"""
Unit tests for statistical analysis methods.
"""
import pytest
import numpy as np
from PIL import Image
from src.core.statistical_tests import chi_square_test, pixel_value_differencing


class TestChiSquareTest:
    """Test chi-square histogram uniformity test."""

    def test_chi_square_clean_image(self, sample_clean_image):
        """Test chi-square on clean image."""
        image = Image.open(sample_clean_image)
        result = chi_square_test(image)
        
        # Should return a dict with some result
        assert isinstance(result, dict)
        # Should contain some kind of score metric
        assert len(result) > 0

    def test_chi_square_grayscale(self, sample_grayscale_image):
        """Test chi-square on grayscale image."""
        image = Image.open(sample_grayscale_image)
        result = chi_square_test(image)
        
        assert isinstance(result, dict)
        assert len(result) > 0

    def test_chi_square_blank_image(self, blank_image):
        """Test chi-square on blank image (edge case)."""
        image = Image.open(blank_image)
        result = chi_square_test(image)
        
        # Blank image should return valid result
        assert isinstance(result, dict)


class TestPixelValueDifferencing:
    """Test pixel value differencing method."""

    def test_pixel_differencing_clean(self, sample_clean_image):
        """Test pixel differencing on clean image."""
        image = Image.open(sample_clean_image)
        result = pixel_value_differencing(image)
        
        assert isinstance(result, dict)
        assert len(result) > 0

    def test_pixel_differencing_grayscale(self, sample_grayscale_image):
        """Test pixel differencing on grayscale image."""
        image = Image.open(sample_grayscale_image)
        result = pixel_value_differencing(image)
        
        assert isinstance(result, dict)
        assert len(result) > 0

    def test_pixel_differencing_blank_image(self, blank_image):
        """Test pixel differencing on blank image (edge case)."""
        image = Image.open(blank_image)
        result = pixel_value_differencing(image)
        
        assert isinstance(result, dict)


class TestStatisticalEdgeCases:
    """Test statistical methods with edge cases."""

    def test_single_pixel_image(self):
        """Test with minimal 1x1 image."""
        img_array = np.array([[128, 64, 32]], dtype=np.uint8).reshape(1, 1, 3)
        image = Image.fromarray(img_array, mode='RGB')
        
        # Should not crash
        result = chi_square_test(image)
        assert isinstance(result, dict)

    def test_rgb_vs_grayscale(self, sample_clean_image):
        """Test that both RGB and grayscale images are handled."""
        image = Image.open(sample_clean_image)
        rgb_result = chi_square_test(image)
        
        # Convert to grayscale
        gray_image = image.convert('L')
        gray_result = chi_square_test(gray_image)
        
        # Both should return valid results
        assert isinstance(rgb_result, dict)
        assert isinstance(gray_result, dict)
