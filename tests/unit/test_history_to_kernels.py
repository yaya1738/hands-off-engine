"""
Unit tests for history_to_kernels module (Part 3: User Expansion)

Tests the history-to-kernels connector that generates kernel update prompts.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch

from ai_nexus.spark_plug_types import create_history_event, MemoryKernel, Decision
from ai_nexus import history_logger, history_to_kernels, spark_plug_history
from ai_nexus.memory_kernels import save_kernel


@pytest.fixture
def temp_dirs(monkeypatch):
    """Create temporary directories for history and kernels"""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir)

        # Override paths
        history_dir = temp_path / "history"
        history_dir.mkdir(parents=True)

        legacy_history_file = history_dir / "user_events.jsonl"
        new_history_file = history_dir / "events.jsonl"
        kernels_dir = temp_path / "kernels"

        # Monkeypatch old history logger
        monkeypatch.setattr(history_logger, "HISTORY_FILE", legacy_history_file)
        monkeypatch.setattr("ai_nexus.memory_kernels.KERNELS_DIR", kernels_dir)

        # Monkeypatch unified history loader (spark_plug_history)
        monkeypatch.setattr(spark_plug_history, "REPO_ROOT", temp_path)
        monkeypatch.setattr(spark_plug_history, "NEW_HISTORY_FILE", new_history_file)
        monkeypatch.setattr(spark_plug_history, "LEGACY_HISTORY_FILE", legacy_history_file)

        yield {
            "history_file": legacy_history_file,
            "kernels_dir": kernels_dir
        }


@pytest.fixture
def sample_history(temp_dirs):
    """Create sample history events"""
    events = [
        create_history_event(
            event_type="user_message",
            source="user:froggy",
            content="What's the current Kelly fraction?",
            kernel_id="risk_model_v2"
        ),
        create_history_event(
            event_type="system_decision",
            source="cpu_risk_01",
            content="Updated Kelly fraction to 0.15 based on drawdown analysis",
            kernel_id="risk_model_v2"
        ),
        create_history_event(
            event_type="observation",
            source="monitoring",
            content="System running smoothly, no alerts",
        ),
        create_history_event(
            event_type="user_message",
            source="user:froggy",
            content="Can we increase position size?",
            kernel_id="risk_model_v2"
        ),
    ]

    for event in events:
        history_logger.append_history_event(event)

    return events


@pytest.fixture
def sample_kernel(temp_dirs):
    """Create sample memory kernel"""
    kernel = MemoryKernel(
        kernel_id="risk_model_v2",
        topic="Risk Management Model",
        summary="Manages position sizing and risk limits using Kelly criterion",
        key_decisions=[
            Decision(
                decision="Set initial Kelly fraction to 0.12",
                rationale="Conservative start for staged rollout",
                source="cpu_risk_01",
                date="2025-11-25T10:00:00Z"
            )
        ],
        failed_paths=[],
        open_questions=["What should be the maximum Kelly fraction cap?"]
    )

    save_kernel(kernel)
    return kernel


class TestHistoryToKernels:
    """Test history-to-kernels connector"""

    def test_build_history_summary_empty(self, temp_dirs):
        """Test building summary with no history"""
        summary = history_to_kernels.build_history_summary(max_events=20)
        assert "No recent history events found" in summary

    def test_build_history_summary(self, temp_dirs, sample_history):
        """Test building history summary"""
        summary = history_to_kernels.build_history_summary(max_events=20)

        # Should contain all events
        assert "user_message" in summary
        assert "system_decision" in summary
        assert "observation" in summary
        assert "What's the current Kelly fraction?" in summary
        assert "Updated Kelly fraction to 0.15" in summary

    def test_build_history_summary_with_limit(self, temp_dirs, sample_history):
        """Test building summary with event limit"""
        summary = history_to_kernels.build_history_summary(max_events=2)

        # Should only include 2 most recent events
        lines = summary.split("\n")
        event_count = summary.count("from ")  # Each event has "from <source>"
        assert event_count == 2

    def test_build_history_summary_filter_by_type(self, temp_dirs, sample_history):
        """Test filtering by event type"""
        summary = history_to_kernels.build_history_summary(
            max_events=20,
            event_type="user_message"
        )

        # Should only contain user messages
        assert "user_message" in summary
        assert "system_decision" not in summary
        assert "What's the current Kelly fraction?" in summary
        assert "Can we increase position size?" in summary

    def test_build_history_summary_filter_by_kernel(self, temp_dirs, sample_history):
        """Test filtering by kernel_id"""
        summary = history_to_kernels.build_history_summary(
            max_events=20,
            kernel_id="risk_model_v2"
        )

        # Should only include events for risk_model_v2 kernel
        assert "What's the current Kelly fraction?" in summary
        assert "Updated Kelly fraction to 0.15" in summary
        # Should NOT include the monitoring observation (no kernel_id)
        lines = summary.split("\n")
        assert "System running smoothly" not in summary

    def test_build_kernel_update_prompt(self, temp_dirs, sample_history, sample_kernel):
        """Test building kernel update prompt"""
        prompt = history_to_kernels.build_kernel_update_prompt(
            kernel_id="risk_model_v2",
            max_events=20
        )

        # Should include key sections
        assert "KERNEL UPDATE TASK" in prompt
        assert "Target Kernel: risk_model_v2" in prompt
        assert "Current Kernel State" in prompt
        assert "Recent History" in prompt
        assert "Task" in prompt

        # Should include kernel state
        assert "Risk Management Model" in prompt
        assert "Set initial Kelly fraction to 0.12" in prompt
        assert "What should be the maximum Kelly fraction cap?" in prompt

        # Should include relevant history
        assert "What's the current Kelly fraction?" in prompt
        assert "Updated Kelly fraction to 0.15" in prompt

    def test_build_kernel_update_prompt_no_kernel_state(self, temp_dirs, sample_history, sample_kernel):
        """Test prompt without kernel state"""
        prompt = history_to_kernels.build_kernel_update_prompt(
            kernel_id="risk_model_v2",
            max_events=20,
            include_kernel_state=False
        )

        # Should NOT include kernel state
        assert "Current Kernel State" not in prompt
        assert "Risk Management Model" not in prompt

        # Should still include history
        assert "Recent History" in prompt
        assert "What's the current Kelly fraction?" in prompt

    def test_build_kernel_update_prompt_nonexistent_kernel(self, temp_dirs, sample_history):
        """Test prompt for non-existent kernel"""
        prompt = history_to_kernels.build_kernel_update_prompt(
            kernel_id="nonexistent_kernel",
            max_events=20
        )

        # Should include warning
        assert "Warning" in prompt
        assert "not found" in prompt

    def test_filter_events_by_kernel(self, temp_dirs, sample_history):
        """Test filtering events by kernel"""
        all_events = history_logger.load_history_events()

        filtered = history_to_kernels.filter_events_by_kernel(
            all_events,
            kernel_id="risk_model_v2"
        )

        # Should only get events with kernel_id = risk_model_v2
        assert len(filtered) == 3  # 2 user_message + 1 system_decision
        assert all(e.context.get("kernel_id") == "risk_model_v2" for e in filtered)

    def test_suggest_kernel_topics_empty(self, temp_dirs):
        """Test suggesting topics with no history"""
        topics = history_to_kernels.suggest_kernel_topics(max_events=100)
        assert topics == []

    def test_suggest_kernel_topics(self, temp_dirs):
        """Test suggesting kernel topics from history"""
        # Add events with various topics
        events = [
            create_history_event(
                event_type="user_message",
                source="user",
                content="What's the risk exposure?",
                kernel_id="risk_model_v2"
            ),
            create_history_event(
                event_type="system_decision",
                source="cpu",
                content="Risk level adjusted due to high volatility",
            ),
            create_history_event(
                event_type="observation",
                source="monitor",
                content="Alpha signal strength increasing",
            ),
            create_history_event(
                event_type="user_message",
                source="user",
                content="Check the alpha strategy performance",
            ),
        ]

        for event in events:
            history_logger.append_history_event(event)

        topics = history_to_kernels.suggest_kernel_topics(max_events=50)

        # Should suggest risk and alpha topics
        assert "risk_model_v2" in topics  # From explicit kernel_id

    def test_suggest_kernel_topics_keyword_detection(self, temp_dirs):
        """Test keyword-based topic detection"""
        # Add multiple events with risk-related keywords
        for i in range(5):
            history_logger.append_history_event(
                create_history_event(
                    event_type="observation",
                    source="test",
                    content=f"Checking risk and drawdown metrics iteration {i}"
                )
            )

        topics = history_to_kernels.suggest_kernel_topics(max_events=50)

        # Should suggest risk topic (mentioned >= 3 times)
        assert "risk" in topics

    def test_build_history_summary_formatting(self, temp_dirs, sample_history):
        """Test that summary has proper formatting"""
        summary = history_to_kernels.build_history_summary(max_events=20)

        # Check for expected formatting elements
        assert "Recent History" in summary
        assert "=" in summary  # Header line
        assert "[" in summary  # Timestamp brackets
        assert "from " in summary  # Source indicator
        assert '"' in summary  # Content quotes

    def test_kernel_update_prompt_structure(self, temp_dirs, sample_history, sample_kernel):
        """Test prompt has all required sections"""
        prompt = history_to_kernels.build_kernel_update_prompt(
            kernel_id="risk_model_v2",
            max_events=20
        )

        # Verify all required sections are present
        required_sections = [
            "KERNEL UPDATE TASK",
            "Target Kernel:",
            "Current Kernel State",
            "Topic:",
            "Last Updated:",
            "Summary:",
            "Key Decisions:",
            "Recent History",
            "Task",
            "Consider:",
            "Output:"
        ]

        for section in required_sections:
            assert section in prompt, f"Missing section: {section}"

    def test_build_history_summary_with_complex_context(self, temp_dirs):
        """Test summary with complex context metadata"""
        event = create_history_event(
            event_type="system_decision",
            source="cpu_alpha_01",
            content="Multi-factor decision made",
            kernel_id="alpha_v2",
            confidence=0.88,
            factors=["momentum", "volatility"],
            model_version="v2.1"
        )
        history_logger.append_history_event(event)

        summary = history_to_kernels.build_history_summary(max_events=10)

        # Should include context
        assert "kernel_id=alpha_v2" in summary
        assert "confidence=0.88" in summary


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
