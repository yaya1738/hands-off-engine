"""
LLM Intelligence Layer for Hands-Off Trading System

Provides AI-driven market analysis using multiple LLM backends:
- Claude API (reasoning-focused, during promo)
- OpenRouter (cost-optimized fallback)
- Local models (future privacy/offline support)

Architecture:
- backend_selector: Route requests to appropriate LLM
- prompt_library: Category-specific prompt templates
- market_analyst: Main LLMMarketAnalyst class
- models/: Category-specific analysis models
- ensemble: Multi-model voting and aggregation
- cost_tracker: Token usage monitoring
- evaluation: Performance comparison vs baseline models
"""

__version__ = "0.1.0"

from .backend_selector import LLMBackend, select_backend
from .market_analyst import LLMMarketAnalyst
from .cost_tracker import CostTracker

__all__ = [
    "LLMBackend",
    "select_backend",
    "LLMMarketAnalyst",
    "CostTracker",
]
