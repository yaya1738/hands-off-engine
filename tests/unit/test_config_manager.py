"""
Unit tests for config/manager.py

Tests the Configuration Manager system including:
- Loading configs from files
- Environment variable overrides
- Schema validation
- Hot-reload functionality
"""

import json
import os
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

# Note: pytest is not available in the environment, so we'll use basic assertions
# and structure tests to be compatible with unittest if needed

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.manager import ConfigManager, ConfigValidationError, get_config


def test_config_manager_initialization():
    """Test that ConfigManager initializes correctly."""
    manager = ConfigManager()
    assert manager.config_dir.exists()
    assert manager.schemas_dir.exists()
    assert len(manager._config_files) == 5


def test_load_risk_config():
    """Test loading the risk configuration."""
    manager = ConfigManager()
    config = manager.load_config('risk', validate=False)
    
    assert 'version' in config
    assert 'position_sizing' in config
    assert config['position_sizing']['max_position_size'] == 100.0
    assert config['position_sizing']['max_bankroll_fraction'] == 0.10


def test_load_all_configs():
    """Test loading all configurations."""
    manager = ConfigManager()
    manager.load_all(validate=False)
    
    assert 'system' in manager._configs
    assert 'risk' in manager._configs
    assert 'trading' in manager._configs
    assert 'notifications' in manager._configs
    assert 'agents' in manager._configs


def test_get_config_value():
    """Test getting specific config values."""
    manager = ConfigManager()
    
    # Get nested value
    max_pos = manager.get('risk', 'position_sizing', 'max_position_size')
    assert max_pos == 100.0
    
    # Get top-level value
    version = manager.get('risk', 'version')
    assert version == "1.0"
    
    # Get with default
    missing = manager.get('risk', 'nonexistent', 'key', default='default_value')
    assert missing == 'default_value'


def test_environment_override():
    """Test that environment variables override config values."""
    with patch.dict(os.environ, {
        'HO_RISK__POSITION_SIZING__MAX_POSITION_SIZE': '200.0'
    }):
        manager = ConfigManager()
        config = manager.load_config('risk', validate=False)
        
        # Should be overridden by env var
        assert config['position_sizing']['max_position_size'] == 200.0


def test_environment_override_boolean():
    """Test boolean environment variable conversion."""
    with patch.dict(os.environ, {
        'HO_RISK__SAFETY_LAYERS__CIRCUIT_BREAKERS': 'false'
    }):
        manager = ConfigManager()
        config = manager.load_config('risk', validate=False)
        
        # Should be converted to boolean
        assert config['safety_layers']['circuit_breakers'] is False


def test_validate_config():
    """Test configuration validation against schema."""
    manager = ConfigManager()
    
    # Valid config should pass
    try:
        manager.load_config('risk', validate=True)
        validation_passed = True
    except ConfigValidationError:
        validation_passed = False
    
    assert validation_passed


def test_get_full_config():
    """Test getting full configuration."""
    manager = ConfigManager()
    config = manager.get_full_config('risk')
    
    assert isinstance(config, dict)
    assert 'position_sizing' in config
    assert 'entry_thresholds' in config
    assert 'daily_limits' in config


def test_singleton_pattern():
    """Test that get_config returns singleton instance."""
    config1 = get_config()
    config2 = get_config()
    
    assert config1 is config2


def test_config_reload():
    """Test reloading configuration."""
    manager = ConfigManager()
    
    # Load initial config
    config1 = manager.get_full_config('risk')
    
    # Reload
    manager.reload('risk')
    
    # Should still have same values (no changes to file)
    config2 = manager.get_full_config('risk')
    assert config1['version'] == config2['version']


def test_check_for_changes():
    """Test checking for file changes."""
    manager = ConfigManager()
    
    # Load config to establish baseline
    manager.load_config('risk')
    
    # Check for changes (should be none)
    changes = manager.check_for_changes()
    assert 'risk' in changes
    assert changes['risk'] is False


def test_convert_env_value():
    """Test environment value conversion."""
    manager = ConfigManager()
    
    # Test boolean conversion
    assert manager._convert_env_value('true') is True
    assert manager._convert_env_value('false') is False
    assert manager._convert_env_value('yes') is True
    assert manager._convert_env_value('no') is False
    
    # Test number conversion
    assert manager._convert_env_value('100') == 100
    assert manager._convert_env_value('100.5') == 100.5
    
    # Test string passthrough
    assert manager._convert_env_value('hello') == 'hello'


def test_missing_config_file():
    """Test handling of missing config file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = ConfigManager(tmpdir)
        
        try:
            manager.load_config('risk')
            file_error_raised = False
        except FileNotFoundError:
            file_error_raised = True
        
        assert file_error_raised


def test_invalid_config_name():
    """Test handling of invalid config name."""
    manager = ConfigManager()
    
    try:
        manager.load_config('nonexistent_config')
        error_raised = False
    except ValueError:
        error_raised = True
    
    assert error_raised


def test_nested_environment_overrides():
    """Test deeply nested environment variable overrides."""
    with patch.dict(os.environ, {
        'HO_RISK__ENTRY_THRESHOLDS__PRICE_BOUNDARIES__MIN_PRICE': '0.10'
    }):
        manager = ConfigManager()
        config = manager.load_config('risk', validate=False)
        
        # Should override nested value
        assert config['entry_thresholds']['price_boundaries']['min_price'] == 0.10


def run_all_tests():
    """Run all tests and report results."""
    tests = [
        test_config_manager_initialization,
        test_load_risk_config,
        test_load_all_configs,
        test_get_config_value,
        test_environment_override,
        test_environment_override_boolean,
        test_validate_config,
        test_get_full_config,
        test_singleton_pattern,
        test_config_reload,
        test_check_for_changes,
        test_convert_env_value,
        test_missing_config_file,
        test_invalid_config_name,
        test_nested_environment_overrides,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            print(f"✓ {test.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__}: Unexpected error: {e}")
            failed += 1
    
    print(f"\n{passed} passed, {failed} failed")
    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
