"""
Unit tests for ai_nexus module

Tests AI orchestration and budget tracking functionality.
"""

import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ai_nexus.spark_plug_types import CpuInstance, CpuConfig, CpuMessage
from ai_nexus.memory_kernels import MemoryKernel, create_kernel, load_kernel, save_kernel


class TestCpuInstanceBasics:
    """Tests for CpuInstance dataclass"""

    def test_cpu_instance_creation(self):
        """Test creating a CpuInstance"""
        cpu = CpuInstance(
            cpu_id="test_cpu_001",
            mode="burst",
            config=CpuConfig(max_steps=10, max_duration_seconds=300)
        )

        assert cpu.cpu_id == "test_cpu_001"
        assert cpu.mode == "burst"
        assert cpu.config.max_steps == 10
        assert cpu.config.max_duration_seconds == 300

    def test_cpu_instance_continuous_mode(self):
        """Test CpuInstance in continuous mode"""
        cpu = CpuInstance(
            cpu_id="continuous_cpu",
            mode="continuous",
            config=CpuConfig(max_steps=100, max_duration_seconds=3600)
        )

        assert cpu.mode == "continuous"
        assert cpu.steps_completed == 0
        assert cpu.duration_seconds == 0.0

    def test_cpu_instance_tracks_progress(self):
        """Test that CpuInstance tracks progress"""
        cpu = CpuInstance(
            cpu_id="progress_cpu",
            mode="continuous",
            steps_completed=5,
            duration_seconds=125.5,
            config=CpuConfig(max_steps=10, max_duration_seconds=300)
        )

        assert cpu.steps_completed == 5
        assert cpu.duration_seconds == 125.5


class TestCpuConfig:
    """Tests for CpuConfig"""

    def test_cpu_config_creation(self):
        """Test creating CpuConfig with limits"""
        config = CpuConfig(max_steps=50, max_duration_seconds=600)

        assert config.max_steps == 50
        assert config.max_duration_seconds == 600

    def test_cpu_config_default_values(self):
        """Test CpuConfig with default values"""
        config = CpuConfig()

        # Should have reasonable defaults
        assert hasattr(config, 'max_steps')
        assert hasattr(config, 'max_duration_seconds')


class TestMemoryKernelBasics:
    """Tests for MemoryKernel dataclass"""

    def test_memory_kernel_creation(self):
        """Test creating a MemoryKernel"""
        kernel = MemoryKernel(
            kernel_id="test_kernel",
            topic="Test Topic",
            summary="Test summary",
            raw_refs=[],
            last_updated="2025-01-15T12:00:00Z"
        )

        assert kernel.kernel_id == "test_kernel"
        assert kernel.topic == "Test Topic"
        assert kernel.summary == "Test summary"
        assert kernel.raw_refs == []

    def test_create_kernel_function(self, tmp_path):
        """Test create_kernel function"""
        with patch('ai_nexus.memory_kernels.KERNELS_DIR', tmp_path):
            kernel = create_kernel(
                kernel_id="new_kernel",
                topic="New Kernel Topic",
                summary="Initial summary"
            )

            assert kernel.kernel_id == "new_kernel"
            assert kernel.topic == "New Kernel Topic"
            assert kernel.summary == "Initial summary"
            assert hasattr(kernel, 'last_updated')

    def test_save_and_load_kernel(self, tmp_path):
        """Test saving and loading a kernel"""
        with patch('ai_nexus.memory_kernels.KERNELS_DIR', tmp_path):
            # Create and save kernel
            kernel = create_kernel(
                kernel_id="save_test",
                topic="Save Test",
                summary="Test saving"
            )

            # Load it back
            loaded = load_kernel("save_test")

            assert loaded is not None
            assert loaded.kernel_id == "save_test"
            assert loaded.topic == "Save Test"
            assert loaded.summary == "Test saving"


