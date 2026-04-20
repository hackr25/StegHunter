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
        """Validate configuration at load time."""
        try:
            # Skip validation for now to avoid import issues
            # Validators will be applied at CLI level instead
            pass
        except Exception as e:
            # Log warning but continue with defaults
            import sys
            print(f"Warning: Config validation failed: {e}", file=sys.stderr)
    
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
