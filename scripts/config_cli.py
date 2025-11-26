#!/usr/bin/env python3
"""
Configuration CLI for Hands-Off Engine

Utility for viewing, validating, and managing configuration files.

Usage:
    python scripts/config_cli.py view [config_name]       # View current config
    python scripts/config_cli.py validate [config_name]   # Validate config files
    python scripts/config_cli.py get <config> <keys...>   # Get specific value
    python scripts/config_cli.py diff [config_name]       # Show differences from defaults
    python scripts/config_cli.py list                     # List all configs
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.manager import ConfigManager, ConfigValidationError


def format_json(data: dict) -> str:
    """Format JSON with nice indentation."""
    return json.dumps(data, indent=2, sort_keys=False)


def view_config(manager: ConfigManager, config_name: Optional[str] = None) -> int:
    """
    View configuration(s).
    
    Args:
        manager: ConfigManager instance
        config_name: Specific config to view, or None for all
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        if config_name is None:
            # View all configs
            print("=== All Configurations ===\n")
            for name in ['system', 'risk', 'trading', 'notifications', 'agents']:
                try:
                    config = manager.get_full_config(name)
                    print(f"--- {name.upper()} ---")
                    print(format_json(config))
                    print()
                except Exception as e:
                    print(f"Error loading {name}: {e}")
                    print()
        else:
            # View specific config
            config = manager.get_full_config(config_name)
            print(f"=== {config_name.upper()} Configuration ===\n")
            print(format_json(config))
        
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def validate_config(manager: ConfigManager, config_name: Optional[str] = None) -> int:
    """
    Validate configuration(s) against schemas.
    
    Args:
        manager: ConfigManager instance
        config_name: Specific config to validate, or None for all
        
    Returns:
        Exit code (0 if all valid, 1 if any invalid)
    """
    configs_to_validate = [config_name] if config_name else ['system', 'risk', 'trading', 'notifications', 'agents']
    
    all_valid = True
    
    for name in configs_to_validate:
        try:
            manager.load_config(name, validate=True)
            print(f"✓ {name}: Valid")
        except FileNotFoundError as e:
            print(f"✗ {name}: File not found - {e}")
            all_valid = False
        except ConfigValidationError as e:
            print(f"✗ {name}: Validation failed - {e}")
            all_valid = False
        except Exception as e:
            print(f"✗ {name}: Error - {e}")
            all_valid = False
    
    if all_valid:
        print("\n✓ All configurations are valid")
        return 0
    else:
        print("\n✗ Some configurations have errors")
        return 1


def get_value(manager: ConfigManager, config_name: str, keys: list) -> int:
    """
    Get a specific configuration value.
    
    Args:
        manager: ConfigManager instance
        config_name: Name of config
        keys: List of keys to navigate to value
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        value = manager.get(config_name, *keys)
        if value is None:
            print(f"Key not found: {config_name}.{'.'.join(keys)}", file=sys.stderr)
            return 1
        
        if isinstance(value, (dict, list)):
            print(format_json(value))
        else:
            print(value)
        
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def list_configs(manager: ConfigManager) -> int:
    """
    List all available configurations.
    
    Args:
        manager: ConfigManager instance
        
    Returns:
        Exit code (0 for success)
    """
    print("Available configurations:")
    print()
    
    configs = [
        ('system', 'Core system settings'),
        ('risk', 'Risk management parameters from RISK_MODEL_V1'),
        ('trading', 'Trading settings and execution parameters'),
        ('notifications', 'Alert and notification settings'),
        ('agents', 'AI agent settings and orchestration')
    ]
    
    for name, description in configs:
        config_file = manager.config_dir / manager._config_files[name]
        exists = "✓" if config_file.exists() else "✗"
        print(f"  {exists} {name:15s} - {description}")
    
    print()
    print("Config directory:", manager.config_dir)
    print("Schemas directory:", manager.schemas_dir)
    
    return 0


def show_diff(manager: ConfigManager, config_name: Optional[str] = None) -> int:
    """
    Show differences from default configurations.
    
    Args:
        manager: ConfigManager instance
        config_name: Specific config to check, or None for all
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
    # For now, just show which values have been overridden by environment variables
    print("Environment variable overrides:")
    print()
    
    found_overrides = False
    prefix = "HO_"
    
    import os
    for key, value in sorted(os.environ.items()):
        if key.startswith(prefix):
            found_overrides = True
            print(f"  {key}={value}")
    
    if not found_overrides:
        print("  (none)")
    
    print()
    print("Note: Full diff functionality requires storing default configs separately.")
    
    return 0


def main() -> int:
    """Main entry point for config CLI."""
    parser = argparse.ArgumentParser(
        description='Configuration management CLI for Hands-Off Engine',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s list                           # List all available configs
  %(prog)s view                           # View all configs
  %(prog)s view risk                      # View risk config
  %(prog)s validate                       # Validate all configs
  %(prog)s validate risk                  # Validate risk config
  %(prog)s get risk position_sizing max_position_size  # Get specific value
  %(prog)s diff                           # Show environment overrides
"""
    )
    
    parser.add_argument(
        'command',
        choices=['list', 'view', 'validate', 'get', 'diff'],
        help='Command to execute'
    )
    
    parser.add_argument(
        'args',
        nargs='*',
        help='Additional arguments (config name, keys, etc.)'
    )
    
    parser.add_argument(
        '--config-dir',
        help='Path to config directory (default: ./config)'
    )
    
    args = parser.parse_args()
    
    # Create config manager
    try:
        manager = ConfigManager(args.config_dir)
    except Exception as e:
        print(f"Error initializing config manager: {e}", file=sys.stderr)
        return 1
    
    # Execute command
    try:
        if args.command == 'list':
            return list_configs(manager)
        
        elif args.command == 'view':
            config_name = args.args[0] if args.args else None
            return view_config(manager, config_name)
        
        elif args.command == 'validate':
            config_name = args.args[0] if args.args else None
            return validate_config(manager, config_name)
        
        elif args.command == 'get':
            if len(args.args) < 2:
                print("Error: 'get' requires config name and at least one key", file=sys.stderr)
                print("Example: config_cli.py get risk position_sizing max_position_size")
                return 1
            
            config_name = args.args[0]
            keys = args.args[1:]
            return get_value(manager, config_name, keys)
        
        elif args.command == 'diff':
            config_name = args.args[0] if args.args else None
            return show_diff(manager, config_name)
        
        else:
            print(f"Unknown command: {args.command}", file=sys.stderr)
            return 1
    
    except KeyboardInterrupt:
        print("\nInterrupted", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