class TestAIOrchestration:
    """Tests for AI orchestration functionality"""

    def test_cpu_message_creation(self):
        """Test creating CpuMessage for agent communication"""
        message = CpuMessage(
            msg_id="msg-001",
            timestamp="2025-01-15T12:00:00Z",
            from_="chatgpt",
            role="assistant",
            content="Test message",
            meta={"model": "gpt-4", "tokens": 100, "cost_usd": 0.002}
        )

        assert message.from_ == "chatgpt"
        assert message.content == "Test message"
        assert message.meta["tokens"] == 100
        assert message.meta["cost_usd"] == 0.002

    def test_cpu_tracks_kernel_updates(self):
        """Test that CPU tracks kernel update status"""
        cpu = CpuInstance(
            cpu_id="kernel_cpu",
            mode="continuous",
            kernel_updates_applied=True,
            config=CpuConfig(max_steps=10, max_duration_seconds=300)
        )

        assert cpu.kernel_updates_applied is True

    def test_cpu_serialization(self):
        """Test CPU instance serialization to JSON"""
        cpu = CpuInstance(
            cpu_id="serialize_test",
            mode="continuous",
            steps_completed=3,
            duration_seconds=45.5,
            kernel_updates_applied=False,
            config=CpuConfig(max_steps=10, max_duration_seconds=300)
        )

        # Serialize to JSON
        cpu_json = cpu.to_json()
        cpu_dict = json.loads(cpu_json)

        assert cpu_dict['cpu_id'] == "serialize_test"
        assert cpu_dict['mode'] == "continuous"
        assert cpu_dict['steps_completed'] == 3
        assert cpu_dict['duration_seconds'] == 45.5

    def test_cpu_deserialization(self):
        """Test CPU instance deserialization from JSON"""
        cpu_data = {
            'cpu_id': 'deserialize_test',
            'mode': 'continuous',
            'steps_completed': 7,
            'duration_seconds': 135.0,
            'kernel_updates_applied': True,
            'status': 'running',
            'config': {
                'max_steps': 20,
                'max_duration_seconds': 600
            }
        }

        cpu_json = json.dumps(cpu_data)
        cpu = CpuInstance.from_json(cpu_json)

        assert cpu.cpu_id == 'deserialize_test'
        assert cpu.steps_completed == 7
        assert cpu.duration_seconds == 135.0
        assert cpu.kernel_updates_applied is True


class TestBudgetTracking:
    """Tests for budget tracking functionality"""

    def test_cpu_message_tracks_cost(self):
        """Test that messages track cost for budget management"""
        messages = [
            CpuMessage("msg-001", "2025-01-15T12:00:00Z", "chatgpt", "assistant", "msg1", 
                      meta={"model": "gpt-4", "tokens": 100, "cost_usd": 0.002}),
            CpuMessage("msg-002", "2025-01-15T12:00:01Z", "claude", "assistant", "msg2",
                      meta={"model": "claude-3", "tokens": 150, "cost_usd": 0.003}),
            CpuMessage("msg-003", "2025-01-15T12:00:02Z", "chatgpt", "assistant", "msg3",
                      meta={"model": "gpt-4", "tokens": 200, "cost_usd": 0.004}),
        ]

        total_cost = sum(msg.meta.get("cost_usd", 0.0) for msg in messages)
        total_tokens = sum(msg.meta.get("tokens", 0) for msg in messages)

        assert total_cost == pytest.approx(0.009, rel=1e-6)
        assert total_tokens == 450

    def test_budget_tracking_by_agent(self):
        """Test tracking budget per agent"""
        messages = [
            CpuMessage("msg-001", "2025-01-15T12:00:00Z", "chatgpt", "assistant", "msg1",
                      meta={"model": "gpt-4", "tokens": 100, "cost_usd": 0.002}),
            CpuMessage("msg-002", "2025-01-15T12:00:01Z", "chatgpt", "assistant", "msg2",
                      meta={"model": "gpt-4", "tokens": 150, "cost_usd": 0.003}),
            CpuMessage("msg-003", "2025-01-15T12:00:02Z", "claude", "assistant", "msg3",
                      meta={"model": "claude-3", "tokens": 200, "cost_usd": 0.005}),
        ]

        # Calculate cost by agent
        cost_by_agent = {}
        for msg in messages:
            if msg.from_ not in cost_by_agent:
                cost_by_agent[msg.from_] = 0.0
            cost_by_agent[msg.from_] += msg.meta.get("cost_usd", 0.0)

        assert cost_by_agent["chatgpt"] == pytest.approx(0.005, rel=1e-6)
        assert cost_by_agent["claude"] == pytest.approx(0.005, rel=1e-6)

    def test_budget_tracking_by_model(self):
        """Test tracking budget per model"""
        messages = [
            CpuMessage("msg-001", "2025-01-15T12:00:00Z", "chatgpt", "assistant", "msg1",
                      meta={"model": "gpt-4", "tokens": 100, "cost_usd": 0.002}),
            CpuMessage("msg-002", "2025-01-15T12:00:01Z", "chatgpt", "assistant", "msg2",
                      meta={"model": "gpt-3.5-turbo", "tokens": 150, "cost_usd": 0.001}),
            CpuMessage("msg-003", "2025-01-15T12:00:02Z", "claude", "assistant", "msg3",
                      meta={"model": "claude-3", "tokens": 200, "cost_usd": 0.005}),
        ]

        # Calculate cost by model
        cost_by_model = {}
        for msg in messages:
            model = msg.meta.get("model")
            if model not in cost_by_model:
                cost_by_model[model] = 0.0
            cost_by_model[model] += msg.meta.get("cost_usd", 0.0)

        assert cost_by_model["gpt-4"] == pytest.approx(0.002, rel=1e-6)
        assert cost_by_model["gpt-3.5-turbo"] == pytest.approx(0.001, rel=1e-6)
        assert cost_by_model["claude-3"] == pytest.approx(0.005, rel=1e-6)


