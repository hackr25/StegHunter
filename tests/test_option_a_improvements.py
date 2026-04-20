"""
Test suite for Option A improvements:
1. Method Failure Isolation
2. Config Validation  
3. Timeout Protection
"""
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.core.analyzer import SteganographyAnalyzer
from src.common.config_manager import ConfigManager
from src.common.validators import ConfigValidator


class TestMethodFailureIsolation:
    """Test that method errors are handled gracefully."""
    
    def test_errors_list_in_results(self, sample_clean_image):
        """Results should include 'errors' list tracking failed methods."""
        analyzer = SteganographyAnalyzer()
        results = analyzer.analyze_image(str(sample_clean_image))
        
        # Should have errors list even if empty
        assert 'errors' in results
        assert isinstance(results['errors'], list)
    
    def test_failed_method_returns_zero_score(self, sample_clean_image):
        """Failed methods should return 0.0 suspicion_score, not crash."""
        analyzer = SteganographyAnalyzer()
        
        # Mock a method to raise an exception
        with patch('src.core.analyzer.lsb_analysis', side_effect=ValueError("Test error")):
            results = analyzer.analyze_image(str(sample_clean_image))
            
            # Analysis should complete even with method failure
            assert results['final_suspicion_score'] >= 0.0
            assert 'lsb' in results['methods']
            assert 'error' in results['methods']['lsb']
            assert results['methods']['lsb']['lsb_suspicion_score'] == 0.0
    
    def test_error_message_in_results(self, sample_clean_image):
        """Error messages should be included in results."""
        analyzer = SteganographyAnalyzer()
        
        with patch('src.core.analyzer.chi_square_test', side_effect=RuntimeError("Chi-square failed")):
            results = analyzer.analyze_image(str(sample_clean_image))
            
            # Error message should be in results
            assert len(results['errors']) > 0
            error_msg = results['errors'][0]
            assert 'chi_square' in error_msg or 'Chi-square' in error_msg
    
    def test_multiple_method_failures(self, sample_clean_image):
        """Multiple method failures should all be tracked."""
        analyzer = SteganographyAnalyzer()
        
        with patch('src.core.analyzer.lsb_analysis', side_effect=ValueError("LSB error")):
            with patch('src.core.analyzer.chi_square_test', side_effect=ValueError("Chi-square error")):
                results = analyzer.analyze_image(str(sample_clean_image))
                
                # Should track multiple errors
                assert len(results['errors']) >= 2
                error_str = ' '.join(results['errors'])
                assert 'lsb' in error_str
                assert 'chi_square' in error_str


class TestConfigValidation:
    """Test config validation and auto-correction."""
    
    def test_weights_validation_pass(self):
        """Valid weights should pass validation."""
        weights = {'a': 0.4, 'b': 0.6}
        is_valid, msg = ConfigValidator.validate_weights(weights)
        assert is_valid
        assert msg == ""
    
    def test_weights_validation_tolerance(self):
        """Weights within tolerance should pass."""
        # Sum is 1.001, within 0.01 tolerance
        weights = {'a': 0.5, 'b': 0.501}
        is_valid, msg = ConfigValidator.validate_weights(weights, tolerance=0.01)
        assert is_valid
    
    def test_weights_validation_fail(self):
        """Invalid weights should fail validation."""
        weights = {'a': 0.5, 'b': 0.3}  # Sum = 0.8
        is_valid, msg = ConfigValidator.validate_weights(weights)
        assert not is_valid
        assert "must equal 1.0" in msg
    
    def test_enabled_methods_validation(self):
        """Should validate that enabled methods are valid."""
        enabled = ['lsb', 'ela', 'invalid_method']
        valid = ['lsb', 'ela', 'chi_square']
        
        is_valid, msg = ConfigValidator.validate_enabled_methods(enabled, valid)
        assert not is_valid
        assert 'invalid_method' in msg
    
    def test_config_manager_weight_normalization(self, temp_output_dir):
        """ConfigManager should auto-normalize invalid weights."""
        # Create a config with invalid weights
        config_path = temp_output_dir / "test_config.yaml"
        config_content = """
suspicion_threshold: 50.0
weights:
  lsb: 0.5
  ela: 0.3
enabled_methods:
  - lsb
  - ela
"""
        config_path.write_text(config_content)
        
        config = ConfigManager(config_path)
        weights = config.get('weights')
        
        # Weights should be normalized to sum to 1.0
        total = sum(weights.values())
        assert abs(total - 1.0) < 0.01
    
    def test_config_manager_performance_bounds(self, temp_output_dir):
        """ConfigManager should clamp performance settings to valid ranges."""
        config_path = temp_output_dir / "test_config.yaml"
        config_content = """
suspicion_threshold: 50.0
performance:
  max_workers: 999
  timeout_seconds: 0
enabled_methods:
  - lsb
"""
        config_path.write_text(config_content)
        
        config = ConfigManager(config_path)
        perf = config.get('performance')
        
        # Should be clamped to valid ranges
        assert 1 <= perf['max_workers'] <= 64
        assert 1 <= perf['timeout_seconds'] <= 300


