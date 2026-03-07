import yaml
from pathlib import Path

class ConfigManager:
    def __init__(self, config_path=None):
        if config_path is None:
            config_path = Path('config/steg_hunter_config.yaml')
        else:
            config_path = Path(config_path)
        
        self.config_path = config_path
        self.config = self.load_config()
    
    def load_config(self):
        """Load configuration from YAML file"""
        if not self.config_path.exists():
            # Return default configuration
            return self.get_default_config()
        
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def get_default_config(self):
        """Return default configuration"""
        return {
            'suspicion_threshold': 50.0,
            'weights': {
                'basic': 0.2,
                'lsb': 0.5,
                'chi_square': 0.2,
                'pixel_differencing': 0.1
            },
            'output': {
                'default_format': 'json',
                'include_detailed': False
            },
            'performance': {
                'max_workers': 4,
                'chunk_size': 10
            },
            'enabled_methods': ['basic', 'lsb', 'chi_square', 'pixel_differencing']
        }
    
    def get(self, key, default=None):
        """Get configuration value by key (supports nested keys)"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def save_config(self, config=None):
        """Save configuration to YAML file"""
        if config is None:
            config = self.config
        
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
    
    def update_threshold(self, threshold):
        """Update suspicion threshold"""
        self.config['suspicion_threshold'] = threshold
        self.save_config()
