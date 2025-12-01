"""
AI Nexus - Multi-Brain Orchestration Layer for Hands-Off Engine

Coordinates multiple AI agents (Copilot, ChatGPT, Claude, etc.) with full audit trail
and ledger tracking for accountability and self-improvement.

Also provides flexible provider-based architecture for routing tasks to different
AI providers with support for context files, retry logic, and structured result formats.
"""

# Core orchestration
from .nexus import AINexus, AITask, AIResult, AIProvider, TaskPriority, TaskStatus
from .ledger import ActionLedger

# Provider implementations
try:
    from .provider_chatgpt import ChatGPTProvider
except ImportError:
    ChatGPTProvider = None

try:
    from .provider_groq import GroqProvider
except ImportError:
    GroqProvider = None

try:
    from .provider_google import GoogleProvider
except ImportError:
    GoogleProvider = None

__all__ = [
    # Core
    'AINexus', 'AITask', 'AIResult', 'AIProvider', 'TaskPriority', 'TaskStatus', 'ActionLedger',
    # Providers
    'ChatGPTProvider', 'GroqProvider', 'GoogleProvider'
]
__version__ = '2.0.0'
