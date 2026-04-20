"""
Configuration and input validation utilities.
"""
from pathlib import Path
from typing import Dict, Any, List
import yaml


class ConfigValidator:
    """Validate configuration for StegHunter."""
    
    @staticmethod
    def validate_weights(weights: Dict[str, float], tolerance: float = 0.01) -> tuple[bool, str]:
        """
        Validate that weights sum to 1.0.
        
        Args:
            weights: Dictionary of method weights
            tolerance: Acceptable deviation from 1.0
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        total_weight = sum(weights.values())
        
        if abs(total_weight - 1.0) > tolerance:
            return False, f"Weights sum to {total_weight:.3f}, must equal 1.0. Weights: {weights}"
        
        return True, ""
    
    @staticmethod
    def validate_enabled_methods(enabled_methods: List[str], valid_methods: List[str]) -> tuple[bool, str]:
        """
        Validate that all enabled methods exist.
        
        Args:
            enabled_methods: List of method names from config
            valid_methods: List of valid method names in code
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        invalid = [m for m in enabled_methods if m not in valid_methods]
        
        if invalid:
            return False, f"Invalid method names in config: {invalid}. Valid methods: {valid_methods}"
        
        return True, ""
    
    @staticmethod
    def validate_required_keys(config: Dict[str, Any], required_keys: List[str]) -> tuple[bool, str]:
        """
        Validate that all required keys exist in config.
        
        Args:
            config: Configuration dictionary
            required_keys: List of required key paths (dot notation, e.g., 'weights.lsb')
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        missing = []
        
        for key_path in required_keys:
            keys = key_path.split('.')
            value = config
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    missing.append(key_path)
                    break
        
        if missing:
            return False, f"Missing required config keys: {missing}"
        
        return True, ""
    
    @staticmethod
    def validate_performance_settings(config: Dict[str, Any]) -> tuple[bool, str]:
        """
        Validate performance settings.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        perf = config.get('performance', {})
        
        max_workers = perf.get('max_workers', 1)
        if max_workers < 1 or max_workers > 64:
            return False, f"max_workers must be 1-64, got {max_workers}"
        
        chunk_size = perf.get('chunk_size', 1)
        if chunk_size < 1:
            return False, f"chunk_size must be >= 1, got {chunk_size}"
        
        return True, ""


class AnalysisValidator:
    """Validate analysis inputs and outputs."""
    
    @staticmethod
    def validate_suspicion_score(score: float) -> tuple[bool, str]:
        """
        Validate that suspicion score is 0-100.
        
        Args:
            score: Suspicion score value
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(score, (int, float)):
            return False, f"Score must be numeric, got {type(score)}"
        
        if not 0.0 <= score <= 100.0:
            return False, f"Score must be 0-100, got {score}"
        
        return True, ""
    
    @staticmethod
    def validate_analysis_result(result: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate structure of analysis result.
        
        Args:
            result: Analysis result dictionary
            
        Returns:
            Tuple of (is_valid, list_of_warnings)
        """
        warnings = []
        
        # Check required fields
        required_fields = ['filename', 'analysis_time']
        for field in required_fields:
            if field not in result:
                warnings.append(f"Missing field: {field}")
        
        # Check method results
        if 'methods' in result and isinstance(result['methods'], dict):
            for method, method_result in result['methods'].items():
                if 'error' in method_result and isinstance(method_result.get('error'), str):
                    warnings.append(f"Method {method} failed: {method_result['error']}")
        
        return len(warnings) == 0, warnings
