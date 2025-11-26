"""
Config package for Hands-Off Engine

Provides centralized configuration management with validation and hot-reload support.
"""

from .manager import ConfigManager, get_config

__all__ = ['ConfigManager', 'get_config']
