"""
Integration tests for SteganographyAnalyzer.
"""
import pytest
from src.core.analyzer import SteganographyAnalyzer
from src.common.exceptions import InvalidImageError


class TestAnalyzerBasicAnalysis:
    """Test basic_analysis method."""

    def test_basic_analysis_clean_image(self, analyzer, sample_clean_image):
        """Test basic analysis on valid image."""
        result = analyzer.basic_analysis(str(sample_clean_image))
        
        assert "filename" in result
        assert "file_size" in result
        assert "dimensions" in result
        assert "format" in result
        assert "basic_suspicion_score" in result
        assert isinstance(result["basic_suspicion_score"], (int, float))
        assert 0 <= result["basic_suspicion_score"] <= 100

    def test_basic_analysis_dimensions(self, analyzer, sample_clean_image):
        """Test that dimensions are correctly reported."""
        result = analyzer.basic_analysis(str(sample_clean_image))
        
        # We created 256x256 test images
        assert result["dimensions"] == (256, 256)

    def test_basic_analysis_file_size(self, analyzer, sample_clean_image):
        """Test that file size is correctly reported."""
        result = analyzer.basic_analysis(str(sample_clean_image))
        
        assert result["file_size"] > 0
        assert isinstance(result["file_size"], int)


class TestAnalyzerImageAnalysis:
    """Test analyze_image method."""

    def test_analyze_image_clean(self, analyzer, sample_clean_image):
        """Test full analysis pipeline on clean image."""
        result = analyzer.analyze_image(str(sample_clean_image))
        
        assert "filename" in result
        assert "full_path" in result
        assert "file_size" in result
        assert "explanation" in result or "methods" in result
        assert "analysis_time" in result

    def test_analyze_image_explanation(self, analyzer, sample_clean_image):
        """Test that explanation contains final score."""
        result = analyzer.analyze_image(str(sample_clean_image))
        
        if "explanation" in result:
            explanation = result["explanation"]
            assert "final_score" in explanation
            score = float(explanation["final_score"])
            assert 0 <= score <= 100

    def test_analyze_image_suspicious_flag_via_explanation(self, analyzer, sample_clean_image):
        """Test that suspicion evaluation is present in explanation."""
        result = analyzer.analyze_image(str(sample_clean_image))
        
        if "explanation" in result:
            explanation = result["explanation"]
            assert "summary" in explanation  # Should contain verdict
            assert isinstance(explanation["summary"], str)

    def test_analyze_image_method_results(self, analyzer, sample_clean_image):
        """Test that methods contains individual analysis results."""
        result = analyzer.analyze_image(str(sample_clean_image))
        
        # Should have methods dict with results
        assert "methods" in result
        assert len(result["methods"]) > 0
        
        # Each method should have some content
        for method, method_result in result["methods"].items():
            assert isinstance(method_result, dict)

    def test_analyze_image_analysis_time(self, analyzer, sample_clean_image):
        """Test that analysis_time is measured."""
        result = analyzer.analyze_image(str(sample_clean_image))
        
        assert result["analysis_time"] >= 0
        assert isinstance(result["analysis_time"], float)

    def test_analyze_image_stego_vs_clean(self, analyzer, sample_clean_image, sample_stego_image):
        """Test that both stego and clean images are analyzed successfully."""
        clean_result = analyzer.analyze_image(str(sample_clean_image))
        stego_result = analyzer.analyze_image(str(sample_stego_image))
        
        # Both should have analysis results
        assert "explanation" in clean_result or "methods" in clean_result
        assert "explanation" in stego_result or "methods" in stego_result
        
        # Both should have timing info
        assert clean_result["analysis_time"] >= 0
        assert stego_result["analysis_time"] >= 0

    def test_analyze_image_rgba(self, analyzer, sample_rgba_image):
        """Test analysis on RGBA image."""
        result = analyzer.analyze_image(str(sample_rgba_image))
        
        assert "filename" in result
        assert "analysis_time" in result
        assert result["analysis_time"] >= 0

    def test_analyze_image_grayscale(self, analyzer, sample_grayscale_image):
        """Test analysis on grayscale image."""
        result = analyzer.analyze_image(str(sample_grayscale_image))
        
        assert "filename" in result
        assert "analysis_time" in result
        assert result["analysis_time"] >= 0


class TestAnalyzerErrorHandling:
    """Test error handling in analyzer."""

    def test_analyze_invalid_path(self, analyzer):
        """Test handling of non-existent file."""
        with pytest.raises(InvalidImageError):
            analyzer.analyze_image("/path/that/does/not/exist.png")

    def test_analyze_corrupted_image(self, analyzer, corrupted_image):
        """Test handling of corrupted image file."""
        with pytest.raises(InvalidImageError):
            analyzer.analyze_image(str(corrupted_image))

    def test_analyze_unsupported_format(self, analyzer, tmp_path):
        """Test handling of unsupported file format."""
        # Create a text file with image extension
        bad_file = tmp_path / "test.jpg"
        bad_file.write_text("This is not a real image")
        
        with pytest.raises(InvalidImageError):
            analyzer.analyze_image(str(bad_file))


class TestAnalyzerConfiguration:
    """Test analyzer configuration handling."""

    def test_analyzer_default_config(self, analyzer):
        """Test analyzer with default configuration."""
        # Should work without any config
        assert analyzer._config is None

    def test_analyzer_custom_config(self, analyzer, config_manager):
        """Test analyzer with custom configuration."""
        config_data = config_manager.config
        analyzer_custom = SteganographyAnalyzer(config=config_data)
        
        assert analyzer_custom._config is not None
        assert "suspicion_threshold" in analyzer_custom._config
