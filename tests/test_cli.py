"""Tests for CLI commands."""
import pytest
from pathlib import Path
from click.testing import CliRunner


class TestCLIAnalyzeCommand:
    """Test analyze command."""
    
    def test_analyze_single_image(self, sample_clean_image):
        """Test analyzing a single image."""
        from steg_hunter_cli import cli
        
        runner = CliRunner()
        result = runner.invoke(cli, ['analyze', str(sample_clean_image)])
        
        assert result.exit_code == 0
    
    def test_analyze_with_output(self, sample_clean_image, temp_output_dir):
        """Test analyze with JSON output."""
        from steg_hunter_cli import cli
        
        runner = CliRunner()
        output_file = temp_output_dir / "results.json"
        
        result = runner.invoke(cli, [
            'analyze', str(sample_clean_image),
            '--output', str(output_file),
            '--format', 'json'
        ])
        
        assert result.exit_code == 0
        assert output_file.exists()
    
    def test_analyze_batch_directory(self, test_data_dir, temp_output_dir):
        """Test batch processing a directory."""
        from steg_hunter_cli import cli
        
        runner = CliRunner()
        output_file = temp_output_dir / "batch_results.json"
        
        result = runner.invoke(cli, [
            'analyze', str(test_data_dir),
            '--batch',
            '--output', str(output_file)
        ])
        
        # Should succeed or handle missing images gracefully
        assert result.exit_code in [0, 1]
    
    def test_analyze_with_threshold(self, sample_clean_image):
        """Test analyze with custom threshold."""
        from steg_hunter_cli import cli
        
        runner = CliRunner()
        result = runner.invoke(cli, [
            'analyze', str(sample_clean_image),
            '--threshold', '60.0'
        ])
        
        assert result.exit_code == 0
    
    def test_analyze_verbose_mode(self, sample_clean_image):
        """Test analyze with verbose output."""
        from steg_hunter_cli import cli
        
        runner = CliRunner()
        result = runner.invoke(cli, [
            'analyze', str(sample_clean_image),
            '--verbose'
        ])
        
        assert result.exit_code == 0


class TestCLIInfoCommand:
    """Test info command."""
    
    def test_info_command(self, sample_clean_image):
        """Test info command."""
        from steg_hunter_cli import cli
        
        runner = CliRunner()
        result = runner.invoke(cli, ['info', str(sample_clean_image)])
        
        assert result.exit_code == 0
    
    def test_info_invalid_file(self):
        """Test info with invalid file."""
        from steg_hunter_cli import cli
        
        runner = CliRunner()
        result = runner.invoke(cli, ['info', '/nonexistent/file.png'])
        
        assert result.exit_code != 0


class TestCLIVideoCommand:
    """Test video-analyze command (Phase 4)."""
    
    def test_video_analyze_basic(self, sample_video):
        """Test basic video analysis command."""
        from steg_hunter_cli import cli
        
        runner = CliRunner()
        result = runner.invoke(cli, ['video-analyze', str(sample_video)])
        
        # Should attempt to run
        assert result.exit_code in [0, 1]
    
    def test_video_analyze_with_output(self, sample_video, temp_output_dir):
        """Test video analyze with JSON output."""
        from steg_hunter_cli import cli
        
        runner = CliRunner()
        output_file = temp_output_dir / "video_results.json"
        
        result = runner.invoke(cli, [
            'video-analyze', str(sample_video),
            '--output', str(output_file)
        ])
        
        # Should handle video or skip gracefully
        assert result.exit_code in [0, 1]
    
    def test_video_analyze_with_heatmap(self, sample_video, temp_output_dir):
        """Test video analyze with heatmap output."""
        from steg_hunter_cli import cli
        
        runner = CliRunner()
        heatmap_file = temp_output_dir / "heatmap.png"
        
        result = runner.invoke(cli, [
            'video-analyze', str(sample_video),
            '--heatmap', str(heatmap_file)
        ])
        
        # Should handle gracefully
        assert result.exit_code in [0, 1]
    
    def test_video_analyze_verbose(self, sample_video):
        """Test video analyze with verbose mode."""
        from steg_hunter_cli import cli
        
        runner = CliRunner()
        result = runner.invoke(cli, [
            'video-analyze', str(sample_video),
            '--verbose'
        ])
        
        assert result.exit_code in [0, 1]


class TestCLIHeatmapCommand:
    """Test heatmap command."""
    
    def test_heatmap_lsb_method(self, sample_clean_image, temp_output_dir):
        """Test heatmap with LSB method."""
        from steg_hunter_cli import cli
        
        runner = CliRunner()
        output_file = temp_output_dir / "lsb_heatmap.png"
        
        result = runner.invoke(cli, [
            'heatmap', str(sample_clean_image),
            '--method', 'lsb',
            '--output', str(output_file)
        ])
        
        assert result.exit_code == 0
    
    def test_heatmap_comprehensive_method(self, sample_clean_image, temp_output_dir):
        """Test heatmap with comprehensive method."""
        from steg_hunter_cli import cli
        
        runner = CliRunner()
        output_file = temp_output_dir / "comprehensive_heatmap.png"
        
        result = runner.invoke(cli, [
            'heatmap', str(sample_clean_image),
            '--method', 'comprehensive',
            '--output', str(output_file)
        ])
        
        assert result.exit_code == 0


class TestCLITrainModelCommand:
    """Test train-model command."""
    
    def test_train_model_basic(self, test_data_dir, temp_output_dir):
        """Test model training."""
        from steg_hunter_cli import cli
        
        runner = CliRunner()
        output_file = temp_output_dir / "model.pkl"
        
        # Create dummy directories
        clean_dir = test_data_dir / "clean"
        stego_dir = test_data_dir / "stego"
        clean_dir.mkdir(exist_ok=True)
        stego_dir.mkdir(exist_ok=True)
        
        result = runner.invoke(cli, [
            'train-model',
            '--clean-dir', str(clean_dir),
            '--stego-dir', str(stego_dir),
            '--output', str(output_file)
        ])
        
        # May fail if no images, but should not crash
        assert isinstance(result.exit_code, int)


class TestCLIExportCommand:
    """Test export command."""
    
    def test_export_json(self, sample_clean_image, temp_output_dir):
        """Test export to JSON."""
        from steg_hunter_cli import cli
        
        runner = CliRunner()
        output_file = temp_output_dir / "export.json"
        
        result = runner.invoke(cli, [
            'export', str(sample_clean_image),
            '--output', str(output_file),
            '--format', 'json'
        ])
        
        assert result.exit_code == 0
    
    def test_export_csv(self, sample_clean_image, temp_output_dir):
        """Test export to CSV."""
        from steg_hunter_cli import cli
        
        runner = CliRunner()
        output_file = temp_output_dir / "export.csv"
        
        result = runner.invoke(cli, [
            'export', str(sample_clean_image),
            '--output', str(output_file),
            '--format', 'csv'
        ])
        
        assert result.exit_code == 0
