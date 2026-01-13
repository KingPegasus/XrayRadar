"""
Configuration management for xrayradar
"""

import os
from typing import Any, Dict, Optional, Union


class Config:
    """Configuration class for error tracker settings"""

    def __init__(self, **kwargs):
        """
        Initialize configuration

        Args can include:
        - dsn: Data Source Name
        - debug: Enable debug mode
        - environment: Environment name
        - release: Release version
        - server_name: Server name
        - sample_rate: Sampling rate (0.0 to 1.0)
        - max_breadcrumbs: Maximum number of breadcrumbs
        - timeout: HTTP timeout
        - verify_ssl: Whether to verify SSL certificates
        - max_payload_size: Maximum payload size in bytes
        """
        # Set defaults
        self.dsn = kwargs.get('dsn') or os.getenv('XRAYRADAR_DSN')
        self.debug = kwargs.get('debug', False) or os.getenv(
            'XRAYRADAR_DEBUG', '').lower() in ('true', '1', 'yes')
        self.environment = kwargs.get('environment') or os.getenv(
            'XRAYRADAR_ENVIRONMENT', 'development')
        self.release = kwargs.get('release') or os.getenv(
            'XRAYRADAR_RELEASE')
        self.server_name = kwargs.get('server_name') or os.getenv(
            'XRAYRADAR_SERVER_NAME', self._get_default_server_name())
        self.sample_rate = float(kwargs.get('sample_rate', 1.0) or os.getenv(
            'XRAYRADAR_SAMPLE_RATE', 1.0))
        self.max_breadcrumbs = int(kwargs.get('max_breadcrumbs', 100) or os.getenv(
            'XRAYRADAR_MAX_BREADCRUMBS', 100))

        # Transport settings
        self.timeout = float(kwargs.get('timeout', 10.0)
                             or os.getenv('XRAYRADAR_TIMEOUT', 10.0))
        self.verify_ssl = kwargs.get('verify_ssl', True) and os.getenv(
            'XRAYRADAR_VERIFY_SSL', '').lower() not in ('false', '0', 'no')
        self.max_payload_size = int(kwargs.get(
            'max_payload_size', 100 * 1024) or os.getenv('XRAYRADAR_MAX_PAYLOAD_SIZE', 100 * 1024))

        # Validate configuration
        self._validate()

    def _get_default_server_name(self) -> str:
        """Get default server name"""
        try:
            import socket
            return socket.gethostname()
        except Exception:
            return 'unknown'

    def _validate(self):
        """Validate configuration values"""
        if self.sample_rate < 0.0 or self.sample_rate > 1.0:
            raise ValueError("sample_rate must be between 0.0 and 1.0")

        if self.max_breadcrumbs < 0:
            raise ValueError("max_breadcrumbs must be non-negative")

        if self.timeout <= 0:
            raise ValueError("timeout must be positive")

        if self.max_payload_size <= 0:
            raise ValueError("max_payload_size must be positive")

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'dsn': self.dsn,
            'debug': self.debug,
            'environment': self.environment,
            'release': self.release,
            'server_name': self.server_name,
            'sample_rate': self.sample_rate,
            'max_breadcrumbs': self.max_breadcrumbs,
            'timeout': self.timeout,
            'verify_ssl': self.verify_ssl,
            'max_payload_size': self.max_payload_size,
        }

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "Config":
        """Create configuration from dictionary"""
        return cls(**config_dict)

    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables"""
        return cls()


def load_config(config_source: Optional[Union[Dict[str, Any], str, Config]] = None) -> Config:
    """
    Load configuration from various sources

    Args:
        config_source: Configuration source - can be:
            - Dict[str, Any]: Configuration dictionary
            - str: Path to configuration file (JSON/YAML)
            - Config: Existing Config instance
            - None: Load from environment variables

    Returns:
        Config instance
    """
    if config_source is None:
        return Config.from_env()
    elif isinstance(config_source, Config):
        return config_source
    elif isinstance(config_source, dict):
        return Config.from_dict(config_source)
    elif isinstance(config_source, str):
        # Load from file
        return _load_config_from_file(config_source)
    else:
        raise TypeError(
            f"Unsupported config source type: {type(config_source)}")


def _load_config_from_file(file_path: str) -> Config:
    """Load configuration from file"""
    import json
    import yaml

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Configuration file not found: {file_path}")

    with open(file_path, 'r') as f:
        if file_path.endswith('.json'):
            config_dict = json.load(f)
        elif file_path.endswith(('.yml', '.yaml')):
            config_dict = yaml.safe_load(f)
        else:
            raise ValueError(
                f"Unsupported configuration file format: {file_path}")

    return Config.from_dict(config_dict)
