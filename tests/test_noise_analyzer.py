"""Tests for Noise analyzer (Phase 2 forensics)."""
import pytest
from pathlib import Path
from PIL import Image
import numpy as np


class TestNoiseAnalyzer:
    """Test Noise detection using Laplacian filtering."""
    
    def test_noise_basic(self, sample_clean_image):
        """Test basic noise analysis."""
        from src.core.noise_analyzer import NoiseAnalyzer
        
        analyzer = NoiseAnalyzer()
        result = analyzer.analyze(str(sample_clean_image))
        
        assert isinstance(result, dict)
        assert "suspicion_score" in result
        assert 0 <= result["suspicion_score"] <= 100
    
    def test_noise_return_format(self, sample_stego_image):
        """Test return value structure."""
        from src.core.noise_analyzer import NoiseAnalyzer
        
        analyzer = NoiseAnalyzer()
        result = analyzer.analyze(str(sample_stego_image))
        
        assert "suspicion_score" in result
        assert "description" in result
        assert isinstance(result["suspicion_score"], (int, float))
    
    def test_noise_clean_vs_stego(self, sample_clean_image, sample_stego_image):
        """Test that stego images may have different noise patterns."""
        from src.core.noise_analyzer import NoiseAnalyzer
        
        analyzer = NoiseAnalyzer()
        clean_result = analyzer.analyze(str(sample_clean_image))
        stego_result = analyzer.analyze(str(sample_stego_image))
        
        assert "suspicion_score" in clean_result
        assert "suspicion_score" in stego_result
        # Both should be valid scores
        assert 0 <= clean_result["suspicion_score"] <= 100
        assert 0 <= stego_result["suspicion_score"] <= 100
    
    def test_noise_blank_image(self, blank_image):
        """Test with blank image (no noise)."""
        from src.core.noise_analyzer import NoiseAnalyzer
        
        analyzer = NoiseAnalyzer()
        result = analyzer.analyze(str(blank_image))
        
        assert "suspicion_score" in result
        # Blank image should have low noise
        assert result["suspicion_score"] >= 0
    
    def test_noise_high_entropy_image(self, test_data_dir):
        """Test with high-entropy (random) image."""
        from src.core.noise_analyzer import NoiseAnalyzer
        
        # Create high-entropy image
        path = test_data_dir / "high_entropy.png"
        if not path.exists():
            img_array = np.random.randint(0, 256, (256, 256, 3), dtype=np.uint8)
            img = Image.fromarray(img_array)
            img.save(path)
        
        analyzer = NoiseAnalyzer()
        result = analyzer.analyze(str(path))
        
        assert "suspicion_score" in result
    
    def test_noise_smooth_image(self, test_data_dir):
        """Test with smooth (low entropy) image."""
        from src.core.noise_analyzer import NoiseAnalyzer
        
        # Create smooth image
        path = test_data_dir / "smooth_image.png"
        if not path.exists():
            img_array = np.full((256, 256, 3), 128, dtype=np.uint8)
            img = Image.fromarray(img_array)
            img.save(path)
        
        analyzer = NoiseAnalyzer()
        result = analyzer.analyze(str(path))
        
        assert "suspicion_score" in result
        # Smooth image should have low noise
        assert result["suspicion_score"] >= 0
    
    def test_noise_missing_file(self):
        """Test handling of missing file."""
        from src.core.noise_analyzer import NoiseAnalyzer
        
        analyzer = NoiseAnalyzer()
        result = analyzer.analyze("/nonexistent/file.png")
        
        assert "suspicion_score" in result
    
    def test_noise_grayscale(self, sample_grayscale_image):
        """Test with grayscale image."""
        from src.core.noise_analyzer import NoiseAnalyzer
        
        analyzer = NoiseAnalyzer()
        result = analyzer.analyze(str(sample_grayscale_image))
        
        assert "suspicion_score" in result
    
    def test_noise_rgba(self, sample_rgba_image):
        """Test with RGBA image."""
        from src.core.noise_analyzer import NoiseAnalyzer
        
        analyzer = NoiseAnalyzer()
        result = analyzer.analyze(str(sample_rgba_image))
        
        assert "suspicion_score" in result


class TestNoiseEdgeCases:
    """Test edge cases for noise detection."""
    
    def test_noise_very_small_image(self, test_data_dir):
        """Test with very small image."""
        from src.core.noise_analyzer import NoiseAnalyzer
        
        path = test_data_dir / "tiny_noise.png"
        if not path.exists():
            img = Image.fromarray(np.random.randint(0, 256, (8, 8, 3), dtype=np.uint8))
            img.save(path)
        
        analyzer = NoiseAnalyzer()
        result = analyzer.analyze(str(path))
        
        assert "suspicion_score" in result
    
    def test_noise_large_image(self, test_data_dir):
        """Test with large image."""
        from src.core.noise_analyzer import NoiseAnalyzer
        
        path = test_data_dir / "large_noise.png"
        if not path.exists():
            img = Image.fromarray(np.random.randint(0, 256, (1024, 1024, 3), dtype=np.uint8))
            img.save(path)
        
        analyzer = NoiseAnalyzer()
        result = analyzer.analyze(str(path))
        
        assert "suspicion_score" in result
