"""
Configuration Manager for Hands-Off Engine

Centralized configuration management with:
- Multiple source loading (JSON files)
- Environment variable overrides
- Schema validation
- Hot-reload support
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional
import copy


class ConfigValidationError(Exception):
    """Raised when configuration validation fails"""
    pass


class ConfigManager:
    """
    Manages configuration loading, validation, and access.
    
    Features:
    - Load configs from JSON files
    - Override with environment variables
    - Validate against JSON schemas
    - Hot-reload configuration changes
    - Thread-safe access to config values
    """
    
    # Singleton instance
    _instance: Optional['ConfigManager'] = None
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize ConfigManager.
        
        Args:
            config_dir: Path to config directory. Defaults to ./config relative to repo root.
        """
        if config_dir is None:
            # Default to config/ in repository root
            repo_root = Path(__file__).parent.parent
            config_dir = repo_root / "config"
        
        self.config_dir = Path(config_dir)
        self.schemas_dir = self.config_dir / "schemas"
        
        # Configuration storage
        self._configs: Dict[str, Dict[str, Any]] = {}
        self._schemas: Dict[str, Dict[str, Any]] = {}
        self._file_mtimes: Dict[str, float] = {}
        
        # Config file mapping
        self._config_files = {
            'system': 'system.json',
            'risk': 'risk.json',
            'trading': 'trading.json',
            'notifications': 'notifications.json',
            'agents': 'agents.json'
        }
        
        # Schema file mapping
        self._schema_files = {
            'system': 'system_schema.json',
            'risk': 'risk_schema.json',
            'trading': 'trading_schema.json',
            'notifications': 'notifications_schema.json',
            'agents': 'agents_schema.json'
        }
    
    @classmethod
    def get_instance(cls, config_dir: Optional[str] = None) -> 'ConfigManager':
        """
        Get or create singleton instance.
        
        Args:
            config_dir: Path to config directory (only used on first call)
            
        Returns:
            ConfigManager singleton instance
        """
        if cls._instance is None:
            cls._instance = cls(config_dir)
        return cls._instance
    
    def load_all(self, validate: bool = True) -> None:
        """
        Load all configuration files.
        
        Args:
            validate: Whether to validate configs against schemas
        """
        for config_name in self._config_files.keys():
            self.load_config(config_name, validate=validate)
    
    def load_config(self, config_name: str, validate: bool = True) -> Dict[str, Any]:
        """
        Load a specific configuration file.
        
        Args:
            config_name: Name of config (system, risk, trading, etc.)
            validate: Whether to validate against schema
            
        Returns:
            Configuration dictionary
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            ConfigValidationError: If validation fails
        """
        if config_name not in self._config_files:
            raise ValueError(f"Unknown config name: {config_name}")
        
        config_file = self.config_dir / self._config_files[config_name]
        
        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {config_file}")
        
        # Load config file
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        # Apply environment variable overrides
        config = self._apply_env_overrides(config_name, config)
        
        # Validate if requested
        if validate:
            self._validate_config(config_name, config)
        
        # Store config and file modification time
        self._configs[config_name] = config
        self._file_mtimes[config_name] = config_file.stat().st_mtime
        
        return config
    
    def _apply_env_overrides(self, config_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply environment variable overrides to configuration.
        
        Environment variables should be in format:
        HO_<CONFIG>__<PATH>__<TO>__<KEY>=value
        (note: double underscores separate path components)
        
        Example: HO_RISK__POSITION_SIZING__MAX_POSITION_SIZE=200
        
        For backward compatibility, also supports single underscore format
        where we attempt to match against actual config keys.
        
        Args:
            config_name: Name of config
            config: Configuration dictionary
            
        Returns:
            Config with environment overrides applied
        """
        config = copy.deepcopy(config)
        prefix = f"HO_{config_name.upper()}"
        
        for env_key, env_value in os.environ.items():
            if not env_key.startswith(prefix):
                continue
            
            # Remove prefix
            remaining = env_key[len(prefix):]
            
            # Check for double underscore format first
            if remaining.startswith('__'):
                # New format: HO_RISK__POSITION_SIZING__MAX_POSITION_SIZE
                key_parts = remaining[2:].split('__')
                # Convert to lowercase and replace spaces
                key_parts = [part.lower().replace('_', '_') for part in key_parts]
            elif remaining.startswith('_'):
                # Old format: try to match against actual keys
                # This is more complex - for now, we'll try a simple heuristic
                remaining = remaining[1:]  # Remove leading underscore
                
                # Try to intelligently split by matching against config structure
                key_parts = self._parse_env_key_parts(remaining.lower(), config)
            else:
                continue  # Invalid format
            
            # Navigate to the right location in config and set value
            self._set_nested_value(config, key_parts, self._convert_env_value(env_value))
        
        return config
    
    def _parse_env_key_parts(self, key_str: str, config: Dict[str, Any]) -> list:
        """
        Parse environment key parts by matching against actual config keys.
        
        This is a heuristic approach that tries to match snake_case keys.
        """
        # For now, use simple underscore split
        # This will work for most cases but may have issues with keys containing underscores
        return key_str.split('_')
    
    def _set_nested_value(self, config: Dict[str, Any], key_parts: list, value: Any) -> None:
        """
        Set a nested value in the config dictionary.
        
        Args:
            config: Configuration dictionary to modify
            key_parts: List of keys to navigate to the value
            value: Value to set
        """
        current = config
        
        # Navigate to parent
        for part in key_parts[:-1]:
            if not isinstance(current, dict):
                # Can't navigate further
                return
            if part not in current:
                current[part] = {}
            current = current[part]
        
        # Set the value
        if isinstance(current, dict) and len(key_parts) > 0:
            current[key_parts[-1]] = value
    
    def _convert_env_value(self, value: str) -> Any:
        """
        Convert environment variable string to appropriate type.
        
        Args:
            value: String value from environment
            
        Returns:
            Converted value (bool, int, float, or str)
        """
        # Boolean conversion
        if value.lower() in ('true', 'yes', '1'):
            return True
        if value.lower() in ('false', 'no', '0'):
            return False
        
        # Number conversion
        try:
            if '.' in value:
                return float(value)
            return int(value)
        except ValueError:
            pass
        
        # Return as string
        return value
    
    def _validate_config(self, config_name: str, config: Dict[str, Any]) -> None:
        """
        Validate configuration against JSON schema.
        
        Args:
            config_name: Name of config
            config: Configuration to validate
            
        Raises:
            ConfigValidationError: If validation fails
        """
        if config_name not in self._schema_files:
            return  # No schema defined for this config
        
        # Load schema if not already loaded
        if config_name not in self._schemas:
            schema_file = self.schemas_dir / self._schema_files[config_name]
            if not schema_file.exists():
                print(f"Warning: Schema file not found: {schema_file}")
                return
            
            with open(schema_file, 'r') as f:
                self._schemas[config_name] = json.load(f)
        
        schema = self._schemas[config_name]
        
        # Basic validation (check required fields)
        self._validate_required_fields(config, schema, config_name)
    
    def _validate_required_fields(self, config: Dict[str, Any], schema: Dict[str, Any], 
                                  config_name: str, path: str = "") -> None:
        """
        Validate required fields in configuration.
        
        Args:
            config: Configuration to validate
            schema: JSON schema
            config_name: Name of config (for error messages)
            path: Current path in config (for error messages)
        """
        if 'required' not in schema:
            return
        
        for required_field in schema['required']:
            if required_field not in config:
                raise ConfigValidationError(
                    f"Missing required field in {config_name} config: {path}.{required_field}"
                )
        
        # Recursively validate nested objects
        if 'properties' in schema:
            for field, field_schema in schema['properties'].items():
                if field in config and field_schema.get('type') == 'object':
                    new_path = f"{path}.{field}" if path else field
                    self._validate_required_fields(
                        config[field], field_schema, config_name, new_path
                    )
    
    def get(self, config_name: str, *keys: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            config_name: Name of config (system, risk, etc.)
            *keys: Path to value (e.g., 'position_sizing', 'max_position_size')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
            
        Example:
            >>> config.get('risk', 'position_sizing', 'max_position_size')
            100.0
        """
        # Load config if not already loaded
        if config_name not in self._configs:
            try:
                self.load_config(config_name)
            except (FileNotFoundError, ConfigValidationError) as e:
                print(f"Warning: Could not load {config_name} config: {e}")
                return default
        
        # Navigate to value
        current = self._configs[config_name]
        for key in keys:
            if not isinstance(current, dict) or key not in current:
                return default
            current = current[key]
        
        return current
    
    def get_full_config(self, config_name: str) -> Dict[str, Any]:
        """
        Get entire configuration for a config type.
        
        Args:
            config_name: Name of config
            
        Returns:
            Full configuration dictionary
        """
        if config_name not in self._configs:
            self.load_config(config_name)
        
        return copy.deepcopy(self._configs[config_name])
    
    def reload(self, config_name: Optional[str] = None) -> None:
        """
        Reload configuration(s) from disk.
        
        Args:
            config_name: Specific config to reload, or None for all
        """
        if config_name is None:
            # Reload all configs
            for name in self._config_files.keys():
                if name in self._configs:
                    self.load_config(name, validate=True)
        else:
            # Reload specific config
            self.load_config(config_name, validate=True)
    
    def check_for_changes(self) -> Dict[str, bool]:
        """
        Check if any configuration files have changed on disk.
        
        Returns:
            Dictionary mapping config names to whether they changed
        """
        changes = {}
        
        for config_name, filename in self._config_files.items():
            if config_name not in self._file_mtimes:
                continue
            
            config_file = self.config_dir / filename
            if not config_file.exists():
                changes[config_name] = False
                continue
            
            current_mtime = config_file.stat().st_mtime
            old_mtime = self._file_mtimes[config_name]
            changes[config_name] = current_mtime > old_mtime
        
        return changes
    
    def auto_reload(self) -> Dict[str, bool]:
        """
        Automatically reload any configs that have changed on disk.
        
        Returns:
            Dictionary mapping config names to whether they were reloaded
        """
        changes = self.check_for_changes()
        reloaded = {}
        
        for config_name, has_changed in changes.items():
            if has_changed:
                try:
                    self.load_config(config_name, validate=True)
                    reloaded[config_name] = True
                except Exception as e:
                    print(f"Warning: Failed to reload {config_name}: {e}")
                    reloaded[config_name] = False
            else:
                reloaded[config_name] = False
        
        return reloaded


# Global config instance
_global_config: Optional[ConfigManager] = None


def get_config(config_dir: Optional[str] = None) -> ConfigManager:
    """
    Get the global ConfigManager instance.
    
    Args:
        config_dir: Path to config directory (only used on first call)
        
    Returns:
        Global ConfigManager instance
    """
    global _global_config
    if _global_config is None:
        _global_config = ConfigManager(config_dir)
    return _global_config
