import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from .constants import DEFAULT_CONFIG


class ConfigManager:
    """Manage StegHunter configuration from YAML files."""

    def __init__(self, config_path: Optional[str | Path] = None) -> None:
        """Initialize ConfigManager with optional config file path.
        
        Args:
            config_path: Path to config YAML file. Uses default if None.
        """
        if config_path is None:
            config_path = Path('config/steg_hunter_config.yaml')
        else:
            config_path = Path(config_path)
        
        self.config_path = config_path
        self.config: Dict[str, Any] = self.load_config()
        
        # Validate configuration on load
        self._validate_config()
    
    def _validate_config(self) -> None:
        """Validate configuration at load time.
        
        Checks:
        - Weights sum to approximately 1.0
        - All enabled methods are valid
        - Performance settings are in valid ranges
        """
        from .validators import ConfigValidator
        import logging
        
        logger = logging.getLogger(__name__)
        
        # Validate weights
        weights = self.config.get('weights', {})
        if weights:
            is_valid, error_msg = ConfigValidator.validate_weights(weights)
            if not is_valid:
                logger.warning(f"Config validation: {error_msg}")
                # Auto-normalize weights
                total = sum(weights.values())
                if total > 0:
                    for k in weights:
                        weights[k] = weights[k] / total
                    self.config['weights'] = weights
                    logger.info(f"Weights auto-normalized to sum to 1.0")
        
        # Validate enabled methods
        enabled_methods = self.config.get('enabled_methods', [])
        valid_methods = [
            'basic', 'lsb', 'chi_square', 'pixel_differencing',
            'jpeg_structure', 'metadata', 'format_validation', 'social_media',
            'ela', 'jpeg_ghost', 'noise', 'color_space', 'clone_detection',
            'video_frame_analysis', 'video_container', 'frequency_analysis'
        ]
        if enabled_methods:
            is_valid, error_msg = ConfigValidator.validate_enabled_methods(enabled_methods, valid_methods)
            if not is_valid:
                logger.warning(f"Config validation: {error_msg}")
        
        # Validate performance settings
        performance = self.config.get('performance', {})
        if performance:
            max_workers = performance.get('max_workers', 4)
            timeout = performance.get('timeout_seconds', 30)
            
            if not (1 <= max_workers <= 64):
                logger.warning(f"max_workers={max_workers} out of range [1,64], using 4")
                performance['max_workers'] = 4
                
            if not (1 <= timeout <= 300):
                logger.warning(f"timeout_seconds={timeout} out of range [1,300], using 30")
                performance['timeout_seconds'] = 30
            
            self.config['performance'] = performance
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file.
        
        Returns:
            Configuration dictionary. Returns default if file doesn't exist.
        """
        if not self.config_path.exists():
            # Return default configuration
            return self.get_default_config()
        
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def get_default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return DEFAULT_CONFIG.copy()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key (supports nested keys with dot notation).
        
        Args:
            key: Configuration key, e.g., 'performance.max_workers'
            default: Default value if key not found
            
        Returns:
            Configuration value or default
            
        Example:
            >>> config = ConfigManager()
            >>> workers = config.get('performance.max_workers', 4)
        """
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def save_config(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Save configuration to YAML file.
        
        Args:
            config: Configuration dict to save. Uses current config if None.
        """
        if config is None:
            config = self.config
        
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
    
    def update_threshold(self, threshold: float) -> None:
        """Update suspicion threshold.
        
        Args:
            threshold: New threshold value (0-100)
        """
        self.config['suspicion_threshold'] = threshold
        self.save_config()
