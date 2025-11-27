#!/usr/bin/env python3
"""
Unit tests for self_healing_agent.py resource monitoring features.
"""

import pytest
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from self_healing_agent import ResourceMonitor, DigitalOceanManager, DEFAULT_RESOURCE_LIMITS


class TestResourceMonitor:
    """Tests for the ResourceMonitor class."""

    def test_get_cpu_usage_returns_float(self):
        """CPU usage should return a float value."""
        rm = ResourceMonitor()
        cpu = rm.get_cpu_usage()
        assert isinstance(cpu, float)
        assert 0.0 <= cpu <= 100.0

    def test_get_memory_usage_returns_dict(self):
        """Memory usage should return a dict with expected keys."""
        rm = ResourceMonitor()
        mem = rm.get_memory_usage()
        assert isinstance(mem, dict)
        assert "total_mb" in mem
        assert "used_mb" in mem
        assert "available_mb" in mem
        assert "used_percent" in mem

    def test_get_memory_usage_values_reasonable(self):
        """Memory values should be reasonable."""
        rm = ResourceMonitor()
        mem = rm.get_memory_usage()
        assert mem["total_mb"] > 0
        assert mem["available_mb"] >= 0
        assert 0 <= mem["used_percent"] <= 100

    def test_get_high_cpu_processes_returns_list(self):
        """High CPU processes should return a list."""
        rm = ResourceMonitor()
        procs = rm.get_high_cpu_processes()
        assert isinstance(procs, list)


class TestDigitalOceanManager:
    """Tests for the DigitalOceanManager class."""

    def test_is_configured_returns_false_without_env_vars(self):
        """Without env vars, should not be configured."""
        with patch.dict(os.environ, {}, clear=True):
            dom = DigitalOceanManager()
            # Need to clear the cached values
            dom.api_token = None
            dom.droplet_id = None
            assert dom.is_configured() is False

    def test_is_configured_returns_true_with_env_vars(self):
        """With env vars set, should be configured."""
        with patch.dict(os.environ, {
            "DIGITALOCEAN_API_TOKEN": "test-token",
            "DIGITALOCEAN_DROPLET_ID": "12345"
        }):
            dom = DigitalOceanManager()
            # Check if requests is available
            try:
                import requests
                assert dom.is_configured() is True
            except ImportError:
                assert dom.is_configured() is False  # No requests = not configured

    def test_get_next_size_up_returns_correct_size(self):
        """Should return the next size in the upgrade path."""
        dom = DigitalOceanManager()
        size_list = ["s-1vcpu-1gb", "s-1vcpu-2gb", "s-2vcpu-2gb"]
        max_size = "s-2vcpu-2gb"

        next_size = dom.get_next_size_up("s-1vcpu-1gb", size_list, max_size)
        assert next_size == "s-1vcpu-2gb"

        next_size = dom.get_next_size_up("s-1vcpu-2gb", size_list, max_size)
        assert next_size == "s-2vcpu-2gb"

    def test_get_next_size_up_returns_none_at_max(self):
        """Should return None when already at max size."""
        dom = DigitalOceanManager()
        size_list = ["s-1vcpu-1gb", "s-1vcpu-2gb", "s-2vcpu-2gb"]
        max_size = "s-2vcpu-2gb"

        next_size = dom.get_next_size_up("s-2vcpu-2gb", size_list, max_size)
        assert next_size is None


class TestDefaultResourceLimits:
    """Tests for default resource limit configuration."""

    def test_default_limits_has_required_keys(self):
        """Default limits should have all required configuration keys."""
        required_keys = [
            "cpu_warning_threshold",
            "cpu_critical_threshold",
            "memory_warning_threshold",
            "memory_critical_threshold",
            "auto_scale_enabled",
            "auto_kill_runaway_enabled",
            "runaway_cpu_threshold",
            "runaway_duration_seconds",
            "droplet_upgrade_sizes",
            "max_droplet_size"
        ]
        for key in required_keys:
            assert key in DEFAULT_RESOURCE_LIMITS

    def test_default_thresholds_are_sensible(self):
        """Default thresholds should be in sensible ranges."""
        assert 50 <= DEFAULT_RESOURCE_LIMITS["cpu_warning_threshold"] <= 90
        assert 80 <= DEFAULT_RESOURCE_LIMITS["cpu_critical_threshold"] <= 100
        assert 50 <= DEFAULT_RESOURCE_LIMITS["memory_warning_threshold"] <= 90
        assert 80 <= DEFAULT_RESOURCE_LIMITS["memory_critical_threshold"] <= 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
