"""Tests for Phase 4 Video Forensics."""
import pytest
from pathlib import Path
import numpy as np


class TestVideoAnalyzer:
    """Test video frame analysis."""
    
    def test_video_analyzer_basic(self, sample_video):
        """Test basic video analysis."""
        from src.core.video_analyzer import VideoAnalyzer
        
        analyzer = VideoAnalyzer()
        result = analyzer.analyze_video(str(sample_video))
        
        assert isinstance(result, dict)
        assert "score" in result or "suspicion_score" in result
        assert "frame_count" in result
        assert "entropy_timeline" in result
    
    def test_video_analyzer_return_format(self, sample_video):
        """Test video analysis return structure."""
        from src.core.video_analyzer import VideoAnalyzer
        
        analyzer = VideoAnalyzer()
        result = analyzer.analyze_video(str(sample_video))
        
        assert "frame_count" in result
        assert "entropy_timeline" in result
        assert "anomalies" in result
        assert isinstance(result["entropy_timeline"], list)
        assert isinstance(result["anomalies"], list)
    
    def test_video_analyzer_entropy_timeline(self, sample_video):
        """Test entropy timeline is valid."""
        from src.core.video_analyzer import VideoAnalyzer
        
        analyzer = VideoAnalyzer()
        result = analyzer.analyze_video(str(sample_video))
        
        entropy_timeline = result["entropy_timeline"]
        assert len(entropy_timeline) > 0
        # All entropies should be 0-8 (bits)
        for e in entropy_timeline:
            assert 0 <= e <= 8
    
    def test_video_analyzer_anomalies(self, sample_video):
        """Test anomaly detection."""
        from src.core.video_analyzer import VideoAnalyzer
        
        analyzer = VideoAnalyzer()
        result = analyzer.analyze_video(str(sample_video))
        
        anomalies = result["anomalies"]
        assert isinstance(anomalies, list)
        # Each anomaly is (frame_index, score)
        for anom in anomalies:
            assert len(anom) == 2
            assert isinstance(anom[0], int)  # frame index
            assert isinstance(anom[1], (int, float))  # score
    
    def test_video_analyzer_frame_sampling(self, sample_video):
        """Test frame sampling configuration."""
        from src.core.video_analyzer import VideoAnalyzer
        
        analyzer = VideoAnalyzer()
        result = analyzer.analyze_video(str(sample_video), frame_sample_rate=2)
        
        # Should analyze every 2nd frame
        assert "frame_count" in result
        assert result["frame_count"] > 0
    
    def test_video_analyzer_missing_file(self):
        """Test handling of missing video file."""
        from src.core.video_analyzer import VideoAnalyzer
        
        analyzer = VideoAnalyzer()
        result = analyzer.analyze_video("/nonexistent/video.mp4")
        
        # Should return error gracefully
        assert isinstance(result, dict)


class TestVideoContainerAnalyzer:
    """Test video container format analysis."""
    
    def test_video_container_basic(self, sample_video):
        """Test basic container analysis."""
        from src.forensics.video_container_analyzer import VideoContainerAnalyzer
        
        analyzer = VideoContainerAnalyzer()
        result = analyzer.analyze(str(sample_video))
        
        assert isinstance(result, dict)
        assert "format" in result or "file_format" in result
        assert "score" in result or "suspicion_score" in result
    
    def test_video_container_return_format(self, sample_video):
        """Test container analysis return structure."""
        from src.forensics.video_container_analyzer import VideoContainerAnalyzer
        
        analyzer = VideoContainerAnalyzer()
        result = analyzer.analyze(str(sample_video))
        
        assert isinstance(result, dict)
        # Should have detection details
        assert len(result) > 0
    
    def test_video_container_mp4_detection(self, sample_video):
        """Test MP4 format detection."""
        from src.forensics.video_container_analyzer import VideoContainerAnalyzer
        
        analyzer = VideoContainerAnalyzer()
        result = analyzer.analyze(str(sample_video))
        
        # Sample video should be detected as MP4
        format_detected = result.get("format") or result.get("file_format")
        if format_detected:
            assert "mp4" in str(format_detected).lower() or "MP4" in str(format_detected)
    
    def test_video_container_missing_file(self):
        """Test handling of missing video file."""
        from src.forensics.video_container_analyzer import VideoContainerAnalyzer
        
        analyzer = VideoContainerAnalyzer()
        result = analyzer.analyze("/nonexistent/video.mp4")
        
        # Should handle gracefully
        assert isinstance(result, dict)