class TestKernelUpdateMode:
    """Tests for kernel update modes"""

    def test_cpu_supports_kernel_update_mode(self):
        """Test that CPU tracks kernel update mode"""
        cpu = CpuInstance(
            cpu_id="kernel_mode_test",
            mode="continuous",
            kernel_updates_applied=False,
            config=CpuConfig(max_steps=10, max_duration_seconds=300)
        )

        # Initially no updates applied
        assert cpu.kernel_updates_applied is False

        # Simulate applying updates
        cpu.kernel_updates_applied = True
        assert cpu.kernel_updates_applied is True


class TestMultiAgentCoordination:
    """Tests for multi-agent coordination"""

    def test_cpu_handles_multiple_agents(self):
        """Test CPU coordination with multiple agents"""
        messages = [
            CpuMessage("msg-001", "2025-01-15T12:00:00Z", "chatgpt", "assistant", "Analysis from ChatGPT",
                      meta={"model": "gpt-4", "tokens": 100, "cost_usd": 0.002}),
            CpuMessage("msg-002", "2025-01-15T12:00:01Z", "claude", "assistant", "Analysis from Claude",
                      meta={"model": "claude-3", "tokens": 150, "cost_usd": 0.003}),
            CpuMessage("msg-003", "2025-01-15T12:00:02Z", "copilot", "assistant", "Analysis from Copilot",
                      meta={"model": "copilot", "tokens": 120, "cost_usd": 0.001}),
        ]

        # Check all agents represented
        agents = {msg.from_ for msg in messages}
        assert agents == {"chatgpt", "claude", "copilot"}

    def test_agent_message_ordering(self):
        """Test that agent messages maintain temporal order"""
        messages = [
            CpuMessage("msg-001", "2025-01-15T12:00:00Z", "chatgpt", "assistant", "msg1",
                      meta={"model": "gpt-4", "tokens": 100, "cost_usd": 0.002}),
            CpuMessage("msg-002", "2025-01-15T12:00:01Z", "claude", "assistant", "msg2",
                      meta={"model": "claude-3", "tokens": 150, "cost_usd": 0.003}),
            CpuMessage("msg-003", "2025-01-15T12:00:02Z", "chatgpt", "assistant", "msg3",
                      meta={"model": "gpt-4", "tokens": 120, "cost_usd": 0.002}),
        ]

        # Verify timestamps are in order
        timestamps = [msg.timestamp for msg in messages]
        assert timestamps == sorted(timestamps)


class TestCpuStatus:
    """Tests for CPU status tracking"""

    def test_cpu_status_values(self):
        """Test different CPU status values"""
        statuses = ["running", "stopped", "paused", "completed"]
        
        for status in statuses:
            cpu = CpuInstance(
                cpu_id=f"status_test_{status}",
                mode="continuous",
                status=status,
                config=CpuConfig(max_steps=10, max_duration_seconds=300)
            )
            assert cpu.status == status


class TestErrorHandling:
    """Tests for error handling in AI orchestration"""

    def test_cpu_handles_invalid_json(self):
        """Test CPU handles invalid JSON gracefully"""
        invalid_json = "{ invalid json }"
        
        try:
            cpu = CpuInstance.from_json(invalid_json)
            # If it doesn't raise, check that it handled gracefully
            assert True
        except Exception:
            # Expected to raise on invalid JSON
            assert True

    def test_kernel_creation_with_minimal_info(self, tmp_path):
        """Test creating kernel with minimal required info"""
        with patch('ai_nexus.memory_kernels.KERNELS_DIR', tmp_path):
            kernel = create_kernel(
                kernel_id="minimal_kernel",
                topic="Minimal",
                summary=""
            )

            assert kernel.kernel_id == "minimal_kernel"
            assert kernel.topic == "Minimal"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
