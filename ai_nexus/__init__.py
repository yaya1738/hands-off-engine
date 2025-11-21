"""
AI Nexus - Multi-provider AI task execution system for Hands-Off Engine

This module provides a flexible provider-based architecture for routing
tasks to different AI providers (ChatGPT, Claude, etc.) with support for
context files, retry logic, and structured result formats.
"""

from ai_nexus.provider_chatgpt import ChatGPTProvider

__all__ = ['ChatGPTProvider']
__version__ = '1.0.0'
