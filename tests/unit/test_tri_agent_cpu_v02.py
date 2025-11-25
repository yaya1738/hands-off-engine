"""
Tests for Spark Plug v0.2 - Continuous CPU + Kernel Updates

Tests continuous mode caps and kernel auto-update functionality.
All tests are offline (no real LLM calls).
"""

import pytest
import json
import time
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime

# Add repo root to path
import sys
REPO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from ai_nexus.spark_plug_types import CpuInstance, CpuConfig, CpuMessage, MemoryKernel
from ai_nexus.tri_agent_session_runner import TriAgentSession
from ai_nexus.memory_kernels import create_kernel, load_kernel, save_kernel


@pytest.fixture
def temp_test_dir(tmp_path):
    """Create a temporary test directory"""
    return tmp_path


@pytest.fixture
def mock_agent_providers():
    """Mock agent providers to avoid real LLM calls"""
    def fake_chatgpt(agent_id, prior_messages, session_goal):
        return {
            "content": f"Fake ChatGPT response for: {session_goal}",
            "model": "fake-gpt-4",
            "tokens": 50,
            "cost_usd": 0.001
        }

    def fake_claude(agent_id, prior_messages, session_goal):
        return {
            "content": f"Fake Claude response for: {session_goal}",
            "model": "fake-claude-3",
            "tokens": 60,
            "cost_usd": 0.002
        }

    return {
        "chatgpt": fake_chatgpt,
        "claude_cli": fake_claude
    }


def test_continuous_mode_stops_on_max_steps(temp_test_dir, mock_agent_providers):
    """Test that continuous mode stops when max-steps is reached"""
    # Patch REPO_ROOT and agent providers
    with patch('ai_nexus.tri_agent_session_runner.REPO_ROOT', temp_test_dir), \
         patch('ai_nexus.tri_agent_session_runner.AGENT_PROVIDERS', mock_agent_providers):

        # Create session in continuous mode
        session = TriAgentSession(
            conversation_id="test_max_steps",
            session_goal="Test max steps cap",
            continuous=True,
            max_steps=3,
            max_duration_seconds=9999
        )

        # Run continuous session
        session.run_continuous_session(agents=["chatgpt", "claude_cli"])

        # Check that exactly 3 steps were completed
        assert session.cpu.steps_completed == 3
        assert session.cpu.status == "stopped"

        # Verify messages were written
        messages = session.load_thread()
        # 3 steps × 2 agents = 6 messages
        assert len(messages) == 6


def test_continuous_mode_stops_on_max_duration(temp_test_dir, mock_agent_providers):
    """Test that continuous mode stops when max-duration-seconds is reached"""
    # Patch REPO_ROOT and agent providers
    with patch('ai_nexus.tri_agent_session_runner.REPO_ROOT', temp_test_dir), \
         patch('ai_nexus.tri_agent_session_runner.AGENT_PROVIDERS', mock_agent_providers):

        # Create session with very short duration (1 second)
        session = TriAgentSession(
            conversation_id="test_max_duration",
            session_goal="Test max duration cap",
            continuous=True,
            max_steps=9999,
            max_duration_seconds=1
        )

        # Run continuous session (should stop after ~1 second)
        start = time.time()
        session.run_continuous_session(agents=["chatgpt"])
        elapsed = time.time() - start

        # Should have stopped due to duration, not steps
        assert session.cpu.steps_completed < 9999
        assert session.cpu.duration_seconds >= 1.0
        assert elapsed <= 3.0  # Allow some overhead, but should be close to 1s
        assert session.cpu.status == "stopped"