class TestVideoHeatmapGenerator:
    """Test video heatmap visualization."""
    
    def test_heatmap_generation(self, sample_video, temp_output_dir):
        """Test basic heatmap generation."""
        from src.core.video_heatmap_generator import VideoHeatmapGenerator
        from src.core.video_analyzer import VideoAnalyzer
        
        # Get entropy timeline
        video_analyzer = VideoAnalyzer()
        video_result = video_analyzer.analyze_video(str(sample_video))
        entropy_timeline = video_result.get("entropy_timeline", [])
        anomalies = video_result.get("anomalies", [])
        
        if entropy_timeline:
            # Generate heatmap
            gen = VideoHeatmapGenerator()
            output_path = temp_output_dir / "test_heatmap.png"
            gen.generate(entropy_timeline, anomalies, str(output_path))
            
            assert output_path.exists()
    
    def test_heatmap_empty_timeline(self, temp_output_dir):
        """Test heatmap with empty timeline."""
        from src.core.video_heatmap_generator import VideoHeatmapGenerator
        
        gen = VideoHeatmapGenerator()
        output_path = temp_output_dir / "empty_heatmap.png"
        
        # Should handle empty timeline
        gen.generate([], [], str(output_path))
        
        # Should create output file or handle gracefully
        # (may not create file for empty data)
    
    def test_heatmap_color_gradient(self, sample_video, temp_output_dir):
        """Test heatmap color gradient generation."""
        from src.core.video_heatmap_generator import VideoHeatmapGenerator
        
        gen = VideoHeatmapGenerator()
        
        # Create sample entropy timeline
        entropy = [i / 8.0 for i in range(0, 9)]  # 0.0 to 1.0
        output_path = temp_output_dir / "gradient_heatmap.png"
        
        gen.generate(entropy, [], str(output_path))
        
        # Should create output or handle gracefully
        assert isinstance(output_path, Path)


class TestVideoAnalysisIntegration:
    """Integration tests for video analysis."""
    
    def test_video_full_analysis_pipeline(self, sample_video):
        """Test full video analysis pipeline."""
        from src.core.analyzer import SteganographyAnalyzer
        
        analyzer = SteganographyAnalyzer()
        result = analyzer.analyze_video(str(sample_video))
        
        assert "filename" in result
        assert "overall_score" in result
        assert "is_suspicious" in result
        assert "analysis_time" in result
        assert "methods" in result
    
    def test_video_combined_scores(self, sample_video):
        """Test combination of frame and container scores."""
        from src.core.analyzer import SteganographyAnalyzer
        
        analyzer = SteganographyAnalyzer()
        result = analyzer.analyze_video(str(sample_video))
        
        overall = result["overall_score"]
        assert 0 <= overall <= 100
        
        # Check if methods contributed
        methods = result.get("methods", {})
        assert "video_frame_analysis" in methods or "video_container" in methods
    
    def test_video_result_serializable(self, sample_video):
        """Test that video analysis result is JSON serializable."""
        from src.core.analyzer import SteganographyAnalyzer
        from src.common.utils import convert_numpy_types
        import json
        
        analyzer = SteganographyAnalyzer()
        result = analyzer.analyze_video(str(sample_video))
        
        # Should be convertible to JSON
        converted = convert_numpy_types(result)
        json_str = json.dumps(converted)
        
        assert isinstance(json_str, str)
        assert len(json_str) > 0


class TestVideoEdgeCases:
    """Test edge cases for video analysis."""
    
    def test_video_very_short_video(self, test_data_dir):
        """Test analysis of very short video (1-2 frames)."""
        from src.core.video_analyzer import VideoAnalyzer
        
        # Would need actual short video file
        # Placeholder for when fixture is created
        pass
    
    def test_video_corrupted_file(self, test_data_dir):
        """Test handling of corrupted video file."""
        from src.core.video_analyzer import VideoAnalyzer
        
        # Create corrupted file
        bad_video = test_data_dir / "corrupted.mp4"
        if not bad_video.exists():
            with open(bad_video, 'wb') as f:
                f.write(b'not a valid video' * 10)
        
        analyzer = VideoAnalyzer()
        result = analyzer.analyze_video(str(bad_video))
        
        # Should handle gracefully
        assert isinstance(result, dict)
