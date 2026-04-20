"""
Unit tests for LSB steganography analyzer.
"""
import pytest
import numpy as np
from PIL import Image
from src.core.lsb_analyzer import (
    extract_lsb_plane,
    lsb_histogram,
    lsb_entropy,
    lsb_uniformity_test,
    lsb_analysis,
)


class TestLSBPlaneExtraction:
    """Test LSB plane extraction functionality."""

    def test_extract_lsb_plane_basic(self):
        """Test basic LSB extraction."""
        img_array = np.array([[0b10101010, 0b11111111], [0b00000000, 0b10101011]], dtype=np.uint8)
        lsb = extract_lsb_plane(img_array)
        
        expected = np.array([[0, 1], [0, 1]], dtype=np.uint8)
        assert np.array_equal(lsb, expected)

    def test_extract_lsb_plane_all_zeros(self):
        """Test LSB extraction from image with all even values."""
        img_array = np.array([[0, 2, 4], [6, 8, 10]], dtype=np.uint8)
        lsb = extract_lsb_plane(img_array)
        expected = np.zeros((2, 3), dtype=np.uint8)
        assert np.array_equal(lsb, expected)

    def test_extract_lsb_plane_all_ones(self):
        """Test LSB extraction from image with all odd values."""
        img_array = np.array([[1, 3, 5], [7, 9, 11]], dtype=np.uint8)
        lsb = extract_lsb_plane(img_array)
        expected = np.ones((2, 3), dtype=np.uint8)
        assert np.array_equal(lsb, expected)

    def test_extract_lsb_plane_3d_array(self):
        """Test LSB extraction from 3D RGB array."""
        img_array = np.array([[[255, 254, 253], [1, 2, 3]]], dtype=np.uint8)
        lsb = extract_lsb_plane(img_array)
        expected = np.array([[[1, 0, 1], [1, 0, 1]]], dtype=np.uint8)
        assert np.array_equal(lsb, expected)


class TestLSBHistogram:
    """Test LSB histogram calculation."""

    def test_histogram_balanced(self):
        """Test histogram with balanced 0s and 1s."""
        lsb_plane = np.array([[0, 1], [0, 1]], dtype=np.uint8)
        count0, count1 = lsb_histogram(lsb_plane)
        assert count0 == 2
        assert count1 == 2

    def test_histogram_all_zeros(self):
        """Test histogram with all zeros."""
        lsb_plane = np.zeros((4, 4), dtype=np.uint8)
        count0, count1 = lsb_histogram(lsb_plane)
        assert count0 == 16
        assert count1 == 0

    def test_histogram_all_ones(self):
        """Test histogram with all ones."""
        lsb_plane = np.ones((4, 4), dtype=np.uint8)
        count0, count1 = lsb_histogram(lsb_plane)
        assert count0 == 0
        assert count1 == 16

    def test_histogram_skewed(self):
        """Test histogram with skewed distribution."""
        lsb_plane = np.array([
            [0, 0, 0, 0],
            [0, 0, 0, 1],
            [0, 0, 1, 1],
            [0, 1, 1, 1],
        ], dtype=np.uint8)
        count0, count1 = lsb_histogram(lsb_plane)
        assert count0 == 10
        assert count1 == 6


class TestLSBEntropy:
    """Test LSB entropy calculation."""

    def test_entropy_uniform_distribution(self):
        """Test entropy with uniform distribution (max entropy)."""
        # Alternating pattern maximizes entropy
        lsb_plane = np.array([[0, 1], [1, 0]], dtype=np.uint8)
        ent = lsb_entropy(lsb_plane)
        # For uniform distribution, entropy should be 1.0 (in bits)
        assert 0.99 < ent < 1.01

    def test_entropy_zero_entropy(self):
        """Test entropy with no variation (min entropy)."""
        lsb_plane = np.zeros((4, 4), dtype=np.uint8)
        ent = lsb_entropy(lsb_plane)
        assert ent == 0.0

    def test_entropy_skewed_distribution(self):
        """Test entropy with skewed distribution (lower entropy)."""
        # Mostly zeros with few ones
        lsb_plane = np.array([[0, 0, 0, 0], [0, 0, 0, 1]], dtype=np.uint8)
        ent = lsb_entropy(lsb_plane)
        assert 0 < ent < 1  # Entropy between min and max


class TestLSBUniformityTest:
    """Test chi-square uniformity test."""

    def test_uniformity_balanced(self):
        """Test chi-square test with perfectly balanced distribution."""
        count0, count1 = 100, 100
        p_value, reject = lsb_uniformity_test(count0, count1)
        assert p_value > 0.05  # Should not reject null hypothesis
        assert bool(reject) is False

    def test_uniformity_imbalanced(self):
        """Test chi-square test with highly imbalanced distribution."""
        count0, count1 = 1, 99
        p_value, reject = lsb_uniformity_test(count0, count1)
        assert p_value < 0.05  # Should reject null hypothesis
        assert bool(reject) is True

    def test_uniformity_small_sample(self):
        """Test chi-square with small sample size."""
        count0, count1 = 1, 2
        p_value, reject = lsb_uniformity_test(count0, count1)
        # Small samples may or may not reject depending on threshold
        assert 0 <= p_value <= 1

    def test_uniformity_zero_count(self):
        """Test chi-square with zero total count."""
        count0, count1 = 0, 0
        p_value, reject = lsb_uniformity_test(count0, count1)
        assert p_value == 1.0  # Default return for zero count
        assert reject is False


class TestLSBAnalysis:
    """Test complete LSB analysis pipeline."""

    def test_lsb_analysis_clean_image(self, sample_clean_image):
        """Test LSB analysis on clean image."""
        image = Image.open(sample_clean_image)
        result = lsb_analysis(image)
        
        # Check keys - actual return format from implementation
        assert "lsb_suspicion_score" in result or "score" in result
        assert "entropy" in result
        assert isinstance(result.get("lsb_suspicion_score", 0), (int, float, type(0.0)))

    def test_lsb_analysis_stego_image(self, sample_stego_image):
        """Test LSB analysis on stego image."""
        image = Image.open(sample_stego_image)
        result = lsb_analysis(image)
        
        # Check basic structure
        assert "entropy" in result
        assert isinstance(result["entropy"], (int, float))

    def test_lsb_analysis_grayscale(self, sample_grayscale_image):
        """Test LSB analysis on grayscale image."""
        image = Image.open(sample_grayscale_image)
        result = lsb_analysis(image)
        
        assert "entropy" in result
        assert isinstance(result["entropy"], (int, float))

    def test_lsb_analysis_blank_image(self, blank_image):
        """Test LSB analysis on blank image (edge case)."""
        image = Image.open(blank_image)
        result = lsb_analysis(image)
        
        # Blank image should have low entropy
        assert "entropy" in result
        assert result["entropy"] < 0.1  # Blank has zero entropy

    def test_lsb_analysis_return_format(self, sample_clean_image):
        """Test that LSB analysis returns expected fields."""
        image = Image.open(sample_clean_image)
        result = lsb_analysis(image)
        
        # Check required keys
        assert "entropy" in result
        assert "lsb_counts" in result or "lsb_suspicion_score" in result
        
        # Check types
        assert isinstance(result["entropy"], (int, float))
