#!/usr/bin/env python3
"""
LLM Backend Selector

Routes LLM requests to the appropriate backend based on:
- Task type (analysis, classification, reasoning)
- Priority (cost, speed, quality)
- Available API keys
- Rate limits and quotas

Backends:
- claude-api: Anthropic Claude (during promo, high quality)
- openrouter: OpenRouter proxy (post-promo, cost-optimized)
- local: Local models (future, offline/privacy)
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, Optional, List


class TaskType(str, Enum):
    """Type of LLM task"""
    ANALYSIS = "analysis"          # Deep market analysis
    CLASSIFICATION = "classification"  # Category inference
    REASONING = "reasoning"        # Multi-step thinking
    SIMPLE = "simple"             # Quick responses


class Priority(str, Enum):
    """Request priority"""
    COST = "cost"      # Minimize cost (use cheap models)
    SPEED = "speed"    # Minimize latency (use fast models)
    QUALITY = "quality"  # Maximize accuracy (use best models)


class Backend(str, Enum):
    """Available LLM backends"""
    CLAUDE_API = "claude-api"
    OPENROUTER_GPT4 = "openrouter-gpt4"
    OPENROUTER_CLAUDE = "openrouter-claude"
    OPENROUTER_LLAMA = "openrouter-llama"
    LOCAL_LLAMA = "local-llama"
    FALLBACK_NAIVE = "fallback-naive"  # No LLM, use naive model


@dataclass
class BackendConfig:
    """Configuration for a specific backend"""
    name: Backend
    api_key_env: Optional[str]  # Environment variable for API key
    cost_per_1k_tokens: float  # Approximate cost in USD
    avg_latency_ms: int        # Average response time
    quality_score: float       # Subjective quality (0-1)
    available: bool = True     # Whether backend is currently available


# Backend registry with cost/performance profiles
BACKEND_REGISTRY: Dict[Backend, BackendConfig] = {
    Backend.CLAUDE_API: BackendConfig(
        name=Backend.CLAUDE_API,
        api_key_env="ANTHROPIC_API_KEY",
        cost_per_1k_tokens=0.015,  # Approximate for Claude Sonnet
        avg_latency_ms=2000,
        quality_score=0.95,
    ),
    Backend.OPENROUTER_GPT4: BackendConfig(
        name=Backend.OPENROUTER_GPT4,
        api_key_env="OPENROUTER_API_KEY",
        cost_per_1k_tokens=0.03,  # GPT-4 Turbo via OpenRouter
        avg_latency_ms=1500,
        quality_score=0.90,
    ),
    Backend.OPENROUTER_CLAUDE: BackendConfig(
        name=Backend.OPENROUTER_CLAUDE,
        api_key_env="OPENROUTER_API_KEY",
        cost_per_1k_tokens=0.015,  # Claude via OpenRouter
        avg_latency_ms=2000,
        quality_score=0.95,
    ),
    Backend.OPENROUTER_LLAMA: BackendConfig(
        name=Backend.OPENROUTER_LLAMA,
        api_key_env="OPENROUTER_API_KEY",
        cost_per_1k_tokens=0.0001,  # Very cheap
        avg_latency_ms=800,
        quality_score=0.70,
    ),
    Backend.LOCAL_LLAMA: BackendConfig(
        name=Backend.LOCAL_LLAMA,
        api_key_env=None,  # No API key needed
        cost_per_1k_tokens=0.0,  # Free
        avg_latency_ms=5000,  # Slow on CPU
        quality_score=0.65,
        available=False,  # Not implemented yet
    ),
    Backend.FALLBACK_NAIVE: BackendConfig(
        name=Backend.FALLBACK_NAIVE,
        api_key_env=None,
        cost_per_1k_tokens=0.0,
        avg_latency_ms=10,
        quality_score=0.50,  # Naive model baseline
    ),
}


class LLMBackend:
    """
    LLM Backend Selector

    Routes requests to appropriate LLM based on task type and priority.
    Gracefully falls back when API keys are missing or rate limits hit.
    """

    def __init__(self, default_priority: Priority = Priority.QUALITY):
        self.default_priority = default_priority
        self._check_available_backends()

    def _check_available_backends(self) -> None:
        """Check which backends have API keys configured"""
        for backend_config in BACKEND_REGISTRY.values():
            if backend_config.api_key_env:
                # Check if API key is set in environment
                has_key = bool(os.getenv(backend_config.api_key_env))
                backend_config.available = has_key

    def select_backend(
        self,
        task_type: TaskType = TaskType.ANALYSIS,
        priority: Optional[Priority] = None,
    ) -> Backend:
        """
        Select the best available backend for the given task and priority.

        Args:
            task_type: Type of task (analysis, classification, reasoning, simple)
            priority: Request priority (cost, speed, quality)

        Returns:
            Backend enum indicating which backend to use

        Strategy:
            - QUALITY priority: Claude API > OpenRouter Claude > GPT-4 > fallback
            - SPEED priority: OpenRouter Llama > GPT-4 > Claude > fallback
            - COST priority: Local > OpenRouter Llama > fallback
        """
        priority = priority or self.default_priority

        # Get available backends
        available = [
            config for config in BACKEND_REGISTRY.values()
            if config.available
        ]

        if not available:
            return Backend.FALLBACK_NAIVE

        # Select based on priority
        if priority == Priority.QUALITY:
            # Sort by quality score (descending)
            ranked = sorted(available, key=lambda x: x.quality_score, reverse=True)
        elif priority == Priority.SPEED:
            # Sort by latency (ascending)
            ranked = sorted(available, key=lambda x: x.avg_latency_ms)
        elif priority == Priority.COST:
            # Sort by cost (ascending)
            ranked = sorted(available, key=lambda x: x.cost_per_1k_tokens)
        else:
            ranked = available

        # Return best available
        return ranked[0].name

    def get_backend_config(self, backend: Backend) -> BackendConfig:
        """Get configuration for a specific backend"""
        return BACKEND_REGISTRY[backend]

    def list_available_backends(self) -> List[Backend]:
        """List all currently available backends"""
        return [
            config.name
            for config in BACKEND_REGISTRY.values()
            if config.available
        ]


# Singleton instance for convenience
_default_backend_selector = LLMBackend()


def select_backend(
    task_type: TaskType = TaskType.ANALYSIS,
    priority: Optional[Priority] = None,
) -> Backend:
    """
    Convenience function to select backend using default selector.

    Example:
        backend = select_backend(TaskType.ANALYSIS, Priority.QUALITY)
        if backend == Backend.CLAUDE_API:
            # Use Claude API
        elif backend == Backend.FALLBACK_NAIVE:
            # Fall back to naive model
    """
    return _default_backend_selector.select_backend(task_type, priority)


def get_backend_info(backend: Backend) -> Dict[str, Any]:
    """Get information about a specific backend"""
    config = BACKEND_REGISTRY[backend]
    return {
        "name": config.name.value,
        "available": config.available,
        "cost_per_1k_tokens": config.cost_per_1k_tokens,
        "avg_latency_ms": config.avg_latency_ms,
        "quality_score": config.quality_score,
    }
