"""Tests for JPEG Ghost analyzer (Phase 2 forensics)."""
import pytest
from pathlib import Path
from PIL import Image
import numpy as np


class TestJPEGGhostAnalyzer:
    """Test JPEG Ghost detection (double compression detection)."""
    
    def test_jpeg_ghost_basic(self, sample_stego_image):
        """Test basic JPEG Ghost analysis."""
        from src.core.jpeg_ghost_analyzer import JPEGGhostAnalyzer
        
        analyzer = JPEGGhostAnalyzer()
        result = analyzer.analyze(str(sample_stego_image))
        
        assert isinstance(result, dict)
        assert "suspicion_score" in result
        assert 0 <= result["suspicion_score"] <= 100
    
    def test_jpeg_ghost_return_format(self, sample_stego_image):
        """Test return value structure."""
        from src.core.jpeg_ghost_analyzer import JPEGGhostAnalyzer
        
        analyzer = JPEGGhostAnalyzer()
        result = analyzer.analyze(str(sample_stego_image))
        
        assert "suspicion_score" in result
        assert "description" in result
        assert isinstance(result["suspicion_score"], (int, float))
        assert isinstance(result["description"], str)
    
    def test_jpeg_ghost_non_jpeg(self, sample_clean_image):
        """Test that non-JPEG files are handled gracefully."""
        from src.core.jpeg_ghost_analyzer import JPEGGhostAnalyzer
        
        analyzer = JPEGGhostAnalyzer()
        result = analyzer.analyze(str(sample_clean_image))
        
        # Should return low or zero score for non-JPEG
        assert "suspicion_score" in result
        assert result["suspicion_score"] >= 0
    
    def test_jpeg_ghost_quality_parameter(self, sample_stego_image):
        """Test with different quality parameters."""
        from src.core.jpeg_ghost_analyzer import JPEGGhostAnalyzer
        
        analyzer = JPEGGhostAnalyzer()
        result1 = analyzer.analyze(str(sample_stego_image), quality=90)
        result2 = analyzer.analyze(str(sample_stego_image), quality=75)
        
        assert "suspicion_score" in result1
        assert "suspicion_score" in result2
    
    def test_jpeg_ghost_missing_file(self):
        """Test handling of missing file."""
        from src.core.jpeg_ghost_analyzer import JPEGGhostAnalyzer
        
        analyzer = JPEGGhostAnalyzer()
        result = analyzer.analyze("/nonexistent/file.jpg")
        
        # Should handle gracefully
        assert "suspicion_score" in result
    
    def test_jpeg_ghost_blank_image(self, blank_image):
        """Test with blank image."""
        from src.core.jpeg_ghost_analyzer import JPEGGhostAnalyzer
        
        analyzer = JPEGGhostAnalyzer()
        result = analyzer.analyze(str(blank_image))
        
        assert isinstance(result, dict)
        assert "suspicion_score" in result


class TestJPEGGhostEdgeCases:
    """Test edge cases for JPEG Ghost detection."""
    
    def test_very_small_image(self, test_data_dir):
        """Test with very small image."""
        from src.core.jpeg_ghost_analyzer import JPEGGhostAnalyzer
        
        # Create a 16x16 image
        small_path = test_data_dir / "tiny_image.png"
        if not small_path.exists():
            img = Image.fromarray(np.random.randint(0, 256, (16, 16, 3), dtype=np.uint8))
            img.save(small_path)
        
        analyzer = JPEGGhostAnalyzer()
        result = analyzer.analyze(str(small_path))
        
        assert "suspicion_score" in result
        assert 0 <= result["suspicion_score"] <= 100
    
    def test_large_image(self, test_data_dir):
        """Test with larger image."""
        from src.core.jpeg_ghost_analyzer import JPEGGhostAnalyzer
        
        # Create a 1024x1024 image
        large_path = test_data_dir / "large_image.png"
        if not large_path.exists():
            img = Image.fromarray(np.random.randint(0, 256, (1024, 1024, 3), dtype=np.uint8))
            img.save(large_path)
        
        analyzer = JPEGGhostAnalyzer()
        result = analyzer.analyze(str(large_path))
        
        assert "suspicion_score" in result
    
    def test_grayscale_jpeg_ghost(self, sample_grayscale_image):
        """Test JPEG Ghost with grayscale image."""
        from src.core.jpeg_ghost_analyzer import JPEGGhostAnalyzer
        
        analyzer = JPEGGhostAnalyzer()
        result = analyzer.analyze(str(sample_grayscale_image))
        
        assert "suspicion_score" in result
        assert result["suspicion_score"] >= 0
