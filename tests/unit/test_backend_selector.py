"""Unit tests for LLM backend selector"""
import os
import sys
from pathlib import Path

# Add llm module to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from llm.backend_selector import (
    Backend,
    BackendConfig,
    LLMBackend,
    TaskType,
    Priority,
    select_backend,
    get_backend_info,
    BACKEND_REGISTRY,
)
import pytest


@pytest.mark.unit
class TestBackendSelector:
    """Test suite for LLM backend selection logic"""

    def test_backend_enum_values(self):
        """Backend enum should have expected values"""
        assert Backend.CLAUDE_API == "claude-api"
        assert Backend.OPENROUTER_GPT4 == "openrouter-gpt4"
        assert Backend.FALLBACK_NAIVE == "fallback-naive"

    def test_backend_registry_has_all_backends(self):
        """Registry should include all defined backends"""
        for backend in Backend:
            assert backend in BACKEND_REGISTRY

    def test_backend_config_structure(self):
        """BackendConfig should have required fields"""
        config = BACKEND_REGISTRY[Backend.CLAUDE_API]

        assert hasattr(config, 'name')
        assert hasattr(config, 'api_key_env')
        assert hasattr(config, 'cost_per_1k_tokens')
        assert hasattr(config, 'avg_latency_ms')
        assert hasattr(config, 'quality_score')
        assert hasattr(config, 'available')

        # Validate types
        assert isinstance(config.cost_per_1k_tokens, (int, float))
        assert isinstance(config.avg_latency_ms, int)
        assert isinstance(config.quality_score, float)
        assert isinstance(config.available, bool)

    def test_backend_selector_initialization(self):
        """LLMBackend should initialize with default priority"""
        selector = LLMBackend()

        assert selector.default_priority == Priority.QUALITY

        selector_speed = LLMBackend(default_priority=Priority.SPEED)
        assert selector_speed.default_priority == Priority.SPEED

    def test_select_backend_with_no_api_keys(self, monkeypatch):
        """When no API keys available, should fall back to naive"""
        # Clear all API key env vars
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

        selector = LLMBackend()
        backend = selector.select_backend(TaskType.ANALYSIS, Priority.QUALITY)

        # Should fall back to naive when no backends available
        assert backend == Backend.FALLBACK_NAIVE

    def test_select_backend_with_claude_key(self, monkeypatch):
        """With Claude key, should prefer Claude for quality"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

        selector = LLMBackend()
        backend = selector.select_backend(TaskType.ANALYSIS, Priority.QUALITY)

        assert backend == Backend.CLAUDE_API

    def test_select_backend_quality_priority(self, monkeypatch):
        """Quality priority should select highest quality available"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

        selector = LLMBackend()
        backend = selector.select_backend(TaskType.ANALYSIS, Priority.QUALITY)

        # Should pick Claude (quality=0.95) over others
        assert backend in [Backend.CLAUDE_API, Backend.OPENROUTER_CLAUDE]

    def test_select_backend_speed_priority(self, monkeypatch):
        """Speed priority should select fastest available"""
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

        selector = LLMBackend()
        backend = selector.select_backend(TaskType.ANALYSIS, Priority.SPEED)

        # Should pick fast model (Llama has lowest latency)
        config = selector.get_backend_config(backend)
        assert config.avg_latency_ms <= 2000  # Should be reasonably fast

    def test_select_backend_cost_priority(self, monkeypatch):
        """Cost priority should select cheapest available"""
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

        selector = LLMBackend()
        backend = selector.select_backend(TaskType.ANALYSIS, Priority.COST)

        # Should pick cheap model
        config = selector.get_backend_config(backend)
        assert config.cost_per_1k_tokens <= 0.001  # Should be very cheap

    def test_get_backend_config(self):
        """Should retrieve config for specific backend"""
        selector = LLMBackend()
        config = selector.get_backend_config(Backend.CLAUDE_API)

        assert config.name == Backend.CLAUDE_API
        assert config.quality_score == 0.95
        assert config.api_key_env == "ANTHROPIC_API_KEY"

    def test_list_available_backends_empty(self, monkeypatch):
        """With no API keys, only fallback should be available"""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

        selector = LLMBackend()
        available = selector.list_available_backends()

        # Only fallback and local (if available) should be in list
        for backend in available:
            config = BACKEND_REGISTRY[backend]
            assert config.api_key_env is None or not os.getenv(config.api_key_env)

    def test_list_available_backends_with_keys(self, monkeypatch):
        """With API keys, corresponding backends should be available"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        selector = LLMBackend()
        available = selector.list_available_backends()

        assert Backend.CLAUDE_API in available

    def test_select_backend_convenience_function(self, monkeypatch):
        """Convenience function should work without explicit instantiation"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        backend = select_backend(TaskType.ANALYSIS, Priority.QUALITY)

        assert isinstance(backend, Backend)

    def test_get_backend_info(self):
        """Should return backend information as dict"""
        info = get_backend_info(Backend.CLAUDE_API)

        assert "name" in info
        assert "available" in info
        assert "cost_per_1k_tokens" in info
        assert "avg_latency_ms" in info
        assert "quality_score" in info

        assert info["name"] == "claude-api"
        assert isinstance(info["cost_per_1k_tokens"], (int, float))

    def test_fallback_naive_always_available(self):
        """Fallback naive backend should always be available"""
        config = BACKEND_REGISTRY[Backend.FALLBACK_NAIVE]

        assert config.available is True
        assert config.api_key_env is None
        assert config.cost_per_1k_tokens == 0.0

    def test_task_type_enum(self):
        """TaskType enum should have expected values"""
        assert TaskType.ANALYSIS == "analysis"
        assert TaskType.CLASSIFICATION == "classification"
        assert TaskType.REASONING == "reasoning"
        assert TaskType.SIMPLE == "simple"

    def test_priority_enum(self):
        """Priority enum should have expected values"""
        assert Priority.COST == "cost"
        assert Priority.SPEED == "speed"
        assert Priority.QUALITY == "quality"

    def test_backend_selection_deterministic(self, monkeypatch):
        """Same inputs should produce same backend selection"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        selector = LLMBackend()

        backend1 = selector.select_backend(TaskType.ANALYSIS, Priority.QUALITY)
        backend2 = selector.select_backend(TaskType.ANALYSIS, Priority.QUALITY)

        assert backend1 == backend2
