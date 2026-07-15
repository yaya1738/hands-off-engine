"""
Compatibility wrapper for Claude ABCFC.
Redirects legacy imports to claude_abcfc_bridge.
"""

from .claude_abcfc_bridge import get_bridge


def get_claude_abcfc():
    return get_bridge()
