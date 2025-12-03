"""
AI Integration Package
======================

Provides unified integration between:
- Claude CLI (claude-code)
- GitHub Copilot (copilot)
- ChatGPT (chatgpt)
- Claude Web (claude-web)

All agents serve: Yair Siegel
"""

from .ai_nexus_hub import AINexusHub, get_hub
from .copilot_adapter import CopilotAdapter
from .chatgpt_adapter import ChatGPTAdapter

__all__ = ['AINexusHub', 'get_hub', 'CopilotAdapter', 'ChatGPTAdapter']
