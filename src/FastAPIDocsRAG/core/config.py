"""
Configuration management for the ETVR system.
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path

from .exceptions import ConfigurationError


class Config:
    """Configuration manager for the ETVR system."""
    
    def __init__(self, config_path: Optional[str] = None, environment: str = "development"):
        """
        Initialize configuration.
        
        Args:
            config_path: Path to configuration directory
            environment: Environment name (development, production, test)
        """
        self.environment = environment
        self.config_dir = Path(config_path) if config_path else Path(__file__).parent.parent.parent.parent / "config"
        self._config_data = {}
        self._load_config()
    
    def _load_config(self):
        """Load configuration from YAML files."""
        config_file = self.config_dir / f"{self.environment}.yaml"
        
        if not config_file.exists():
            raise ConfigurationError(f"Configuration file not found: {config_file}")
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                self._config_data = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Failed to load config from {config_file}: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.
        
        Args:
            key: Configuration key (e.g., "ingestion.docs_dir")
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self._config_data
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """
        Set configuration value using dot notation.
        
        Args:
            key: Configuration key (e.g., "ingestion.docs_dir")
            value: Value to set
        """
        keys = key.split('.')
        config = self._config_data
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def save(self):
        """Save current configuration to file."""
        config_file = self.config_dir / f"{self.environment}.yaml"
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(self._config_data, f, default_flow_style=False, indent=2)
    
    @property
    def docs_dir(self) -> str:
        """Get documents directory."""
        return self.get("ingestion.docs_dir", "./docs")
    
    @property
    def docs_src_dir(self) -> str:
        """Get source code directory."""
        return self.get("ingestion.docs_src_dir", "./docs_src")
    
    @property
    def mkdocs_config(self) -> str:
        """Get MkDocs configuration file path."""
        return self.get("mkdocs.config_file", "./mkdocs.yml")
    
    @property
    def storage_type(self) -> str:
        """Get storage backend type."""
        return self.get("storage.type", "local")
    
    @property
    def embedding_type(self) -> str:
        """Get embedding backend type."""
        return self.get("embeddings.type", "local")
