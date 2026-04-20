"""Tests for configuration and validation."""
import pytest
from pathlib import Path


class TestConfigValidator:
    """Test configuration validation."""
    
    def test_validate_weights_valid(self):
        """Test validation of valid weights."""
        from src.common.validators import ConfigValidator
        
        weights = {
            'lsb': 0.25,
            'ela': 0.30,
            'noise': 0.20,
            'color_space': 0.25
        }
        
        # Should not raise
        ConfigValidator.validate_weights(weights)
    
    def test_validate_weights_sum_to_one(self):
        """Test weights that sum to exactly 1.0."""
        from src.common.validators import ConfigValidator
        
        weights = {
            'method1': 0.5,
            'method2': 0.5
        }
        
        ConfigValidator.validate_weights(weights)
    
    def test_validate_weights_tolerance(self):
        """Test weights validation with tolerance."""
        from src.common.validators import ConfigValidator
        
        # Sum is 1.01, should pass with tolerance
        weights = {
            'method1': 0.51,
            'method2': 0.50
        }
        
        ConfigValidator.validate_weights(weights)
    
    def test_validate_weights_invalid(self):
        """Test validation of invalid weights."""
        from src.common.validators import ConfigValidator
        
        # Weights sum to 2.0, clearly invalid even with tolerance
        weights = {
            'method1': 1.0,
            'method2': 1.0
        }
        
        with pytest.raises(ValueError):
            ConfigValidator.validate_weights(weights)
    
    def test_validate_enabled_methods(self):
        """Test validation of enabled methods list."""
        from src.common.validators import ConfigValidator
        
        methods = ['lsb', 'ela', 'noise', 'clone_detection']
        
        # Should not raise (assuming these are valid method names)
        ConfigValidator.validate_enabled_methods(methods)
    
    def test_validate_enabled_methods_empty(self):
        """Test validation with empty methods list."""
        from src.common.validators import ConfigValidator
        
        methods = []
        
        # Empty list should pass (no methods enabled is valid)
        ConfigValidator.validate_enabled_methods(methods)
    
    def test_validate_performance_settings(self):
        """Test validation of performance settings."""
        from src.common.validators import ConfigValidator
        
        perf = {
            'max_workers': 4,
            'chunk_size': 100,
            'timeout_seconds': 60
        }
        
        ConfigValidator.validate_performance_settings(perf)
    
    def test_validate_performance_max_workers(self):
        """Test max_workers validation."""
        from src.common.validators import ConfigValidator
        
        # Valid
        perf = {'max_workers': 4}
        ConfigValidator.validate_performance_settings(perf)
        
        # Invalid (too high)
        perf = {'max_workers': 128}
        with pytest.raises(ValueError):
            ConfigValidator.validate_performance_settings(perf)


class TestAnalysisValidator:
    """Test analysis result validation."""
    
    def test_validate_suspicion_score_valid(self):
        """Test validation of valid suspicion score."""
        from src.common.validators import AnalysisValidator
        
        AnalysisValidator.validate_suspicion_score(50.0)
        AnalysisValidator.validate_suspicion_score(0.0)
        AnalysisValidator.validate_suspicion_score(100.0)
    
    def test_validate_suspicion_score_invalid_low(self):
        """Test validation of too-low suspicion score."""
        from src.common.validators import AnalysisValidator
        
        with pytest.raises(ValueError):
            AnalysisValidator.validate_suspicion_score(-10.0)
    
    def test_validate_suspicion_score_invalid_high(self):
        """Test validation of too-high suspicion score."""
        from src.common.validators import AnalysisValidator
        
        with pytest.raises(ValueError):
            AnalysisValidator.validate_suspicion_score(150.0)
    
    def test_validate_analysis_result_valid(self):
        """Test validation of valid analysis result."""
        from src.common.validators import AnalysisValidator
        
        result = {
            'suspicion_score': 50.0,
            'description': 'Test result',
            'method': 'test_method'
        }
        
        AnalysisValidator.validate_analysis_result(result)
    
    def test_validate_analysis_result_missing_score(self):
        """Test validation of result missing suspicion_score."""
        from src.common.validators import AnalysisValidator
        
        result = {
            'description': 'Test result'
        }
        
        with pytest.raises(ValueError):
            AnalysisValidator.validate_analysis_result(result)


class TestConfigManager:
    """Test configuration management."""
    
    def test_config_manager_default(self):
        """Test ConfigManager with default configuration."""
        from src.common.config_manager import ConfigManager
        
        config = ConfigManager()
        assert config.config is not None
    
    def test_config_manager_get_value(self):
        """Test getting configuration value."""
        from src.common.config_manager import ConfigManager
        
        config = ConfigManager()
        # Get a nested value
        threshold = config.get('suspicion_threshold', 50.0)
        assert isinstance(threshold, (int, float))
    
    def test_config_manager_get_nested(self):
        """Test getting nested configuration value."""
        from src.common.config_manager import ConfigManager
        
        config = ConfigManager()
        # Get a nested value using dot notation
        workers = config.get('performance.max_workers', 4)
        assert isinstance(workers, (int, float))
    
    def test_config_manager_get_default(self):
        """Test ConfigManager default fallback."""
        from src.common.config_manager import ConfigManager
        
        config = ConfigManager()
        # Get non-existent key with default
        value = config.get('nonexistent.key', 'default_value')
        assert value == 'default_value'
    
    def test_config_manager_validation(self, test_config_file):
        """Test ConfigManager runs validation on load."""
        from src.common.config_manager import ConfigManager
        
        # Should not raise even with validation
        config = ConfigManager(str(test_config_file))
        assert config.config is not None


class TestTimeoutHandler:
    """Test timeout decorator and handling."""
    
    def test_timeout_fast_function(self):
        """Test timeout with fast-executing function."""
        from src.common.timeout_handler import timeout
        import time
        
        @timeout(5)
        def fast_function():
            return "success"
        
        result = fast_function()
        assert result == "success"
    
    def test_timeout_decorator_exists(self):
        """Test that timeout decorator exists and can be used."""
        from src.common.timeout_handler import timeout, TimeoutHandler
        
        # Should be able to import and use
        assert callable(timeout)
        assert callable(TimeoutHandler)
    
    def test_graceful_fallback_decorator(self):
        """Test graceful fallback decorator."""
        from src.common.timeout_handler import with_graceful_fallback
        
        # Should exist and be callable
        assert callable(with_graceful_fallback)
    
    def test_timeout_exception_exists(self):
        """Test that TimeoutException exists."""
        from src.common.timeout_handler import TimeoutException
        
        assert issubclass(TimeoutException, Exception)


class TestValidatorsEdgeCases:
    """Test edge cases for validators."""
    
    def test_validate_weights_negative(self):
        """Test validation rejects negative weights."""
        from src.common.validators import ConfigValidator
        
        weights = {
            'method1': -0.5,
            'method2': 1.5
        }
        
        with pytest.raises(ValueError):
            ConfigValidator.validate_weights(weights)
    
    def test_validate_weights_empty(self):
        """Test validation of empty weights dict."""
        from src.common.validators import ConfigValidator
        
        weights = {}
        
        # Empty should pass (no weights specified)
        ConfigValidator.validate_weights(weights)
    
    @pytest.mark.parametrize("score", [0, 50, 100, 25.5, 99.9])
    def test_suspicion_score_range(self, score):
        """Test suspicion score validation with various values."""
        from src.common.validators import AnalysisValidator
        
        AnalysisValidator.validate_suspicion_score(score)
