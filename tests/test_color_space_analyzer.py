"""Tests for Color Space analyzer (Phase 2 forensics)."""
import pytest
from pathlib import Path
from PIL import Image
import numpy as np


class TestColorSpaceAnalyzer:
    """Test color space analysis (YCbCr distribution)."""
    
    def test_color_space_basic(self, sample_clean_image):
        """Test basic color space analysis."""
        from src.core.color_space_analyzer import ColorSpaceAnalyzer
        
        analyzer = ColorSpaceAnalyzer()
        result = analyzer.analyze(str(sample_clean_image))
        
        assert isinstance(result, dict)
        assert "suspicion_score" in result
        assert 0 <= result["suspicion_score"] <= 100
    
    def test_color_space_return_format(self, sample_stego_image):
        """Test return value structure."""
        from src.core.color_space_analyzer import ColorSpaceAnalyzer
        
        analyzer = ColorSpaceAnalyzer()
        result = analyzer.analyze(str(sample_stego_image))
        
        assert "suspicion_score" in result
        assert "description" in result
        assert isinstance(result["suspicion_score"], (int, float))
    
    def test_color_space_rgb_image(self, sample_clean_image):
        """Test with RGB image."""
        from src.core.color_space_analyzer import ColorSpaceAnalyzer
        
        analyzer = ColorSpaceAnalyzer()
        result = analyzer.analyze(str(sample_clean_image))
        
        assert "suspicion_score" in result
        assert result["suspicion_score"] >= 0
    
    def test_color_space_grayscale(self, sample_grayscale_image):
        """Test with grayscale image."""
        from src.core.color_space_analyzer import ColorSpaceAnalyzer
        
        analyzer = ColorSpaceAnalyzer()
        result = analyzer.analyze(str(sample_grayscale_image))
        
        assert "suspicion_score" in result
    
    def test_color_space_rgba(self, sample_rgba_image):
        """Test with RGBA image."""
        from src.core.color_space_analyzer import ColorSpaceAnalyzer
        
        analyzer = ColorSpaceAnalyzer()
        result = analyzer.analyze(str(sample_rgba_image))
        
        assert "suspicion_score" in result
    
    def test_color_space_blank_image(self, blank_image):
        """Test with blank image."""
        from src.core.color_space_analyzer import ColorSpaceAnalyzer
        
        analyzer = ColorSpaceAnalyzer()
        result = analyzer.analyze(str(blank_image))
        
        assert "suspicion_score" in result
    
    def test_color_space_uniform_color(self, test_data_dir):
        """Test with uniform color image."""
        from src.core.color_space_analyzer import ColorSpaceAnalyzer
        
        path = test_data_dir / "uniform_color.png"
        if not path.exists():
            img_array = np.full((256, 256, 3), [100, 150, 200], dtype=np.uint8)
            img = Image.fromarray(img_array)
            img.save(path)
        
        analyzer = ColorSpaceAnalyzer()
        result = analyzer.analyze(str(path))
        
        assert "suspicion_score" in result
    
    def test_color_space_high_variance(self, test_data_dir):
        """Test with high variance color image."""
        from src.core.color_space_analyzer import ColorSpaceAnalyzer
        
        path = test_data_dir / "high_variance_color.png"
        if not path.exists():
            img_array = np.random.randint(0, 256, (256, 256, 3), dtype=np.uint8)
            img = Image.fromarray(img_array)
            img.save(path)
        
        analyzer = ColorSpaceAnalyzer()
        result = analyzer.analyze(str(path))
        
        assert "suspicion_score" in result
    
    def test_color_space_missing_file(self):
        """Test handling of missing file."""
        from src.core.color_space_analyzer import ColorSpaceAnalyzer
        
        analyzer = ColorSpaceAnalyzer()
        result = analyzer.analyze("/nonexistent/file.png")
        
        assert "suspicion_score" in result


class TestColorSpaceEdgeCases:
    """Test edge cases for color space analysis."""
    
    def test_color_space_tiny_image(self, test_data_dir):
        """Test with very small image."""
        from src.core.color_space_analyzer import ColorSpaceAnalyzer
        
        path = test_data_dir / "tiny_color.png"
        if not path.exists():
            img = Image.fromarray(np.random.randint(0, 256, (4, 4, 3), dtype=np.uint8))
            img.save(path)
        
        analyzer = ColorSpaceAnalyzer()
        result = analyzer.analyze(str(path))
        
        assert "suspicion_score" in result
    
    def test_color_space_large_image(self, test_data_dir):
        """Test with large image."""
        from src.core.color_space_analyzer import ColorSpaceAnalyzer
        
        path = test_data_dir / "large_color.png"
        if not path.exists():
            img = Image.fromarray(np.random.randint(0, 256, (1024, 1024, 3), dtype=np.uint8))
            img.save(path)
        
        analyzer = ColorSpaceAnalyzer()
        result = analyzer.analyze(str(path))
        
        assert "suspicion_score" in result
    
    @pytest.mark.parametrize("channels", [1, 3, 4])
    def test_color_space_different_channels(self, test_data_dir, channels):
        """Test with different channel counts."""
        from src.core.color_space_analyzer import ColorSpaceAnalyzer
        
        path = test_data_dir / f"image_channels_{channels}.png"
        if not path.exists():
            if channels == 1:
                img_array = np.random.randint(0, 256, (64, 64), dtype=np.uint8)
                img = Image.fromarray(img_array, mode='L')
            elif channels == 3:
                img_array = np.random.randint(0, 256, (64, 64, 3), dtype=np.uint8)
                img = Image.fromarray(img_array, mode='RGB')
            else:  # 4
                img_array = np.random.randint(0, 256, (64, 64, 4), dtype=np.uint8)
                img = Image.fromarray(img_array, mode='RGBA')
            img.save(path)
        
        analyzer = ColorSpaceAnalyzer()
        result = analyzer.analyze(str(path))
        
        assert "suspicion_score" in result
