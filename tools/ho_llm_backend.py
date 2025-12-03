#!/usr/bin/env python3
"""
Hands-Off LLM Backend Selector

This helper determines which LLM backend to use based on configuration
and error context. It reads termux-hands-off/config/llm_config.json and
selects the appropriate backend.

Usage:
    python3 tools/ho_llm_backend.py
        -> Prints the default backend name

    python3 tools/ho_llm_backend.py --on-error "error message"
        -> If error indicates cap/limit, walks fallback chain and selects
           the first backend whose env_key is set. Falls back to default
           if none qualify.
"""

import argparse
import json
import os
import sys
from pathlib import Path


def get_repo_root() -> Path:
    """Get the repository root directory."""
    # This script is in tools/, so repo root is parent
    return Path(__file__).resolve().parent.parent


def load_config() -> dict:
    """Load and parse the LLM configuration file."""
    repo_root = get_repo_root()
    config_path = repo_root / "termux-hands-off" / "config" / "llm_config.json"

    if not config_path.exists():
        print(f"ERROR: Configuration file not found at: {config_path}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in config file: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Failed to read config file: {e}", file=sys.stderr)
        sys.exit(1)

    # Validate required fields
    required_fields = ['default_backend', 'fallback_chain', 'backends', 'error_patterns']
    for field in required_fields:
        if field not in config:
            print(f"ERROR: Missing required field '{field}' in config", file=sys.stderr)
            sys.exit(1)

    return config


def is_cap_error(error_text: str, error_patterns: list[str]) -> bool:
    """Check if error text matches any cap/limit patterns."""
    error_lower = error_text.lower()
    return any(pattern.lower() in error_lower for pattern in error_patterns)


def is_backend_available(backend_name: str, backends: dict, require_env_key: bool = False) -> bool:
    """
    Check if a backend is available.

    Args:
        backend_name: Name of the backend to check
        backends: Dictionary of backend configurations
        require_env_key: If True, only consider backends with env_key set as available
                        (used for cap error fallback logic)

    Returns:
        True if backend is available, False otherwise
    """
    if backend_name not in backends:
        return False

    backend_config = backends[backend_name]

    # If backend has an env_key requirement, check if it's set
    if 'env_key' in backend_config:
        env_key = backend_config['env_key']
        return env_key in os.environ and os.environ[env_key].strip() != ''

    # If no env_key required
    if require_env_key:
        # When we require env_key (cap error fallback), skip backends without keys
        return False
    else:
        # Normal case: backend is always available if no key required
        return True


def select_backend(config: dict, error_text: str | None = None) -> str:
    """
    Select the appropriate backend based on configuration and error context.

    Args:
        config: The loaded configuration dictionary
        error_text: Optional error text to analyze

    Returns:
        The name of the selected backend
    """
    default_backend = config['default_backend']

    # If no error provided, return default
    if error_text is None:
        return default_backend

    # Check if error indicates a cap/limit issue
    error_patterns = config['error_patterns'].get('treat_as_cap', [])
    if not is_cap_error(error_text, error_patterns):
        # Not a cap error, use default
        return default_backend

    # It's a cap error - walk the fallback chain
    # Prefer backends with API keys configured (skip those without keys)
    fallback_chain = config['fallback_chain']
    backends = config['backends']

    for backend_name in fallback_chain:
        if is_backend_available(backend_name, backends, require_env_key=True):
            return backend_name

    # If no API-based backend is available, fall back to default
    return default_backend


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description='Select LLM backend based on configuration and error context'
    )
    parser.add_argument(
        '--on-error',
        type=str,
        default=None,
        help='Error text to analyze for cap/limit patterns'
    )

    args = parser.parse_args()

    # Load configuration
    config = load_config()

    # Select backend
    selected_backend = select_backend(config, args.on_error)

    # Print the selected backend name
    print(selected_backend)

    return 0


if __name__ == '__main__':
    sys.exit(main())
