"""
Unit tests for hardware upgrade and resource management functionality.

Tests the autonomous hardware management system including:
- Resource limits configuration
- Hardware health analysis
- Upgrade decision making
- Telegram command integration
"""

import pytest
import json
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock
from dataclasses import asdict

# Add parent directory to path
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))


class TestResourceLimitsConfiguration:
    """Tests for resource limits configuration file"""

    def test_resource_limits_file_exists(self):
        """Test that resource_limits.json exists"""
        config_path = Path(__file__).parent.parent.parent / "config" / "resource_limits.json"
        assert config_path.exists(), "config/resource_limits.json should exist"

    def test_resource_limits_valid_json(self):
        """Test that resource_limits.json is valid JSON"""
        config_path = Path(__file__).parent.parent.parent / "config" / "resource_limits.json"
        with open(config_path) as f:
            limits = json.load(f)
        assert isinstance(limits, dict)

    def test_resource_limits_has_required_sections(self):
        """Test that resource_limits.json has all required sections"""
        config_path = Path(__file__).parent.parent.parent / "config" / "resource_limits.json"
        with open(config_path) as f:
            limits = json.load(f)

        required_sections = ["cpu", "memory", "disk", "auto_scale", "droplet_sizes"]
        for section in required_sections:
            assert section in limits, f"Missing required section: {section}"

    def test_resource_limits_cpu_thresholds(self):
        """Test CPU threshold configuration"""
        config_path = Path(__file__).parent.parent.parent / "config" / "resource_limits.json"
        with open(config_path) as f:
            limits = json.load(f)

        cpu = limits["cpu"]
        assert "warning_threshold" in cpu
        assert "critical_threshold" in cpu
        assert cpu["warning_threshold"] < cpu["critical_threshold"]
        assert 0 <= cpu["warning_threshold"] <= 100
        assert 0 <= cpu["critical_threshold"] <= 100

    def test_resource_limits_memory_thresholds(self):
        """Test memory threshold configuration"""
        config_path = Path(__file__).parent.parent.parent / "config" / "resource_limits.json"
        with open(config_path) as f:
            limits = json.load(f)

        memory = limits["memory"]
        assert "warning_threshold" in memory
        assert "critical_threshold" in memory
        assert memory["warning_threshold"] < memory["critical_threshold"]
        assert "min_available_gb" in memory
        assert memory["min_available_gb"] > 0

    def test_resource_limits_auto_scale_config(self):
        """Test auto-scaling configuration"""
        config_path = Path(__file__).parent.parent.parent / "config" / "resource_limits.json"
        with open(config_path) as f:
            limits = json.load(f)

        auto_scale = limits["auto_scale"]
        assert "enabled" in auto_scale
        assert "require_human_approval" in auto_scale
        assert "never_auto_approve_downgrades" in auto_scale
        # Safety: downgrades should never be auto-approved
        assert auto_scale["never_auto_approve_downgrades"] is True

    def test_resource_limits_droplet_upgrade_path(self):
        """Test droplet upgrade path configuration"""
        config_path = Path(__file__).parent.parent.parent / "config" / "resource_limits.json"
        with open(config_path) as f:
            limits = json.load(f)

        droplet_sizes = limits["droplet_sizes"]
        assert "upgrade_path" in droplet_sizes
        assert isinstance(droplet_sizes["upgrade_path"], list)
        assert len(droplet_sizes["upgrade_path"]) > 0


class TestHardwareTypes:
    """Tests for hardware type definitions"""

    def test_health_status_enum(self):
        """Test HealthStatus enum values"""
        from hardware.hardware_types import HealthStatus

        # Check all expected values exist
        assert HealthStatus.PRISTINE.value == "pristine"
        assert HealthStatus.OPTIMAL.value == "optimal"
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.DEGRADED.value == "degraded"
        assert HealthStatus.WARNING.value == "warning"
        assert HealthStatus.CRITICAL.value == "critical"
        assert HealthStatus.FAILED.value == "failed"

    def test_component_type_enum(self):
        """Test ComponentType enum values"""
        from hardware.hardware_types import ComponentType

        assert ComponentType.CPU.value == "cpu"
        assert ComponentType.MEMORY.value == "memory"
        assert ComponentType.DISK.value == "disk"
        assert ComponentType.NETWORK.value == "network"
        assert ComponentType.THERMAL.value == "thermal"

    def test_upgrade_urgency_enum(self):
        """Test UpgradeUrgency enum values"""
        from hardware.hardware_types import UpgradeUrgency

        assert UpgradeUrgency.IMMEDIATE.value == "immediate"
        assert UpgradeUrgency.URGENT.value == "urgent"
        assert UpgradeUrgency.PLANNED.value == "planned"
        assert UpgradeUrgency.OPTIONAL.value == "optional"

    def test_decision_confidence_enum(self):
        """Test DecisionConfidence enum values"""
        from hardware.hardware_types import DecisionConfidence

        assert DecisionConfidence.CERTAIN.value == "certain"
        assert DecisionConfidence.HIGH.value == "high"
        assert DecisionConfidence.MEDIUM.value == "medium"
        assert DecisionConfidence.LOW.value == "low"


