"""
AI Nexus - Multi-Brain Orchestration System

Coordinates multiple AI providers (Claude, ChatGPT, Copilot) with:
- Comprehensive audit logging
- Financial tracking
- Self-improvement based on performance
- Self-financing through ROI analysis
"""
from .nexus_core import AIProvider, AIProviderType, AIRequest, AIResponse, NexusCore
from .provider_claude import ClaudeProvider
from .provider_openai import OpenAIProvider
from .provider_copilot import CopilotProvider

__all__ = [
    "AIProvider",
    "AIProviderType",
    "AIRequest",
    "AIResponse",
    "NexusCore",
    "ClaudeProvider",
    "OpenAIProvider",
    "CopilotProvider"
]
