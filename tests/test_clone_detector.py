"""Tests for Clone detector (Phase 3 forensics)."""
import pytest
from pathlib import Path
from PIL import Image
import numpy as np


class TestCloneDetector:
    """Test copy-move forgery detection using ORB."""
    
    def test_clone_detection_basic(self, sample_clean_image):
        """Test basic clone detection."""
        from src.core.clone_detector import CloneDetector
        
        detector = CloneDetector()
        result = detector.analyze(str(sample_clean_image))
        
        assert isinstance(result, dict)
        assert "suspicion_score" in result
        assert 0 <= result["suspicion_score"] <= 100
    
    def test_clone_detection_return_format(self, sample_stego_image):
        """Test return value structure."""
        from src.core.clone_detector import CloneDetector
        
        detector = CloneDetector()
        result = detector.analyze(str(sample_stego_image))
        
        assert "suspicion_score" in result
        assert "description" in result
        assert isinstance(result["suspicion_score"], (int, float))
    
    def test_clone_detection_blank_image(self, blank_image):
        """Test with blank image (all similar)."""
        from src.core.clone_detector import CloneDetector
        
        detector = CloneDetector()
        result = detector.analyze(str(blank_image))
        
        # Blank image might flag as suspicious due to repetition
        assert "suspicion_score" in result
        assert result["suspicion_score"] >= 0
    
    def test_clone_detection_uniform_regions(self, test_data_dir):
        """Test image with uniform regions (natural clones)."""
        from src.core.clone_detector import CloneDetector
        
        path = test_data_dir / "uniform_regions.png"
        if not path.exists():
            img_array = np.random.randint(0, 256, (256, 256, 3), dtype=np.uint8)
            # Create uniform region
            img_array[50:100, 50:100, :] = 128
            img_array[150:200, 150:200, :] = 128
            img = Image.fromarray(img_array.astype(np.uint8))
            img.save(path)
        
        detector = CloneDetector()
        result = detector.analyze(str(path))
        
        assert "suspicion_score" in result
    
    def test_clone_detection_missing_file(self):
        """Test handling of missing file."""
        from src.core.clone_detector import CloneDetector
        
        detector = CloneDetector()
        result = detector.analyze("/nonexistent/file.png")
        
        assert "suspicion_score" in result
    
    def test_clone_detection_grayscale(self, sample_grayscale_image):
        """Test with grayscale image."""
        from src.core.clone_detector import CloneDetector
        
        detector = CloneDetector()
        result = detector.analyze(str(sample_grayscale_image))
        
        assert "suspicion_score" in result
    
    def test_clone_detection_rgba(self, sample_rgba_image):
        """Test with RGBA image."""
        from src.core.clone_detector import CloneDetector
        
        detector = CloneDetector()
        result = detector.analyze(str(sample_rgba_image))
        
        assert "suspicion_score" in result
    
    def test_clone_detection_parametrized(self, sample_clean_image):
        """Test with different parameter sets."""
        from src.core.clone_detector import CloneDetector
        
        detector = CloneDetector()
        
        # Test with different thresholds
        result1 = detector.analyze(str(sample_clean_image), threshold=30)
        result2 = detector.analyze(str(sample_clean_image), threshold=50)
        
        assert "suspicion_score" in result1
        assert "suspicion_score" in result2


class TestCloneDetectorEdgeCases:
    """Test edge cases for clone detection."""
    
    def test_clone_detection_tiny_image(self, test_data_dir):
        """Test with very small image."""
        from src.core.clone_detector import CloneDetector
        
        path = test_data_dir / "tiny_clone.png"
        if not path.exists():
            img = Image.fromarray(np.random.randint(0, 256, (16, 16, 3), dtype=np.uint8))
            img.save(path)
        
        detector = CloneDetector()
        result = detector.analyze(str(path))
        
        assert "suspicion_score" in result
    
    def test_clone_detection_large_image(self, test_data_dir):
        """Test with large image."""
        from src.core.clone_detector import CloneDetector
        
        path = test_data_dir / "large_clone.png"
        if not path.exists():
            img = Image.fromarray(np.random.randint(0, 256, (1024, 1024, 3), dtype=np.uint8))
            img.save(path)
        
        detector = CloneDetector()
        result = detector.analyze(str(path))
        
        assert "suspicion_score" in result
    
    def test_clone_detection_single_color(self, test_data_dir):
        """Test image with single color (maximum cloning)."""
        from src.core.clone_detector import CloneDetector
        
        path = test_data_dir / "single_color_clone.png"
        if not path.exists():
            img_array = np.full((256, 256, 3), 128, dtype=np.uint8)
            img = Image.fromarray(img_array)
            img.save(path)
        
        detector = CloneDetector()
        result = detector.analyze(str(path))
        
        assert "suspicion_score" in result
        # Single color might flag as high suspicion
        assert result["suspicion_score"] >= 0
    
    def test_clone_detection_natural_image(self, test_data_dir):
        """Test with natural-looking image."""
        from src.core.clone_detector import CloneDetector
        
        path = test_data_dir / "natural_clone.png"
        if not path.exists():
            # Create gradient
            img_array = np.zeros((256, 256, 3), dtype=np.uint8)
            for i in range(256):
                img_array[i, :, :] = i
            img = Image.fromarray(img_array)
            img.save(path)
        
        detector = CloneDetector()
        result = detector.analyze(str(path))
        
        assert "suspicion_score" in result