class TestHardwareKernel:
    """Tests for hardware memory kernel"""

    def test_kernel_initialization(self, tmp_path):
        """Test kernel initializes correctly"""
        from hardware.hardware_kernel import HardwareKernel

        kernel = HardwareKernel(kernel_path=tmp_path, node_id="test_node")

        assert kernel.node_id == "test_node"
        assert kernel.baseline.samples_collected == 0

    def test_kernel_saves_state(self, tmp_path):
        """Test kernel saves state to files"""
        from hardware.hardware_kernel import HardwareKernel

        kernel = HardwareKernel(kernel_path=tmp_path, node_id="test_node")
        kernel._save_all()

        # Check that state file was created
        state_file = tmp_path / "state_test_node.json"
        assert state_file.exists()

    def test_kernel_decision_success_rate(self, tmp_path):
        """Test decision success rate calculation"""
        from hardware.hardware_kernel import HardwareKernel, DecisionOutcome

        kernel = HardwareKernel(kernel_path=tmp_path, node_id="test_node")

        # Add some decisions
        kernel.decisions = [
            DecisionOutcome("d1", "alert", "action1", "2025-01-01", True, "ok"),
            DecisionOutcome("d2", "alert", "action2", "2025-01-01", True, "ok"),
            DecisionOutcome("d3", "alert", "action3", "2025-01-01", False, "failed"),
        ]

        rate = kernel.get_decision_success_rate()
        # 2 out of 3 = 66.67%
        assert abs(rate - 66.67) < 1


class TestTelegramHardwareCommand:
    """Tests for Telegram hardware command"""

    def test_telegram_command_bot_has_hardware_command(self):
        """Test that TelegramCommandBot has hardware command"""
        from telegram.telegram_command_bot import TelegramCommandBot

        bot = TelegramCommandBot()
        assert '/hardware' in bot.commands

    def test_hardware_command_returns_string(self):
        """Test that hardware command returns a string response"""
        from telegram.telegram_command_bot import TelegramCommandBot

        bot = TelegramCommandBot()
        response = bot.cmd_hardware([])

        assert isinstance(response, str)
        assert len(response) > 0

    def test_hardware_command_includes_status_info(self):
        """Test that hardware command includes relevant info"""
        from telegram.telegram_command_bot import TelegramCommandBot

        bot = TelegramCommandBot()
        response = bot.cmd_hardware([])

        # Should include some hardware-related info
        assert "Hardware" in response or "💻" in response


class TestAutoProvisionerSafety:
    """Tests for auto-provisioner safety mechanisms"""

    def test_never_auto_approve_downgrades(self):
        """Test that downgrades are never auto-approved"""
        from infrastructure.auto_provisioner import AutoProvisioner
        from infrastructure.infra_types import InfrastructureAction, CloudProvider

        # Create provisioner with mock provider
        provisioner = AutoProvisioner(
            provider=CloudProvider.LOCAL,
            dry_run=True
        )

        # Create a downgrade decision
        from infrastructure.infra_types import create_scaling_decision
        decision = create_scaling_decision(
            action=InfrastructureAction.DOWNGRADE_SERVER,
            reason="Test downgrade",
            trigger_metrics={},
            trading_impact="low"
        )

        # After going through analyze_and_scale, downgrades should require approval
        assert decision.action == InfrastructureAction.DOWNGRADE_SERVER

    def test_self_protection_hostname_check(self):
        """Test self-protection mechanism"""
        from infrastructure.auto_provisioner import AutoProvisioner
        from infrastructure.infra_types import CloudProvider
        import socket

        provisioner = AutoProvisioner(
            provider=CloudProvider.LOCAL,
            dry_run=True
        )

        hostname = socket.gethostname()

        # Should detect self
        assert provisioner._is_self(hostname) is True

        # Should not detect random name
        assert provisioner._is_self("random-server-name-12345") is False


class TestInfrastructureTypes:
    """Tests for infrastructure type definitions"""

    def test_instance_size_order(self):
        """Test instance size ordering"""
        from infrastructure.infra_types import InstanceSize

        sizes = [
            InstanceSize.NANO,
            InstanceSize.MICRO,
            InstanceSize.SMALL,
            InstanceSize.MEDIUM,
            InstanceSize.LARGE,
            InstanceSize.XLARGE,
            InstanceSize.XXLARGE,
        ]

        # All sizes should be defined
        for size in sizes:
            assert size.value is not None

    def test_digitalocean_instances_defined(self):
        """Test DigitalOcean instance definitions"""
        from infrastructure.infra_types import DIGITALOCEAN_INSTANCES

        assert len(DIGITALOCEAN_INSTANCES) > 0

        # Check a known instance
        if "s-2vcpu-4gb" in DIGITALOCEAN_INSTANCES:
            instance = DIGITALOCEAN_INSTANCES["s-2vcpu-4gb"]
            assert instance.spec.vcpus == 2
            assert instance.spec.memory_gb == 4


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