def test_kernel_update_append_notes(temp_test_dir, mock_agent_providers):
    """Test that kernel updates are applied in append_notes mode"""
    # Patch REPO_ROOT and agent providers
    with patch('ai_nexus.tri_agent_session_runner.REPO_ROOT', temp_test_dir), \
         patch('ai_nexus.tri_agent_session_runner.AGENT_PROVIDERS', mock_agent_providers):

        # Create a test kernel
        kernels_dir = temp_test_dir / "ai" / "memory" / "kernels"
        kernels_dir.mkdir(parents=True, exist_ok=True)

        # Patch KERNELS_DIR in memory_kernels module
        with patch('ai_nexus.memory_kernels.KERNELS_DIR', kernels_dir):
            kernel = create_kernel(
                kernel_id="test_kernel_update",
                topic="Test Kernel",
                summary="Initial summary"
            )

            # Create session with kernel binding and append_notes mode
            session = TriAgentSession(
                conversation_id="test_kernel_updates",
                session_goal="Test kernel updates",
                bound_kernels=["test_kernel_update"],
                continuous=True,
                max_steps=2,
                max_duration_seconds=9999,
                kernel_update_mode="append_notes"
            )

            # Run continuous session
            session.run_continuous_session(agents=["chatgpt"])

            # Check that kernel updates were applied
            assert session.cpu.kernel_updates_applied == True

            # Load kernel and verify update was written
            updated_kernel = load_kernel("test_kernel_update")
            assert updated_kernel is not None
            # The summary_edit update should have modified the summary
            assert "test_kernel_updates" in updated_kernel.summary or len(updated_kernel.raw_refs) > 0


def test_burst_mode_backward_compatibility(temp_test_dir, mock_agent_providers):
    """Test that burst mode (v0.1) still works unchanged"""
    # Patch REPO_ROOT and agent providers
    with patch('ai_nexus.tri_agent_session_runner.REPO_ROOT', temp_test_dir), \
         patch('ai_nexus.tri_agent_session_runner.AGENT_PROVIDERS', mock_agent_providers):

        # Create session in burst mode (continuous=False)
        session = TriAgentSession(
            conversation_id="test_burst_compat",
            session_goal="Test backward compatibility",
            continuous=False,
            max_rounds=2
        )

        # Run burst session (old way)
        session.run_session(agents=["chatgpt", "claude_cli"], rounds=2)

        # Check that burst mode completed correctly
        assert session.cpu.mode == "burst"
        assert session.metadata['rounds_completed'] == 2
        assert session.cpu.status == "stopped"


def test_cpu_instance_v02_fields():
    """Test that CpuInstance has v0.2 fields"""
    cpu = CpuInstance(
        cpu_id="test_cpu",
        mode="continuous",
        config=CpuConfig(max_steps=10, max_duration_seconds=60)
    )

    # Check v0.2 fields exist
    assert hasattr(cpu, 'steps_completed')
    assert hasattr(cpu, 'duration_seconds')
    assert hasattr(cpu, 'kernel_updates_applied')
    assert cpu.steps_completed == 0
    assert cpu.duration_seconds == 0.0
    assert cpu.kernel_updates_applied == False

    # Check config has v0.2 caps
    assert cpu.config.max_steps == 10
    assert cpu.config.max_duration_seconds == 60


def test_cpu_instance_serialization_v02():
    """Test that CpuInstance with v0.2 fields serializes/deserializes correctly"""
    cpu = CpuInstance(
        cpu_id="test_cpu_v02",
        mode="continuous",
        steps_completed=5,
        duration_seconds=12.5,
        kernel_updates_applied=True,
        config=CpuConfig(max_steps=20, max_duration_seconds=900)
    )

    # Serialize to JSON
    cpu_json = cpu.to_json()
    cpu_dict = json.loads(cpu_json)

    # Check v0.2 fields in dict
    assert cpu_dict['steps_completed'] == 5
    assert cpu_dict['duration_seconds'] == 12.5
    assert cpu_dict['kernel_updates_applied'] == True
    assert cpu_dict['config']['max_steps'] == 20
    assert cpu_dict['config']['max_duration_seconds'] == 900

    # Deserialize and verify
    cpu_reloaded = CpuInstance.from_json(cpu_json)
    assert cpu_reloaded.steps_completed == 5
    assert cpu_reloaded.duration_seconds == 12.5
    assert cpu_reloaded.kernel_updates_applied == True
    assert cpu_reloaded.config.max_steps == 20
    assert cpu_reloaded.config.max_duration_seconds == 900


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