class TestTimeoutProtection:
    """Test timeout protection for heavy analysis methods."""
    
    def test_get_timeout_from_config(self):
        """Analyzer should read timeout from config."""
        config = {
            'performance': {
                'timeout_seconds': 45
            }
        }
        analyzer = SteganographyAnalyzer(config)
        timeout = analyzer._get_timeout()
        
        assert timeout == 45
    
    def test_get_timeout_default(self):
        """Should default to 30 seconds if not configured."""
        analyzer = SteganographyAnalyzer()
        timeout = analyzer._get_timeout()
        
        assert timeout == 30
    
    def test_get_timeout_clamped(self):
        """Timeout should be clamped to [1, 300]."""
        # Too low
        config = {'performance': {'timeout_seconds': 0}}
        analyzer = SteganographyAnalyzer(config)
        assert analyzer._get_timeout() == 1
        
        # Too high
        config = {'performance': {'timeout_seconds': 999}}
        analyzer = SteganographyAnalyzer(config)
        assert analyzer._get_timeout() == 300
    
    def test_timeout_protection_applied_to_ela(self, sample_clean_image):
        """ELA should have timeout protection."""
        config = {
            'performance': {'timeout_seconds': 1},
            'enabled_methods': ['ela'],
        }
        analyzer = SteganographyAnalyzer(config)
        
        # This should complete within timeout
        results = analyzer.analyze_image(str(sample_clean_image))
        
        # Even if it times out, analysis should complete gracefully
        assert 'ela' in results['methods']
        assert 'suspicion_score' in results['methods']['ela']


class TestErrorReporting:
    """Test that errors are properly logged and reported."""
    
    def test_error_in_is_suspicious_field(self, sample_clean_image):
        """Overall is_suspicious should still be set even with errors."""
        analyzer = SteganographyAnalyzer()
        
        with patch('src.core.analyzer.lsb_analysis', side_effect=Exception("Test error")):
            results = analyzer.analyze_image(str(sample_clean_image))
            
            assert 'is_suspicious' in results
            assert isinstance(results['is_suspicious'], bool)
    
    def test_final_score_computed_with_errors(self, sample_clean_image):
        """final_suspicion_score should be computed even with errors."""
        analyzer = SteganographyAnalyzer()
        
        with patch('src.core.analyzer.lsb_analysis', side_effect=Exception("Test error")):
            results = analyzer.analyze_image(str(sample_clean_image))
            
            assert 'final_suspicion_score' in results
            assert 0.0 <= results['final_suspicion_score'] <= 100.0


class TestEndToEndWithImprovements:
    """Integration tests for all three improvements together."""
    
    def test_analysis_resilient_to_multiple_failures(self, sample_clean_image):
        """Analysis should complete even with multiple method failures."""
        analyzer = SteganographyAnalyzer({
            'performance': {'timeout_seconds': 30},
            'enabled_methods': ['lsb', 'ela', 'chi_square'],
            'weights': {'lsb': 0.5, 'ela': 0.3, 'chi_square': 0.2}
        })
        
        # Mock multiple failures
        with patch('src.core.analyzer.lsb_analysis', side_effect=Exception("LSB failed")):
            with patch('src.core.analyzer.chi_square_test', side_effect=Exception("Chi-square failed")):
                results = analyzer.analyze_image(str(sample_clean_image))
                
                # Should still return valid results
                assert results['final_suspicion_score'] >= 0.0
                assert 'is_suspicious' in results
                assert len(results['errors']) >= 2
                # ELA should still work
                assert 'ela' in results['methods']
    
    def test_analysis_with_valid_config(self, sample_clean_image, temp_output_dir):
        """Full analysis with validated config should work perfectly."""
        config_path = temp_output_dir / "good_config.yaml"
        config_content = """
suspicion_threshold: 50.0
weights:
  lsb: 0.4
  ela: 0.3
  chi_square: 0.3
enabled_methods:
  - lsb
  - ela
  - chi_square
performance:
  timeout_seconds: 60
  max_workers: 4
"""
        config_path.write_text(config_content)
        
        config = ConfigManager(config_path)
        analyzer = SteganographyAnalyzer(config.config)
        
        results = analyzer.analyze_image(str(sample_clean_image))
        
        # All should be well
        assert results['final_suspicion_score'] >= 0.0
        assert len(results['errors']) == 0  # No errors
        assert results['is_suspicious'] in [True, False]
