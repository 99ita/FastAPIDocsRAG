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
    
    @property
    def output_base_dir(self) -> str:
        """Get output base directory."""
        return self.get("output.base_dir", "./output")
    
    @property
    def ingestion_output_dir(self) -> str:
        """Get ingestion output directory."""
        base_dir = self.output_base_dir
        ingestion_dir = self.get("output.ingestion_dir", "ingestion")
        return f"{base_dir}/{ingestion_dir}"
    
    @property
    def embedding_output_dir(self) -> str:
        """Get embedding output directory."""
        base_dir = self.output_base_dir
        embedding_dir = self.get("output.embedding_dir", "embedding")
        return f"{base_dir}/{embedding_dir}"
    
    @property
    def gcp_project_id(self) -> str:
        """Get GCP project ID."""
        return self.get("gcp.project_id", os.getenv("GCP_PROJECT_ID", ""))
    
    @property
    def gcp_location(self) -> str:
        """Get GCP location."""
        return self.get("gcp.location", os.getenv("GCP_LOCATION", ""))
    
    @property
    def vector_search_endpoint(self) -> str:
        """Get vector search endpoint."""
        return self.get("vector_search.endpoint", "")
    
    @property
    def vector_search_dimensions(self) -> int:
        """Get vector search dimensions."""
        return self.get("vector_search.dimensions", 768)
    
    @property
    def vector_search_top_k(self) -> int:
        """Get vector search top_k results."""
        return self.get("vector_search.top_k", 5)
    
    @property
    def gemini_model(self) -> str:
        """Get Gemini model name."""
        return self.get("gemini.model", "gemini-1.5-flash")
    
    @property
    def gemini_max_tokens(self) -> int:
        """Get Gemini max tokens."""
        return self.get("gemini.max_tokens", 4096)
    
    @property
    def gemini_temperature(self) -> float:
        """Get Gemini temperature."""
        return self.get("gemini.temperature", 0.1)
